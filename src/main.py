"""
FastAPI application for Mooring Line Monitoring System
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import asyncio

from database import get_db, init_db
from schemas import (
    MooringLineCreate, MooringLineUpdate, MooringLineResponse, MooringLineSummary,
    TensionHistoryCreate, TensionHistoryResponse, TensionTimeSeriesData,
    WeatherDataCreate, WeatherDataResponse, CurrentWeather,
    AlertResponse, DashboardData, TensionStatus
)
from services import (
    MooringLineService, TensionService, WeatherService, 
    AlertService, SimulationService
)
from models import WeatherData, MooringLine
from data_parser import initialize_mooring_lines
from live_simulation import start_live_simulation, stop_live_simulation, get_simulation_status
import threading

app = FastAPI(
    title="Mooring Line Monitoring System",
    description="API for monitoring mooring line tension and lifespan",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# This will be set up after all API routes are defined
static_path = os.path.join(os.path.dirname(__file__), "static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    # Initialize 8 mooring lines
    db = next(get_db())
    try:
        initialize_mooring_lines(db)
        print("✅ Database initialized with 8 mooring lines")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
    finally:
        db.close()


# ======================
# Mooring Line Endpoints
# ======================

@app.post("/api/mooring-lines", response_model=MooringLineResponse)
def create_mooring_line(
    data: MooringLineCreate,
    db: Session = Depends(get_db)
):
    """Create a new mooring line"""
    return MooringLineService.create_mooring_line(db, data)


@app.get("/api/mooring-lines", response_model=List[MooringLineSummary])
def get_mooring_lines(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all mooring lines with summary information (8 lines system)"""
    lines = MooringLineService.get_all_mooring_lines(db, active_only)
    
    summaries = []
    for line in lines:
        tension_percentage = (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
        # Simple status calculation
        if line.current_tension > line.reference_tension * 1.2:
            status = "WARNING"
        elif line.current_tension > line.max_tension * 0.9:
            status = "CRITICAL"
        else:
            status = "NORMAL"
        
        summaries.append(MooringLineSummary(
            id=line.id,
            line_id=line.line_id,
            name=line.name,
            side=line.side,
            position_index=line.position_index,
            current_tension=line.current_tension,
            reference_tension=line.reference_tension,
            tension_percentage=tension_percentage,
            remaining_lifespan_percentage=line.remaining_lifespan_percentage,
            status=status
        ))
    
    return summaries


@app.get("/api/mooring-lines/{line_id}", response_model=MooringLineResponse)
def get_mooring_line(
    line_id: int,
    db: Session = Depends(get_db)
):
    """Get specific mooring line details"""
    line = MooringLineService.get_mooring_line(db, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Mooring line not found")
    return line


@app.put("/api/mooring-lines/{line_id}", response_model=MooringLineResponse)
def update_mooring_line(
    line_id: int,
    data: MooringLineUpdate,
    db: Session = Depends(get_db)
):
    """Update mooring line information"""
    line = MooringLineService.update_mooring_line(db, line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Mooring line not found")
    return line


# ======================
# Tension Data Endpoints
# ======================

@app.post("/api/tension", response_model=TensionHistoryResponse)
async def record_tension(
    data: TensionHistoryCreate,
    db: Session = Depends(get_db)
):
    """Record new tension measurement"""
    tension = TensionService.record_tension(db, data)
    
    # Broadcast update via WebSocket
    await manager.broadcast({
        "type": "tension_update",
        "mooring_line_id": data.mooring_line_id,
        "tension_value": data.tension_value,
        "timestamp": tension.timestamp.isoformat()
    })
    
    return tension


@app.get("/api/tension/{line_id}/history", response_model=List[TensionTimeSeriesData])
def get_tension_history(
    line_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get tension history for a mooring line"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    return TensionService.get_tension_history(db, line_id, start_time=start_time, limit=1000)


@app.get("/api/tension/{line_id}/chart-data")
def get_tension_chart_data(
    line_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get tension data formatted for charting"""
    history = TensionService.get_tension_history(
        db, line_id, 
        start_time=datetime.utcnow() - timedelta(hours=hours),
        limit=1000
    )
    
    line = MooringLineService.get_mooring_line(db, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Mooring line not found")
    
    return {
        "mooring_line": {
            "id": line.id,
            "name": line.name,
            "reference_tension": line.reference_tension,
            "max_tension": line.max_tension
        },
        "data": [
            {
                "timestamp": item.timestamp.isoformat(),
                "tension": item.tension_value,
                "status": item.status.value,
                "temperature": item.temperature,
                "humidity": item.humidity,
                "wind_speed": item.wind_speed,
                "wind_direction": item.wind_direction
            }
            for item in history
        ]
    }


# ======================
# Weather Data Endpoints
# ======================

@app.post("/api/weather", response_model=WeatherDataResponse)
async def record_weather(
    data: WeatherDataCreate,
    db: Session = Depends(get_db)
):
    """Record weather data"""
    weather = WeatherService.record_weather(db, data)
    
    # Broadcast update via WebSocket
    await manager.broadcast({
        "type": "weather_update",
        "data": data.dict(),
        "timestamp": weather.timestamp.isoformat()
    })
    
    return weather


@app.get("/api/weather/current", response_model=CurrentWeather)
def get_current_weather(db: Session = Depends(get_db)):
    """Get current weather conditions"""
    weather = WeatherService.get_current_weather(db)
    if not weather:
        # Return default values if no weather data
        return CurrentWeather(
            temperature=20.0,
            humidity=60.0,
            wind_speed=5.0,
            wind_direction=0.0,
            wind_direction_text="N",
            pressure=1013.0,
            wave_height=1.0,
            timestamp=datetime.utcnow()
        )
    
    return CurrentWeather(
        temperature=weather.temperature,
        humidity=weather.humidity,
        wind_speed=weather.wind_speed,
        wind_direction=weather.wind_direction,
        wind_direction_text=WeatherService.get_wind_direction_text(weather.wind_direction),
        pressure=weather.pressure,
        wave_height=weather.wave_height,
        timestamp=weather.timestamp
    )


# ======================
# Alert Endpoints
# ======================

@app.get("/api/alerts", response_model=List[AlertResponse])
def get_alerts(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get system alerts"""
    if active_only:
        return AlertService.get_active_alerts(db)
    # Could add logic for all alerts
    return AlertService.get_active_alerts(db)


@app.put("/api/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Mark an alert as resolved"""
    alert = AlertService.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved", "alert_id": alert_id}


# ======================
# Dashboard Endpoint
# ======================

@app.get("/api/dashboard", response_model=DashboardData)
def get_dashboard_data(db: Session = Depends(get_db)):
    """Get all dashboard data in one request"""
    # Get mooring lines summary - direct query to avoid service issues
    try:
        lines = db.query(MooringLine).filter(MooringLine.is_active == True).all()
        line_summaries = []
        
        for line in lines:
            tension_percentage = (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
            # Simple status calculation
            if line.current_tension > line.reference_tension * 1.2:
                status = "WARNING"
            elif line.current_tension > line.max_tension * 0.9:
                status = "CRITICAL" 
            else:
                status = "NORMAL"
            
            line_summaries.append(MooringLineSummary(
                id=line.id,
                line_id=line.line_id,
                name=line.name,
                side=line.side,
                position_index=line.position_index,
                current_tension=line.current_tension,
                reference_tension=line.reference_tension,
                tension_percentage=tension_percentage,
                remaining_lifespan_percentage=line.remaining_lifespan_percentage,
                status=status
            ))
    except Exception as e:
        print(f"Error loading mooring lines: {e}")
        line_summaries = []
    
    # Get current weather
    weather = WeatherService.get_current_weather(db)
    if weather:
        current_weather = CurrentWeather(
            temperature=weather.temperature,
            humidity=weather.humidity,
            wind_speed=weather.wind_speed,
            wind_direction=weather.wind_direction,
            wind_direction_text=WeatherService.get_wind_direction_text(weather.wind_direction),
            pressure=weather.pressure,
            wave_height=weather.wave_height,
            timestamp=weather.timestamp
        )
    else:
        current_weather = CurrentWeather(
            temperature=20.0,
            humidity=60.0,
            wind_speed=5.0,
            wind_direction=0.0,
            wind_direction_text="N",
            pressure=1013.0,
            wave_height=1.0,
            timestamp=datetime.utcnow()
        )
    
    # Get active alerts (임시로 빈 배열 반환)
    try:
        alerts = AlertService.get_active_alerts(db)
    except Exception as e:
        print(f"Alert service error: {e}")
        alerts = []
    
    # System status
    system_status = {
        "active_lines": len([l for l in lines if l.is_active]),
        "total_lines": len(lines),
        "critical_alerts": len([a for a in alerts if a.severity == "CRITICAL"]),
        "warning_alerts": len([a for a in alerts if a.severity in ["HIGH", "MEDIUM"]]),
        "system_health": "OPERATIONAL"
    }
    
    return DashboardData(
        mooring_lines=line_summaries,
        current_weather=current_weather,
        active_alerts=alerts,
        system_status=system_status
    )


# ======================
# WebSocket Endpoint
# ======================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ======================
# Utility Endpoints
# ======================

@app.post("/api/simulation/generate-data")
def generate_sample_data(db: Session = Depends(get_db)):
    """Generate sample data for testing"""
    try:
        SimulationService.generate_sample_data(db)
        return {"message": "Sample data generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation/start")
async def start_simulation():
    """Start live sensor data simulation with 30-second updates"""
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), "..", "testdata_full.txt")
        
        # Check if simulation is already running
        status = get_simulation_status()
        if status["is_running"]:
            return {"message": "Simulation is already running", "status": status}
        
        # Start simulation in background thread
        def run_simulation():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_live_simulation(data_file_path, 30))
        
        simulation_thread = threading.Thread(target=run_simulation, daemon=True)
        simulation_thread.start()
        
        return {
            "message": "Live simulation started with 30-second updates",
            "data_file": data_file_path,
            "update_interval": 30,
            "status": "starting"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")


@app.post("/api/simulation/stop")
def stop_simulation():
    """Stop live sensor data simulation"""
    try:
        stop_live_simulation()
        return {"message": "Simulation stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {str(e)}")


@app.get("/api/simulation/status")
def get_simulation_status_endpoint():
    """Get current simulation status"""
    try:
        status = get_simulation_status()
        return {
            "simulation": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Mount static files at the end, after all API routes
if os.path.exists(static_path):
    from fastapi.responses import HTMLResponse
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        with open(os.path.join(static_path, "index.html"), "r") as f:
            return f.read()
    
    # Serve static files for all non-API routes
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
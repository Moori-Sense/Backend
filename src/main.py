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
import random

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
from data_parser import SensorDataParser, initialize_mooring_lines
from models import WeatherData

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
    # 8개 계류줄 초기화
    from database import SessionLocal
    db = SessionLocal()
    try:
        initialize_mooring_lines(db)
    finally:
        db.close()
    print("Database initialized with 8 mooring lines")


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
    """Get all 8 mooring lines with summary information (좌측 4개, 우측 4개)"""
    lines = MooringLineService.get_all_mooring_lines(db, active_only)
    
    summaries = []
    for line in lines:
        tension_percentage = (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
        status = MooringLineService.calculate_tension_status(
            line.current_tension, 
            line.reference_tension,
            line.max_tension
        )
        
        summaries.append(MooringLineSummary(
            id=line.id,
            name=line.name,
            position=f"{line.side}-{line.position_index}",  # 위치 정보 업데이트
            current_tension=line.current_tension,
            reference_tension=line.reference_tension,
            tension_percentage=tension_percentage,
            remaining_lifespan_percentage=line.remaining_lifespan_percentage,
            status=status,
            line_id=line.line_id,
            side=line.side,
            line_type=line.line_type,
            position_index=line.position_index
        ))
    
    # 좌측, 우측, 위치 순서대로 정렬
    summaries.sort(key=lambda x: (x.side, x.position_index))
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
    # Get mooring lines summary
    lines = MooringLineService.get_all_mooring_lines(db, active_only=True)
    line_summaries = []
    
    for line in lines:
        tension_percentage = (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
        status = MooringLineService.calculate_tension_status(
            line.current_tension,
            line.reference_tension,
            line.max_tension
        )
        
        line_summaries.append(MooringLineSummary(
            id=line.id,
            name=line.name,
            position=f"{line.side}-{line.position_index}",
            current_tension=line.current_tension,
            reference_tension=line.reference_tension,
            tension_percentage=tension_percentage,
            remaining_lifespan_percentage=line.remaining_lifespan_percentage,
            status=status,
            line_id=line.line_id,
            side=line.side,
            line_type=line.line_type,
            position_index=line.position_index
        ))
    
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
    
    # Get active alerts
    alerts = AlertService.get_active_alerts(db)
    
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
            # Keep connection alive and send periodic updates
            await asyncio.sleep(30)  # 30초마다 업데이트
            
            # 주기적으로 대시보드 데이터 전송
            try:
                dashboard_data = get_dashboard_data(db)
                await websocket.send_json({
                    "type": "dashboard_update",
                    "data": dashboard_data.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"WebSocket periodic update error: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ======================
# Sensor Data Processing
# ======================

@app.post("/api/sensor-data/process")
async def process_sensor_data(
    raw_data: str,
    db: Session = Depends(get_db)
):
    """실제 센서 데이터 처리"""
    parser = SensorDataParser()
    
    try:
        # 단일 라인 파싱
        parsed_data = parser.parse_csv_line(raw_data)
        if parsed_data:
            parser.save_parsed_data(parsed_data, db)
            
            # WebSocket으로 실시간 업데이트 전송
            await manager.broadcast({
                "type": "sensor_data_update",
                "data": parsed_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {"message": "Sensor data processed successfully", "lines_updated": len(parsed_data['lines'])}
        else:
            raise HTTPException(status_code=400, detail="Failed to parse sensor data")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing sensor data: {str(e)}")


@app.post("/api/sensor-data/upload-file")
async def upload_sensor_file(
    file_path: str,
    db: Session = Depends(get_db)
):
    """센서 데이터 파일 전체 처리"""
    parser = SensorDataParser()
    
    try:
        processed_count = parser.process_file(file_path, db)
        return {
            "message": "File processed successfully", 
            "processed_records": processed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


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


@app.post("/api/simulation/process-test-data")
async def process_test_data(db: Session = Depends(get_db)):
    """테스트 데이터 파일 처리"""
    try:
        test_file_path = "/home/user/webapp/testdata_sample.txt"
        if os.path.exists(test_file_path):
            parser = SensorDataParser()
            processed_count = parser.process_file(test_file_path, db)
            return {
                "message": "Test data processed successfully", 
                "processed_records": processed_count
            }
        else:
            raise HTTPException(status_code=404, detail="Test data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/mooring-lines/ship-layout")
def get_ship_layout(db: Session = Depends(get_db)):
    """배 상단뷰 레이아웃을 위한 계류줄 위치 정보"""
    lines = MooringLineService.get_all_mooring_lines(db, active_only=True)
    
    # 좌측과 우측으로 그룹화
    port_lines = []
    starboard_lines = []
    
    for line in lines:
        line_info = {
            "id": line.id,
            "line_id": line.line_id,
            "name": line.name,
            "type": line.line_type,
            "position_index": line.position_index,
            "current_tension": line.current_tension,
            "reference_tension": line.reference_tension,
            "status": MooringLineService.calculate_tension_status(
                line.current_tension, line.reference_tension, line.max_tension
            ),
            "tension_percentage": (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
        }
        
        if line.side == "PORT":
            port_lines.append(line_info)
        else:
            starboard_lines.append(line_info)
    
    # 위치별 정렬
    port_lines.sort(key=lambda x: x["position_index"])
    starboard_lines.sort(key=lambda x: x["position_index"])
    
    return {
        "port_lines": port_lines,
        "starboard_lines": starboard_lines,
        "total_lines": len(lines),
        "ship_dimensions": {
            "length": 200,  # 미터
            "width": 50,    # 미터
            "scale": "1:1000"  # 스케일
        }
    }


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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
"""
FastAPI application for Mooring Line Monitoring System - Simplified Version
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, init_db
from models import MooringLine
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/mooring-lines")
def get_mooring_lines(db: Session = Depends(get_db)):
    """Get all mooring lines"""
    try:
        lines = db.query(MooringLine).filter(MooringLine.is_active == True).all()
        result = []
        for line in lines:
            tension_percentage = (line.current_tension / line.reference_tension * 100) if line.reference_tension > 0 else 0
            # Simple status calculation
            if line.current_tension > line.reference_tension * 1.2:
                status = "WARNING"
            elif line.current_tension > line.max_tension * 0.9:
                status = "CRITICAL"
            else:
                status = "NORMAL"
            
            result.append({
                "id": line.id,
                "line_id": line.line_id,
                "name": line.name,
                "side": line.side,
                "position_index": line.position_index,
                "current_tension": line.current_tension,
                "reference_tension": line.reference_tension,
                "tension_percentage": tension_percentage,
                "remaining_lifespan_percentage": line.remaining_lifespan_percentage,
                "status": status
            })
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []

@app.get("/api/dashboard")
def get_dashboard_data():
    """Get dashboard data - use mooring-lines endpoint"""
    return {
        "mooring_lines": [],  # Frontend should use /api/mooring-lines
        "current_weather": {
            "temperature": 20.0,
            "humidity": 60.0,
            "wind_speed": 5.0,
            "wind_direction": 0.0,
            "wind_direction_text": "N",
            "pressure": 1013.0,
            "wave_height": 1.0,
            "timestamp": datetime.utcnow().isoformat()
        },
        "active_alerts": [],
        "system_status": {
            "active_lines": 8,
            "total_lines": 8,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "system_health": "OPERATIONAL"
        }
    }

@app.post("/api/simulation/start")
async def start_simulation():
    """Start live sensor data simulation"""
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), "..", "testdata_full.txt")
        
        status = get_simulation_status()
        if status["is_running"]:
            return {"message": "Simulation is already running", "status": status}
        
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
        return {"error": str(e)}

@app.post("/api/simulation/stop")
def stop_simulation_endpoint():
    """Stop simulation"""
    stop_live_simulation()
    return {"message": "Simulation stopped"}

@app.get("/api/simulation/status")
def get_simulation_status_endpoint():
    """Get simulation status"""
    return {"simulation": get_simulation_status()}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Serve static files
if os.path.exists(static_path):
    from fastapi.responses import HTMLResponse
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        try:
            with open(os.path.join(static_path, "index.html"), "r") as f:
                return f.read()
        except:
            return "<h1>Mooring Line Monitoring System</h1><p>API is running. Frontend files not found.</p>"
    
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
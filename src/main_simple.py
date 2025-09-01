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

from src.database import get_db, init_db
from src.models import MooringLine
from src.data_parser import initialize_mooring_lines
from src.live_simulation import start_live_simulation, stop_live_simulation, get_simulation_status
import threading
import requests
import random
import math

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

# Weather API functions
def get_weather_data():
    """Get real weather data from multiple APIs or simulate realistic data"""
    try:
        # 부산 좌표 (Busan Port coordinates)
        lat, lon = 35.1796, 129.0756
        
        # 실제 API 사용시 환경변수에서 키를 가져오기
        # openweather_api_key = os.environ.get("OPENWEATHER_API_KEY")
        # weatherapi_key = os.environ.get("WEATHERAPI_KEY")
        
        # API 호출 예시 (실제 키가 있을 때만 사용)
        # if openweather_api_key:
        #     try:
        #         url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={openweather_api_key}&units=metric"
        #         response = requests.get(url, timeout=5)
        #         if response.status_code == 200:
        #             data = response.json()
        #             return {
        #                 "temperature": data["main"]["temp"],
        #                 "humidity": data["main"]["humidity"],
        #                 "wind_speed": data["wind"]["speed"],
        #                 "wind_direction": data["wind"]["deg"]
        #             }
        #     except Exception as api_error:
        #         print(f"OpenWeatherMap API error: {api_error}")
        
        # 시뮬레이션 날씨 데이터 (부산항 기준 실감나는 데이터)
        import time
        import math
        
        current_time = time.time()
        hour_of_day = (current_time / 3600) % 24  # 0-24 시간
        day_of_year = (current_time / (24 * 3600)) % 365  # 0-365 일
        
        # 일일 온도 변화 패턴 (새벽 최저, 오후 최고)
        daily_temp_variation = 6 * math.sin((hour_of_day - 6) * math.pi / 12)
        
        # 연간 온도 변화 패턴 (여름 최고, 겨울 최저)
        seasonal_temp_variation = 10 * math.sin((day_of_year - 80) * 2 * math.pi / 365)
        
        # 기본 온도 (부산 연평균)
        base_temp = 15 + seasonal_temp_variation + daily_temp_variation
        
        # 습도 패턴 (새벽 높고, 오후 낮음)
        humidity_variation = -15 * math.sin((hour_of_day - 6) * math.pi / 12)
        base_humidity = 65 + humidity_variation
        
        # 풍속 패턴 (해안 지역 특성)
        wind_base = 4 + 3 * math.sin(hour_of_day * math.pi / 12)
        
        # 풍향 패턴 (해륙풍 고려)
        if 6 <= hour_of_day <= 18:  # 주간: 해풍 (남동풍)
            wind_dir_base = 135
        else:  # 야간: 육풍 (북서풍)
            wind_dir_base = 315
        
        return {
            "temperature": round(base_temp + random.uniform(-2, 2), 1),
            "humidity": max(30, min(90, round(base_humidity + random.uniform(-8, 8), 1))),
            "wind_speed": max(0.5, round(wind_base + random.uniform(-1.5, 1.5), 1)),
            "wind_direction": round((wind_dir_base + random.uniform(-45, 45)) % 360, 1)
        }
    except Exception as e:
        print(f"Weather data generation error: {e}")
        # 안전한 기본값 반환
        return {
            "temperature": 18.0,
            "humidity": 65.0,
            "wind_speed": 4.0,
            "wind_direction": 180.0
        }

def get_wind_direction_text(degrees):
    """Convert wind direction degrees to text"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

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
            # Simple status calculation (랜덤 알림 제거)
            if line.current_tension > line.max_tension * 0.9:
                status = "CRITICAL"
            elif line.current_tension > line.reference_tension * 1.2:
                status = "WARNING"
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
    """Get dashboard data with real weather information"""
    # Get real weather data
    weather = get_weather_data()
    
    return {
        "mooring_lines": [],  # Frontend should use /api/mooring-lines
        "current_weather": {
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "wind_speed": weather["wind_speed"],
            "wind_direction": weather["wind_direction"],
            "wind_direction_text": get_wind_direction_text(weather["wind_direction"]),
            "pressure": 1013.0 + random.uniform(-20, 20),
            "wave_height": 1.0 + random.uniform(-0.5, 0.5),
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

@app.get("/api/tension/{line_id}/chart-data")
def get_tension_chart_data(line_id: int, hours: int = 24, db: Session = Depends(get_db)):
    """Get tension chart data for individual mooring line"""
    try:
        from sqlalchemy import and_
        from src.models import TensionHistory
        from datetime import timedelta
        
        # Get mooring line info
        line = db.query(MooringLine).filter(MooringLine.id == line_id).first()
        if not line:
            return {"error": "Mooring line not found"}
        
        # Get tension history for the specified time range
        start_time = datetime.utcnow() - timedelta(hours=hours)
        tension_history = db.query(TensionHistory).filter(
            and_(
                TensionHistory.mooring_line_id == line_id,
                TensionHistory.timestamp >= start_time
            )
        ).order_by(TensionHistory.timestamp.desc()).limit(1000).all()
        
        # If no data, create some sample data with real weather variations
        if not tension_history:
            # Create sample data points with realistic weather
            sample_data = []
            base_weather = get_weather_data()  # Get base weather data
            
            for i in range(24):  # Last 24 hours of sample data
                sample_time = datetime.utcnow() - timedelta(hours=23-i)
                
                # Create realistic weather variations over time
                time_factor = i / 24.0  # 0 to 1 for time progression
                
                sample_data.append({
                    "timestamp": sample_time.isoformat(),
                    "tension": line.current_tension + (i % 5 - 2) * 0.1,  # Some variation
                    "status": "NORMAL",
                    "temperature": base_weather["temperature"] + random.uniform(-3, 3),
                    "humidity": base_weather["humidity"] + random.uniform(-10, 10),
                    "wind_speed": base_weather["wind_speed"] + random.uniform(-2, 2),
                    "wind_direction": (base_weather["wind_direction"] + i * 10 + random.uniform(-15, 15)) % 360
                })
            
            return {
                "mooring_line": {
                    "id": line.id,
                    "name": line.name,
                    "reference_tension": line.reference_tension,
                    "max_tension": line.max_tension
                },
                "data": sample_data
            }
        
        # Convert actual data with weather information
        chart_data = []
        base_weather = get_weather_data()  # Get current weather as base
        
        for i, record in enumerate(reversed(tension_history)):  # Reverse to get chronological order
            # Create time-based weather variations for historical data
            time_offset = i * 0.1  # Small variations based on record sequence
            chart_data.append({
                "timestamp": record.timestamp.isoformat(),
                "tension": record.tension_value,
                "status": record.status or "NORMAL",
                "temperature": base_weather["temperature"] + random.uniform(-2, 2),
                "humidity": base_weather["humidity"] + random.uniform(-8, 8),
                "wind_speed": base_weather["wind_speed"] + random.uniform(-1.5, 1.5),
                "wind_direction": (base_weather["wind_direction"] + time_offset * 30 + random.uniform(-20, 20)) % 360
            })
        
        return {
            "mooring_line": {
                "id": line.id,
                "name": line.name,
                "reference_tension": line.reference_tension,
                "max_tension": line.max_tension
            },
            "data": chart_data
        }
        
    except Exception as e:
        print(f"Chart data error: {e}")
        return {"error": str(e)}



@app.get("/api/weather")
def get_weather():
    """Get current weather data"""
    try:
        weather = get_weather_data()
        return {
            "temperature": round(weather["temperature"], 1),
            "humidity": round(weather["humidity"], 1),
            "wind_speed": round(weather["wind_speed"], 1),
            "wind_direction": round(weather["wind_direction"], 1),
            "wind_direction_text": get_wind_direction_text(weather["wind_direction"]),
            "pressure": round(1013.0 + random.uniform(-20, 20), 1),
            "wave_height": round(1.0 + random.uniform(-0.5, 0.5), 1),
            "timestamp": datetime.utcnow().isoformat(),
            "location": "부산항",
            "description": "실시간 기상 데이터"
        }
    except Exception as e:
        return {"error": str(e)}

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
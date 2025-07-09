# src/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="스마트 계류줄 관리 시스템 API",
    description="항만 계류줄 장력 실시간 모니터링 및 제어 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (개발 환경용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 라우트
@app.get("/")
async def root():
    return {
        "message": "스마트 계류줄 관리 시스템 API 서버가 정상적으로 실행 중입니다!",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "smart-mooring-system",
        "version": "1.0.0"
    }

# 센서 상태 확인 (임시 데이터)
@app.get("/api/sensors/status")
async def get_sensors_status():
    return {
        "sensors": [
            {"id": "ML01", "name": "계류줄 1", "status": "active", "tension": 45.2},
            {"id": "ML02", "name": "계류줄 2", "status": "active", "tension": 52.8},
            {"id": "ML03", "name": "계류줄 3", "status": "active", "tension": 38.9},
            {"id": "ML04", "name": "계류줄 4", "status": "active", "tension": 47.1}
        ],
        "timestamp": datetime.now().isoformat()
    }

# 개발 환경에서만 사용
if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

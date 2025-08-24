"""
Database models for the mooring line monitoring system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class MooringLine(Base):
    """계류줄 정보 모델"""
    __tablename__ = "mooring_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 계류줄 이름 (예: Line-1, Line-2)
    position = Column(String(50))  # 위치 (예: Port-Bow, Starboard-Stern)
    
    # 장력 관련 정보
    reference_tension = Column(Float, nullable=False)  # 기준 장력 (kN)
    max_tension = Column(Float, nullable=False)  # 최대 허용 장력 (kN)
    current_tension = Column(Float, default=0.0)  # 현재 장력 (kN)
    
    # 수명 관련 정보
    installation_date = Column(DateTime, default=datetime.utcnow)  # 설치일
    expected_lifespan_days = Column(Integer, default=365)  # 예상 수명 (일)
    remaining_lifespan_percentage = Column(Float, default=100.0)  # 잔여 수명 (%)
    
    # 상태 정보
    is_active = Column(Boolean, default=True)  # 활성 상태
    last_inspection_date = Column(DateTime)  # 마지막 점검일
    
    # Relationships
    tension_history = relationship("TensionHistory", back_populates="mooring_line", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TensionHistory(Base):
    """장력 이력 데이터 모델"""
    __tablename__ = "tension_history"
    
    id = Column(Integer, primary_key=True, index=True)
    mooring_line_id = Column(Integer, ForeignKey("mooring_lines.id"), nullable=False)
    
    tension_value = Column(Float, nullable=False)  # 장력 값 (kN)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # 측정 시간
    
    # 장력 상태
    status = Column(String(20))  # NORMAL, WARNING, CRITICAL
    
    # Relationship
    mooring_line = relationship("MooringLine", back_populates="tension_history")
    
    # 날씨 정보 참조
    weather_id = Column(Integer, ForeignKey("weather_data.id"))
    weather = relationship("WeatherData", back_populates="tension_records")


class WeatherData(Base):
    """날씨 데이터 모델"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 기상 정보
    temperature = Column(Float)  # 온도 (°C)
    humidity = Column(Float)  # 습도 (%)
    wind_speed = Column(Float)  # 풍속 (m/s)
    wind_direction = Column(Float)  # 풍향 (degrees, 0-360)
    
    # 추가 정보
    pressure = Column(Float)  # 기압 (hPa)
    wave_height = Column(Float)  # 파고 (m)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tension_records = relationship("TensionHistory", back_populates="weather")


class Alert(Base):
    """경고/알림 모델"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    mooring_line_id = Column(Integer, ForeignKey("mooring_lines.id"))
    
    alert_type = Column(String(50))  # TENSION_WARNING, TENSION_CRITICAL, LIFESPAN_WARNING
    message = Column(String(500))
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    mooring_line = relationship("MooringLine")
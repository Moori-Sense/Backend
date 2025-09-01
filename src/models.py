"""
Database models for the mooring line monitoring system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class MooringLine(Base):
    """계류줄 정보 모델 - 8개 계류줄 (좌측 4개, 우측 4개)"""
    __tablename__ = "mooring_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(String(20), nullable=False, unique=True)  # L0, L1, L2, L3, L4, L5, L6, L7
    name = Column(String(100), nullable=False)  # 계류줄 이름 (예: L0-PORT-BREAST)
    line_type = Column(String(20))  # BREAST, SPRING
    side = Column(String(10))  # PORT(좌측), STARBOARD(우측)
    position_index = Column(Integer)  # 0-3 (각 면에서의 위치)
    
    # 장력 관련 정보 (N 단위로 변경)
    reference_tension = Column(Float, nullable=False)  # 기준 장력 (N)
    max_tension = Column(Float, nullable=False)  # 최대 허용 장력 (N)
    current_tension = Column(Float, default=0.0)  # 현재 장력 (N)
    
    # 거리 정보
    distance_to_port = Column(Float)  # 항만과의 거리 (cm)
    
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
    """장력 이력 데이터 모델 - 실제 센서 데이터 저장"""
    __tablename__ = "tension_history"
    
    id = Column(Integer, primary_key=True, index=True)
    mooring_line_id = Column(Integer, ForeignKey("mooring_lines.id"), nullable=False)
    
    # 센서 데이터
    tension_value = Column(Float, nullable=False)  # 장력 값 (N)
    distance_to_port = Column(Float)  # 초음파 센서 거리 측정값 (cm)
    line_length = Column(Float, default=0.0)  # 엔코더 측정 줄 길이 (m)
    
    # 원시 타임스탬프 (센서에서 온 시간)
    raw_timestamp = Column(String(20))  # 예: "22:59:42.719"
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # 시스템 저장 시간
    
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
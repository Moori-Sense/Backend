"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TensionStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    TENSION_WARNING = "TENSION_WARNING"
    TENSION_CRITICAL = "TENSION_CRITICAL"
    LIFESPAN_WARNING = "LIFESPAN_WARNING"


# Mooring Line Schemas
class MooringLineBase(BaseModel):
    name: str
    position: Optional[str] = None
    reference_tension: float = Field(..., description="Reference tension in kN")
    max_tension: float = Field(..., description="Maximum allowed tension in kN")


class MooringLineCreate(MooringLineBase):
    expected_lifespan_days: int = 365


class MooringLineUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    reference_tension: Optional[float] = None
    max_tension: Optional[float] = None
    current_tension: Optional[float] = None
    remaining_lifespan_percentage: Optional[float] = None


class MooringLineResponse(MooringLineBase):
    id: int
    current_tension: float
    installation_date: datetime
    expected_lifespan_days: int
    remaining_lifespan_percentage: float
    is_active: bool
    last_inspection_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MooringLineSummary(BaseModel):
    """계류줄 요약 정보"""
    id: int
    name: str
    position: Optional[str]
    current_tension: float
    reference_tension: float
    tension_percentage: float  # (current/reference) * 100
    remaining_lifespan_percentage: float
    status: TensionStatus
    
    class Config:
        from_attributes = True


# Tension History Schemas
class TensionHistoryCreate(BaseModel):
    mooring_line_id: int
    tension_value: float
    weather_id: Optional[int] = None


class TensionHistoryResponse(BaseModel):
    id: int
    mooring_line_id: int
    tension_value: float
    timestamp: datetime
    status: Optional[str]
    weather_id: Optional[int]
    
    class Config:
        from_attributes = True


class TensionTimeSeriesData(BaseModel):
    """시계열 장력 데이터"""
    timestamp: datetime
    tension_value: float
    status: TensionStatus
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None


# Weather Schemas
class WeatherDataCreate(BaseModel):
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity in percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_direction: float = Field(..., description="Wind direction in degrees (0-360)")
    pressure: Optional[float] = Field(None, description="Pressure in hPa")
    wave_height: Optional[float] = Field(None, description="Wave height in meters")


class WeatherDataResponse(WeatherDataCreate):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CurrentWeather(BaseModel):
    """현재 날씨 정보"""
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float
    wind_direction_text: str  # N, NE, E, SE, S, SW, W, NW
    pressure: Optional[float]
    wave_height: Optional[float]
    timestamp: datetime


# Alert Schemas
class AlertCreate(BaseModel):
    mooring_line_id: int
    alert_type: AlertType
    message: str
    severity: AlertSeverity


class AlertResponse(BaseModel):
    id: int
    mooring_line_id: int
    alert_type: str
    message: str
    severity: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardData(BaseModel):
    """대시보드 전체 데이터"""
    mooring_lines: List[MooringLineSummary]
    current_weather: CurrentWeather
    active_alerts: List[AlertResponse]
    system_status: dict  # 시스템 상태 정보
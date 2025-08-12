# SQLAIchemy DB 모델(models.py)
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime 


class Berth(Base):
    """부두/선석 테이블"""
    __tablename__ = "berths"

    berth_id = Column(Integer, primary_key=True, index=True)
    berth_name = Column(String(50), nullable=False, comment="부두명")
    max_ship_length = Column(Decimal(8,2), comment="최대 수용 선박 길이(m)")
    max_ship_beam = Column(Decimal(8,2), comment="최대 수용 선박 폭(m)")
    status = Column(String(20), default="AVAILABLE", comment="부두상태")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    ships = relationship("Ship", back_populates="berth")


class Ship(Base):
    """선박 테이블"""
    __tablename__ = "ships"

    ship_id = Column(Integer, primary_key=True, index=True)
    ship_name = Column(String(100), nullable=False, comment="선박명")
    ship_type = Column(String(50), comment="선박 종류")
    length = Column(Decimal(8,2), comment="선박 길이(m)")
    berth_id = Column(Integer, ForeignKey("berths.berth_id"), nullable=True)
    arrival_time = Column(DateTime, comment="접안 시간")
    departure_time = Column(DateTime, comment="출항 시간")
    status = Column(String(20), default="BERTED", comment="선박 상태")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    berth = relationship("Berth", back_populates="ships")
    mooring_lines = relationship("MooringLine", back_populates="ship")
    sensor_data = relationship("SensorData", back_populates="ship")
    alerts = relationship("Alert", back_populates="ship")
    control_commands = relationship("ControlCommand", back_populates="ship")

class MooringLine(Base):
    """계류줄 설정 테이블"""
    __tablename__ = "mooring_lines"

    line_id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(String(20), ForeignKey("ships.ship_id"), nullable=False)
    line_position = Column(String(20), nullable=False, comment="계류줄 위치")
    max_tension = Column(Decimal(8,2), nullable=False, comment="최대 허용 장력(N)")
    length = Column(Decimal(8,2), comment="계류줄 길이(m)")
    status = Column(String(20), default="ACTIVE", comment="계류줄 상태")
    installed_at = Column(DateTime, default=func.now(), comment="설치 일시")

    # 관계 설정 
    ship = relationship("Ship", back_populates="mooring_lines")

class SensorData(Base):
    """센서 데이터 테이블(시계열 데이터)"""
    __tablename__ = "sensor_data"

    # 복합 키 구조
    ship_id = Column(Integer, ForeignKey("ships.ship_id"), primary_key=True)
    line_position = Column(String(20), primary_key=True, comment="계류줄 위치")
    measured_at = Column(DateTime, primary_key=True, default=func.now(), comment="측정 시간")

    tension_value = Column(Decimal(10, 3), nullable=False, comment="장력 측정값(kN)")

    # 관계 설정
    ship = relationship("Ship", back_populates="sensor_data")

class Alert(Base):
    """경보 시스템 테이블"""
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.ship_id"), nullable=False)
    line_position = Column(String(20), nullable=False, comment="계류줄 위치")
    alert_type = Column(String(30), nullable=False, comment="경보 종류")
    actual_value = Column(Decimal(10,3), comment="실제 측정값")
    status = Column(String(20), default="ACTIVE", comment="경보 상태")
    created_at = Column(DateTime, default=func.now(), comment="발생일시")
    resolved_at = Column(DateTime, comment="해결일시")
    
    # 관계 설정
    ship = relationship("Ship", back_populates="alerts")

class ControlCommand(Base):
    """제어 명령 테이블"""
    __tablename__ = "control_commands"
    
    command_id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.ship_id"), nullable=False)
    line_position = Column(String(20), nullable=False, comment="제어 대상 계류줄")
    command_type = Column(String(30), nullable=False, comment="명령 종류")
    status = Column(String(20), default="PENDING", comment="실행 상태")
    command_source = Column(String(20), comment="명령 출처")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    executed_at = Column(DateTime, comment="실행일시")
    completed_at = Column(DateTime, comment="완료일시")
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # 관계 설정
    ship = relationship("Ship", back_populates="control_commands")
    creator = relationship("User", back_populates="commands")

class User(Base):
    """사용자 관리 테이블"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, comment="로그인 ID")
    password_hash = Column(String(255), nullable=False, comment="암호화된 비밀번호")
    full_name = Column(String(100), comment="실명")
    email = Column(String(100), comment="이메일")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    last_login = Column(DateTime, comment="마지막 접속일시")
    
    # 관계 설정
    commands = relationship("ControlCommand", back_populates="creator")
    


"""
Business logic services
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import random  # For simulation
from src.models import MooringLine, TensionHistory, WeatherData, Alert
from src.schemas import (
    MooringLineCreate, MooringLineUpdate, TensionHistoryCreate,
    WeatherDataCreate, AlertCreate, TensionStatus, AlertSeverity, AlertType,
    TensionTimeSeriesData
)


class MooringLineService:
    """계류줄 관련 서비스"""
    
    @staticmethod
    def create_mooring_line(db: Session, data: MooringLineCreate) -> MooringLine:
        """새 계류줄 생성"""
        mooring_line = MooringLine(
            name=data.name,
            position=data.position,
            reference_tension=data.reference_tension,
            max_tension=data.max_tension,
            expected_lifespan_days=data.expected_lifespan_days,
            current_tension=0.0,
            remaining_lifespan_percentage=100.0
        )
        db.add(mooring_line)
        db.commit()
        db.refresh(mooring_line)
        return mooring_line
    
    @staticmethod
    def get_all_mooring_lines(db: Session, active_only: bool = True) -> List[MooringLine]:
        """모든 계류줄 조회"""
        query = db.query(MooringLine)
        if active_only:
            query = query.filter(MooringLine.is_active == True)
        return query.all()
    
    @staticmethod
    def get_mooring_line(db: Session, line_id: int) -> Optional[MooringLine]:
        """특정 계류줄 조회"""
        return db.query(MooringLine).filter(MooringLine.id == line_id).first()
    
    @staticmethod
    def update_mooring_line(db: Session, line_id: int, data: MooringLineUpdate) -> Optional[MooringLine]:
        """계류줄 정보 업데이트"""
        mooring_line = db.query(MooringLine).filter(MooringLine.id == line_id).first()
        if not mooring_line:
            return None
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mooring_line, field, value)
        
        db.commit()
        db.refresh(mooring_line)
        return mooring_line
    
    @staticmethod
    def calculate_tension_status(tension: float, reference: float, max_tension: float) -> TensionStatus:
        """장력 상태 계산"""
        percentage = (tension / reference) * 100
        
        if tension >= max_tension * 0.9:  # 최대 장력의 90% 이상
            return TensionStatus.CRITICAL
        elif percentage >= 120:  # 기준 장력의 120% 이상
            return TensionStatus.WARNING
        else:
            return TensionStatus.NORMAL
    
    @staticmethod
    def update_lifespan(db: Session, line_id: int):
        """수명 업데이트 (장력 누적 기반)"""
        mooring_line = db.query(MooringLine).filter(MooringLine.id == line_id).first()
        if not mooring_line:
            return
        
        # 설치일로부터 경과 일수 계산
        days_used = (datetime.utcnow() - mooring_line.installation_date).days
        
        # 과장력 누적 시간 고려 (간단한 계산)
        critical_hours = db.query(TensionHistory).filter(
            and_(
                TensionHistory.mooring_line_id == line_id,
                TensionHistory.status == TensionStatus.CRITICAL.value
            )
        ).count() / 12  # 5분 간격 데이터 가정
        
        # 수명 계산 (과장력 시간은 2배로 계산)
        effective_days = days_used + (critical_hours / 24) * 2
        remaining_percentage = max(0, 100 - (effective_days / mooring_line.expected_lifespan_days * 100))
        
        mooring_line.remaining_lifespan_percentage = remaining_percentage
        db.commit()


class TensionService:
    """장력 데이터 서비스"""
    
    @staticmethod
    def record_tension(db: Session, data: TensionHistoryCreate) -> TensionHistory:
        """장력 데이터 기록"""
        mooring_line = db.query(MooringLine).filter(MooringLine.id == data.mooring_line_id).first()
        if not mooring_line:
            raise ValueError(f"Mooring line {data.mooring_line_id} not found")
        
        # 장력 상태 계산
        status = MooringLineService.calculate_tension_status(
            data.tension_value,
            mooring_line.reference_tension,
            mooring_line.max_tension
        )
        
        # 장력 이력 저장
        tension_history = TensionHistory(
            mooring_line_id=data.mooring_line_id,
            tension_value=data.tension_value,
            status=status.value,
            weather_id=data.weather_id
        )
        db.add(tension_history)
        
        # 현재 장력 업데이트
        mooring_line.current_tension = data.tension_value
        
        # 경고 생성 (필요시)
        if status == TensionStatus.CRITICAL:
            AlertService.create_tension_alert(db, mooring_line, data.tension_value, AlertSeverity.CRITICAL)
        elif status == TensionStatus.WARNING:
            AlertService.create_tension_alert(db, mooring_line, data.tension_value, AlertSeverity.HIGH)
        
        db.commit()
        db.refresh(tension_history)
        return tension_history
    
    @staticmethod
    def get_tension_history(
        db: Session,
        line_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TensionTimeSeriesData]:
        """장력 이력 조회"""
        query = db.query(TensionHistory, WeatherData).outerjoin(
            WeatherData, TensionHistory.weather_id == WeatherData.id
        ).filter(TensionHistory.mooring_line_id == line_id)
        
        if start_time:
            query = query.filter(TensionHistory.timestamp >= start_time)
        if end_time:
            query = query.filter(TensionHistory.timestamp <= end_time)
        
        query = query.order_by(desc(TensionHistory.timestamp)).limit(limit)
        results = query.all()
        
        time_series_data = []
        for tension, weather in results:
            data = TensionTimeSeriesData(
                timestamp=tension.timestamp,
                tension_value=tension.tension_value,
                status=TensionStatus(tension.status) if tension.status else TensionStatus.NORMAL
            )
            
            if weather:
                data.temperature = weather.temperature
                data.humidity = weather.humidity
                data.wind_speed = weather.wind_speed
                data.wind_direction = weather.wind_direction
            
            time_series_data.append(data)
        
        return time_series_data[::-1]  # Reverse to get chronological order


class WeatherService:
    """날씨 데이터 서비스"""
    
    @staticmethod
    def record_weather(db: Session, data: WeatherDataCreate) -> WeatherData:
        """날씨 데이터 기록"""
        weather = WeatherData(**data.dict())
        db.add(weather)
        db.commit()
        db.refresh(weather)
        return weather
    
    @staticmethod
    def get_current_weather(db: Session) -> Optional[WeatherData]:
        """현재 날씨 조회"""
        return db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()
    
    @staticmethod
    def get_wind_direction_text(degrees: float) -> str:
        """풍향 각도를 텍스트로 변환"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]


class AlertService:
    """경고/알림 서비스"""
    
    @staticmethod
    def create_tension_alert(
        db: Session,
        mooring_line: MooringLine,
        tension_value: float,
        severity: AlertSeverity
    ) -> Alert:
        """장력 경고 생성"""
        alert_type = AlertType.TENSION_CRITICAL if severity == AlertSeverity.CRITICAL else AlertType.TENSION_WARNING
        
        message = f"Mooring line '{mooring_line.name}' tension ({tension_value:.1f} kN) "
        if alert_type == AlertType.TENSION_CRITICAL:
            message += f"exceeded critical threshold ({mooring_line.max_tension * 0.9:.1f} kN)"
        else:
            message += f"exceeded warning threshold ({mooring_line.reference_tension * 1.2:.1f} kN)"
        
        alert = Alert(
            mooring_line_id=mooring_line.id,
            alert_type=alert_type.value,
            message=message,
            severity=severity.value
        )
        db.add(alert)
        # Don't commit here, let the caller commit
        return alert
    
    @staticmethod
    def get_active_alerts(db: Session) -> List[Alert]:
        """활성 경고 조회"""
        return db.query(Alert).filter(Alert.is_resolved == False).order_by(desc(Alert.created_at)).all()
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """경고 해결 처리"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            db.commit()
        return alert


class SimulationService:
    """시뮬레이션 데이터 생성 서비스"""
    
    @staticmethod
    def generate_sample_data(db: Session):
        """샘플 데이터 생성"""
        # 계류줄 4개 생성
        lines = []
        positions = ["Port-Bow", "Port-Stern", "Starboard-Bow", "Starboard-Stern"]
        
        for i, pos in enumerate(positions, 1):
            line = MooringLineService.create_mooring_line(
                db,
                MooringLineCreate(
                    name=f"Line-{i}",
                    position=pos,
                    reference_tension=100.0,  # 기준 장력 100 kN
                    max_tension=150.0,  # 최대 장력 150 kN
                    expected_lifespan_days=365
                )
            )
            lines.append(line)
        
        # 최근 24시간 데이터 생성
        now = datetime.utcnow()
        for hours_ago in range(24, -1, -1):
            timestamp = now - timedelta(hours=hours_ago)
            
            # 날씨 데이터 생성
            weather = WeatherService.record_weather(
                db,
                WeatherDataCreate(
                    temperature=20 + random.uniform(-5, 5),
                    humidity=60 + random.uniform(-20, 20),
                    wind_speed=5 + random.uniform(0, 10),
                    wind_direction=random.uniform(0, 360),
                    pressure=1013 + random.uniform(-10, 10),
                    wave_height=0.5 + random.uniform(0, 2)
                )
            )
            
            # 각 계류줄의 장력 데이터 생성 (5분 간격)
            for minutes in range(0, 60, 5):
                for line in lines:
                    # 시간대별로 다른 장력 패턴 생성
                    base_tension = line.reference_tension
                    if 6 <= hours_ago <= 10:  # 오전 활동 시간
                        base_tension *= 1.1
                    elif 14 <= hours_ago <= 18:  # 오후 활동 시간
                        base_tension *= 1.15
                    
                    # 랜덤 변동 추가
                    tension = base_tension + random.uniform(-20, 30)
                    tension = max(0, min(tension, line.max_tension))  # 범위 제한
                    
                    TensionService.record_tension(
                        db,
                        TensionHistoryCreate(
                            mooring_line_id=line.id,
                            tension_value=tension,
                            weather_id=weather.id
                        )
                    )
        
        # 수명 업데이트
        for line in lines:
            MooringLineService.update_lifespan(db, line.id)
        
        print("Sample data generated successfully!")
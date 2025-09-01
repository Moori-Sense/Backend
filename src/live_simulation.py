"""
실시간 센서 데이터 시뮬레이션 시스템
실제 센서 데이터를 30초마다 순환하면서 업데이트하고 알림 생성
"""
import asyncio
import time
from datetime import datetime
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.data_parser import SensorDataParser
from src.models import MooringLine, TensionHistory, Alert
import random
from typing import List, Dict

class AlertManager:
    """알림 관리 시스템 - 최대 5개 알림 유지"""
    
    def __init__(self):
        self.max_alerts = 5
        self.alert_history = []
    
    def create_alert(self, db: Session, line_name: str, tension: float, reference: float, alert_type: str = "TENSION_UPDATE"):
        """새로운 알림 생성"""
        try:
            # 기존 알림 정리 (5개 이상이면 오래된 것 삭제)
            existing_alerts = db.query(Alert).filter(Alert.is_resolved == False).order_by(Alert.created_at.desc()).all()
            
            if len(existing_alerts) >= self.max_alerts:
                # 가장 오래된 알림들을 해결됨으로 표시
                alerts_to_resolve = existing_alerts[self.max_alerts-1:]
                for alert in alerts_to_resolve:
                    alert.is_resolved = True
                    alert.resolved_at = datetime.utcnow()
            
            # 새 알림 생성
            message = f"{line_name} 장력 업데이트: {tension:.2f}N (기준: {reference:.2f}N)"
            severity = "LOW"
            
            if tension > reference * 1.2:
                severity = "HIGH"
                message = f"⚠️ {line_name} 장력 초과: {tension:.2f}N > 기준 {reference:.2f}N"
            elif tension > reference * 1.1:
                severity = "MEDIUM"
                message = f"🔶 {line_name} 장력 주의: {tension:.2f}N (기준: {reference:.2f}N)"
            elif tension < reference * 0.5:
                severity = "MEDIUM"
                message = f"🔻 {line_name} 장력 저하: {tension:.2f}N < 기준 {reference:.2f}N"
            else:
                message = f"✅ {line_name}: {tension:.2f}N (정상)"
            
            new_alert = Alert(
                alert_type=alert_type,
                message=message,
                severity=severity,
                is_resolved=False,
                created_at=datetime.utcnow()
            )
            
            db.add(new_alert)
            db.commit()
            
            return new_alert
            
        except Exception as e:
            print(f"알림 생성 오류: {e}")
            db.rollback()
            return None

class LiveDataSimulator:
    """실시간 데이터 시뮬레이션"""
    
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.parser = SensorDataParser()
        self.alert_manager = AlertManager()
        self.data_lines = []
        self.current_index = 0
        self.is_running = False
        self.update_count = 0
        
        # 데이터 파일 로드
        self.load_data()
        
    def load_data(self):
        """센서 데이터 파일을 메모리에 로드"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                self.data_lines = [line.strip() for line in file if line.strip()]
            print(f"✅ 센서 데이터 로드 완료: {len(self.data_lines)}줄")
        except Exception as e:
            print(f"❌ 데이터 파일 로드 실패: {e}")
            self.data_lines = []
    
    def get_next_data_line(self) -> str:
        """다음 데이터 라인 반환 (순환)"""
        if not self.data_lines:
            return None
            
        data_line = self.data_lines[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.data_lines)
        return data_line
    
    def add_random_variation(self, parsed_data: dict) -> dict:
        """데이터에 약간의 랜덤 변화 추가 (더 실감나게)"""
        if not parsed_data or 'lines' not in parsed_data:
            return parsed_data
        
        # 각 계류줄의 장력에 ±8% 범위의 랜덤 변화 추가 (더 다양하게)
        for line_name, line_data in parsed_data['lines'].items():
            if 'tension' in line_data:
                original_tension = line_data['tension']
                variation = random.uniform(-0.08, 0.08)  # ±8%
                new_tension = max(0.0, original_tension * (1 + variation))
                parsed_data['lines'][line_name]['tension'] = round(new_tension, 3)
        
        # 거리에도 약간의 변화 추가
        if parsed_data.get('distance'):
            original_distance = parsed_data['distance']
            distance_variation = random.uniform(-1.0, 1.0)  # ±1.0cm
            new_distance = max(10.0, original_distance + distance_variation)
            parsed_data['distance'] = round(new_distance, 1)
        
        # 현재 시간으로 타임스탬프 업데이트
        current_time = datetime.now()
        parsed_data['timestamp'] = current_time.strftime("%H:%M:%S.%f")[:-3]
        
        return parsed_data
    
    async def simulate_single_update(self) -> bool:
        """단일 데이터 업데이트 시뮬레이션"""
        try:
            # 다음 데이터 라인 가져오기
            raw_line = self.get_next_data_line()
            if not raw_line:
                print("❌ 데이터가 없습니다")
                return False
            
            # 데이터 파싱
            parsed_data = self.parser.parse_csv_line(raw_line)
            if not parsed_data:
                print(f"❌ 데이터 파싱 실패: {raw_line[:100]}...")
                return False
            
            # 랜덤 변화 추가
            parsed_data = self.add_random_variation(parsed_data)
            
            # 데이터베이스에 저장
            db = SessionLocal()
            try:
                self.parser.save_parsed_data(parsed_data, db)
                
                # 알림 생성 (각 계류줄별로)
                for line_id, line_data in parsed_data['lines'].items():
                    mooring_line = db.query(MooringLine).filter(MooringLine.line_id == line_id).first()
                    if mooring_line:
                        self.alert_manager.create_alert(
                            db, 
                            mooring_line.name, 
                            line_data['tension'], 
                            mooring_line.reference_tension
                        )
                
                # 처리된 데이터 요약 출력
                lines_updated = len(parsed_data['lines'])
                timestamp = parsed_data['timestamp']
                distance = parsed_data.get('distance', 0)
                self.update_count += 1
                
                # 각 계류줄의 장력 정보 출력
                tension_info = []
                for line_name, line_data in parsed_data['lines'].items():
                    tension = line_data.get('tension', 0)
                    tension_info.append(f"{line_name}:{tension:.2f}N")
                
                print(f"🔄 업데이트#{self.update_count} [{timestamp}] 거리:{distance}cm | {' | '.join(tension_info[:4])}")
                print(f"   └─ {' | '.join(tension_info[4:])}")
                
                return True
                
            except Exception as e:
                print(f"❌ 데이터 저장 실패: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ 시뮬레이션 업데이트 실패: {e}")
            return False
    
    async def start_simulation(self, update_interval: int = 30):
        """시뮬레이션 시작"""
        self.is_running = True
        self.update_count = 0
        print(f"🚀 실시간 센서 데이터 시뮬레이션 시작 (간격: {update_interval}초)")
        print(f"📊 총 {len(self.data_lines)}개 데이터 순환 처리")
        print(f"🔔 최대 5개 알림 유지하며 실시간 업데이트")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 데이터 업데이트 실행
                success = await self.simulate_single_update()
                
                if success:
                    elapsed = time.time() - start_time
                    print(f"✅ 업데이트 #{self.update_count} 완료 ({elapsed:.2f}초 소요)")
                else:
                    print(f"⚠️ 업데이트 #{self.update_count + 1} 실패")
                
                # 다음 업데이트까지 대기
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                print("🛑 시뮬레이션이 중단되었습니다")
                break
            except Exception as e:
                print(f"❌ 시뮬레이션 오류: {e}")
                await asyncio.sleep(5)  # 오류 시 5초 후 재시도
    
    def stop_simulation(self):
        """시뮬레이션 중지"""
        self.is_running = False
        print("🛑 시뮬레이션 중지 요청")


# 글로벌 시뮬레이터 인스턴스
global_simulator = None

async def start_live_simulation(data_file_path: str, interval: int = 30):
    """전역 시뮬레이션 시작"""
    global global_simulator
    
    if global_simulator and global_simulator.is_running:
        print("⚠️ 시뮬레이션이 이미 실행 중입니다")
        return
    
    global_simulator = LiveDataSimulator(data_file_path)
    await global_simulator.start_simulation(interval)

def stop_live_simulation():
    """전역 시뮬레이션 중지"""
    global global_simulator
    
    if global_simulator:
        global_simulator.stop_simulation()
        print("✅ 시뮬레이션이 중지되었습니다")
    else:
        print("⚠️ 실행 중인 시뮬레이션이 없습니다")

def get_simulation_status():
    """시뮬레이션 상태 반환"""
    global global_simulator
    
    if global_simulator:
        return {
            "is_running": global_simulator.is_running,
            "data_lines_count": len(global_simulator.data_lines),
            "current_index": global_simulator.current_index,
            "update_count": global_simulator.update_count,
            "data_file": global_simulator.data_file_path
        }
    
    return {
        "is_running": False,
        "data_lines_count": 0,
        "current_index": 0,
        "update_count": 0,
        "data_file": None
    }
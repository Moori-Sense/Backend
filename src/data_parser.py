"""
실제 센서 데이터 파싱 모듈
CSV 형태의 센서 데이터를 파싱하여 8개 계류줄에 분산 저장
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import random

from models import MooringLine, TensionHistory


class SensorDataParser:
    """센서 데이터 파서 - 8개 계류줄 지원"""
    
    def __init__(self):
        # 실제 센서 데이터를 8개 계류줄에 매핑
        self.sensor_to_line_mapping = {
            'L0-BREAST': {'target_lines': ['L0', 'L4'], 'multiplier': [1.0, 0.8]},
            'L1-BREAST': {'target_lines': ['L1', 'L5'], 'multiplier': [1.0, 0.9]},
            'L2-SPRING': {'target_lines': ['L2', 'L6'], 'multiplier': [1.0, 0.85]},
            'L3-SPRING': {'target_lines': ['L3', 'L7'], 'multiplier': [1.0, 0.75]}
        }
        
        self.line_mapping = {
            'L0': {'id': 'L0', 'side': 'PORT', 'type': 'BREAST', 'index': 0},
            'L1': {'id': 'L1', 'side': 'STARBOARD', 'type': 'BREAST', 'index': 0},
            'L2': {'id': 'L2', 'side': 'PORT', 'type': 'SPRING', 'index': 1},
            'L3': {'id': 'L3', 'side': 'STARBOARD', 'type': 'SPRING', 'index': 1},
            'L4': {'id': 'L4', 'side': 'PORT', 'type': 'BREAST', 'index': 2},
            'L5': {'id': 'L5', 'side': 'STARBOARD', 'type': 'BREAST', 'index': 2},
            'L6': {'id': 'L6', 'side': 'PORT', 'type': 'SPRING', 'index': 3},
            'L7': {'id': 'L7', 'side': 'STARBOARD', 'type': 'SPRING', 'index': 3}
        }
    
    def parse_csv_line(self, line: str) -> Optional[Dict]:
        """
        단일 CSV 라인 파싱하여 8개 계류줄에 데이터 분산
        
        예시 입력:
        "22:59:42.719 -> CSV,DIST,14.5cm,L0-BREAST,T,0.95,LEN,0.000m,SPD,0,OVR,0,BRK,1,..."
        
        반환:
        {
            'timestamp': '22:59:42.719',
            'distance': 14.5,
            'lines': {
                'L0': {'tension': 0.95, 'length': 0.000},
                'L1': {'tension': 1.55, 'length': 0.000},
                'L2': {'tension': 0.71, 'length': 0.000},
                'L3': {'tension': 0.73, 'length': 0.000},
                'L4': {'tension': 0.76, 'length': 0.000},  # L0 기반 생성
                'L5': {'tension': 1.40, 'length': 0.000},  # L1 기반 생성
                'L6': {'tension': 0.60, 'length': 0.000},  # L2 기반 생성
                'L7': {'tension': 0.55, 'length': 0.000}   # L3 기반 생성
            }
        }
        """
        try:
            # 타임스탬프 추출
            timestamp_match = re.match(r'^(\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if not timestamp_match:
                return None
            
            timestamp = timestamp_match.group(1)
            
            # CSV 데이터 부분 추출
            csv_part = line.split(' -> ')[1] if ' -> ' in line else line
            parts = csv_part.split(',')
            
            if len(parts) < 3 or parts[0] != 'CSV':
                return None
            
            # 거리 정보 추출
            distance = None
            if parts[1] == 'DIST' and parts[2].endswith('cm'):
                distance = float(parts[2].replace('cm', ''))
            
            # 원본 센서 데이터 파싱
            original_lines_data = {}
            i = 3
            while i < len(parts):
                if i + 5 < len(parts):
                    line_name = parts[i]
                    if parts[i+1] == 'T':  # Tension
                        tension = float(parts[i+2])
                    if parts[i+3] == 'LEN':  # Length
                        length = float(parts[i+4].replace('m', ''))
                    
                    original_lines_data[line_name] = {
                        'tension': tension,
                        'length': length
                    }
                    
                    # 다음 계류줄로 이동 (각 계류줄당 8개 필드)
                    i += 8
                else:
                    break
            
            # 8개 계류줄에 데이터 분산
            expanded_lines_data = {}
            
            for sensor_line, sensor_data in original_lines_data.items():
                if sensor_line in self.sensor_to_line_mapping:
                    mapping = self.sensor_to_line_mapping[sensor_line]
                    target_lines = mapping['target_lines']
                    multipliers = mapping['multiplier']
                    
                    for i, target_line in enumerate(target_lines):
                        multiplier = multipliers[i]
                        # 약간의 랜덤 변화 추가 (±3%)
                        variation = random.uniform(0.97, 1.03)
                        final_tension = sensor_data['tension'] * multiplier * variation
                        
                        expanded_lines_data[target_line] = {
                            'tension': round(final_tension, 3),
                            'length': sensor_data['length']
                        }
            
            return {
                'timestamp': timestamp,
                'distance': distance,
                'lines': expanded_lines_data
            }
            
        except Exception as e:
            print(f"파싱 에러: {e}, 라인: {line}")
            return None
    
    def save_parsed_data(self, parsed_data: Dict, db: Session):
        """파싱된 데이터를 8개 계류줄에 저장"""
        try:
            for line_id, line_data in parsed_data['lines'].items():
                if line_id not in self.line_mapping:
                    continue
                
                # 계류줄 정보 조회
                mooring_line = db.query(MooringLine).filter(
                    MooringLine.line_id == line_id
                ).first()
                
                if not mooring_line:
                    continue  # 계류줄이 존재하지 않으면 스킵
                
                # 장력 이력 데이터 저장
                tension_history = TensionHistory(
                    mooring_line_id=mooring_line.id,
                    tension_value=line_data['tension'],
                    line_length=line_data['length'],
                    distance_to_port=parsed_data['distance'],
                    raw_timestamp=parsed_data['timestamp'],
                    timestamp=datetime.utcnow()
                )
                
                db.add(tension_history)
                
                # 현재 장력 업데이트
                mooring_line.current_tension = line_data['tension']
                if parsed_data['distance']:
                    mooring_line.distance_to_port = parsed_data['distance']
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"데이터 저장 에러: {e}")
    
    def process_file(self, file_path: str, db: Session) -> int:
        """파일 전체를 처리하여 데이터베이스에 저장"""
        processed_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed_data = self.parse_csv_line(line)
                    if parsed_data:
                        self.save_parsed_data(parsed_data, db)
                        processed_count += 1
                    
                    # 10줄마다 진행상황 출력
                    if line_num % 10 == 0:
                        print(f"처리된 라인: {line_num}, 저장된 데이터: {processed_count}")
        
        except Exception as e:
            print(f"파일 처리 에러: {e}")
        
        return processed_count


def initialize_mooring_lines(db: Session):
    """8개 계류줄 초기 데이터 생성"""
    lines_config = [
        # 좌측 (PORT) 4개
        {'line_id': 'L0', 'name': 'L0-PORT-BREAST', 'type': 'BREAST', 'side': 'PORT', 'index': 0, 'ref_tension': 1.0},
        {'line_id': 'L2', 'name': 'L2-PORT-SPRING', 'type': 'SPRING', 'side': 'PORT', 'index': 1, 'ref_tension': 0.8},
        {'line_id': 'L4', 'name': 'L4-PORT-BREAST', 'type': 'BREAST', 'side': 'PORT', 'index': 2, 'ref_tension': 1.0},
        {'line_id': 'L6', 'name': 'L6-PORT-SPRING', 'type': 'SPRING', 'side': 'PORT', 'index': 3, 'ref_tension': 0.8},
        
        # 우측 (STARBOARD) 4개
        {'line_id': 'L1', 'name': 'L1-STARBOARD-BREAST', 'type': 'BREAST', 'side': 'STARBOARD', 'index': 0, 'ref_tension': 1.5},
        {'line_id': 'L3', 'name': 'L3-STARBOARD-SPRING', 'type': 'SPRING', 'side': 'STARBOARD', 'index': 1, 'ref_tension': 0.7},
        {'line_id': 'L5', 'name': 'L5-STARBOARD-BREAST', 'type': 'BREAST', 'side': 'STARBOARD', 'index': 2, 'ref_tension': 1.5},
        {'line_id': 'L7', 'name': 'L7-STARBOARD-SPRING', 'type': 'SPRING', 'side': 'STARBOARD', 'index': 3, 'ref_tension': 0.7}
    ]
    
    for config in lines_config:
        existing = db.query(MooringLine).filter(MooringLine.line_id == config['line_id']).first()
        if not existing:
            mooring_line = MooringLine(
                line_id=config['line_id'],
                name=config['name'],
                line_type=config['type'],
                side=config['side'],
                position_index=config['index'],
                reference_tension=config['ref_tension'],
                max_tension=config['ref_tension'] * 2.0,
                current_tension=0.0,
                distance_to_port=14.5  # 기본값
            )
            db.add(mooring_line)
    
    db.commit()
    print("8개 계류줄 초기화 완료")
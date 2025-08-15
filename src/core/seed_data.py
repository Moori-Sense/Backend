# 테스트 데이터 생성
from sqlalchemy.orm import Session
from database import SessionLocal, create_tables
from models import Berth, Ship, MooringLine, User
from datetime import datetime

def create_sample_data():
    """샘플 데이터 생성"""
    db = SessionLocal()
    
    try:
        # 1. 부두 데이터
        berths = [
            Berth(berth_name="부두 A", max_ship_length=300.0, max_ship_beam=50.0, status="AVAILABLE"),
            Berth(berth_name="부두 B", max_ship_length=250.0, max_ship_beam=40.0, status="OCCUPIED"),
            Berth(berth_name="부두 C", max_ship_length=200.0, max_ship_beam=35.0, status="AVAILABLE"),
        ]
        
        for berth in berths:
            db.add(berth)
        db.commit()
        
        # 2. 선박 데이터
        ships = [
            Ship(
                ship_name="PACIFIC OCEAN",
                ship_type="유조선",
                length=250.5,
                berth_id=2,  # 부두 B
                arrival_time=datetime.now(),
                status="BERTHED"
            ),
            Ship(
                ship_name="KOREA STAR",
                ship_type="컨테이너선",
                length=180.0,
                berth_id=1,  # 부두 A
                arrival_time=datetime.now(),
                status="BERTHED"
            )
        ]
        
        for ship in ships:
            db.add(ship)
        db.commit()
        
        # 3. 계류줄 설정 (각 선박마다 4개씩)
        mooring_positions = ["bow_port", "bow_starboard", "stern_port", "stern_starboard"]
        
        for ship in ships:
            for position in mooring_positions:
                mooring_line = MooringLine(
                    ship_id=ship.ship_id,
                    line_position=position,
                    max_tension=80.0,  # 80kN
                    length=50.0,  # 50m
                    status="ACTIVE"
                )
                db.add(mooring_line)
        
        db.commit()
        
        # 4. 관리자 사용자
        admin_user = User(
            username="admin",
            password_hash="hashed_password_here",  # 실제로는 해시 처리 필요
            full_name="시스템 관리자",
            email="admin@mooring-system.com"
        )
        db.add(admin_user)
        db.commit()
        
        print("✅ 샘플 데이터가 생성되었습니다!")
        print(f"   - 부두: {len(berths)}개")
        print(f"   - 선박: {len(ships)}개")
        print(f"   - 계류줄: {len(ships) * 4}개")
        print(f"   - 사용자: 1개")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()  # 테이블 생성
    create_sample_data()  # 샘플 데이터 생성
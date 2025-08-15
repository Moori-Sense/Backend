#database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

# 환경변수에서 DB 정보 읽어오기
DB_USER = os.getenv("postgres")
DB_PASSWORD = os.getenv("12345") 
DB_HOST = os.getenv("localhost")
DB_PORT = os.getenv("5432")
DB_NAME = os.getenv("mooring_system")

#데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345d@localhost:5432/mooring_system")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# 테이블 생성 함수
def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블이 생성되었습니다")

def drop_tables():
    """모든 테이블 삭제"""
    Base.metadata.drop_all(bind=engine)
    print("모든 테이블이 삭제되었습니다.")

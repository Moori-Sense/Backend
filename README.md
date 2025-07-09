# 스마트 계류줄 관리 시스템 백엔드 API

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.0+-orange.svg)](https://www.timescale.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## **📋 프로젝트 개요**

항만에서 계류줄의 장력을 실시간으로 모니터링하고 자동으로 제어하는 스마트 안전 관리 시스템의 백엔드 API입니다. IoT 센서, AI 예측 모델, 자동 제어 시스템을 통합하여 계류줄 파단 사고를 예방하고 항만 안전성을 향상시킵니다.


### **🎯 주요 기능**

**실시간 모니터링 및 제어**
- 토크 센서를 통한 계류줄 장력 실시간 측정 및 저장
- 서보 모터 기반 계류줄 길이 자동 조절 시스템
- 설정 임계치 초과 시 즉시 경고 및 선박 스피커 경보

**AI 기반 예측 및 분석**
- XGBoost 모델을 활용한 시계열 장력 데이터 이상탐지
- 기상 정보/조위 정보 연동 예측 모델
- 과장력 누적 시간 분석을 통한 예방정비 지원

**통합 관리 시스템**
- FastAPI 기반 REST API 서버
- TimescaleDB를 통한 시계열 데이터베이스 구축
- 실시간 웹 대시보드 API 제공
- 계류줄별 장력 추이 및 경보 상황 모니터링

## **🏗️ 시스템 아키텍처**

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     하드웨어        │    │      백엔드         │    │     프론트엔드      │
│                     │    │                     │    │                     │
│ • 토크 센서 (4개)   │◄──►│ • FastAPI           │◄──►│ • React 대시보드    │
│ • 서보 모터 (4SET)  │    │ • TimescaleDB       │    │ • 실시간 차트       │
│ • 아두이노          │    │ • XGBoost ML        │    │ • 경고 알림         │
│ • 선박 모형         │    │ • WebSocket         │    │ • 제어 인터페이스   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## **🚀 기술 스택**

**백엔드 프레임워크**
- **Python 3.9+**: 메인 개발 언어
- **FastAPI**: 고성능 웹 프레임워크 및 자동 API 문서 생성
- **Uvicorn**: ASGI 서버

**데이터베이스 및 ORM**
- **TimescaleDB**: PostgreSQL 기반 시계열 데이터베이스
- **SQLAlchemy**: ORM 및 데이터베이스 추상화
- **Alembic**: 데이터베이스 마이그레이션 관리

**머신러닝 및 데이터 처리**
- **XGBoost**: 시계열 예측 및 이상탐지 모델
- **Pandas**: 데이터 처리 및 분석
- **NumPy**: 수치 계산

**개발 도구**
- **Pydantic**: 데이터 검증 및 설정 관리
- **pytest**: 테스트 프레임워크
- **Docker**: 컨테이너화 및 배포

## **📁 프로젝트 구조**

```
backend/
├── Dockerfile                  # Docker 이미지 빌드를 위한 설정
├── docker-compose.yml          # 여러 컨테이너 서비스 정의 및 실행 설정
├── Makefile                    # 빌드/테스트 명령 자동화
├── pyproject.toml              # 프로젝트 의존성 및 패키지 설정 (또는 requirements.txt)
├── .env                        # 환경 변수 설정 (DB_URL, JWT_SECRET 등)
├── .gitignore                  # Git 버전 관리에서 제외할 파일 목록
├── alembic/                    # 데이터베이스 마이그레이션 관리 (Alembic)
│   ├── env.py                  # 마이그레이션 환경 설정
│   └── versions/               # 마이그레이션 버전 파일 저장소
├── alembic.ini                 # Alembic 설정 파일
├── src/                        # 메인 애플리케이션 소스 코드
│   ├── auth/                   # 인증/사용자 관리 도메인
│   │   ├── router.py           # 인증 API 엔드포인트 (FastAPI APIRouter)
│   │   ├── schemas.py          # Pydantic 요청/응답 모델
│   │   ├── models.py           # SQLAlchemy 데이터베이스 모델
│   │   ├── service.py          # 비즈니스 로직 (서비스 계층)
│   │   ├── dependencies.py     # FastAPI 의존성 주입 (JWT 검증 등)
│   │   ├── constants.py        # 모듈 상수 및 에러 코드
│   │   ├── exceptions.py       # 커스텀 예외 정의
│   │   └── utils.py            # 유틸리티 함수
│   ├── items/                  # 다른 도메인 예시 (아이템 관리)
│   │   ├── router.py           # 아이템 API 엔드포인트
│   │   ├── schemas.py          # 요청/응답 데이터 모델
│   │   ├── models.py           # 데이터베이스 모델
│   │   ├── service.py          # 비즈니스 로직
│   │   ├── dependencies.py     # 의존성 주입
│   │   ├── constants.py        # 상수 정의
│   │   ├── exceptions.py       # 예외 정의
│   │   └── utils.py            # 유틸리티 함수
│   ├── core/                   # 공통 기능 모듈
│   │   ├── database.py         # DB 세션 관리, SQLAlchemy Base 설정
│   │   ├── config.py           # 환경 설정 (Pydantic BaseSettings)
│   │   ├── dependencies.py     # 전역 의존성 주입 (DB 세션 등)
│   │   └── security.py         # 공통 보안 로직 (JWT 처리)
│   ├── models.py               # 전역 데이터 모델 (공통 Base 등)
│   ├── main.py                 # FastAPI 앱 생성 및 라우터 등록
│   └── utils/                  # 범용 유틸리티 함수
├── tests/                      # 테스트 코드
│   ├── auth/                   # 인증 모듈 테스트
│   ├── items/                  # 아이템 모듈 테스트
│   └── ...
└── README.md                   # 프로젝트 문서 (현재 파일)
```

## **⚙️ 설치 및 실행**

### **전제 조건**
- Python 3.9 이상
- PostgreSQL 14+ (TimescaleDB 확장)
- Docker & Docker Compose (권장)

### **1. 저장소 클론 및 환경 설정**

```bash
# 저장소 클론
git clone https://github.com/Moori-Sense/Backend.git
cd backend

# 가상환경 생성 및 활성화
python -m venv backend_env
source backend_env/bin/activate  # Linux/Mac
# 또는 backend_env\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
# 또는 pyproject.toml 사용 시
pip install -e .
```

### **2. 환경 변수 설정**

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집 (예시)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mooring_system
DB_USER=postgres
DB_PASSWORD=your_password
API_HOST=0.0.0.0
API_PORT=8000
TENSION_WARNING_THRESHOLD=80.0
TENSION_CRITICAL_THRESHOLD=95.0
```

### **3. 데이터베이스 설정**

```bash
# Docker Compose로 TimescaleDB 실행
docker-compose up -d timescaledb

# 데이터베이스 마이그레이션
alembic upgrade head
```

### **4. 서버 실행**

```bash
# src 디렉토리로 이동
cd src

# 개발 서버 실행
uvicorn main:app --reload

# 또는 호스트와 포트 지정
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **5. API 문서 확인**

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## **📊 주요 API 엔드포인트**

### **센서 데이터 관리**
- `GET /api/sensors/status` - 전체 센서 상태 조회
- `POST /api/sensors/data` - 센서 데이터 수집 (아두이노에서 전송)
- `GET /api/sensors/tension/{mooring_line_id}` - 특정 계류줄 장력 데이터

### **제어 시스템**
- `POST /api/control/adjust` - 수동 장력 조절
- `GET /api/control/status` - 제어 시스템 상태
- `POST /api/control/emergency-stop` - 비상 정지

### **대시보드 및 모니터링**
- `GET /api/dashboard/overview` - 전체 시스템 개요
- `GET /api/dashboard/alerts` - 경고 이력 조회
- `WebSocket /ws/realtime` - 실시간 데이터 스트림

### **예측 및 분석**
- `GET /api/ml/predictions` - XGBoost 기반 장력 예측
- `GET /api/ml/anomalies` - 이상탐지 결과
- `POST /api/ml/retrain` - 모델 재학습

## **🧪 테스트 실행**

```bash
# 전체 테스트 실행
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/auth/ -v

# 커버리지 리포트
pytest --cov=src tests/

# 테스트 결과 HTML 리포트
pytest --cov=src --cov-report=html tests/
```

## **🔧 개발 워크플로우**

### **코드 품질 관리**

```bash
# 코드 포맷팅
black src/
isort src/

# 린팅 검사
flake8 src/

# 타입 체크 (선택사항)
mypy src/
```

### **데이터베이스 마이그레이션**

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

## **🐳 Docker 배포**

```bash
# 이미지 빌드
docker build -t smart-mooring-backend .

# 컨테이너 실행
docker run -p 8000:8000 smart-mooring-backend

# Docker Compose 사용
docker-compose up -d
```

## **📈 모니터링 및 로깅**

시스템은 다음과 같은 모니터링 기능을 제공합니다:

**로깅 시스템**
- 구조화된 JSON 로그 출력
- 센서 데이터 수집 이력
- API 요청/응답 로그
- 에러 및 예외 상황 추적

**헬스 체크**
- `/health` 엔드포인트를 통한 시스템 상태 확인
- 데이터베이스 연결 상태 모니터링
- 센서 통신 상태 확인

**성능 메트릭**
- API 응답 시간 측정
- 센서 데이터 수집 빈도 추적
- 메모리 및 CPU 사용량 모니터링


## **🔗 관련 링크**

- **프로젝트 문서**: [2025년 스마트 해운물류 ICT 멘토링 프로젝트](docs/)
- **API 문서**: http://localhost:8000/docs



**2025년 스마트 해운물류 ICT 멘토링 프로젝트**  
*항만 안전을 위한 스마트 계류줄 관리 시스템*
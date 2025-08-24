# 🚢 선박 계류줄 모니터링 시스템

실시간으로 선박 계류줄의 장력을 모니터링하고 수명을 관리하는 웹 기반 시스템입니다.

## 📌 주요 기능

### 계류줄 모니터링
- **실시간 장력 측정**: 각 계류줄의 현재 장력을 실시간으로 표시
- **기준 장력 비교**: 현재 장력과 기준 장력을 시각적으로 비교
- **수명 관리**: 계류줄의 잔여 수명을 백분율로 표시
- **상태 표시**: NORMAL, WARNING, CRITICAL 상태를 색상으로 구분

### 시계열 데이터 분석
- **장력 변화 그래프**: 시간대별 장력 변화를 차트로 시각화
- **날씨 연동**: 온도, 습도, 풍속과 장력의 상관관계 표시
- **통계 정보**: 최대/최소/평균 장력 및 경고 발생 횟수

### 날씨 정보
- **실시간 날씨**: 온도, 습도, 풍속, 풍향 표시
- **기압 및 파고**: 추가 환경 정보 제공

### 경고 시스템
- **자동 경고 생성**: 임계값 초과 시 자동으로 경고 생성
- **경고 수준**: LOW, MEDIUM, HIGH, CRITICAL로 구분

## 🛠 기술 스택

### Backend
- **FastAPI**: Python 웹 프레임워크
- **SQLAlchemy**: ORM
- **SQLite**: 데이터베이스
- **Uvicorn**: ASGI 서버
- **WebSocket**: 실시간 통신

### Frontend
- **React 18**: UI 프레임워크
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 스타일링
- **Recharts**: 데이터 시각화
- **Axios**: HTTP 클라이언트
- **Vite**: 빌드 도구

### DevOps
- **PM2**: 프로세스 관리
- **Git**: 버전 관리

## 🚀 접속 URL

- **Frontend (대시보드)**: https://5173-ir0ri94bpy59cyqsm8eok-6532622b.e2b.dev
- **Backend API**: https://8000-ir0ri94bpy59cyqsm8eok-6532622b.e2b.dev
- **API 문서 (Swagger)**: https://8000-ir0ri94bpy59cyqsm8eok-6532622b.e2b.dev/docs

## 📊 API 엔드포인트

### 계류줄 관리
- `GET /api/mooring-lines` - 모든 계류줄 목록 조회
- `GET /api/mooring-lines/{id}` - 특정 계류줄 상세 정보
- `POST /api/mooring-lines` - 새 계류줄 등록
- `PUT /api/mooring-lines/{id}` - 계류줄 정보 수정

### 장력 데이터
- `POST /api/tension` - 장력 데이터 기록
- `GET /api/tension/{id}/history` - 장력 이력 조회
- `GET /api/tension/{id}/chart-data` - 차트용 데이터 조회

### 날씨 정보
- `POST /api/weather` - 날씨 데이터 기록
- `GET /api/weather/current` - 현재 날씨 조회

### 대시보드
- `GET /api/dashboard` - 전체 대시보드 데이터
- `GET /api/alerts` - 활성 경고 목록
- `WebSocket /ws` - 실시간 업데이트

### 시뮬레이션
- `POST /api/simulation/generate-data` - 샘플 데이터 생성

## 💻 로컬 실행 방법

### 요구사항
- Python 3.9+
- Node.js 18+
- npm 또는 yarn

### 설치 및 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd webapp
```

2. **백엔드 설치 및 실행**
```bash
# Python 의존성 설치
pip install -r requirements.txt

# 백엔드 서버 실행
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **프론트엔드 설치 및 실행**
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

4. **PM2로 실행 (권장)**
```bash
# PM2 설치
npm install pm2

# 모든 서비스 시작
npx pm2 start ecosystem.config.js

# 상태 확인
npx pm2 status

# 로그 확인
npx pm2 logs
```

## 📝 사용 방법

1. **대시보드 접속**: 브라우저에서 프론트엔드 URL 접속
2. **샘플 데이터 생성**: 처음 실행 시 "샘플 데이터 생성" 버튼 클릭
3. **계류줄 상태 확인**: 각 계류줄 카드에서 현재 상태 확인
4. **상세 차트 보기**: 계류줄 카드 클릭하여 시계열 차트 확인
5. **시간 범위 변경**: 차트에서 6시간, 12시간, 24시간, 48시간 선택 가능

## 🔍 시스템 구조

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   IoT Sensors   │────▶│   Backend API   │────▶│   Frontend UI   │
│  (Simulation)   │     │    (FastAPI)    │     │     (React)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Database     │
                        │    (SQLite)     │
                        └─────────────────┘
```

## 📈 데이터 모델

### MooringLine (계류줄)
- `id`: 고유 ID
- `name`: 계류줄 이름
- `position`: 위치
- `reference_tension`: 기준 장력 (kN)
- `max_tension`: 최대 허용 장력 (kN)
- `current_tension`: 현재 장력 (kN)
- `remaining_lifespan_percentage`: 잔여 수명 (%)

### TensionHistory (장력 이력)
- `id`: 고유 ID
- `mooring_line_id`: 계류줄 ID
- `tension_value`: 장력 값 (kN)
- `timestamp`: 측정 시간
- `status`: 상태 (NORMAL/WARNING/CRITICAL)

### WeatherData (날씨 데이터)
- `temperature`: 온도 (°C)
- `humidity`: 습도 (%)
- `wind_speed`: 풍속 (m/s)
- `wind_direction`: 풍향 (degrees)
- `pressure`: 기압 (hPa)
- `wave_height`: 파고 (m)

## 🎯 향후 개선 사항

- [ ] 실제 IoT 센서 연동
- [ ] 데이터 예측 모델 (AI/ML) 적용
- [ ] 모바일 반응형 디자인 개선
- [ ] 알림 시스템 (이메일/SMS)
- [ ] 데이터 내보내기 기능
- [ ] 다국어 지원
- [ ] 사용자 인증 시스템

## 📄 라이선스

MIT License

## 👥 개발팀

2025년 스마트 해운물류 ICT 멘토링 프로젝트 팀

---

**문의사항이나 버그 리포트는 이슈 트래커를 이용해 주세요.**
# 🔥 FPAT FastAPI Server

FPAT(Firewall Policy Analysis Tool)을 FastAPI로 변환한 웹 서비스입니다.

## 📋 주요 기능

- **📁 파일 관리**: 정책 파일 업로드/다운로드
- **📊 정책 비교**: 정책 변경사항 분석  
- **🔍 정책 분석**: 중복성, Shadow 정책 탐지
- **🔎 정책 필터링**: IP/포트 기반 정책 검색
- **🔗 방화벽 연동**: PaloAlto, NGF, MF2 실시간 연동
- **⚡ 백그라운드 작업**: 대용량 데이터 비동기 처리
- **📈 실시간 모니터링**: WebSocket 기반 작업 진행률 추적

## 🏗️ 지원 방화벽

| 벤더 | 모델 | 연결 방식 | 지원 기능 |
|------|------|-----------|-----------|
| **PaloAlto Networks** | PAN-OS | HTTPS API | 전체 기능 |
| **SECUI** | NGF | SSH | 정책 분석 |
| **SECUI** | MF2 | SSH | 정책 분석 |
| **Mock** | Test | Virtual | 전체 기능 |

## 🚀 빠른 시작

### 1. 로컬 개발 환경

```bash
# 1. 프로젝트 클론
git clone <repository>
cd fastapi-fpat

# 2. 환경 설정
cp .env.example .env
# .env 파일 수정 필요

# 3. 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 4. 실행
chmod +x start.sh
./start.sh
```

### 2. Docker 환경

```bash
# 전체 스택 실행 (FastAPI + PostgreSQL + Redis)
docker-compose up -d

# API만 실행
docker-compose up fpat-api
```

### 3. 접속 URL

- **🏠 홈페이지**: http://localhost:8000
- **📖 API 문서**: http://localhost:8000/docs  
- **📚 ReDoc**: http://localhost:8000/redoc
- **💚 Health Check**: http://localhost:8000/health

## 📦 프로젝트 구조

```
fastapi-fpat/
├── app/                          # FastAPI 애플리케이션
│   ├── api/v1/endpoints/        # API 엔드포인트
│   │   ├── files.py            # 파일 관리 API
│   │   ├── policy.py           # 정책 분석 API
│   │   ├── firewall.py         # 방화벽 연동 API
│   │   └── jobs.py             # 작업 관리 API + WebSocket
│   ├── core/                   # 핵심 설정
│   │   └── config.py           # 애플리케이션 설정
│   ├── models/                 # 데이터 모델
│   │   └── schemas.py          # Pydantic 스키마
│   ├── services/               # 비즈니스 로직
│   │   ├── fpat_service.py     # FPAT 모듈 통합
│   │   └── job_service.py      # 백그라운드 작업 관리
│   └── main.py                 # FastAPI 앱 메인
├── fpat/                       # 기존 FPAT 모듈 (심볼릭 링크 또는 복사)
├── uploads/                    # 업로드된 파일 저장소
├── logs/                       # 로그 파일
├── requirements.txt            # Python 의존성
├── Dockerfile                  # Docker 이미지 빌드
├── docker-compose.yml          # Docker 스택 정의
├── .env.example               # 환경 변수 예시
└── start.sh                   # 로컬 실행 스크립트
```

## 📋 API 엔드포인트

### 파일 관리
- `POST /api/v1/files/upload` - 파일 업로드
- `GET /api/v1/files/download/{file_id}` - 파일 다운로드
- `GET /api/v1/files/list` - 파일 목록 조회

### 정책 분석
- `POST /api/v1/policy/compare` - 정책 비교 (백그라운드)
- `POST /api/v1/policy/analyze` - 정책 분석 (백그라운드)
- `POST /api/v1/policy/filter` - 정책 필터링 (백그라운드)
- `POST /api/v1/policy/*/quick` - 즉시 실행 버전

### 방화벽 연동
- `POST /api/v1/firewall/test-connection` - 연결 테스트
- `POST /api/v1/firewall/export` - 데이터 익스포트 (백그라운드)
- `GET /api/v1/firewall/vendors` - 지원 벤더 목록

### 작업 관리
- `GET /api/v1/jobs/{job_id}` - 작업 상태 조회
- `GET /api/v1/jobs/` - 작업 목록 조회
- `POST /api/v1/jobs/{job_id}/cancel` - 작업 취소
- `WS /api/v1/jobs/ws` - 실시간 작업 상태 (WebSocket)

## 🌐 WebSocket 사용법

### JavaScript 예시

```javascript
// 전체 작업 모니터링
const ws = new WebSocket('ws://localhost:8000/api/v1/jobs/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('작업 업데이트:', data);
};

// 특정 작업 구독
ws.send(JSON.stringify({
    type: "subscribe",
    job_id: "your-job-id"
}));

// 특정 작업의 진행률 모니터링
const jobWs = new WebSocket('ws://localhost:8000/api/v1/jobs/ws/your-job-id');
```

## ⚙️ 환경 설정

### 필수 환경 변수

```bash
# 기본 설정
APP_NAME=FPAT API
DEBUG=true

# 보안
SECRET_KEY=your-secret-key-here

# 데이터베이스 (선택사항)
POSTGRES_SERVER=localhost
POSTGRES_USER=fpat
POSTGRES_PASSWORD=fpat123

# 파일 업로드
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB
```

## 🔧 개발 가이드

### 새로운 API 엔드포인트 추가

1. `app/api/v1/endpoints/` 에 새 파일 생성
2. `app/models/schemas.py` 에 Pydantic 모델 추가
3. `app/main.py` 에 라우터 등록

### 새로운 백그라운드 작업 추가

1. `app/services/job_service.py` 에 작업 함수 추가
2. `app/api/v1/endpoints/` 에서 작업 호출

### FPAT 모듈 확장

1. `fpat/` 디렉토리에 새 모듈 추가
2. `app/services/fpat_service.py` 에서 통합

## 🐛 문제 해결

### 일반적인 문제들

1. **FPAT 모듈 import 오류**
   ```bash
   # PYTHONPATH 설정 확인
   export PYTHONPATH="$(pwd):$(pwd)/../"
   ```

2. **포트 충돌**
   ```bash
   # 다른 포트 사용
   uvicorn app.main:app --port 8001
   ```

3. **의존성 설치 오류**
   ```bash
   # 가상환경 사용 권장
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 로그 확인

```bash
# 애플리케이션 로그
tail -f logs/fpat.log

# Docker 로그
docker-compose logs -f fpat-api
```

## 📈 성능 최적화

### 프로덕션 설정

1. **환경 변수 수정**
   ```bash
   DEBUG=false
   SECRET_KEY=<strong-secret-key>
   ```

2. **Worker 프로세스 증가**
   ```bash
   uvicorn app.main:app --workers 4
   ```

3. **Nginx 리버스 프록시 사용**
   ```yaml
   # docker-compose.yml에서 nginx 서비스 활성화
   ```

## 🧪 테스트

```bash
# 단위 테스트 실행
pytest tests/

# API 테스트
curl -X GET http://localhost:8000/health

# 파일 업로드 테스트
curl -X POST -F "file=@test.xlsx" http://localhost:8000/api/v1/files/upload
```

## 🤝 기여 방법

1. Fork 프로젝트
2. 새 브랜치 생성 (`git checkout -b feature/new-feature`)
3. 변경사항 커밋 (`git commit -am 'Add new feature'`)
4. 브랜치 푸시 (`git push origin feature/new-feature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 [라이선스명] 라이선스를 따릅니다.

## 📞 지원

- **이슈 리포트**: GitHub Issues
- **문서**: http://localhost:8000/docs
- **이메일**: support@your-domain.com

---

**🔥 FPAT FastAPI Server v1.0.0**  
*방화벽 정책 분석을 위한 현대적인 웹 API 서버*
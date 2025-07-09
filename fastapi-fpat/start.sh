#!/bin/bash

# FPAT FastAPI 애플리케이션 시작 스크립트

echo "🔥 FPAT FastAPI 애플리케이션 시작 중..."

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "📋 .env 파일이 없습니다. .env.example을 복사합니다..."
    cp .env.example .env
    echo "⚠️  .env 파일을 수정한 후 다시 실행해주세요."
    exit 1
fi

# 필요한 디렉토리 생성
mkdir -p uploads logs

# Python 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "📦 Python 가상환경 활성화 중..."
    source venv/bin/activate
fi

# 의존성 설치
echo "📦 Python 패키지 설치 중..."
pip install -r requirements.txt

# FPAT 모듈 경로 확인
if [ ! -d "../fpat" ]; then
    echo "⚠️  ../fpat 디렉토리가 없습니다. FPAT 모듈 경로를 확인해주세요."
    echo "    현재 fpat_service.py에서 ../fpat 경로를 참조하고 있습니다."
fi

# 애플리케이션 시작
echo "🚀 FastAPI 애플리케이션 시작..."
echo "📊 서버 URL: http://localhost:8000"
echo "📖 API 문서: http://localhost:8000/docs"
echo "💚 Health Check: http://localhost:8000/health"

export PYTHONPATH="$(pwd):$(pwd)/../"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
#!/bin/bash

# Hoon Firewall Modules 라이브러리 빌드 및 설치 스크립트

echo "🚀 Hoon Firewall Modules 라이브러리 빌드 시작"

# 기존 빌드 파일 정리
echo "1. 기존 빌드 파일 정리 중..."
rm -rf build/ dist/ *.egg-info/
echo "   ✅ 완료"

# 가상환경이 활성화되어 있는지 확인
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "2. 가상환경 감지: $VIRTUAL_ENV"
else
    echo "⚠️  가상환경이 활성화되지 않았습니다. 가상환경 사용을 권장합니다."
fi

# 필요한 빌드 도구 설치
echo "3. 빌드 도구 설치 중..."
pip install --upgrade pip setuptools wheel build
echo "   ✅ 완료"

# 라이브러리 빌드
echo "4. 라이브러리 빌드 중..."
python -m build
if [ $? -eq 0 ]; then
    echo "   ✅ 빌드 성공"
else
    echo "   ❌ 빌드 실패"
    exit 1
fi

# 개발 모드로 설치
echo "5. 개발 모드로 라이브러리 설치 중..."
pip install -e .
if [ $? -eq 0 ]; then
    echo "   ✅ 설치 성공"
else
    echo "   ❌ 설치 실패"
    exit 1
fi

# 테스트 실행
echo "6. 라이브러리 테스트 실행 중..."
python test_library.py
if [ $? -eq 0 ]; then
    echo "   ✅ 테스트 통과"
else
    echo "   ⚠️  테스트 실패 - 하지만 설치는 완료되었습니다"
fi

echo ""
echo "🎉 라이브러리 빌드 및 설치 완료!"
echo ""
echo "📚 사용법:"
echo "   python -c 'from hoon_firewall_modules import PolicyComparator; print(\"라이브러리 import 성공!\")'"
echo ""
echo "📦 패키지 파일 위치: dist/"
echo "   - $(ls dist/*.whl 2>/dev/null || echo '빌드된 wheel 파일 없음')"
echo "   - $(ls dist/*.tar.gz 2>/dev/null || echo '빌드된 source 파일 없음')" 
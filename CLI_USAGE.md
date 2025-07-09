# 🔥 FPAT CLI 사용 가이드

FPAT CLI는 방화벽 정책 분석을 위한 고급 명령줄 도구입니다.

## ✅ 최신 업데이트 (Interactive 모드 실제 연동 완료!)

이제 **모든 Interactive 모드 기능이 실제 FPAT 모듈과 연동**되어 완전히 작동합니다:

- 🛡️ **방화벽 데이터 수집**: 실제 방화벽에서 정책/객체 데이터 추출
- 🔍 **정책/객체 비교**: 변경사항을 실제로 분석하고 Excel로 저장  
- 📊 **정책 분석**: 중복성, Shadow, IP 필터링 실제 수행
- 🗑️ **삭제 영향도 분석**: 정책 삭제 전 실제 영향도 분석
- 💾 **Excel 자동 저장**: 모든 결과가 실제로 Excel 파일로 저장

## 📦 설치

먼저 필요한 패키지들을 설치합니다:

```bash
pip install -r requirements.txt
```

## 🚀 빠른 시작

### 1. 🎯 대화형 모드 (추천)
```bash
python3 fpat_cli.py interactive
```

### 2. 📋 메뉴 보기
```bash
python3 fpat_cli.py menu
```

### 3. ⚡ 자동완성 설정
```bash
# 자동으로 설치
python3 fpat_cli.py --install-completion

# 수동 설정 방법 보기
python3 fpat_cli.py completion
```

### 4. 도움말 확인
```bash
python3 fpat_cli.py --help
```

## 🛡️ 방화벽 연동 (firewall)

### 방화벽 설정 추가
```bash
python fpat_cli.py firewall add \
    --name "production-fw" \
    --hostname "192.168.1.100" \
    --username "admin" \
    --password "password123" \
    --vendor "paloalto"
```

### 방화벽 목록 보기
```bash
python fpat_cli.py firewall list
```

### 데이터 수집
```bash
# 정책과 객체 모두 수집
python fpat_cli.py firewall collect --name "production-fw"

# 정책만 수집
python fpat_cli.py firewall collect --name "production-fw" --no-objects

# 객체만 수집
python fpat_cli.py firewall collect --name "production-fw" --no-policies

# 출력 파일명 지정
python fpat_cli.py firewall collect --name "production-fw" --output "fw_data.xlsx"
```

## 🔍 정책 비교 (compare)

### 정책 비교
```bash
python fpat_cli.py compare policies \
    --old "old_policies.xlsx" \
    --new "new_policies.xlsx" \
    --output "policy_changes.xlsx"
```

### 객체 비교
```bash
python fpat_cli.py compare objects \
    --old "old_objects.xlsx" \
    --new "new_objects.xlsx" \
    --output "object_changes.xlsx"
```

### 전체 비교 (정책 + 객체)
```bash
python fpat_cli.py compare full \
    --old-policy "old_policies.xlsx" \
    --new-policy "new_policies.xlsx" \
    --old-objects "old_objects.xlsx" \
    --new-objects "new_objects.xlsx" \
    --output "full_comparison.xlsx"
```

## 📊 정책 분석 (analyze)

### 중복성 분석
```bash
python fpat_cli.py analyze redundancy \
    --file "policies.xlsx" \
    --vendor "paloalto" \
    --output "redundancy_report.xlsx"
```

### Shadow 정책 분석
```bash
python fpat_cli.py analyze shadow \
    --file "policies.xlsx" \
    --vendor "paloalto" \
    --output "shadow_report.xlsx"
```

### IP 주소 기반 필터링
```bash
# Source 주소로 필터링
python fpat_cli.py analyze filter \
    --file "policies.xlsx" \
    --address "192.168.1.0/24" \
    --type "source" \
    --include-any \
    --output "filtered_policies.xlsx"

# Destination 주소로 필터링
python fpat_cli.py analyze filter \
    --file "policies.xlsx" \
    --address "10.0.0.0/8" \
    --type "destination" \
    --exclude-any

# 양방향 검색
python fpat_cli.py analyze filter \
    --file "policies.xlsx" \
    --address "192.168.1.100" \
    --type "both"

# IP 범위 검색
python fpat_cli.py analyze filter \
    --file "policies.xlsx" \
    --address "192.168.1.1-192.168.1.100" \
    --type "source"
```

## 🗑️ 삭제 영향도 분석 (deletion)

```bash
python fpat_cli.py deletion analyze \
    --file "policies.xlsx" \
    --policies "policy1,policy2,policy3" \
    --output "deletion_impact.xlsx"
```

## 📁 출력 파일

모든 결과는 Excel 파일로 저장되며, 기본 출력 디렉토리는 `./outputs`입니다.

### 출력 디렉토리 변경
설정 파일 `~/.fpat_config.json`을 편집하여 출력 디렉토리를 변경할 수 있습니다:

```json
{
  "output_dir": "/path/to/custom/output",
  "log_level": "INFO",
  "excel_format": "xlsx"
}
```

## 🎨 고급 기능

### 🎯 대화형 모드 (Interactive Mode)
```bash
# 전체 기능을 대화형으로 사용
python3 fpat_cli.py interactive
```
- 📋 메뉴 기반 선택
- 🔍 자동 파일 검색 및 선택
- ✅ 단계별 안내
- 🎨 아름다운 UI

### ⚡ 자동완성 (Tab Completion)
```bash
# 1단계: 자동완성 설치
python3 fpat_cli.py --install-completion

# 2단계: 새 터미널 열기 또는 reload
source ~/.bashrc

# 3단계: Tab 키로 자동완성 사용!
python3 fpat_cli.py fire[TAB]    # → firewall
python3 fpat_cli.py firewall [TAB]    # → add, collect, list
```

#### 자동완성 지원 항목:
- ✅ **명령어**: `firewall`, `analyze`, `compare`, `deletion`
- ✅ **방화벽 이름**: 저장된 방화벽 목록 자동완성
- ✅ **벤더**: `paloalto`, `ngf`, `mf2`, `mock`
- ✅ **파일명**: 현재 디렉토리의 `.xlsx`, `.xls` 파일
- ✅ **검색 타입**: `source`, `destination`, `both`

### Verbose 모드
```bash
python3 fpat_cli.py -v analyze redundancy --file "policies.xlsx"
```

### 사용자 정의 설정 파일
```bash
python3 fpat_cli.py --config "/path/to/config.json" firewall list
```

### 버전 확인
```bash
python3 fpat_cli.py version
```

## 💡 사용 팁

1. **🎯 대화형 모드 우선 사용**: `python3 fpat_cli.py interactive` 명령어로 모든 기능을 편리하게 사용할 수 있습니다.

2. **⚡ 자동완성 활용**: Tab 키를 눌러 명령어, 파일명, 옵션을 자동완성하세요.

3. **📋 메뉴 활용**: `python3 fpat_cli.py menu` 명령어로 사용 가능한 모든 기능을 확인할 수 있습니다.

4. **📖 도움말**: 각 명령어에 `--help`를 붙이면 상세한 도움말을 볼 수 있습니다.

5. **📊 결과 확인**: 모든 작업 완료 후 결과 요약이 화면에 표시됩니다.

6. **⏱️ 진행률 표시**: 시간이 오래 걸리는 작업들은 실시간 진행률을 표시합니다.

7. **🔧 오류 처리**: 상세한 오류 메시지와 해결 방법이 제공됩니다.

8. **🎨 Rich UI**: 컬러풀하고 구조화된 출력으로 정보를 쉽게 파악할 수 있습니다.

## 🔧 문제 해결

### 모듈을 찾을 수 없는 경우
```bash
# FPAT 모듈이 설치되어 있는지 확인
pip list | grep fpat

# 개발 모드로 설치
pip install -e .
```

### 권한 오류
```bash
# 실행 권한 부여
chmod +x fpat_cli.py
```

### 메모리 부족
대용량 파일 처리 시 메모리가 부족할 수 있습니다. 이 경우 파일을 분할하여 처리하거나 더 많은 메모리를 가진 환경에서 실행하세요.

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 파일 경로가 올바른지 확인
2. 파일 형식이 Excel인지 확인  
3. 필요한 권한이 있는지 확인
4. 로그를 확인하여 자세한 오류 정보 파악

상세한 로그는 `-v` 옵션으로 확인할 수 있습니다.
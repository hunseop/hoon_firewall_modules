# Hoon Firewall Modules

방화벽 정책 관리를 위한 통합 Python 라이브러리입니다.

## 🚀 주요 기능

- **정책 비교**: 방화벽 정책과 객체의 변경사항을 비교하고 분석
- **다중 벤더 지원**: PaloAlto, NGF, MF2 등 다양한 방화벽 벤더 지원
- **정책 분석**: 중복성, 변경사항, 사용현황, Shadow 정책 분석
- **정책 필터링**: IP 주소, CIDR, 범위 기반 정책 검색
- **삭제 시나리오**: 정책 삭제 영향도 분석 및 처리

## 📦 설치

### GitHub에서 직접 설치
```bash
pip install git+https://github.com/yourusername/hoon_firewall_modules.git
```

### 로컬 개발 설치
```bash
git clone https://github.com/yourusername/hoon_firewall_modules.git
cd hoon-firewall-modules
pip install -e .
```

### PyPI에서 설치 (향후)
```bash
pip install hoon-firewall-modules
```

## 🔧 사용법

### 1. 정책 비교

```python
from hoon_firewall_modules import PolicyComparator

# 정책 비교 인스턴스 생성
comparator = PolicyComparator(
    policy_old="old_policy.xlsx",
    policy_new="new_policy.xlsx", 
    object_old="old_objects.xlsx",
    object_new="new_objects.xlsx"
)

# 객체 변경사항 비교
comparator.compare_all_objects()

# 정책 변경사항 비교
comparator.compare_policies()
```

### 2. 방화벽 연동

```python
from hoon_firewall_modules import FirewallCollectorFactory

# PaloAlto 방화벽 연결
firewall = FirewallCollectorFactory.get_collector(
    source_type="paloalto",
    hostname="192.168.1.1",
    username="admin",
    password="password"
)

# 정책 데이터 수집
policies = firewall.export_security_rules()
objects = firewall.export_network_objects()
```

### 3. 정책 분석

```python
from modules.firewall_analyzer import PolicyAnalyzer, RedundancyAnalyzer, ShadowAnalyzer, PolicyFilter
import pandas as pd

# 정책 데이터 로드
df = pd.read_excel("policies.xlsx")

# 중복 정책 분석
redundancy_analyzer = RedundancyAnalyzer()
redundancy_result = redundancy_analyzer.analyze(df, vendor="paloalto")

# Shadow 정책 분석
shadow_analyzer = ShadowAnalyzer()
shadow_result = shadow_analyzer.analyze(df, vendor="paloalto")

# 정책 필터링 (IP 주소 기반)
policy_filter = PolicyFilter()

# Source 주소로 필터링
filtered_policies = policy_filter.filter_by_source(
    df, 
    search_address="192.168.1.0/24",
    include_any=True
)

# Destination 주소로 필터링
filtered_policies = policy_filter.filter_by_destination(
    df,
    search_address="10.0.0.0/8", 
    include_any=False
)

# 복합 조건 필터링
filtered_policies = policy_filter.filter_by_criteria(
    df,
    source_address="192.168.1.0/24",
    destination_address="10.0.0.0/8",
    match_mode="AND",
    include_any=True
)
```

### 4. 모듈별 사용법

```python
# 기본 사용법 (권장)
from modules.policy_comparator import PolicyComparator
from modules.firewall_analyzer import (
    PolicyAnalyzer, 
    RedundancyAnalyzer, 
    ShadowAnalyzer, 
    PolicyFilter
)
from modules.firewall_module import FirewallInterface

# 고급 기능 (개별 import)
from modules.firewall_module.collector_factory import FirewallCollectorFactory
from modules.policy_deletion_processor.processors import policy_usage_processor
```

### 5. 정책 필터링 상세 사용법

```python
from modules.firewall_analyzer import PolicyFilter
import pandas as pd

# PolicyFilter 인스턴스 생성
filter_obj = PolicyFilter()

# 정책 데이터 로드
df = pd.read_excel("firewall_policies.xlsx")

# 1. Source 주소 기반 필터링
# CIDR 검색
source_filtered = filter_obj.filter_by_source(
    df, 
    search_address="192.168.1.0/24",
    include_any=True,      # any 정책 포함 여부
    use_extracted=True     # Extracted Source 컬럼 사용 여부
)

# IP 범위 검색
source_filtered = filter_obj.filter_by_source(
    df, 
    search_address="192.168.1.1-192.168.1.100",
    include_any=False
)

# 단일 IP 검색
source_filtered = filter_obj.filter_by_source(
    df, 
    search_address="192.168.1.100",
    include_any=False
)

# 2. Destination 주소 기반 필터링
dest_filtered = filter_obj.filter_by_destination(
    df,
    search_address="10.0.0.0/8",
    include_any=False
)

# 3. Source 또는 Destination 모두 검색
both_filtered = filter_obj.filter_by_both(
    df,
    search_address="192.168.1.0/24",
    include_any=True
)

# 4. 복합 조건 필터링
# AND 모드: Source와 Destination 모두 만족
and_filtered = filter_obj.filter_by_criteria(
    df,
    source_address="192.168.1.0/24",
    destination_address="10.0.0.0/8", 
    match_mode="AND",
    include_any=True
)

# OR 모드: Source 또는 Destination 중 하나만 만족
or_filtered = filter_obj.filter_by_criteria(
    df,
    source_address="192.168.1.0/24",
    destination_address="10.0.0.0/8",
    match_mode="OR", 
    include_any=False
)

# 5. 필터링 결과 요약
summary = filter_obj.get_filter_summary(
    original_df=df,
    filtered_df=source_filtered,
    search_criteria={
        'search_type': 'source',
        'address': '192.168.1.0/24',
        'include_any': True
    }
)

print(f"총 정책 수: {summary['total_policies']}")
print(f"매치된 정책 수: {summary['matched_policies']}")
print(f"매치 비율: {summary['match_percentage']:.1f}%")
```

### 6. 고급 사용법

```python
# 방화벽 컬렉터 팩토리 사용 (복잡한 의존성)
from modules.firewall_module.collector_factory import FirewallCollectorFactory

collector = FirewallCollectorFactory.get_collector(
    source_type="paloalto",
    hostname="192.168.1.1", 
    username="admin",
    password="password"
)

# 삭제 시나리오 처리
from modules.policy_deletion_processor.processors import policy_usage_processor
from modules.policy_deletion_processor.utils import excel_manager
```

## 📚 모듈 구조

```
hoon_firewall_modules/
├── modules/
│   ├── policy_comparator/     # 정책 비교 기능
│   ├── firewall_module/       # 방화벽 연동 기능
│   ├── firewall_analyzer/       # 정책 분석 기능
│   └── policy_deletion_processor/       # 삭제 시나리오 처리
```

## 🔧 지원 방화벽

- **PaloAlto Networks**: PAN-OS
- **NGF**: SECUI NGF
- **MF2**: SECUI MF2
- **Mock**: 테스트 및 개발용

## 📋 요구사항

- Python 3.8+
- pandas >= 1.3.0
- openpyxl >= 3.0.0
- requests >= 2.25.0

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👤 작성자

**Hoon**
- Email: khunseop@gmail.com
- GitHub: [@hunseop](https://github.com/hunseop)

## 🆕 변경 사항

### v1.1.0
- **PolicyFilter** 추가: IP 주소, CIDR, 범위 기반 정책 필터링 기능
- **ShadowAnalyzer** 추가: Shadow 정책 분석 기능
- 정책 관리 필터링 기능 강화
- 복합 조건 검색 지원 (AND/OR 모드)
- any 포함 여부 설정 가능

### v1.0.0
- 초기 릴리스
- 정책 비교 기능 추가
- 다중 벤더 방화벽 지원
- 정책 분석 기능 추가 
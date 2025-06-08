# Hoon Firewall Modules

방화벽 정책 관리를 위한 통합 Python 라이브러리입니다.

## 🚀 주요 기능

- **정책 비교**: 방화벽 정책과 객체의 변경사항을 비교하고 분석
- **다중 벤더 지원**: PaloAlto, NGF, MF2 등 다양한 방화벽 벤더 지원
- **정책 분석**: 중복성, 변경사항, 사용현황 분석
- **삭제 시나리오**: 정책 삭제 영향도 분석 및 처리

## 📦 설치

### GitHub에서 직접 설치
```bash
pip install git+https://github.com/yourusername/hoon-firewall-modules.git
```

### 로컬 개발 설치
```bash
git clone https://github.com/yourusername/hoon-firewall-modules.git
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
from hoon_firewall_modules import PolicyAnalyzer
import pandas as pd

# 분석기 초기화
analyzer = PolicyAnalyzer()

# 정책 데이터 로드
df = pd.read_excel("policies.xlsx")

# 중복 정책 분석
result = analyzer.analyze_redundancy(
    df=df,
    vendor="paloalto", 
    output_file="redundancy_analysis.xlsx"
)
```

### 4. 모듈별 사용법

```python
# 기본 사용법 (권장)
from modules.policy_comparator import PolicyComparator
from modules.analysis_module import PolicyAnalyzer, RedundancyAnalyzer
from modules.firewall_module import FirewallInterface

# 고급 기능 (개별 import)
from modules.firewall_module.collector_factory import FirewallCollectorFactory
from modules.delete_scenario.processors import policy_usage_processor
```

### 5. 고급 사용법

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
from modules.delete_scenario.processors import policy_usage_processor
from modules.delete_scenario.utils import excel_manager
```

## 📚 모듈 구조

```
hoon_firewall_modules/
├── modules/
│   ├── policy_comparator/     # 정책 비교 기능
│   ├── firewall_module/       # 방화벽 연동 기능
│   ├── analysis_module/       # 정책 분석 기능
│   └── delete_scenario/       # 삭제 시나리오 처리
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

### v1.0.0
- 초기 릴리스
- 정책 비교 기능 추가
- 다중 벤더 방화벽 지원
- 정책 분석 기능 추가 
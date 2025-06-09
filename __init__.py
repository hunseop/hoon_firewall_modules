"""
Hoon Firewall Modules - 방화벽 정책 관리를 위한 통합 라이브러리

이 라이브러리는 다음과 같은 기능을 제공합니다:
- 방화벽 정책 비교 및 분석
- 다양한 방화벽 벤더 지원 (PaloAlto, NGF, MF2 등)
- 정책 중복성 및 변경사항 분석
- 정책 삭제 시나리오 처리
"""

__version__ = "1.0.0"
__author__ = "Hoon"
__email__ = "your-email@example.com"

# 주요 클래스들을 최상위 레벨에서 import 가능하게 함
try:
    from modules.policy_comparator.comparator import PolicyComparator
    from modules.policy_comparator.excel_formatter import save_results_to_excel
    from modules.firewall_module.firewall_interface import FirewallInterface
    from modules.firewall_module.exporter import export_policy_to_excel
    from modules.firewall_analyzer import PolicyAnalyzer, RedundancyAnalyzer, ChangeAnalyzer, PolicyResolver
    
    # 각 모듈별로 네임스페이스 제공
    import modules
except ImportError:
    # 상대 import로 시도
    from .modules.policy_comparator.comparator import PolicyComparator
    from .modules.policy_comparator.excel_formatter import save_results_to_excel
    from .modules.firewall_module.firewall_interface import FirewallInterface
    from .modules.firewall_module.exporter import export_policy_to_excel
    from .modules.firewall_analyzer import PolicyAnalyzer, RedundancyAnalyzer, ChangeAnalyzer, PolicyResolver
    
    # 각 모듈별로 네임스페이스 제공
    from . import modules

# 복잡한 의존성이 있는 클래스들은 개별 import 권장:
# from modules.firewall_module.collector_factory import FirewallCollectorFactory

__all__ = [
    # 정책 비교 관련
    'PolicyComparator',
    'save_results_to_excel',
    
    # 방화벽 모듈 관련
    'FirewallInterface', 
    'export_policy_to_excel',
    
    # 분석 모듈 관련
    'PolicyAnalyzer',
    'RedundancyAnalyzer', 
    'ChangeAnalyzer',
    'PolicyResolver',
    
    # 모듈 네임스페이스
    'modules',
] 
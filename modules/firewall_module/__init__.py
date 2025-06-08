"""
방화벽 모듈 - 다양한 방화벽 벤더와 연동하는 통합 인터페이스를 제공합니다.

지원 벤더:
- PaloAlto Networks
- NGF (Next Generation Firewall)
- MF2 (Multi-Function Firewall 2)
- Mock (테스트용)

주요 기능:
- 방화벽 추상 인터페이스 (FirewallInterface)
- 벤더별 컬렉터 팩토리 (CollectorFactory)
- 데이터 익스포터 (Exporter)
"""

from .firewall_interface import FirewallInterface
from .exporter import export_policy_to_excel

# collector_factory는 복잡한 의존성이 있어서 개별 import 권장
# from .collector_factory import FirewallCollectorFactory

__all__ = ['FirewallInterface', 'export_policy_to_excel']

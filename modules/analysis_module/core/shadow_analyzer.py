"""
Shadow 정책 분석을 위한 클래스입니다.
Shadow 정책은 다른 정책에 의해 가려져서 실제로 적용되지 않는 정책을 의미합니다.
"""

import pandas as pd
import logging
import ipaddress
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from .policy_resolver import PolicyResolver
from .redundancy_analyzer import RedundancyAnalyzer

class ShadowAnalyzer:
    """Shadow 정책 분석을 위한 클래스"""
    
    def __init__(self):
        """ShadowAnalyzer 초기화"""
        self.logger = logging.getLogger(__name__)
        self.policy_resolver = PolicyResolver()
        self.redundancy_analyzer = RedundancyAnalyzer()
        
        # 벤더별 분석 컬럼 정의
        self.vendor_columns = {
            'paloalto': ['Enable', 'Action', 'Extracted Source', 'Extracted Destination', 'Extracted Service', 'Application', 'User'],
            'ngf': ['Enable', 'Action', 'Extracted Source', 'Extracted Destination', 'Extracted Service', 'Application', 'User'],
            'default': ['Enable', 'Action', 'Extracted Source', 'Extracted Destination', 'Extracted Service', 'Application', 'User']
        }
    
    def _normalize_ip_range(self, ip_str: str) -> Set[str]:
        """
        IP 주소나 범위를 정규화합니다.
        
        Args:
            ip_str: IP 주소 문자열 (콤마로 구분된 여러 IP 가능)
        
        Returns:
            정규화된 IP 주소 집합
        """
        normalized_ips = set()
        
        if not ip_str or ip_str.strip() in ['any', 'Any', 'ANY', '']:
            return {'any'}
        
        for ip in str(ip_str).split(','):
            ip = ip.strip()
            if not ip:
                continue
                
            try:
                # CIDR 형태 처리
                if '/' in ip:
                    network = ipaddress.ip_network(ip, strict=False)
                    normalized_ips.add(str(network))
                # 범위 형태 처리 (예: 192.168.1.1-192.168.1.10)
                elif '-' in ip and '.' in ip:
                    normalized_ips.add(ip)
                # 단일 IP 처리
                else:
                    try:
                        single_ip = ipaddress.ip_address(ip)
                        normalized_ips.add(f"{single_ip}/32")
                    except:
                        # IP가 아닌 경우 (호스트명 등) 그대로 추가
                        normalized_ips.add(ip)
            except:
                # 파싱 실패시 원본 그대로 추가
                normalized_ips.add(ip)
        
        return normalized_ips if normalized_ips else {'any'}
    
    def _normalize_port_range(self, port_str: str) -> Set[str]:
        """
        포트나 서비스를 정규화합니다.
        
        Args:
            port_str: 포트 문자열 (콤마로 구분된 여러 포트 가능)
        
        Returns:
            정규화된 포트 집합
        """
        normalized_ports = set()
        
        if not port_str or port_str.strip() in ['any', 'Any', 'ANY', '']:
            return {'any'}
        
        for port in str(port_str).split(','):
            port = port.strip()
            if not port:
                continue
            
            # 프로토콜/포트 형태 처리 (예: TCP/80, UDP/53)
            if '/' in port:
                normalized_ports.add(port.upper())
            else:
                normalized_ports.add(port)
        
        return normalized_ports if normalized_ports else {'any'}
    
    def _is_ip_subset(self, subset_ips: Set[str], superset_ips: Set[str]) -> bool:
        """
        한 IP 집합이 다른 IP 집합의 부분집합인지 확인합니다.
        
        Args:
            subset_ips: 부분집합 후보
            superset_ips: 상위집합 후보
        
        Returns:
            부분집합 여부
        """
        # any가 있으면 모든 것을 포함
        if 'any' in superset_ips:
            return True
        if 'any' in subset_ips and 'any' not in superset_ips:
            return False
        
        # 실제 IP 범위 비교 로직 (간단한 버전)
        for subset_ip in subset_ips:
            covered = False
            for superset_ip in superset_ips:
                if subset_ip == superset_ip:
                    covered = True
                    break
                # CIDR 범위 체크 (간단한 버전)
                try:
                    if '/' in subset_ip and '/' in superset_ip:
                        subset_net = ipaddress.ip_network(subset_ip, strict=False)
                        superset_net = ipaddress.ip_network(superset_ip, strict=False)
                        if subset_net.subnet_of(superset_net):
                            covered = True
                            break
                except:
                    continue
            
            if not covered:
                return False
        
        return True
    
    def _is_port_subset(self, subset_ports: Set[str], superset_ports: Set[str]) -> bool:
        """
        한 포트 집합이 다른 포트 집합의 부분집합인지 확인합니다.
        
        Args:
            subset_ports: 부분집합 후보
            superset_ports: 상위집합 후보
        
        Returns:
            부분집합 여부
        """
        # any가 있으면 모든 것을 포함
        if 'any' in superset_ports:
            return True
        if 'any' in subset_ports and 'any' not in superset_ports:
            return False
        
        # 포트 범위 비교 (간단한 버전)
        for subset_port in subset_ports:
            if subset_port not in superset_ports:
                return False
        
        return True
    
    def _is_shadowed_by(self, policy1: pd.Series, policy2: pd.Series) -> bool:
        """
        policy1이 policy2에 의해 가려지는지 확인합니다.
        
        Args:
            policy1: 가려질 수 있는 정책
            policy2: 가릴 수 있는 정책
        
        Returns:
            가려짐 여부
        """
        # 둘 다 활성화되어 있어야 함
        if policy1.get('Enable', 'N') != 'Y' or policy2.get('Enable', 'N') != 'Y':
            return False
        
        # Action이 다르면 shadow 관계가 성립하지 않음
        if policy1.get('Action', '').lower() != policy2.get('Action', '').lower():
            return False
        
        # Source IP 범위 체크
        policy1_src = self._normalize_ip_range(policy1.get('Extracted Source', ''))
        policy2_src = self._normalize_ip_range(policy2.get('Extracted Source', ''))
        
        if not self._is_ip_subset(policy1_src, policy2_src):
            return False
        
        # Destination IP 범위 체크
        policy1_dst = self._normalize_ip_range(policy1.get('Extracted Destination', ''))
        policy2_dst = self._normalize_ip_range(policy2.get('Extracted Destination', ''))
        
        if not self._is_ip_subset(policy1_dst, policy2_dst):
            return False
        
        # Service/Port 범위 체크
        policy1_svc = self._normalize_port_range(policy1.get('Extracted Service', ''))
        policy2_svc = self._normalize_port_range(policy2.get('Extracted Service', ''))
        
        if not self._is_port_subset(policy1_svc, policy2_svc):
            return False
        
        # Application 체크 (있는 경우)
        if 'Application' in policy1 and 'Application' in policy2:
            app1 = str(policy1.get('Application', 'any')).lower()
            app2 = str(policy2.get('Application', 'any')).lower()
            
            if app2 != 'any' and app1 != 'any' and app1 != app2:
                return False
        
        # User 체크 (있는 경우)
        if 'User' in policy1 and 'User' in policy2:
            user1 = str(policy1.get('User', 'any')).lower()
            user2 = str(policy2.get('User', 'any')).lower()
            
            if user2 != 'any' and user1 != 'any' and user1 != user2:
                return False
        
        return True
    
    def _prepare_data(self, df: pd.DataFrame, vendor: str) -> pd.DataFrame:
        """
        분석을 위해 데이터를 준비합니다.
        
        Args:
            df: 원본 데이터프레임
            vendor: 방화벽 벤더
        
        Returns:
            전처리된 데이터프레임
        """
        # 복사본 생성
        df_prepared = df.copy()
        
        # Extracted 컬럼이 없으면 원본 컬럼 사용
        if 'Extracted Source' not in df_prepared.columns:
            if 'Source' in df_prepared.columns:
                df_prepared['Extracted Source'] = df_prepared['Source']
        
        if 'Extracted Destination' not in df_prepared.columns:
            if 'Destination' in df_prepared.columns:
                df_prepared['Extracted Destination'] = df_prepared['Destination']
        
        if 'Extracted Service' not in df_prepared.columns:
            if 'Service' in df_prepared.columns:
                df_prepared['Extracted Service'] = df_prepared['Service']
        
        # 활성화된 정책만 필터링
        df_prepared = df_prepared[df_prepared.get('Enable', 'Y') == 'Y'].copy()
        
        # 인덱스 리셋
        df_prepared = df_prepared.reset_index(drop=True)
        
        return df_prepared
    
    def analyze(self, df: pd.DataFrame, vendor: str = 'default', **kwargs) -> pd.DataFrame:
        """
        Shadow 정책을 분석합니다.
        
        Args:
            df: 분석할 정책 데이터프레임
            vendor: 방화벽 벤더
            **kwargs: 추가 매개변수
        
        Returns:
            분석 결과 데이터프레임
        """
        try:
            self.logger.info("Shadow 정책 분석 시작")
            
            # 데이터 준비
            df_prepared = self._prepare_data(df, vendor)
            
            if df_prepared.empty:
                self.logger.warning("분석할 활성화된 정책이 없습니다.")
                return pd.DataFrame()
            
            # Shadow 관계 분석
            shadow_results = []
            total = len(df_prepared)
            
            self.logger.info("Shadow 정책 관계 분석 중...")
            
            for i in range(total):
                # 진행률 표시
                if i % max(1, total // 10) == 0 or i == total - 1:
                    progress = (i + 1) / total * 100
                    print(f"\rShadow 정책 분석 중: {progress:.1f}% ({i + 1}/{total})", end='', flush=True)
                
                current_policy = df_prepared.iloc[i]
                
                # 현재 정책보다 앞에 있는 정책들과 비교
                for j in range(i):
                    earlier_policy = df_prepared.iloc[j]
                    
                    # 현재 정책이 앞선 정책에 의해 가려지는지 확인
                    if self._is_shadowed_by(current_policy, earlier_policy):
                        shadow_result = current_policy.to_dict()
                        shadow_result.update({
                            'Shadow_Type': 'Shadowed',
                            'Shadow_By_Index': j,
                            'Shadow_By_Rule': earlier_policy.get('Rule Name', f"Rule_{j}"),
                            'Shadow_Reason': f"Rule at index {j} covers this rule completely"
                        })
                        shadow_results.append(shadow_result)
                        break  # 첫 번째 shadow를 찾으면 중단
            
            print()  # 줄바꿈
            
            # 결과 데이터프레임 생성
            if not shadow_results:
                self.logger.info("Shadow 정책이 발견되지 않았습니다.")
                return pd.DataFrame()
            
            results_df = pd.DataFrame(shadow_results)
            
            # 컬럼 순서 재조정
            shadow_columns = ['Shadow_Type', 'Shadow_By_Index', 'Shadow_By_Rule', 'Shadow_Reason']
            other_columns = [col for col in results_df.columns if col not in shadow_columns]
            results_df = results_df[shadow_columns + other_columns]
            
            self.logger.info(f"Shadow 정책 분석 완료. {len(results_df)}개의 shadow 정책 발견")
            return results_df
            
        except Exception as e:
            self.logger.error(f"Shadow 정책 분석 중 오류 발생: {e}")
            raise
    
    def get_shadow_summary(self, df: pd.DataFrame) -> Dict:
        """
        Shadow 분석 결과 요약을 반환합니다.
        
        Args:
            df: analyze() 메서드의 결과 데이터프레임
        
        Returns:
            요약 정보 딕셔너리
        """
        if df.empty:
            return {
                'total_shadow_policies': 0,
                'shadow_by_action': {},
                'most_shadowing_rules': []
            }
        
        summary = {
            'total_shadow_policies': len(df),
            'shadow_by_action': df.get('Action', pd.Series()).value_counts().to_dict(),
            'most_shadowing_rules': df['Shadow_By_Rule'].value_counts().head(5).to_dict() if 'Shadow_By_Rule' in df.columns else {}
        }
        
        return summary 
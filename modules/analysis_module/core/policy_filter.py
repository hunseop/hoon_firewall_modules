"""
정책 필터링을 위한 클래스입니다.
IP 주소, CIDR, 범위를 기준으로 방화벽 정책을 검색하고 추출하는 기능을 제공합니다.
"""

import pandas as pd
import logging
import ipaddress
from typing import Dict, List, Tuple, Set, Optional, Union
import re

class PolicyFilter:
    """정책 필터링을 위한 클래스"""
    
    def __init__(self):
        """PolicyFilter 초기화"""
        self.logger = logging.getLogger(__name__)
    
    def _normalize_ip_input(self, ip_input: str) -> Set[str]:
        """
        입력된 IP 주소를 정규화합니다.
        
        Args:
            ip_input: IP 주소 문자열 (CIDR, Range, Single IP)
        
        Returns:
            정규화된 IP 주소 집합
        """
        normalized_ips = set()
        
        if not ip_input or ip_input.strip().lower() in ['any', '']:
            return {'any'}
        
        # 콤마로 구분된 여러 IP 처리
        for ip_part in str(ip_input).split(','):
            ip_part = ip_part.strip()
            if not ip_part:
                continue
            
            try:
                # CIDR 형태 처리
                if '/' in ip_part:
                    network = ipaddress.ip_network(ip_part, strict=False)
                    normalized_ips.add(str(network))
                # 범위 형태 처리 (예: 192.168.1.1-192.168.1.10)
                elif '-' in ip_part and '.' in ip_part:
                    normalized_ips.add(ip_part)
                # 단일 IP 처리
                else:
                    try:
                        single_ip = ipaddress.ip_address(ip_part)
                        normalized_ips.add(str(single_ip))
                    except:
                        # IP가 아닌 경우 (호스트명 등) 그대로 추가
                        normalized_ips.add(ip_part)
            except Exception as e:
                self.logger.warning(f"IP 주소 파싱 실패: {ip_part} - {e}")
                # 파싱 실패시 원본 그대로 추가
                normalized_ips.add(ip_part)
        
        return normalized_ips if normalized_ips else {'any'}
    
    def _parse_policy_ips(self, policy_ip_str: str) -> Set[str]:
        """
        정책의 IP 주소 문자열을 파싱합니다.
        
        Args:
            policy_ip_str: 정책의 IP 주소 문자열
        
        Returns:
            파싱된 IP 주소 집합
        """
        if not policy_ip_str or str(policy_ip_str).strip().lower() in ['any', 'any4', '']:
            return {'any'}
        
        policy_ips = set()
        
        for ip in str(policy_ip_str).split(','):
            ip = ip.strip()
            if not ip:
                continue
            
            try:
                # CIDR 형태
                if '/' in ip:
                    network = ipaddress.ip_network(ip, strict=False)
                    policy_ips.add(str(network))
                # 범위 형태
                elif '-' in ip and '.' in ip:
                    policy_ips.add(ip)
                # 단일 IP
                else:
                    try:
                        single_ip = ipaddress.ip_address(ip)
                        policy_ips.add(str(single_ip))
                    except:
                        policy_ips.add(ip)
            except:
                policy_ips.add(ip)
        
        return policy_ips if policy_ips else {'any'}
    
    def _is_ip_match(self, search_ips: Set[str], policy_ips: Set[str], include_any: bool = True) -> bool:
        """
        검색 IP와 정책 IP가 매치되는지 확인합니다.
        
        Args:
            search_ips: 검색할 IP 집합
            policy_ips: 정책의 IP 집합
            include_any: any를 포함할지 여부
        
        Returns:
            매치 여부
        """
        # any 처리
        if include_any:
            if 'any' in policy_ips or 'any' in search_ips:
                return True
        
        # 정확한 매치 확인
        for search_ip in search_ips:
            for policy_ip in policy_ips:
                if self._ip_overlaps(search_ip, policy_ip):
                    return True
        
        return False
    
    def _ip_overlaps(self, ip1: str, ip2: str) -> bool:
        """
        두 IP 주소/범위가 겹치는지 확인합니다.
        
        Args:
            ip1: 첫 번째 IP
            ip2: 두 번째 IP
        
        Returns:
            겹침 여부
        """
        if ip1 == ip2:
            return True
        
        if ip1 == 'any' or ip2 == 'any':
            return True
        
        try:
            # 둘 다 CIDR인 경우
            if '/' in ip1 and '/' in ip2:
                net1 = ipaddress.ip_network(ip1, strict=False)
                net2 = ipaddress.ip_network(ip2, strict=False)
                return net1.overlaps(net2)
            
            # 하나는 CIDR, 하나는 단일 IP인 경우
            elif '/' in ip1:
                net1 = ipaddress.ip_network(ip1, strict=False)
                addr2 = ipaddress.ip_address(ip2)
                return addr2 in net1
            elif '/' in ip2:
                net2 = ipaddress.ip_network(ip2, strict=False)
                addr1 = ipaddress.ip_address(ip1)
                return addr1 in net2
            
            # 범위 처리 (간단한 버전)
            elif '-' in ip1 or '-' in ip2:
                return self._range_overlaps(ip1, ip2)
            
            # 둘 다 단일 IP인 경우
            else:
                addr1 = ipaddress.ip_address(ip1)
                addr2 = ipaddress.ip_address(ip2)
                return addr1 == addr2
                
        except Exception as e:
            self.logger.debug(f"IP 비교 중 오류: {ip1} vs {ip2} - {e}")
            # 문자열 비교로 폴백
            return ip1 == ip2
    
    def _range_overlaps(self, ip1: str, ip2: str) -> bool:
        """
        IP 범위가 겹치는지 확인합니다. (간단한 구현)
        
        Args:
            ip1: 첫 번째 IP 또는 범위
            ip2: 두 번째 IP 또는 범위
        
        Returns:
            겹침 여부
        """
        try:
            # 범위를 CIDR로 변환하여 비교하는 간단한 방법
            # 실제 구현에서는 더 정교한 범위 비교가 필요할 수 있습니다
            
            def parse_range(ip_range):
                if '-' in ip_range:
                    start_str, end_str = ip_range.split('-', 1)
                    start_ip = ipaddress.ip_address(start_str.strip())
                    end_ip = ipaddress.ip_address(end_str.strip())
                    return start_ip, end_ip
                else:
                    ip = ipaddress.ip_address(ip_range)
                    return ip, ip
            
            start1, end1 = parse_range(ip1)
            start2, end2 = parse_range(ip2)
            
            # 범위 겹침 확인
            return not (end1 < start2 or end2 < start1)
            
        except Exception as e:
            self.logger.debug(f"범위 비교 중 오류: {ip1} vs {ip2} - {e}")
            return ip1 == ip2
    
    def filter_by_source(self, df: pd.DataFrame, search_address: str, 
                        include_any: bool = True, use_extracted: bool = True) -> pd.DataFrame:
        """
        Source 주소를 기준으로 정책을 필터링합니다.
        
        Args:
            df: 정책 데이터프레임
            search_address: 검색할 주소 (CIDR, Range, Single IP)
            include_any: any를 포함할지 여부
            use_extracted: Extracted Source 컬럼 사용 여부
        
        Returns:
            필터링된 정책 데이터프레임
        """
        try:
            self.logger.info(f"Source 주소 기준 정책 필터링 시작: {search_address}")
            
            if df.empty:
                return pd.DataFrame()
            
            # 검색할 IP 정규화
            search_ips = self._normalize_ip_input(search_address)
            
            # 사용할 컬럼 결정
            source_column = 'Extracted Source' if use_extracted and 'Extracted Source' in df.columns else 'Source'
            
            if source_column not in df.columns:
                self.logger.error(f"Source 컬럼이 존재하지 않습니다: {source_column}")
                return pd.DataFrame()
            
            # 필터링 수행
            filtered_rows = []
            total = len(df)
            
            for idx, row in df.iterrows():
                if idx % max(1, total // 10) == 0:
                    progress = (idx + 1) / total * 100
                    print(f"\rSource 필터링 중: {progress:.1f}%", end='', flush=True)
                
                policy_ips = self._parse_policy_ips(row[source_column])
                
                if self._is_ip_match(search_ips, policy_ips, include_any):
                    filtered_rows.append(row)
            
            print()  # 줄바꿈
            
            result_df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame()
            self.logger.info(f"Source 필터링 완료. {len(result_df)}개 정책 발견")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Source 필터링 중 오류 발생: {e}")
            raise
    
    def filter_by_destination(self, df: pd.DataFrame, search_address: str, 
                             include_any: bool = True, use_extracted: bool = True) -> pd.DataFrame:
        """
        Destination 주소를 기준으로 정책을 필터링합니다.
        
        Args:
            df: 정책 데이터프레임
            search_address: 검색할 주소 (CIDR, Range, Single IP)
            include_any: any를 포함할지 여부
            use_extracted: Extracted Destination 컬럼 사용 여부
        
        Returns:
            필터링된 정책 데이터프레임
        """
        try:
            self.logger.info(f"Destination 주소 기준 정책 필터링 시작: {search_address}")
            
            if df.empty:
                return pd.DataFrame()
            
            # 검색할 IP 정규화
            search_ips = self._normalize_ip_input(search_address)
            
            # 사용할 컬럼 결정
            dest_column = 'Extracted Destination' if use_extracted and 'Extracted Destination' in df.columns else 'Destination'
            
            if dest_column not in df.columns:
                self.logger.error(f"Destination 컬럼이 존재하지 않습니다: {dest_column}")
                return pd.DataFrame()
            
            # 필터링 수행
            filtered_rows = []
            total = len(df)
            
            for idx, row in df.iterrows():
                if idx % max(1, total // 10) == 0:
                    progress = (idx + 1) / total * 100
                    print(f"\rDestination 필터링 중: {progress:.1f}%", end='', flush=True)
                
                policy_ips = self._parse_policy_ips(row[dest_column])
                
                if self._is_ip_match(search_ips, policy_ips, include_any):
                    filtered_rows.append(row)
            
            print()  # 줄바꿈
            
            result_df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame()
            self.logger.info(f"Destination 필터링 완료. {len(result_df)}개 정책 발견")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Destination 필터링 중 오류 발생: {e}")
            raise
    
    def filter_by_both(self, df: pd.DataFrame, search_address: str, 
                       include_any: bool = True, use_extracted: bool = True) -> pd.DataFrame:
        """
        Source 또는 Destination 주소를 기준으로 정책을 필터링합니다.
        
        Args:
            df: 정책 데이터프레임
            search_address: 검색할 주소 (CIDR, Range, Single IP)
            include_any: any를 포함할지 여부
            use_extracted: Extracted 컬럼 사용 여부
        
        Returns:
            필터링된 정책 데이터프레임
        """
        try:
            self.logger.info(f"Source/Destination 주소 기준 정책 필터링 시작: {search_address}")
            
            if df.empty:
                return pd.DataFrame()
            
            # 검색할 IP 정규화
            search_ips = self._normalize_ip_input(search_address)
            
            # 사용할 컬럼 결정
            source_column = 'Extracted Source' if use_extracted and 'Extracted Source' in df.columns else 'Source'
            dest_column = 'Extracted Destination' if use_extracted and 'Extracted Destination' in df.columns else 'Destination'
            
            if source_column not in df.columns and dest_column not in df.columns:
                self.logger.error("Source와 Destination 컬럼이 모두 존재하지 않습니다")
                return pd.DataFrame()
            
            # 필터링 수행
            filtered_rows = []
            total = len(df)
            
            for idx, row in df.iterrows():
                if idx % max(1, total // 10) == 0:
                    progress = (idx + 1) / total * 100
                    print(f"\rSource/Destination 필터링 중: {progress:.1f}%", end='', flush=True)
                
                match_found = False
                
                # Source 체크
                if source_column in df.columns:
                    source_ips = self._parse_policy_ips(row[source_column])
                    if self._is_ip_match(search_ips, source_ips, include_any):
                        match_found = True
                
                # Destination 체크
                if not match_found and dest_column in df.columns:
                    dest_ips = self._parse_policy_ips(row[dest_column])
                    if self._is_ip_match(search_ips, dest_ips, include_any):
                        match_found = True
                
                if match_found:
                    filtered_rows.append(row)
            
            print()  # 줄바꿈
            
            result_df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame()
            self.logger.info(f"Source/Destination 필터링 완료. {len(result_df)}개 정책 발견")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Source/Destination 필터링 중 오류 발생: {e}")
            raise
    
    def filter_by_criteria(self, df: pd.DataFrame, 
                          source_address: Optional[str] = None,
                          destination_address: Optional[str] = None,
                          include_any: bool = True, 
                          use_extracted: bool = True,
                          match_mode: str = 'AND') -> pd.DataFrame:
        """
        복합 조건으로 정책을 필터링합니다.
        
        Args:
            df: 정책 데이터프레임
            source_address: 검색할 Source 주소
            destination_address: 검색할 Destination 주소
            include_any: any를 포함할지 여부
            use_extracted: Extracted 컬럼 사용 여부
            match_mode: 'AND' 또는 'OR' (둘 다 매치/하나만 매치)
        
        Returns:
            필터링된 정책 데이터프레임
        """
        try:
            if df.empty:
                return pd.DataFrame()
            
            result_df = df.copy()
            
            # Source 필터링
            if source_address:
                source_filtered = self.filter_by_source(result_df, source_address, include_any, use_extracted)
                if match_mode.upper() == 'AND':
                    result_df = source_filtered
                else:  # OR mode
                    result_df = source_filtered
            
            # Destination 필터링
            if destination_address:
                dest_filtered = self.filter_by_destination(result_df if match_mode.upper() == 'AND' else df, 
                                                         destination_address, include_any, use_extracted)
                if match_mode.upper() == 'AND':
                    result_df = dest_filtered
                else:  # OR mode
                    if source_address:
                        # OR: Source 또는 Destination이 매치하는 경우
                        combined_indices = set(result_df.index) | set(dest_filtered.index)
                        result_df = df.loc[list(combined_indices)]
                    else:
                        result_df = dest_filtered
            
            self.logger.info(f"복합 조건 필터링 완료. {len(result_df)}개 정책 발견")
            return result_df
            
        except Exception as e:
            self.logger.error(f"복합 조건 필터링 중 오류 발생: {e}")
            raise
    
    def get_filter_summary(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame, 
                          search_criteria: Dict) -> Dict:
        """
        필터링 결과 요약을 반환합니다.
        
        Args:
            original_df: 원본 데이터프레임
            filtered_df: 필터링된 데이터프레임
            search_criteria: 검색 조건
        
        Returns:
            요약 정보 딕셔너리
        """
        summary = {
            'search_criteria': search_criteria,
            'total_policies': len(original_df),
            'matched_policies': len(filtered_df),
            'match_percentage': (len(filtered_df) / len(original_df) * 100) if len(original_df) > 0 else 0,
            'enabled_policies': len(filtered_df[filtered_df.get('Enable', 'Y') == 'Y']) if 'Enable' in filtered_df.columns else len(filtered_df),
            'action_distribution': filtered_df['Action'].value_counts().to_dict() if 'Action' in filtered_df.columns else {}
        }
        
        return summary 
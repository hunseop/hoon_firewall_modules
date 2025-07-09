"""
FPAT 모듈 통합 서비스
기존 FPAT 모듈을 FastAPI에서 사용할 수 있도록 래핑
"""

import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime
import traceback

# FPAT 모듈 import (경로 조정 필요)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'fpat'))

try:
    from fpat.policy_comparator import PolicyComparator
    from fpat.firewall_module import FirewallCollectorFactory
    from fpat.firewall_analyzer import PolicyAnalyzer, RedundancyAnalyzer, ShadowAnalyzer, PolicyFilter
    from fpat.firewall_module.exceptions import (
        FirewallError, FirewallConnectionError, FirewallAuthenticationError
    )
except ImportError as e:
    logging.warning(f"FPAT 모듈 import 실패: {e}")
    # Mock 클래스들 (개발 중)
    class PolicyComparator:
        def __init__(self, *args, **kwargs): pass
        def compare_all_objects(self): return {}
        def compare_policies(self): return {}
    
    class FirewallCollectorFactory:
        @staticmethod
        def get_collector(*args, **kwargs): return None
    
    class PolicyAnalyzer:
        def __init__(self): pass
        def analyze_redundancy(self, *args, **kwargs): return pd.DataFrame()
    
    class RedundancyAnalyzer:
        def analyze(self, *args, **kwargs): return pd.DataFrame()
    
    class ShadowAnalyzer:
        def analyze(self, *args, **kwargs): return pd.DataFrame()
    
    class PolicyFilter:
        def filter_by_source(self, *args, **kwargs): return pd.DataFrame()
        def filter_by_destination(self, *args, **kwargs): return pd.DataFrame()
        def filter_by_criteria(self, *args, **kwargs): return pd.DataFrame()


logger = logging.getLogger(__name__)


class FPATService:
    """FPAT 모듈 통합 서비스"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 각 분석기 인스턴스 생성
        self.policy_analyzer = PolicyAnalyzer()
        self.redundancy_analyzer = RedundancyAnalyzer()
        self.shadow_analyzer = ShadowAnalyzer()
        self.policy_filter = PolicyFilter()
    
    async def test_firewall_connection(
        self, 
        hostname: str, 
        username: str, 
        password: str, 
        vendor: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        방화벽 연결 테스트
        """
        try:
            logger.info(f"방화벽 연결 테스트 시작: {vendor}@{hostname}")
            
            # 비동기로 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._test_firewall_connection_sync,
                hostname, username, password, vendor, timeout
            )
            
            return {
                "success": True,
                "message": "연결 테스트 성공",
                "connection_info": result
            }
            
        except Exception as e:
            logger.error(f"방화벽 연결 테스트 실패: {e}")
            return {
                "success": False,
                "message": f"연결 테스트 실패: {str(e)}",
                "error": str(e)
            }
    
    def _test_firewall_connection_sync(
        self, hostname: str, username: str, password: str, vendor: str, timeout: int
    ) -> Dict[str, Any]:
        """동기 방화벽 연결 테스트"""
        try:
            collector = FirewallCollectorFactory.get_collector(
                source_type=vendor,
                hostname=hostname,
                username=username,
                password=password,
                timeout=timeout,
                test_connection=True
            )
            
            if collector and collector.test_connection():
                return {
                    "vendor": vendor,
                    "hostname": hostname,
                    "username": username,
                    "connected": True,
                    "connection_time": datetime.now().isoformat()
                }
            else:
                raise Exception("연결 테스트 실패")
                
        except Exception as e:
            raise Exception(f"연결 실패: {str(e)}")
    
    async def export_firewall_data(
        self,
        hostname: str,
        username: str, 
        password: str,
        vendor: str,
        export_types: List[str],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        방화벽 데이터 익스포트
        """
        try:
            logger.info(f"방화벽 데이터 익스포트 시작: {vendor}@{hostname}")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._export_firewall_data_sync,
                hostname, username, password, vendor, export_types, timeout
            )
            
            return result
            
        except Exception as e:
            logger.error(f"방화벽 데이터 익스포트 실패: {e}")
            raise Exception(f"데이터 익스포트 실패: {str(e)}")
    
    def _export_firewall_data_sync(
        self, hostname: str, username: str, password: str, 
        vendor: str, export_types: List[str], timeout: int
    ) -> Dict[str, Any]:
        """동기 방화벽 데이터 익스포트"""
        try:
            collector = FirewallCollectorFactory.get_collector(
                source_type=vendor,
                hostname=hostname,
                username=username,
                password=password,
                timeout=timeout
            )
            
            exported_data = {}
            file_ids = {}
            
            for export_type in export_types:
                if export_type == "policy":
                    data = collector.export_security_rules()
                elif export_type == "address":
                    data = collector.export_network_objects()
                elif export_type == "address_group":
                    data = collector.export_network_group_objects()
                elif export_type == "service":
                    data = collector.export_service_objects()
                elif export_type == "service_group":
                    data = collector.export_service_group_objects()
                elif export_type == "usage":
                    data = collector.export_usage_logs()
                else:
                    continue
                
                # 데이터를 파일로 저장
                file_id = str(uuid.uuid4())
                file_path = self.upload_dir / f"{file_id}_{export_type}.xlsx"
                data.to_excel(file_path, index=False)
                
                exported_data[export_type] = {
                    "records": len(data),
                    "columns": list(data.columns)
                }
                file_ids[export_type] = file_id
            
            return {
                "vendor": vendor,
                "hostname": hostname,
                "export_time": datetime.now().isoformat(),
                "exported_data": exported_data,
                "file_ids": file_ids,
                "summary": {
                    "total_types": len(export_types),
                    "successful_exports": len(file_ids),
                    "total_records": sum(data["records"] for data in exported_data.values())
                }
            }
            
        except Exception as e:
            raise Exception(f"데이터 익스포트 실패: {str(e)}")
    
    async def compare_policies(
        self,
        policy_old_path: str,
        policy_new_path: str,
        object_old_path: str,
        object_new_path: str,
        comparison_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        정책 비교 분석
        """
        try:
            logger.info("정책 비교 분석 시작")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._compare_policies_sync,
                policy_old_path, policy_new_path, object_old_path, object_new_path, comparison_options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"정책 비교 실패: {e}")
            raise Exception(f"정책 비교 실패: {str(e)}")
    
    def _compare_policies_sync(
        self, policy_old_path: str, policy_new_path: str, 
        object_old_path: str, object_new_path: str, 
        comparison_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """동기 정책 비교"""
        try:
            comparator = PolicyComparator(
                policy_old=policy_old_path,
                policy_new=policy_new_path,
                object_old=object_old_path,
                object_new=object_new_path
            )
            
            # 객체 비교
            comparator.compare_all_objects()
            
            # 정책 비교
            comparator.compare_policies()
            
            # 결과 파일 생성
            result_file_id = str(uuid.uuid4())
            result_file_path = self.upload_dir / f"{result_file_id}_comparison_result.xlsx"
            
            # Excel 파일로 결과 저장 (실제 구현 필요)
            # comparator.save_results_to_excel(result_file_path)
            
            return {
                "added_policies": len(comparator.added_df),
                "removed_policies": len(comparator.removed_df),
                "modified_policies": len(comparator.modified_list),
                "added_objects": sum(len(diff[0]) for diff in comparator.object_diffs.values()),
                "removed_objects": sum(len(diff[1]) for diff in comparator.object_diffs.values()),
                "modified_objects": sum(len(diff[2]) for diff in comparator.object_diffs.values()),
                "result_file_id": result_file_id,
                "summary": {
                    "total_changes": len(comparator.added_df) + len(comparator.removed_df) + len(comparator.modified_list),
                    "comparison_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise Exception(f"정책 비교 처리 실패: {str(e)}")
    
    async def analyze_redundancy(
        self,
        policy_file_path: str,
        vendor: str,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        중복 정책 분석
        """
        try:
            logger.info("중복 정책 분석 시작")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._analyze_redundancy_sync,
                policy_file_path, vendor, analysis_options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"중복 정책 분석 실패: {e}")
            raise Exception(f"중복 정책 분석 실패: {str(e)}")
    
    def _analyze_redundancy_sync(
        self, policy_file_path: str, vendor: str, analysis_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """동기 중복 정책 분석"""
        try:
            # 정책 파일 로드
            df = pd.read_excel(policy_file_path, sheet_name=0)
            
            # 중복 분석 수행
            result_df = self.redundancy_analyzer.analyze(df, vendor)
            
            # 결과 파일 저장
            result_file_id = str(uuid.uuid4())
            result_file_path = self.upload_dir / f"{result_file_id}_redundancy_analysis.xlsx"
            result_df.to_excel(result_file_path, index=False)
            
            return {
                "analysis_type": "redundancy",
                "vendor": vendor,
                "total_policies": len(df),
                "analyzed_policies": len(result_df),
                "findings": {
                    "redundant_policies": len(result_df),
                    "unique_policy_groups": len(result_df['No'].unique()) if 'No' in result_df.columns else 0
                },
                "result_file_id": result_file_id,
                "summary": {
                    "redundancy_percentage": (len(result_df) / len(df) * 100) if len(df) > 0 else 0,
                    "analysis_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise Exception(f"중복 정책 분석 처리 실패: {str(e)}")
    
    async def analyze_shadow_policies(
        self,
        policy_file_path: str,
        vendor: str,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Shadow 정책 분석
        """
        try:
            logger.info("Shadow 정책 분석 시작")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._analyze_shadow_policies_sync,
                policy_file_path, vendor, analysis_options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Shadow 정책 분석 실패: {e}")
            raise Exception(f"Shadow 정책 분석 실패: {str(e)}")
    
    def _analyze_shadow_policies_sync(
        self, policy_file_path: str, vendor: str, analysis_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """동기 Shadow 정책 분석"""
        try:
            # 정책 파일 로드
            df = pd.read_excel(policy_file_path, sheet_name=0)
            
            # Shadow 분석 수행
            result_df = self.shadow_analyzer.analyze(df, vendor)
            
            # 결과 파일 저장
            result_file_id = str(uuid.uuid4())
            result_file_path = self.upload_dir / f"{result_file_id}_shadow_analysis.xlsx"
            result_df.to_excel(result_file_path, index=False)
            
            return {
                "analysis_type": "shadow",
                "vendor": vendor,
                "total_policies": len(df),
                "analyzed_policies": len(result_df),
                "findings": {
                    "shadow_policies": len(result_df),
                    "shadow_percentage": (len(result_df) / len(df) * 100) if len(df) > 0 else 0
                },
                "result_file_id": result_file_id,
                "summary": {
                    "shadow_policies_found": len(result_df),
                    "analysis_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise Exception(f"Shadow 정책 분석 처리 실패: {str(e)}")
    
    async def filter_policies(
        self,
        policy_file_path: str,
        filter_criteria: Dict[str, Any],
        include_any: bool = True,
        use_extracted: bool = True
    ) -> Dict[str, Any]:
        """
        정책 필터링
        """
        try:
            logger.info("정책 필터링 시작")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._filter_policies_sync,
                policy_file_path, filter_criteria, include_any, use_extracted
            )
            
            return result
            
        except Exception as e:
            logger.error(f"정책 필터링 실패: {e}")
            raise Exception(f"정책 필터링 실패: {str(e)}")
    
    def _filter_policies_sync(
        self, policy_file_path: str, filter_criteria: Dict[str, Any], 
        include_any: bool, use_extracted: bool
    ) -> Dict[str, Any]:
        """동기 정책 필터링"""
        try:
            # 정책 파일 로드
            df = pd.read_excel(policy_file_path, sheet_name=0)
            
            # 필터링 수행
            if filter_criteria.get("source_address"):
                result_df = self.policy_filter.filter_by_source(
                    df, filter_criteria["source_address"], include_any, use_extracted
                )
            elif filter_criteria.get("destination_address"):
                result_df = self.policy_filter.filter_by_destination(
                    df, filter_criteria["destination_address"], include_any, use_extracted
                )
            elif filter_criteria.get("source_address") and filter_criteria.get("destination_address"):
                result_df = self.policy_filter.filter_by_criteria(
                    df, 
                    source_address=filter_criteria.get("source_address"),
                    destination_address=filter_criteria.get("destination_address"),
                    include_any=include_any,
                    use_extracted=use_extracted,
                    match_mode=filter_criteria.get("match_mode", "AND")
                )
            else:
                result_df = df
            
            # 결과 파일 저장
            result_file_id = str(uuid.uuid4())
            result_file_path = self.upload_dir / f"{result_file_id}_filtered_policies.xlsx"
            result_df.to_excel(result_file_path, index=False)
            
            # 요약 생성
            filter_summary = self.policy_filter.get_filter_summary(df, result_df, filter_criteria)
            
            return {
                "total_policies": len(df),
                "filtered_policies": len(result_df),
                "match_percentage": (len(result_df) / len(df) * 100) if len(df) > 0 else 0,
                "result_file_id": result_file_id,
                "filter_summary": filter_summary
            }
            
        except Exception as e:
            raise Exception(f"정책 필터링 처리 실패: {str(e)}")
    
    def get_file_path(self, file_id: str) -> Path:
        """파일 ID로 파일 경로 반환"""
        # 실제 구현에서는 데이터베이스에서 조회
        for file_path in self.upload_dir.glob(f"{file_id}*"):
            return file_path
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_id}")


# 전역 서비스 인스턴스
fpat_service = FPATService()
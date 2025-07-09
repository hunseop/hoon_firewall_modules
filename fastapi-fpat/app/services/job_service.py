"""
백그라운드 작업 관리 서비스
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from enum import Enum

from app.models.schemas import JobInfo, JobStatus
from app.services.fpat_service import fpat_service

logger = logging.getLogger(__name__)


class JobService:
    """백그라운드 작업 관리 서비스"""
    
    def __init__(self):
        self.jobs: Dict[str, JobInfo] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
    
    def create_job(self, job_type: str, parameters: Dict[str, Any], priority: int = 0) -> str:
        """새 작업 생성"""
        job_id = str(uuid.uuid4())
        
        job_info = JobInfo(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            progress=0.0,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            result=None,
            error_message=None,
            parameters=parameters
        )
        
        self.jobs[job_id] = job_info
        logger.info(f"작업 생성: {job_id} ({job_type})")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """작업 정보 조회"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self, skip: int = 0, limit: int = 100) -> List[JobInfo]:
        """모든 작업 목록 조회"""
        jobs_list = list(self.jobs.values())
        # 최신순 정렬
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        return jobs_list[skip:skip + limit]
    
    def update_job_status(self, job_id: str, status: JobStatus, progress: Optional[float] = None):
        """작업 상태 업데이트"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            if progress is not None:
                self.jobs[job_id].progress = progress
            
            if status == JobStatus.RUNNING and self.jobs[job_id].started_at is None:
                self.jobs[job_id].started_at = datetime.now()
            elif status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                self.jobs[job_id].completed_at = datetime.now()
                # 완료된 작업은 실행 목록에서 제거
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
    
    def set_job_result(self, job_id: str, result: Dict[str, Any]):
        """작업 결과 설정"""
        if job_id in self.jobs:
            self.jobs[job_id].result = result
    
    def set_job_error(self, job_id: str, error_message: str):
        """작업 오류 설정"""
        if job_id in self.jobs:
            self.jobs[job_id].error_message = error_message
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id not in self.jobs:
            return False
        
        # 실행 중인 작업 취소
        if job_id in self.running_jobs:
            task = self.running_jobs[job_id]
            task.cancel()
            del self.running_jobs[job_id]
        
        self.update_job_status(job_id, JobStatus.CANCELLED)
        logger.info(f"작업 취소: {job_id}")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """작업 삭제"""
        if job_id not in self.jobs:
            return False
        
        # 실행 중인 작업은 먼저 취소
        if job_id in self.running_jobs:
            self.cancel_job(job_id)
        
        del self.jobs[job_id]
        logger.info(f"작업 삭제: {job_id}")
        return True
    
    # 백그라운드 작업 실행 함수들
    async def run_policy_comparison(
        self,
        job_id: str,
        policy_old_path: str,
        policy_new_path: str,
        object_old_path: str,
        object_new_path: str,
        comparison_options: Optional[Dict[str, Any]] = None
    ):
        """정책 비교 백그라운드 작업"""
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, 0.0)
            logger.info(f"정책 비교 작업 시작: {job_id}")
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 10.0)
            
            # FPAT 서비스 호출
            result = await fpat_service.compare_policies(
                policy_old_path,
                policy_new_path,
                object_old_path,
                object_new_path,
                comparison_options
            )
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 90.0)
            
            # 결과 저장
            self.set_job_result(job_id, result)
            self.update_job_status(job_id, JobStatus.SUCCESS, 100.0)
            
            logger.info(f"정책 비교 작업 완료: {job_id}")
            
        except asyncio.CancelledError:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"정책 비교 작업 취소: {job_id}")
        except Exception as e:
            error_msg = f"정책 비교 작업 실패: {str(e)}"
            self.set_job_error(job_id, error_msg)
            self.update_job_status(job_id, JobStatus.FAILED)
            logger.error(f"작업 {job_id} 실패: {e}")
    
    async def run_redundancy_analysis(
        self,
        job_id: str,
        policy_file_path: str,
        vendor: str,
        analysis_options: Optional[Dict[str, Any]] = None
    ):
        """중복 정책 분석 백그라운드 작업"""
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, 0.0)
            logger.info(f"중복 정책 분석 작업 시작: {job_id}")
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 10.0)
            
            # FPAT 서비스 호출
            result = await fpat_service.analyze_redundancy(
                policy_file_path,
                vendor,
                analysis_options
            )
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 90.0)
            
            # 결과 저장
            self.set_job_result(job_id, result)
            self.update_job_status(job_id, JobStatus.SUCCESS, 100.0)
            
            logger.info(f"중복 정책 분석 작업 완료: {job_id}")
            
        except asyncio.CancelledError:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"중복 정책 분석 작업 취소: {job_id}")
        except Exception as e:
            error_msg = f"중복 정책 분석 작업 실패: {str(e)}"
            self.set_job_error(job_id, error_msg)
            self.update_job_status(job_id, JobStatus.FAILED)
            logger.error(f"작업 {job_id} 실패: {e}")
    
    async def run_shadow_analysis(
        self,
        job_id: str,
        policy_file_path: str,
        vendor: str,
        analysis_options: Optional[Dict[str, Any]] = None
    ):
        """Shadow 정책 분석 백그라운드 작업"""
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, 0.0)
            logger.info(f"Shadow 정책 분석 작업 시작: {job_id}")
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 10.0)
            
            # FPAT 서비스 호출
            result = await fpat_service.analyze_shadow_policies(
                policy_file_path,
                vendor,
                analysis_options
            )
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 90.0)
            
            # 결과 저장
            self.set_job_result(job_id, result)
            self.update_job_status(job_id, JobStatus.SUCCESS, 100.0)
            
            logger.info(f"Shadow 정책 분석 작업 완료: {job_id}")
            
        except asyncio.CancelledError:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"Shadow 정책 분석 작업 취소: {job_id}")
        except Exception as e:
            error_msg = f"Shadow 정책 분석 작업 실패: {str(e)}"
            self.set_job_error(job_id, error_msg)
            self.update_job_status(job_id, JobStatus.FAILED)
            logger.error(f"작업 {job_id} 실패: {e}")
    
    async def run_policy_filter(
        self,
        job_id: str,
        policy_file_path: str,
        filter_criteria: Dict[str, Any],
        include_any: bool = True,
        use_extracted: bool = True
    ):
        """정책 필터링 백그라운드 작업"""
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, 0.0)
            logger.info(f"정책 필터링 작업 시작: {job_id}")
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 10.0)
            
            # FPAT 서비스 호출
            result = await fpat_service.filter_policies(
                policy_file_path,
                filter_criteria,
                include_any,
                use_extracted
            )
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 90.0)
            
            # 결과 저장
            self.set_job_result(job_id, result)
            self.update_job_status(job_id, JobStatus.SUCCESS, 100.0)
            
            logger.info(f"정책 필터링 작업 완료: {job_id}")
            
        except asyncio.CancelledError:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"정책 필터링 작업 취소: {job_id}")
        except Exception as e:
            error_msg = f"정책 필터링 작업 실패: {str(e)}"
            self.set_job_error(job_id, error_msg)
            self.update_job_status(job_id, JobStatus.FAILED)
            logger.error(f"작업 {job_id} 실패: {e}")
    
    async def run_firewall_export(
        self,
        job_id: str,
        hostname: str,
        username: str,
        password: str,
        vendor: str,
        export_types: List[str],
        timeout: int = 30
    ):
        """방화벽 데이터 익스포트 백그라운드 작업"""
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, 0.0)
            logger.info(f"방화벽 데이터 익스포트 작업 시작: {job_id}")
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 10.0)
            
            # FPAT 서비스 호출
            result = await fpat_service.export_firewall_data(
                hostname,
                username,
                password,
                vendor,
                export_types,
                timeout
            )
            
            # 진행률 업데이트
            self.update_job_status(job_id, JobStatus.RUNNING, 90.0)
            
            # 결과 저장
            self.set_job_result(job_id, result)
            self.update_job_status(job_id, JobStatus.SUCCESS, 100.0)
            
            logger.info(f"방화벽 데이터 익스포트 작업 완료: {job_id}")
            
        except asyncio.CancelledError:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"방화벽 데이터 익스포트 작업 취소: {job_id}")
        except Exception as e:
            error_msg = f"방화벽 데이터 익스포트 작업 실패: {str(e)}"
            self.set_job_error(job_id, error_msg)
            self.update_job_status(job_id, JobStatus.FAILED)
            logger.error(f"작업 {job_id} 실패: {e}")
    
    def get_active_jobs_count(self) -> int:
        """실행 중인 작업 수 반환"""
        return len([job for job in self.jobs.values() if job.status == JobStatus.RUNNING])
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """작업 통계 반환"""
        total_jobs = len(self.jobs)
        
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = len([
                job for job in self.jobs.values() if job.status == status
            ])
        
        return {
            "total_jobs": total_jobs,
            "status_distribution": status_counts,
            "active_jobs": self.get_active_jobs_count()
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """오래된 작업 정리"""
        current_time = datetime.now()
        jobs_to_delete = []
        
        for job_id, job in self.jobs.items():
            # 완료된 작업 중 24시간 이상 된 것들
            if job.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at and (current_time - job.completed_at).total_seconds() > max_age_hours * 3600:
                    jobs_to_delete.append(job_id)
        
        for job_id in jobs_to_delete:
            del self.jobs[job_id]
        
        if jobs_to_delete:
            logger.info(f"{len(jobs_to_delete)}개의 오래된 작업을 정리했습니다")
        
        return len(jobs_to_delete)


# 전역 작업 서비스 인스턴스
job_service = JobService()
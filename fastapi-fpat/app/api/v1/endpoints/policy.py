"""
정책 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from app.models.schemas import (
    PolicyComparisonRequest, PolicyComparisonResult,
    PolicyAnalysisRequest, PolicyAnalysisResult,
    PolicyFilterRequest, PolicyFilterResult,
    BaseResponse, JobStatusResponse, JobInfo, JobStatus
)
from app.services.fpat_service import fpat_service
from app.services.job_service import job_service

router = APIRouter()


@router.post("/compare", response_model=JobStatusResponse)
async def compare_policies(
    request: PolicyComparisonRequest,
    background_tasks: BackgroundTasks
):
    """
    정책 비교 분석 (백그라운드 작업)
    
    - **policy_old_file_id**: 이전 정책 파일 ID
    - **policy_new_file_id**: 새 정책 파일 ID
    - **object_old_file_id**: 이전 객체 파일 ID
    - **object_new_file_id**: 새 객체 파일 ID
    - **comparison_options**: 비교 옵션 (선택사항)
    """
    try:
        # 파일 존재 확인
        policy_old_path = fpat_service.get_file_path(request.policy_old_file_id)
        policy_new_path = fpat_service.get_file_path(request.policy_new_file_id)
        object_old_path = fpat_service.get_file_path(request.object_old_file_id)
        object_new_path = fpat_service.get_file_path(request.object_new_file_id)
        
        # 백그라운드 작업 생성
        job_id = job_service.create_job(
            job_type="policy_comparison",
            parameters={
                "policy_old_path": str(policy_old_path),
                "policy_new_path": str(policy_new_path),
                "object_old_path": str(object_old_path),
                "object_new_path": str(object_new_path),
                "comparison_options": request.comparison_options
            }
        )
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            job_service.run_policy_comparison,
            job_id,
            str(policy_old_path),
            str(policy_new_path),
            str(object_old_path),
            str(object_new_path),
            request.comparison_options
        )
        
        job_info = job_service.get_job(job_id)
        
        return JobStatusResponse(
            success=True,
            message="정책 비교 작업이 시작되었습니다",
            data=job_info
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 비교 작업 생성 실패: {str(e)}")


@router.post("/analyze", response_model=JobStatusResponse)
async def analyze_policy(
    request: PolicyAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    정책 분석 (백그라운드 작업)
    
    - **policy_file_id**: 분석할 정책 파일 ID
    - **vendor**: 방화벽 벤더 (paloalto, ngf, mf2, mock)
    - **analysis_type**: 분석 유형 (redundancy, shadow)
    - **analysis_options**: 분석 옵션 (선택사항)
    """
    try:
        # 파일 존재 확인
        policy_file_path = fpat_service.get_file_path(request.policy_file_id)
        
        # 백그라운드 작업 생성
        job_id = job_service.create_job(
            job_type=f"policy_analysis_{request.analysis_type}",
            parameters={
                "policy_file_path": str(policy_file_path),
                "vendor": request.vendor,
                "analysis_type": request.analysis_type,
                "analysis_options": request.analysis_options
            }
        )
        
        # 분석 유형에 따른 백그라운드 작업 시작
        if request.analysis_type == "redundancy":
            background_tasks.add_task(
                job_service.run_redundancy_analysis,
                job_id,
                str(policy_file_path),
                request.vendor,
                request.analysis_options
            )
        elif request.analysis_type == "shadow":
            background_tasks.add_task(
                job_service.run_shadow_analysis,
                job_id,
                str(policy_file_path),
                request.vendor,
                request.analysis_options
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 분석 유형입니다: {request.analysis_type}"
            )
        
        job_info = job_service.get_job(job_id)
        
        return JobStatusResponse(
            success=True,
            message=f"{request.analysis_type} 분석 작업이 시작되었습니다",
            data=job_info
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 분석 작업 생성 실패: {str(e)}")


@router.post("/filter", response_model=JobStatusResponse)
async def filter_policies(
    request: PolicyFilterRequest,
    background_tasks: BackgroundTasks
):
    """
    정책 필터링 (백그라운드 작업)
    
    - **policy_file_id**: 필터링할 정책 파일 ID
    - **filter_criteria**: 필터링 조건
    - **include_any**: any 값 포함 여부
    - **use_extracted**: Extracted 컬럼 사용 여부
    """
    try:
        # 파일 존재 확인
        policy_file_path = fpat_service.get_file_path(request.policy_file_id)
        
        # 백그라운드 작업 생성
        job_id = job_service.create_job(
            job_type="policy_filter",
            parameters={
                "policy_file_path": str(policy_file_path),
                "filter_criteria": request.filter_criteria,
                "include_any": request.include_any,
                "use_extracted": request.use_extracted
            }
        )
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            job_service.run_policy_filter,
            job_id,
            str(policy_file_path),
            request.filter_criteria,
            request.include_any,
            request.use_extracted
        )
        
        job_info = job_service.get_job(job_id)
        
        return JobStatusResponse(
            success=True,
            message="정책 필터링 작업이 시작되었습니다",
            data=job_info
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 필터링 작업 생성 실패: {str(e)}")


@router.post("/compare/quick", response_model=BaseResponse)
async def compare_policies_quick(request: PolicyComparisonRequest):
    """
    정책 비교 분석 (즉시 실행 - 작은 파일용)
    
    - **policy_old_file_id**: 이전 정책 파일 ID
    - **policy_new_file_id**: 새 정책 파일 ID
    - **object_old_file_id**: 이전 객체 파일 ID
    - **object_new_file_id**: 새 객체 파일 ID
    """
    try:
        # 파일 존재 확인
        policy_old_path = fpat_service.get_file_path(request.policy_old_file_id)
        policy_new_path = fpat_service.get_file_path(request.policy_new_file_id)
        object_old_path = fpat_service.get_file_path(request.object_old_file_id)
        object_new_path = fpat_service.get_file_path(request.object_new_file_id)
        
        # 즉시 실행
        result = await fpat_service.compare_policies(
            str(policy_old_path),
            str(policy_new_path),
            str(object_old_path),
            str(object_new_path),
            request.comparison_options
        )
        
        return BaseResponse(
            success=True,
            message="정책 비교 완료",
            data=result
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 비교 실패: {str(e)}")


@router.post("/analyze/quick", response_model=BaseResponse)
async def analyze_policy_quick(request: PolicyAnalysisRequest):
    """
    정책 분석 (즉시 실행 - 작은 파일용)
    
    - **policy_file_id**: 분석할 정책 파일 ID
    - **vendor**: 방화벽 벤더
    - **analysis_type**: 분석 유형
    """
    try:
        # 파일 존재 확인
        policy_file_path = fpat_service.get_file_path(request.policy_file_id)
        
        # 분석 유형에 따른 즉시 실행
        if request.analysis_type == "redundancy":
            result = await fpat_service.analyze_redundancy(
                str(policy_file_path),
                request.vendor,
                request.analysis_options
            )
        elif request.analysis_type == "shadow":
            result = await fpat_service.analyze_shadow_policies(
                str(policy_file_path),
                request.vendor,
                request.analysis_options
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 분석 유형입니다: {request.analysis_type}"
            )
        
        return BaseResponse(
            success=True,
            message=f"{request.analysis_type} 분석 완료",
            data=result
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 분석 실패: {str(e)}")


@router.post("/filter/quick", response_model=BaseResponse)
async def filter_policies_quick(request: PolicyFilterRequest):
    """
    정책 필터링 (즉시 실행 - 작은 파일용)
    
    - **policy_file_id**: 필터링할 정책 파일 ID
    - **filter_criteria**: 필터링 조건
    """
    try:
        # 파일 존재 확인
        policy_file_path = fpat_service.get_file_path(request.policy_file_id)
        
        # 즉시 실행
        result = await fpat_service.filter_policies(
            str(policy_file_path),
            request.filter_criteria,
            request.include_any,
            request.use_extracted
        )
        
        return BaseResponse(
            success=True,
            message="정책 필터링 완료",
            data=result
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 필터링 실패: {str(e)}")


@router.get("/templates", response_model=BaseResponse)
async def get_policy_templates():
    """
    정책 파일 템플릿 정보 조회
    """
    try:
        templates = {
            "paloalto": {
                "policy_columns": [
                    "Rule Name", "Enable", "Action", "Source", "User", 
                    "Destination", "Service", "Application", "Security Profile", 
                    "Category", "Description"
                ],
                "object_columns": {
                    "address": ["Name", "Type", "Value"],
                    "address_group": ["Group Name", "Entry"],
                    "service": ["Name", "Protocol", "Port"],
                    "service_group": ["Group Name", "Entry"]
                }
            },
            "ngf": {
                "policy_columns": [
                    "Rule Name", "Enable", "Action", "Source", "User",
                    "Destination", "Service", "Application", "Description"
                ],
                "object_columns": {
                    "address": ["Name", "Type", "Value"],
                    "address_group": ["Group Name", "Entry"],
                    "service": ["Name", "Protocol", "Port"],
                    "service_group": ["Group Name", "Entry"]
                }
            },
            "mf2": {
                "policy_columns": [
                    "Rule Name", "Enable", "Action", "Source", "User",
                    "Destination", "Service", "Application", "Description"
                ],
                "object_columns": {
                    "address": ["Name", "Type", "Value"],
                    "address_group": ["Group Name", "Entry"],
                    "service": ["Name", "Protocol", "Port"],
                    "service_group": ["Group Name", "Entry"]
                }
            }
        }
        
        return BaseResponse(
            success=True,
            message="정책 템플릿 정보 조회 성공",
            data=templates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 정보 조회 실패: {str(e)}")


@router.get("/vendors", response_model=BaseResponse)
async def get_supported_vendors():
    """
    지원되는 방화벽 벤더 목록 조회
    """
    try:
        vendors = {
            "paloalto": {
                "name": "PaloAlto Networks",
                "description": "PAN-OS 기반 방화벽",
                "supported_features": [
                    "정책 비교", "중복 분석", "Shadow 분석", 
                    "정책 필터링", "실시간 연동"
                ]
            },
            "ngf": {
                "name": "SECUI NGF",
                "description": "SECUI Next Generation Firewall",
                "supported_features": [
                    "정책 비교", "중복 분석", "Shadow 분석", 
                    "정책 필터링", "실시간 연동"
                ]
            },
            "mf2": {
                "name": "SECUI MF2",
                "description": "SECUI Multi-Function Firewall 2",
                "supported_features": [
                    "정책 비교", "중복 분석", "Shadow 분석", 
                    "정책 필터링", "실시간 연동"
                ]
            },
            "mock": {
                "name": "Mock Firewall",
                "description": "테스트 및 데모용 가상 방화벽",
                "supported_features": [
                    "정책 비교", "중복 분석", "Shadow 분석", 
                    "정책 필터링", "데모 데이터 생성"
                ]
            }
        }
        
        return BaseResponse(
            success=True,
            message="지원 벤더 목록 조회 성공",
            data=vendors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벤더 목록 조회 실패: {str(e)}")


@router.get("/analysis-types", response_model=BaseResponse)
async def get_analysis_types():
    """
    지원되는 분석 유형 목록 조회
    """
    try:
        analysis_types = {
            "redundancy": {
                "name": "중복 정책 분석",
                "description": "동일한 효과를 가진 중복된 정책 규칙을 찾습니다",
                "output": "중복 정책 그룹 및 상세 비교 결과"
            },
            "shadow": {
                "name": "Shadow 정책 분석", 
                "description": "상위 정책에 의해 가려져서 실행되지 않는 정책을 찾습니다",
                "output": "Shadow 정책 목록 및 가려지는 이유"
            },
            "comparison": {
                "name": "정책 비교",
                "description": "두 개의 정책 세트 간 변경사항을 비교 분석합니다",
                "output": "추가/삭제/변경된 정책 및 객체 목록"
            },
            "filter": {
                "name": "정책 필터링",
                "description": "특정 조건(IP, 포트 등)에 해당하는 정책을 필터링합니다",
                "output": "조건에 맞는 정책 목록"
            }
        }
        
        return BaseResponse(
            success=True,
            message="분석 유형 목록 조회 성공",
            data=analysis_types
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 유형 조회 실패: {str(e)}")
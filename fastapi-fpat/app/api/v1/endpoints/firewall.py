"""
방화벽 연동 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from app.models.schemas import (
    FirewallConnection, FirewallConnectionResponse,
    FirewallExportRequest, FirewallExportResult,
    BaseResponse, JobStatusResponse
)
from app.services.fpat_service import fpat_service
from app.services.job_service import job_service

router = APIRouter()


@router.post("/test-connection", response_model=FirewallConnectionResponse)
async def test_firewall_connection(connection: FirewallConnection):
    """
    방화벽 연결 테스트
    
    - **hostname**: 방화벽 호스트명 또는 IP
    - **username**: 로그인 사용자명
    - **password**: 로그인 비밀번호
    - **vendor**: 방화벽 벤더 (paloalto, ngf, mf2, mock)
    - **timeout**: 연결 타임아웃 (초)
    """
    try:
        result = await fpat_service.test_firewall_connection(
            connection.hostname,
            connection.username,
            connection.password,
            connection.vendor.value,
            connection.timeout
        )
        
        return FirewallConnectionResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("connection_info")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방화벽 연결 테스트 실패: {str(e)}")


@router.post("/export", response_model=JobStatusResponse)
async def export_firewall_data(
    request: FirewallExportRequest,
    background_tasks: BackgroundTasks
):
    """
    방화벽 데이터 익스포트 (백그라운드 작업)
    
    - **connection**: 방화벽 연결 정보
    - **export_types**: 익스포트할 데이터 유형 목록
    - **export_options**: 익스포트 옵션 (선택사항)
    """
    try:
        # 백그라운드 작업 생성
        job_id = job_service.create_job(
            job_type="firewall_export",
            parameters={
                "hostname": request.connection.hostname,
                "username": request.connection.username,
                "vendor": request.connection.vendor.value,
                "export_types": request.export_types,
                "timeout": request.connection.timeout,
                "export_options": request.export_options
            }
        )
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            job_service.run_firewall_export,
            job_id,
            request.connection.hostname,
            request.connection.username,
            request.connection.password,
            request.connection.vendor.value,
            request.export_types,
            request.connection.timeout
        )
        
        job_info = job_service.get_job(job_id)
        
        return JobStatusResponse(
            success=True,
            message="방화벽 데이터 익스포트 작업이 시작되었습니다",
            data=job_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방화벽 데이터 익스포트 작업 생성 실패: {str(e)}")


@router.post("/export/quick", response_model=BaseResponse)
async def export_firewall_data_quick(request: FirewallExportRequest):
    """
    방화벽 데이터 익스포트 (즉시 실행 - 작은 데이터용)
    
    - **connection**: 방화벽 연결 정보
    - **export_types**: 익스포트할 데이터 유형 목록
    """
    try:
        result = await fpat_service.export_firewall_data(
            request.connection.hostname,
            request.connection.username,
            request.connection.password,
            request.connection.vendor.value,
            request.export_types,
            request.connection.timeout
        )
        
        return BaseResponse(
            success=True,
            message="방화벽 데이터 익스포트 완료",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방화벽 데이터 익스포트 실패: {str(e)}")


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
                "connection_requirements": ["hostname", "username", "password"],
                "supported_exports": [
                    "policy", "address", "address_group", 
                    "service", "service_group", "usage"
                ],
                "default_port": 443
            },
            "ngf": {
                "name": "SECUI NGF",
                "description": "SECUI Next Generation Firewall",
                "connection_requirements": ["hostname", "username", "password"],
                "supported_exports": [
                    "policy", "address", "address_group", 
                    "service", "service_group"
                ],
                "default_port": 22
            },
            "mf2": {
                "name": "SECUI MF2",
                "description": "SECUI Multi-Function Firewall 2",
                "connection_requirements": ["hostname", "username", "password"],
                "supported_exports": [
                    "policy", "address", "address_group", 
                    "service", "service_group"
                ],
                "default_port": 22
            },
            "mock": {
                "name": "Mock Firewall",
                "description": "테스트 및 데모용 가상 방화벽",
                "connection_requirements": ["hostname", "username", "password"],
                "supported_exports": [
                    "policy", "address", "address_group", 
                    "service", "service_group", "usage"
                ],
                "default_port": 443
            }
        }
        
        return BaseResponse(
            success=True,
            message="지원 벤더 목록 조회 성공",
            data=vendors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벤더 목록 조회 실패: {str(e)}")


@router.get("/export-types", response_model=BaseResponse)
async def get_export_types():
    """
    지원되는 익스포트 데이터 유형 목록 조회
    """
    try:
        export_types = {
            "policy": {
                "name": "보안 정책",
                "description": "방화벽 보안 규칙 데이터",
                "columns": [
                    "Rule Name", "Enable", "Action", "Source", 
                    "Destination", "Service", "Application"
                ]
            },
            "address": {
                "name": "주소 객체",
                "description": "네트워크 주소 객체 데이터",
                "columns": ["Name", "Type", "Value"]
            },
            "address_group": {
                "name": "주소 그룹",
                "description": "네트워크 주소 그룹 데이터",
                "columns": ["Group Name", "Entry"]
            },
            "service": {
                "name": "서비스 객체",
                "description": "서비스 객체 데이터",
                "columns": ["Name", "Protocol", "Port"]
            },
            "service_group": {
                "name": "서비스 그룹",
                "description": "서비스 그룹 데이터",
                "columns": ["Group Name", "Entry"]
            },
            "usage": {
                "name": "정책 사용 현황",
                "description": "정책 히트 카운트 및 사용 이력",
                "columns": ["Rule Name", "Last Hit Date", "Unused Days", "미사용여부"]
            }
        }
        
        return BaseResponse(
            success=True,
            message="익스포트 유형 목록 조회 성공",
            data=export_types
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"익스포트 유형 조회 실패: {str(e)}")


@router.post("/validate-connection", response_model=BaseResponse)
async def validate_connection_info(connection: FirewallConnection):
    """
    방화벽 연결 정보 검증 (연결하지 않고 정보만 검증)
    
    - **hostname**: 방화벽 호스트명 또는 IP
    - **username**: 로그인 사용자명
    - **password**: 로그인 비밀번호
    - **vendor**: 방화벽 벤더
    """
    try:
        validation_result = {
            "hostname_valid": bool(connection.hostname and len(connection.hostname.strip()) > 0),
            "username_valid": bool(connection.username and len(connection.username.strip()) > 0),
            "password_valid": bool(connection.password and len(connection.password.strip()) > 0),
            "vendor_supported": connection.vendor.value in ["paloalto", "ngf", "mf2", "mock"],
            "timeout_valid": 5 <= connection.timeout <= 300
        }
        
        all_valid = all(validation_result.values())
        
        validation_messages = []
        if not validation_result["hostname_valid"]:
            validation_messages.append("유효하지 않은 호스트명")
        if not validation_result["username_valid"]:
            validation_messages.append("유효하지 않은 사용자명")
        if not validation_result["password_valid"]:
            validation_messages.append("유효하지 않은 비밀번호")
        if not validation_result["vendor_supported"]:
            validation_messages.append("지원하지 않는 벤더")
        if not validation_result["timeout_valid"]:
            validation_messages.append("타임아웃은 5-300초 범위여야 함")
        
        return BaseResponse(
            success=all_valid,
            message="연결 정보 검증 완료" if all_valid else f"검증 실패: {', '.join(validation_messages)}",
            data={
                "validation_result": validation_result,
                "all_valid": all_valid,
                "messages": validation_messages
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 정보 검증 실패: {str(e)}")


@router.get("/connection-templates", response_model=BaseResponse)
async def get_connection_templates():
    """
    벤더별 연결 템플릿 정보 조회
    """
    try:
        templates = {
            "paloalto": {
                "name": "PaloAlto Networks",
                "example": {
                    "hostname": "192.168.1.1 또는 firewall.company.com",
                    "username": "admin",
                    "password": "password",
                    "vendor": "paloalto",
                    "timeout": 30
                },
                "notes": [
                    "HTTPS API를 사용합니다 (포트 443)",
                    "API 키가 자동으로 생성됩니다",
                    "관리자 권한이 필요합니다"
                ]
            },
            "ngf": {
                "name": "SECUI NGF",
                "example": {
                    "hostname": "192.168.1.1",
                    "username": "admin",
                    "password": "password",
                    "vendor": "ngf",
                    "timeout": 30
                },
                "notes": [
                    "SSH 연결을 사용합니다 (포트 22)",
                    "관리자 권한이 필요합니다"
                ]
            },
            "mf2": {
                "name": "SECUI MF2",
                "example": {
                    "hostname": "192.168.1.1",
                    "username": "admin",
                    "password": "password",
                    "vendor": "mf2",
                    "timeout": 30
                },
                "notes": [
                    "SSH 연결을 사용합니다 (포트 22)",
                    "관리자 권한이 필요합니다"
                ]
            },
            "mock": {
                "name": "Mock Firewall",
                "example": {
                    "hostname": "test.firewall.local",
                    "username": "demo",
                    "password": "demo123",
                    "vendor": "mock",
                    "timeout": 30
                },
                "notes": [
                    "테스트 및 데모용 가상 방화벽",
                    "실제 연결 없이 샘플 데이터 생성",
                    "모든 기능 테스트 가능"
                ]
            }
        }
        
        return BaseResponse(
            success=True,
            message="연결 템플릿 정보 조회 성공",
            data=templates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 템플릿 조회 실패: {str(e)}")
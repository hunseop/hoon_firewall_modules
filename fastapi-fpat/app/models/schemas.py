"""
FastAPI Pydantic 스키마 모델들
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enum 정의
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FirewallVendor(str, Enum):
    PALOALTO = "paloalto"
    NGF = "ngf"
    MF2 = "mf2"
    MOCK = "mock"


class AnalysisType(str, Enum):
    REDUNDANCY = "redundancy"
    SHADOW = "shadow"
    COMPARISON = "comparison"
    FILTER = "filter"


# 기본 응답 모델
class BaseResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 인증 관련
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool = True
    created_at: datetime


# 파일 업로드 관련
class FileInfo(BaseModel):
    filename: str
    file_id: str
    file_path: str
    file_size: int
    upload_time: datetime
    content_type: str


class FileUploadResponse(BaseResponse):
    data: FileInfo


# 방화벽 연결 관련
class FirewallConnection(BaseModel):
    hostname: str = Field(..., description="방화벽 호스트명 또는 IP")
    username: str = Field(..., description="로그인 사용자명")
    password: str = Field(..., description="로그인 비밀번호")
    vendor: FirewallVendor = Field(..., description="방화벽 벤더")
    timeout: Optional[int] = Field(30, ge=5, le=300, description="연결 타임아웃(초)")
    test_connection: bool = Field(True, description="연결 테스트 수행 여부")


class FirewallConnectionResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = None


# 정책 비교 관련
class PolicyComparisonRequest(BaseModel):
    policy_old_file_id: str = Field(..., description="이전 정책 파일 ID")
    policy_new_file_id: str = Field(..., description="새 정책 파일 ID")
    object_old_file_id: str = Field(..., description="이전 객체 파일 ID")
    object_new_file_id: str = Field(..., description="새 객체 파일 ID")
    comparison_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PolicyComparisonResult(BaseModel):
    added_policies: int
    removed_policies: int
    modified_policies: int
    added_objects: int
    removed_objects: int
    modified_objects: int
    result_file_id: str
    summary: Dict[str, Any]


# 정책 분석 관련
class PolicyAnalysisRequest(BaseModel):
    policy_file_id: str = Field(..., description="분석할 정책 파일 ID")
    vendor: FirewallVendor = Field(..., description="방화벽 벤더")
    analysis_type: AnalysisType = Field(..., description="분석 유형")
    analysis_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PolicyAnalysisResult(BaseModel):
    analysis_type: AnalysisType
    vendor: FirewallVendor
    total_policies: int
    analyzed_policies: int
    findings: Dict[str, Any]
    result_file_id: Optional[str] = None
    summary: Dict[str, Any]


# 정책 필터링 관련
class PolicyFilterRequest(BaseModel):
    policy_file_id: str = Field(..., description="필터링할 정책 파일 ID")
    filter_criteria: Dict[str, Any] = Field(..., description="필터링 조건")
    include_any: bool = Field(True, description="any 값 포함 여부")
    use_extracted: bool = Field(True, description="Extracted 컬럼 사용 여부")


class PolicyFilterResult(BaseModel):
    total_policies: int
    filtered_policies: int
    match_percentage: float
    result_file_id: str
    filter_summary: Dict[str, Any]


# 백그라운드 작업 관련
class JobRequest(BaseModel):
    job_type: str
    parameters: Dict[str, Any]
    priority: Optional[int] = Field(0, description="작업 우선순위 (높을수록 우선)")


class JobInfo(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    progress: Optional[float] = Field(None, ge=0, le=100)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    parameters: Dict[str, Any]


class JobStatusResponse(BaseResponse):
    data: JobInfo


class JobListResponse(BaseResponse):
    data: List[JobInfo]


# 방화벽 데이터 익스포트 관련
class FirewallExportRequest(BaseModel):
    connection: FirewallConnection
    export_types: List[str] = Field(
        default=["policy", "address", "service"],
        description="익스포트할 데이터 유형"
    )
    export_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FirewallExportResult(BaseModel):
    vendor: FirewallVendor
    hostname: str
    export_time: datetime
    exported_data: Dict[str, Any]
    file_ids: Dict[str, str]
    summary: Dict[str, Any]


# 시스템 정보 관련
class SystemInfo(BaseModel):
    app_name: str
    app_version: str
    api_version: str
    uptime: str
    active_jobs: int
    total_files: int
    disk_usage: Dict[str, Any]


class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    services: Dict[str, str]
    version: str


# 웹소켓 메시지
class WebSocketMessage(BaseModel):
    type: str
    job_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# 진행률 업데이트
class ProgressUpdate(BaseModel):
    job_id: str
    progress: float = Field(..., ge=0, le=100)
    status: JobStatus
    message: Optional[str] = None
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    current_step_number: Optional[int] = None
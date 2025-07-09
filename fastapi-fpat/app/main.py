"""
FastAPI FPAT 애플리케이션 메인 파일
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
import time
from datetime import datetime
import uvicorn

from app.core.config import settings
from app.models.schemas import HealthCheck, SystemInfo, BaseResponse
from app.api.v1.endpoints import files, policy, firewall, jobs

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    FPAT (Firewall Policy Analysis Tool) API 서버
    
    ## 주요 기능
    
    * **파일 관리**: 정책 파일 업로드/다운로드
    * **정책 비교**: 정책 변경사항 분석
    * **정책 분석**: 중복성, Shadow 정책 분석
    * **정책 필터링**: IP, 포트 기반 정책 검색
    * **방화벽 연동**: 실시간 방화벽 데이터 수집
    * **작업 관리**: 백그라운드 작업 모니터링
    
    ## 지원 방화벽
    
    * PaloAlto Networks (PAN-OS)
    * SECUI NGF
    * SECUI MF2
    * Mock Firewall (테스트용)
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (향후 웹 UI용)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 앱 시작 시간 기록
app_start_time = datetime.now()


# 루트 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    홈페이지 - 기본 정보 표시
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            .info-box {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .api-link {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }}
            .api-link:hover {{ background: #2980b9; }}
            .status {{ color: #27ae60; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔥 {settings.APP_NAME}</h1>
            
            <div class="info-box">
                <h3>📊 서버 상태</h3>
                <p><strong>상태:</strong> <span class="status">실행 중</span></p>
                <p><strong>버전:</strong> {settings.APP_VERSION}</p>
                <p><strong>시작 시간:</strong> {app_start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>업타임:</strong> {str(datetime.now() - app_start_time).split('.')[0]}</p>
            </div>
            
            <div class="info-box">
                <h3>🚀 주요 기능</h3>
                <ul>
                    <li><strong>정책 비교:</strong> 방화벽 정책 변경사항 분석</li>
                    <li><strong>정책 분석:</strong> 중복성, Shadow 정책 탐지</li>
                    <li><strong>정책 필터링:</strong> IP/포트 기반 정책 검색</li>
                    <li><strong>방화벽 연동:</strong> PaloAlto, NGF, MF2 실시간 연동</li>
                    <li><strong>백그라운드 작업:</strong> 대용량 데이터 비동기 처리</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>📖 API 문서</h3>
                <a href="/docs" class="api-link">📋 Swagger UI</a>
                <a href="/redoc" class="api-link">📚 ReDoc</a>
                <a href="/health" class="api-link">💚 Health Check</a>
                <a href="/system-info" class="api-link">🖥️ System Info</a>
            </div>
            
            <div class="info-box">
                <h3>🔗 API 엔드포인트</h3>
                <ul>
                    <li><strong>/api/v1/files/</strong> - 파일 업로드/다운로드</li>
                    <li><strong>/api/v1/policy/</strong> - 정책 비교/분석</li>
                    <li><strong>/api/v1/firewall/</strong> - 방화벽 연동</li>
                    <li><strong>/api/v1/jobs/</strong> - 작업 관리</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>🌐 WebSocket</h3>
                <ul>
                    <li><strong>/api/v1/jobs/ws</strong> - 실시간 작업 상태</li>
                    <li><strong>/api/v1/jobs/ws/{{job_id}}</strong> - 특정 작업 진행률</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """


# Health Check 엔드포인트
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    서비스 상태 확인
    """
    try:
        # 기본 서비스 상태 체크
        services_status = {
            "api": "healthy",
            "file_system": "healthy",
            "fpat_modules": "healthy"
        }
        
        # 파일 시스템 체크
        try:
            import os
            if not os.path.exists(settings.UPLOAD_DIR):
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        except Exception:
            services_status["file_system"] = "unhealthy"
        
        # FPAT 모듈 체크
        try:
            from app.services.fpat_service import fpat_service
            # Mock 연결 테스트
            result = await fpat_service.test_firewall_connection(
                "test.local", "test", "test", "mock", 5
            )
            if not result.get("success"):
                services_status["fpat_modules"] = "degraded"
        except Exception:
            services_status["fpat_modules"] = "degraded"
        
        overall_status = "healthy"
        if "unhealthy" in services_status.values():
            overall_status = "unhealthy"
        elif "degraded" in services_status.values():
            overall_status = "degraded"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.now(),
            services=services_status,
            version=settings.APP_VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check 실패: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.now(),
            services={"api": "unhealthy"},
            version=settings.APP_VERSION
        )


# 시스템 정보 엔드포인트
@app.get("/system-info", response_model=BaseResponse)
async def get_system_info():
    """
    시스템 정보 조회
    """
    try:
        from app.services.job_service import job_service
        import os
        import psutil
        
        # 디스크 사용량
        upload_dir_size = 0
        upload_file_count = 0
        
        if os.path.exists(settings.UPLOAD_DIR):
            for root, dirs, files in os.walk(settings.UPLOAD_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        upload_dir_size += os.path.getsize(file_path)
                        upload_file_count += 1
        
        # 시스템 리소스 정보
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        uptime = str(datetime.now() - app_start_time).split('.')[0]
        
        system_info = SystemInfo(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            api_version="v1",
            uptime=uptime,
            active_jobs=job_service.get_active_jobs_count(),
            total_files=upload_file_count,
            disk_usage={
                "upload_dir_size_mb": round(upload_dir_size / (1024 * 1024), 2),
                "upload_file_count": upload_file_count,
                "system_disk_total_gb": round(disk_info.total / (1024 ** 3), 2),
                "system_disk_used_gb": round(disk_info.used / (1024 ** 3), 2),
                "system_disk_free_gb": round(disk_info.free / (1024 ** 3), 2),
                "memory_total_gb": round(memory_info.total / (1024 ** 3), 2),
                "memory_used_gb": round(memory_info.used / (1024 ** 3), 2),
                "memory_available_gb": round(memory_info.available / (1024 ** 3), 2)
            }
        )
        
        return BaseResponse(
            success=True,
            message="시스템 정보 조회 성공",
            data=system_info.model_dump()
        )
        
    except Exception as e:
        logger.error(f"시스템 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 정보 조회 실패: {str(e)}")


# API 라우터 등록
app.include_router(
    files.router,
    prefix=f"{settings.API_V1_STR}/files",
    tags=["파일 관리"]
)

app.include_router(
    policy.router,
    prefix=f"{settings.API_V1_STR}/policy",
    tags=["정책 분석"]
)

app.include_router(
    firewall.router,
    prefix=f"{settings.API_V1_STR}/firewall",
    tags=["방화벽 연동"]
)

app.include_router(
    jobs.router,
    prefix=f"{settings.API_V1_STR}/jobs",
    tags=["작업 관리"]
)


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """글로벌 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "success": False,
        "message": "서버 내부 오류가 발생했습니다",
        "detail": str(exc) if settings.DEBUG else "Internal server error"
    }


# 미들웨어 - 요청 로깅
@app.middleware("http")
async def log_requests(request, call_next):
    """HTTP 요청 로깅 미들웨어"""
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"요청 시작: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # 응답 시간 계산
    process_time = time.time() - start_time
    
    # 응답 정보 로깅
    logger.info(
        f"요청 완료: {request.method} {request.url} - "
        f"상태: {response.status_code} - 처리시간: {process_time:.3f}s"
    )
    
    # 응답 헤더에 처리 시간 추가
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 앱 시작/종료 이벤트
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 시작")
    logger.info(f"설정: DEBUG={settings.DEBUG}")
    logger.info(f"업로드 디렉토리: {settings.UPLOAD_DIR}")
    
    # 필요한 디렉토리 생성
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info(f"{settings.APP_NAME} 종료")
    
    # 리소스 정리
    from app.services.job_service import job_service
    
    # 실행 중인 모든 작업 취소
    for job_id, job_info in job_service.jobs.items():
        if job_info.status.value == "running":
            job_service.cancel_job(job_id)
            logger.info(f"종료 시 작업 취소: {job_id}")


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
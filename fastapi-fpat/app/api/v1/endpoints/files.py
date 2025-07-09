"""
파일 업로드/다운로드 API 엔드포인트
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
import aiofiles
import uuid
from datetime import datetime
from pathlib import Path
import os

from app.core.config import settings
from app.models.schemas import FileUploadResponse, BaseResponse, FileInfo

router = APIRouter()


async def validate_file(file: UploadFile) -> None:
    """업로드 파일 검증"""
    # 파일 확장자 확인
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다. 허용 형식: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 파일 크기 확인 (FastAPI는 기본적으로 메모리에 로드하므로 여기서는 체크하지 않음)
    # 실제 환경에서는 streaming upload를 사용해야 함


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    파일 업로드
    
    - **file**: 업로드할 파일 (xlsx, xls, csv 형식)
    """
    try:
        # 파일 검증
        await validate_file(file)
        
        # 고유 파일 ID 생성
        file_id = str(uuid.uuid4())
        
        # 원본 파일명과 확장자 분리
        original_name = Path(file.filename).stem
        file_extension = Path(file.filename).suffix
        
        # 저장할 파일명 생성
        saved_filename = f"{file_id}_{original_name}{file_extension}"
        file_path = Path(settings.UPLOAD_DIR) / saved_filename
        
        # 파일 저장
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 파일 정보 생성
        file_info = FileInfo(
            filename=file.filename,
            file_id=file_id,
            file_path=str(file_path),
            file_size=len(content),
            upload_time=datetime.now(),
            content_type=file.content_type or "application/octet-stream"
        )
        
        return FileUploadResponse(
            success=True,
            message="파일 업로드 성공",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.post("/upload/multiple", response_model=BaseResponse)
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    다중 파일 업로드
    
    - **files**: 업로드할 파일들의 리스트
    """
    try:
        uploaded_files = []
        
        for file in files:
            # 파일 검증
            await validate_file(file)
            
            # 고유 파일 ID 생성
            file_id = str(uuid.uuid4())
            
            # 원본 파일명과 확장자 분리
            original_name = Path(file.filename).stem
            file_extension = Path(file.filename).suffix
            
            # 저장할 파일명 생성
            saved_filename = f"{file_id}_{original_name}{file_extension}"
            file_path = Path(settings.UPLOAD_DIR) / saved_filename
            
            # 파일 저장
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # 파일 정보 생성
            file_info = FileInfo(
                filename=file.filename,
                file_id=file_id,
                file_path=str(file_path),
                file_size=len(content),
                upload_time=datetime.now(),
                content_type=file.content_type or "application/octet-stream"
            )
            
            uploaded_files.append(file_info)
        
        return BaseResponse(
            success=True,
            message=f"{len(uploaded_files)}개 파일 업로드 성공",
            data={"uploaded_files": uploaded_files}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 파일 업로드 실패: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    파일 다운로드
    
    - **file_id**: 다운로드할 파일 ID
    """
    try:
        # 파일 찾기
        upload_dir = Path(settings.UPLOAD_DIR)
        file_pattern = f"{file_id}_*"
        
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        file_path = matching_files[0]
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")
        
        # 원본 파일명 추출 (file_id_ 부분 제거)
        filename_parts = file_path.name.split('_', 1)
        if len(filename_parts) > 1:
            original_filename = filename_parts[1]
        else:
            original_filename = file_path.name
        
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 실패: {str(e)}")


@router.get("/info/{file_id}", response_model=BaseResponse)
async def get_file_info(file_id: str):
    """
    파일 정보 조회
    
    - **file_id**: 조회할 파일 ID
    """
    try:
        # 파일 찾기
        upload_dir = Path(settings.UPLOAD_DIR)
        file_pattern = f"{file_id}_*"
        
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        file_path = matching_files[0]
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")
        
        # 파일 정보 생성
        stat = file_path.stat()
        
        # 원본 파일명 추출
        filename_parts = file_path.name.split('_', 1)
        if len(filename_parts) > 1:
            original_filename = filename_parts[1]
        else:
            original_filename = file_path.name
        
        file_info = {
            "file_id": file_id,
            "filename": original_filename,
            "file_path": str(file_path),
            "file_size": stat.st_size,
            "upload_time": datetime.fromtimestamp(stat.st_ctime),
            "modified_time": datetime.fromtimestamp(stat.st_mtime),
            "file_extension": file_path.suffix
        }
        
        return BaseResponse(
            success=True,
            message="파일 정보 조회 성공",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 정보 조회 실패: {str(e)}")


@router.delete("/{file_id}", response_model=BaseResponse)
async def delete_file(file_id: str):
    """
    파일 삭제
    
    - **file_id**: 삭제할 파일 ID
    """
    try:
        # 파일 찾기
        upload_dir = Path(settings.UPLOAD_DIR)
        file_pattern = f"{file_id}_*"
        
        matching_files = list(upload_dir.glob(file_pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        file_path = matching_files[0]
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")
        
        # 파일 삭제
        file_path.unlink()
        
        return BaseResponse(
            success=True,
            message="파일 삭제 성공",
            data={"deleted_file_id": file_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {str(e)}")


@router.get("/list", response_model=BaseResponse)
async def list_files(skip: int = 0, limit: int = 100):
    """
    업로드된 파일 목록 조회
    
    - **skip**: 건너뛸 파일 수
    - **limit**: 조회할 최대 파일 수
    """
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        
        if not upload_dir.exists():
            return BaseResponse(
                success=True,
                message="파일 목록 조회 성공",
                data={"files": [], "total": 0}
            )
        
        # 모든 파일 조회
        all_files = list(upload_dir.glob("*"))
        all_files.sort(key=lambda x: x.stat().st_ctime, reverse=True)  # 최신순 정렬
        
        # 페이징 적용
        paged_files = all_files[skip:skip + limit]
        
        file_list = []
        for file_path in paged_files:
            if file_path.is_file():
                # 파일 ID 추출
                filename = file_path.name
                if '_' in filename:
                    file_id = filename.split('_')[0]
                    original_filename = '_'.join(filename.split('_')[1:])
                else:
                    file_id = filename
                    original_filename = filename
                
                stat = file_path.stat()
                
                file_info = {
                    "file_id": file_id,
                    "filename": original_filename,
                    "file_size": stat.st_size,
                    "upload_time": datetime.fromtimestamp(stat.st_ctime),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime),
                    "file_extension": file_path.suffix
                }
                
                file_list.append(file_info)
        
        return BaseResponse(
            success=True,
            message="파일 목록 조회 성공",
            data={
                "files": file_list,
                "total": len(all_files),
                "skip": skip,
                "limit": limit,
                "returned": len(file_list)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 목록 조회 실패: {str(e)}")


@router.get("/disk-usage", response_model=BaseResponse)
async def get_disk_usage():
    """
    디스크 사용량 조회
    """
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        
        if not upload_dir.exists():
            return BaseResponse(
                success=True,
                message="디스크 사용량 조회 성공",
                data={
                    "total_files": 0,
                    "total_size": 0,
                    "total_size_mb": 0,
                    "upload_dir": str(upload_dir)
                }
            )
        
        total_size = 0
        total_files = 0
        
        for file_path in upload_dir.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                total_files += 1
        
        total_size_mb = total_size / (1024 * 1024)  # MB 변환
        
        return BaseResponse(
            success=True,
            message="디스크 사용량 조회 성공",
            data={
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size_mb, 2),
                "upload_dir": str(upload_dir),
                "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디스크 사용량 조회 실패: {str(e)}")
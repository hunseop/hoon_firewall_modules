"""
작업 관리 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
import asyncio
import json

from app.models.schemas import (
    JobStatusResponse, JobListResponse, JobInfo,
    BaseResponse, ProgressUpdate, WebSocketMessage
)
from app.services.job_service import job_service

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    작업 상태 조회
    
    - **job_id**: 조회할 작업 ID
    """
    try:
        job_info = job_service.get_job(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        return JobStatusResponse(
            success=True,
            message="작업 상태 조회 성공",
            data=job_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 실패: {str(e)}")


@router.get("/", response_model=JobListResponse)
async def get_all_jobs(skip: int = 0, limit: int = 100):
    """
    모든 작업 목록 조회
    
    - **skip**: 건너뛸 작업 수
    - **limit**: 조회할 최대 작업 수
    """
    try:
        jobs = job_service.get_all_jobs(skip, limit)
        
        return JobListResponse(
            success=True,
            message="작업 목록 조회 성공",
            data=jobs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 목록 조회 실패: {str(e)}")


@router.post("/{job_id}/cancel", response_model=BaseResponse)
async def cancel_job(job_id: str):
    """
    작업 취소
    
    - **job_id**: 취소할 작업 ID
    """
    try:
        success = job_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        return BaseResponse(
            success=True,
            message="작업이 취소되었습니다",
            data={"job_id": job_id, "cancelled": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 취소 실패: {str(e)}")


@router.delete("/{job_id}", response_model=BaseResponse)
async def delete_job(job_id: str):
    """
    작업 삭제
    
    - **job_id**: 삭제할 작업 ID
    """
    try:
        success = job_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        return BaseResponse(
            success=True,
            message="작업이 삭제되었습니다",
            data={"job_id": job_id, "deleted": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 삭제 실패: {str(e)}")


@router.get("/{job_id}/result", response_model=BaseResponse)
async def get_job_result(job_id: str):
    """
    작업 결과 조회
    
    - **job_id**: 결과를 조회할 작업 ID
    """
    try:
        job_info = job_service.get_job(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        if job_info.status.value not in ["success", "failed"]:
            raise HTTPException(status_code=400, detail="작업이 아직 완료되지 않았습니다")
        
        return BaseResponse(
            success=True,
            message="작업 결과 조회 성공",
            data={
                "job_id": job_id,
                "status": job_info.status.value,
                "result": job_info.result,
                "error_message": job_info.error_message,
                "completed_at": job_info.completed_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 결과 조회 실패: {str(e)}")


@router.get("/statistics/summary", response_model=BaseResponse)
async def get_job_statistics():
    """
    작업 통계 조회
    """
    try:
        stats = job_service.get_job_statistics()
        
        return BaseResponse(
            success=True,
            message="작업 통계 조회 성공",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 통계 조회 실패: {str(e)}")


@router.post("/cleanup", response_model=BaseResponse)
async def cleanup_old_jobs(max_age_hours: int = 24):
    """
    오래된 작업 정리
    
    - **max_age_hours**: 정리할 최대 나이 (시간)
    """
    try:
        cleaned_count = job_service.cleanup_old_jobs(max_age_hours)
        
        return BaseResponse(
            success=True,
            message=f"{cleaned_count}개의 오래된 작업을 정리했습니다",
            data={
                "cleaned_count": cleaned_count,
                "max_age_hours": max_age_hours
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 정리 실패: {str(e)}")


# WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.job_subscribers: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # 작업별 구독에서도 제거
        for job_id, subscribers in self.job_subscribers.items():
            if websocket in subscribers:
                subscribers.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 연결이 끊어진 경우 무시
                pass

    def subscribe_to_job(self, job_id: str, websocket: WebSocket):
        """특정 작업의 진행률 업데이트 구독"""
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = []
        if websocket not in self.job_subscribers[job_id]:
            self.job_subscribers[job_id].append(websocket)

    async def send_job_update(self, job_id: str, update: dict):
        """특정 작업의 구독자들에게 업데이트 전송"""
        if job_id in self.job_subscribers:
            message = json.dumps(update)
            disconnected = []
            
            for websocket in self.job_subscribers[job_id]:
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)
            
            # 연결이 끊어진 WebSocket 정리
            for ws in disconnected:
                self.job_subscribers[job_id].remove(ws)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    작업 상태 실시간 업데이트를 위한 WebSocket 엔드포인트
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # 클라이언트에서 특정 작업 구독 요청
                if message.get("type") == "subscribe" and message.get("job_id"):
                    job_id = message["job_id"]
                    manager.subscribe_to_job(job_id, websocket)
                    
                    # 현재 작업 상태 전송
                    job_info = job_service.get_job(job_id)
                    if job_info:
                        response = {
                            "type": "job_status",
                            "job_id": job_id,
                            "data": {
                                "status": job_info.status.value,
                                "progress": job_info.progress,
                                "message": f"작업 상태: {job_info.status.value}"
                            }
                        }
                        await manager.send_personal_message(json.dumps(response), websocket)
                
                # 작업 목록 요청
                elif message.get("type") == "get_jobs":
                    jobs = job_service.get_all_jobs(0, 10)  # 최근 10개 작업
                    response = {
                        "type": "job_list",
                        "data": [
                            {
                                "job_id": job.job_id,
                                "job_type": job.job_type,
                                "status": job.status.value,
                                "progress": job.progress,
                                "created_at": job.created_at.isoformat()
                            }
                            for job in jobs
                        ]
                    }
                    await manager.send_personal_message(json.dumps(response), websocket)
                
                # 작업 통계 요청
                elif message.get("type") == "get_statistics":
                    stats = job_service.get_job_statistics()
                    response = {
                        "type": "statistics",
                        "data": stats
                    }
                    await manager.send_personal_message(json.dumps(response), websocket)
                
                else:
                    # 알 수 없는 메시지 타입
                    error_response = {
                        "type": "error",
                        "message": f"알 수 없는 메시지 타입: {message.get('type')}"
                    }
                    await manager.send_personal_message(json.dumps(error_response), websocket)
                    
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "잘못된 JSON 형식입니다"
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """
    특정 작업의 진행률 실시간 업데이트를 위한 WebSocket 엔드포인트
    """
    await manager.connect(websocket)
    manager.subscribe_to_job(job_id, websocket)
    
    try:
        # 현재 작업 상태 즉시 전송
        job_info = job_service.get_job(job_id)
        if job_info:
            initial_update = {
                "type": "progress_update",
                "job_id": job_id,
                "status": job_info.status.value,
                "progress": job_info.progress,
                "message": f"현재 상태: {job_info.status.value}"
            }
            await manager.send_personal_message(json.dumps(initial_update), websocket)
        
        # 연결 유지
        while True:
            try:
                # 클라이언트로부터 메시지 수신 (keepalive 등)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # ping-pong 처리
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # 타임아웃 시 연결 상태 확인을 위한 ping 전송
                try:
                    await websocket.send_text("ping")
                except:
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# 작업 진행률 업데이트 함수 (job_service에서 호출)
async def notify_job_progress(job_id: str, status: str, progress: float, message: str = ""):
    """작업 진행률 업데이트를 WebSocket 클라이언트들에게 전송"""
    update = {
        "type": "progress_update",
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": job_service.get_job(job_id).started_at.isoformat() if job_service.get_job(job_id) else None
    }
    
    await manager.send_job_update(job_id, update)
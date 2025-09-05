# app/routers/media.py
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/{file_path:path}")
async def get_media_file(file_path: str):
    """
    미디어 파일을 반환하는 API 엔드포인트
    
    Args:
        file_path: media/ 이후의 파일 경로 (예: challenges/img_references/image.png)
    
    Returns:
        FileResponse: 요청된 파일
    """
    # 전체 파일 경로 구성
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # 파일 존재 확인
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 보안: 상위 디렉토리 접근 방지
    if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(full_path)

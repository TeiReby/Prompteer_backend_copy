# app/utils/file_handler.py
import os
import time
from io import BytesIO

import aiofiles
from fastapi import UploadFile
from PIL import Image

from app.core.config import settings


def _add_timestamp(filename: str) -> str:
    """파일명에 타임스탬프를 추가하여 고유한 파일명을 생성합니다."""
    filename_base, file_extension = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"{filename_base}_{timestamp}{file_extension}"


async def save_upload_file(upload_file: UploadFile, filename: str, destination: str) -> str:
    """
    업로드된 파일을 지정된 목적지 폴더에 비동기적으로 저장하고, 파일 경로를 반환합니다.

    - `destination`은 `settings.MEDIA_ROOT`의 하위 경로입니다.
    - 파일명 중복을 방지하기 위해 타임스탬프를 파일명에 추가합니다.

    Args:
        upload_file: FastAPI의 `UploadFile` 객체.
        filename: 저장될 파일의 원본 이름.
        destination: `MEDIA_ROOT` 하위의 파일 저장 목적지 디렉토리.

    Returns:
        서버에 저장된 파일의 전체 경로.
    """
    try:
        full_destination_dir = os.path.join(settings.MEDIA_ROOT, destination)
        os.makedirs(full_destination_dir, exist_ok=True)

        unique_filename = _add_timestamp(filename)
        file_path = os.path.join(full_destination_dir, unique_filename)

        async with aiofiles.open(file_path, "wb") as f:
            content = await upload_file.read()
            await f.write(content)

        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        raise


async def save_png(image_binary: bytes, filename: str, destination: str) -> str:
    """
    이미지 바이너리 데이터를 PNG 파일로 변환하여 비동기적으로 저장합니다.

    - `destination`은 `settings.MEDIA_ROOT`의 하위 경로입니다.
    """
    full_destination_dir = os.path.join(settings.MEDIA_ROOT, destination)
    os.makedirs(full_destination_dir, exist_ok=True)

    filename_base, _ = os.path.splitext(filename)
    unique_filename = _add_timestamp(f"{filename_base}.png")
    file_path = os.path.join(full_destination_dir, unique_filename)

    try:
        image = Image.open(BytesIO(image_binary))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(image_bytes)

        return file_path
    except Exception as e:
        raise Exception(f"Failed to save image: {str(e)}")


async def save_mp4(video_bytes: bytes, filename: str, destination: str) -> str:
    """
    비디오 바이너리 데이터를 파일로 비동기적으로 저장합니다.

    - `destination`은 `settings.MEDIA_ROOT`의 하위 경로입니다.
    """
    full_destination_dir = os.path.join(settings.MEDIA_ROOT, destination)
    os.makedirs(full_destination_dir, exist_ok=True)

    unique_filename = _add_timestamp(f"{filename}.mp4")
    file_path = os.path.join(full_destination_dir, unique_filename)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(video_bytes)

        return file_path

    except Exception as e:
        raise Exception(f"Failed to save video: {str(e)}")

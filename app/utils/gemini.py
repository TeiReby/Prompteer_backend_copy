# app/utils/gemini.py
import asyncio

from google import genai
from google.genai import types

from app.core.config import settings


async def generate_code(prompt: str) -> dict:
    """
    Gemini 모델을 사용하여 주어진 프롬프트에 기반한 코드를 생성합니다.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction="Based on the user's prompt, provide the new python code. Only return the code, no additional text, explanations, or comments."
            ),
            contents=f"{prompt}",
        )
        return {"content": response.text}

    except Exception as e:
        raise Exception(f"code generation failed: {str(e)}")


async def generate_png_binary(prompt: str) -> bytes:
    """
    Gemini 이미지 생성 모델을 사용하여 PNG 이미지의 바이너리 데이터를 생성합니다.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        candidates = getattr(response, "candidates", None)
        if not candidates or not candidates[0]:
            raise Exception("No candidates found in image generation response")

        content = getattr(candidates[0], "content", None)
        if not content or not hasattr(content, "parts"):
            raise Exception("No content parts found in image generation response")

        for part in content.parts:
            if part.inline_data:
                return part.inline_data.data

        raise Exception("No image binary found in the response")
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


async def generate_mp4_binary(prompt: str) -> bytes:
    """
    Gemini Veo 모델을 사용하여 비디오를 생성하고 바이너리 데이터를 반환합니다.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        # 1. 비디오 생성 시작
        operation = await client.aio.models.generate_videos(
            model="veo-3.0-fast-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                negative_prompt="",
                duration_seconds=5,
                enhance_prompt=True,
            ),
        )

        # 2. 작업 완료 폴링
        while not operation.done:
            await asyncio.sleep(10)
            operation = await client.aio.operations.get(operation)

        # 3. 결과 확인
        if (
            not operation.response
            or not hasattr(operation.response, "generated_videos")
            or not operation.response.generated_videos
        ):
            raise Exception("No video data returned in operation response.")

        generated_video = operation.response.generated_videos[0]
        if not generated_video or not hasattr(generated_video, "video"):
            raise Exception("Generated video sample is invalid.")

        # 4. 비디오 데이터 다운로드 (전체 video 객체를 전달)
        video_file = getattr(generated_video, "video", None)
        if video_file is None:
            raise Exception("Video file object not found.")
        video_bytes = await client.aio.files.download(file=video_file)

        if not video_bytes:
            raise Exception("Downloaded video data is empty.")

        return video_bytes

    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")

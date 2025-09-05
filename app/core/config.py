# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    애플리케이션의 설정을 관리하는 클래스.

    pydantic-settings를 사용하여 .env 파일 또는 환경 변수에서
    설정 값을 자동으로 읽어옵니다.

    Attributes:
        GEMINI_API_KEY: Google Gemini API 사용을 위한 API 키.
        DATABASE_URL: 애플리케이션이 연결할 데이터베이스의 URL.
        DEBUG: 디버그 모드 활성화 여부.
        MEDIA_ROOT: 미디어 파일(이미지, 비디오 등)이 저장될 루트 디렉터리.
        SECRET_KEY: JWT 토큰 서명에 사용될 비밀 키.
        ALGORITHM: JWT 토큰 서명에 사용될 해싱 알고리즘.
        ACCESS_TOKEN_EXPIRE_MINUTES: 액세스 토큰의 만료 시간 (분 단위).
    """

    # --- API Keys & Secrets ---
    GEMINI_API_KEY: str

    # --- Database ---
    DATABASE_URL: str

    # --- Application Settings ---
    DEBUG: bool = True
    MEDIA_ROOT: str = "media"

    # --- JWT Settings ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600

    # .env 파일을 읽어오도록 설정
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# 설정 객체를 인스턴스화하여 애플리케이션 전역에서 사용할 수 있도록 합니다.
# `from app.core.config import settings`로 임포트하여 사용합니다.
settings = Settings()

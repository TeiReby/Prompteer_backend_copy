# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routers import challenge, post, share, user


def setup_media_directories():
    """
    애플리케이션에서 사용할 미디어 파일 저장 디렉토리를 설정합니다.
    `settings.MEDIA_ROOT`를 기반으로, 각 도메인별 하위 디렉토리를 생성하여
    업로드된 파일을 체계적으로 관리합니다.
    """
    base_dir = settings.MEDIA_ROOT
    # 도메인별 파일 저장을 위한 계층적 디렉토리 구조
    domain_dirs = {
        "challenges": ["img_references", "video_references"],
        "shares": ["img_shares", "video_shares"],
    }

    # 기본 디렉토리 및 하위 디렉토리 생성 (이미 존재하면 무시)
    os.makedirs(base_dir, exist_ok=True)
    for domain, sub_dirs in domain_dirs.items():
        domain_path = os.path.join(base_dir, domain)
        os.makedirs(domain_path, exist_ok=True)
        for sub_dir in sub_dirs:
            os.makedirs(os.path.join(domain_path, sub_dir), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션의 시작과 종료 시점에 실행될 로직을 관리하는
    lifespan 이벤트 핸들러입니다.

    - 시작 시: 데이터베이스와 테이블을 생성하고, 미디어 디렉토리를 설정합니다.
    - 종료 시: 애플리케이션 종료 메시지를 출력합니다.
    """
    print("애플리케이션 시작...")
    # 데이터베이스 및 테이블 생성
    create_db_and_tables()
    # 미디어 디렉토리 설정
    setup_media_directories()
    yield
    print("애플리케이션 종료.")


# FastAPI 앱 인턴스 생성 및 lifespan 이벤트 핸들러 등록
app = FastAPI(lifespan=lifespan, root_path="/api")

# --- CORS 미들웨어 추가 ---
# 개발 환경을 위해 모든 오리진, 메소드, 헤더를 허용합니다.
# 프로덕션 환경에서는 보안을 위해 허용할 오리진을 명시적으로 지정해야 합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://likelion.site",
        "http://www.likelion.site",
        "https://likelion.site",
        "https://www.likelion.site",
        "http://localhost:3000", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 포함 ---
# 각 기능별로 분리된 라우터들을 메인 앱에 포함시킵니다.
app.include_router(user.router)
app.include_router(challenge.router)
app.include_router(share.router)
app.include_router(post.router)

# --- 정적 파일 마운트 ---
# MEDIA_ROOT 디렉토리가 없으면 생성 후 마운트합니다.
if not os.path.exists(settings.MEDIA_ROOT):
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

app.mount(
    f"/{settings.MEDIA_ROOT}",
    StaticFiles(directory=settings.MEDIA_ROOT),
    name="media",
)


@app.get("/")
async def read_root():
    """
    애플리케이션의 루트 경로("/")에 대한 기본 응답을 반환합니다.
    서버가 정상적으로 실행 중인지 확인하는 용도로 사용할 수 있습니다.
    """
    return {"message": "Welcome to the Prompteer!"}

# tests/conftest.py
import base64

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.crud import challenge as crud_challenge
from app.crud import share as crud_share
from app.crud import user as crud_user
from app.dependency import get_db
from app.main import app
from app.models.serializers import (
    ChallengeCreate,
    ImgShareCreate,
    PSShareCreate,
    ShareCreate,
    VideoShareCreate,
)

# =================================================================
# Pytest Customization
# =================================================================


def pytest_addoption(parser):
    """'--run-gemini-api' 커스텀 옵션을 pytest에 추가합니다."""
    parser.addoption(
        "--run-gemini-api",
        action="store_true",
        default=False,
        help="Run tests that call the live Gemini API",
    )


# =================================================================
# 테스트 환경 설정
# =================================================================

# 테스트용 데이터베이스를 SQLite 인메모리 DB가 아닌 파일 기반으로 설정합니다.
# 이를 통해 테스트 실행 중 DB 상태를 직접 확인하거나 디버깅하기 용이합니다.
TEST_DATABASE_URL = "sqlite:///test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


def override_get_db():
    """
    FastAPI의 `get_db` 의존성을 오버라이드하여 테스트용 DB 세션을 제공하는 함수.
    각 테스트는 격리된 DB 세션을 사용하게 됩니다.
    """
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment(tmp_path_factory):
    """
    각 테스트 함수 실행 전후로 테스트 환경을 설정하고 정리하는 최상위 픽스처.

    - `autouse=True`: 모든 테스트 함수에서 자동으로 이 픽스처를 사용합니다.
    - `scope="function"`: 각 테스트 함수마다 독립적으로 실행됩니다.

    실행 전 작업:
    1. 임시 미디어 디렉터리 생성 및 설정 적용.
    2. `get_db` 의존성을 `override_get_db`로 교체하여 테스트 DB를 사용하도록 설정.
    3. 테스트 DB에 모든 테이블 생성.

    실행 후 작업:
    1. 테스트 DB의 모든 테이블 삭제하여 다음 테스트에 영향을 주지 않도록 함.
    """
    # 1. 임시 미디어 디렉터리 생성
    temp_media_root = tmp_path_factory.mktemp("media")
    settings.MEDIA_ROOT = str(temp_media_root)

    # 2. 의존성 오버라이드
    app.dependency_overrides[get_db] = override_get_db

    # 3. 테이블 생성
    SQLModel.metadata.create_all(engine)

    yield  # 여기에서 실제 테스트 함수가 실행됩니다.

    # 4. 테이블 삭제
    SQLModel.metadata.drop_all(engine)


# =================================================================
# 테스트용 클라이언트 픽스처
# =================================================================


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    테스트 전체 모듈에서 공유되는 FastAPI `TestClient` 인스턴스를 생성합니다.
    - `scope="module"`: 이 픽스처는 모듈 단위로 한 번만 생성되어 재사용됩니다.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """테스트 함수 내에서 DB에 직접 접근해야 할 때 사용하는 세션 픽스처."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient) -> dict:
    """
    일반 사용자(user)로 회원가입 및 로그인된 상태의 클라이언트를 제공하는 픽스처.

    Returns:
        dict: 'client', 'headers'(인증 토큰 포함), 'user_id'를 포함하는 딕셔너리.
    """
    user_data = {
        "nickname": "auth_user",
        "email": "auth@example.com",
        "password": "authpassword",
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 201, "테스트 사용자 생성 실패"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    user_id = response.json()["id"]
    return {"client": client, "headers": headers, "user_id": user_id}


@pytest.fixture(scope="function")
def authenticated_client_2(client: TestClient) -> dict:
    """
    다른 일반 사용자(user_2)로 로그인된 상태의 클라이언트를 제공하는 픽스처.
    여러 사용자가 상호작용하는 시나리오를 테스트할 때 사용됩니다.
    """
    user_data = {
        "nickname": "auth_user_2",
        "email": "auth2@example.com",
        "password": "authpassword2",
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 201, "테스트 사용자 2 생성 실패"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    user_id = response.json()["id"]
    return {"client": client, "headers": headers, "user_id": user_id}


@pytest.fixture(scope="function")
def authenticated_admin_client(client: TestClient) -> dict:
    """
    관리자(admin) 권한으로 로그인된 상태의 클라이언트를 제공하는 픽스처.
    관리자 전용 API를 테스트할 때 사용됩니다.
    """
    user_data = {
        "nickname": "admin_user",
        "email": "admin@example.com",
        "password": "adminpassword",
        "is_admin": True,
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 201, "테스트 관리자 생성 실패"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    user_id = response.json()["id"]
    return {"client": client, "headers": headers, "user_id": user_id}


# =================================================================
# 테스트 데이터 생성 픽스처
# =================================================================


@pytest.fixture(scope="function")
def created_ps_share(db_session: Session, authenticated_client: dict) -> dict:
    """테스트용 PS 챌린지와 그에 대한 공유를 미리 생성하는 픽스처."""
    user = crud_user.get_user(db_session, authenticated_client["user_id"])
    challenge_in = ChallengeCreate(
        tag="ps",
        level="Easy",
        title="PS Share Test Challenge",
        challenge_number=9001,
    )
    db_challenge = crud_challenge.create_ps_challenge(db_session, challenge_in, [], user)

    share_in = ShareCreate(challenge_id=db_challenge.id, prompt="Test Prompt")
    ps_share_in = PSShareCreate(code="print('hello')")
    db_share = crud_share.create_ps_share(db_session, share_in, ps_share_in, user)

    return {
        "id": db_share.id,
        "challenge_id": db_challenge.id,
        "user_id": user.id,
        "prompt": "Test Prompt",
    }


@pytest.fixture(scope="function")
def created_img_share(db_session: Session, authenticated_client: dict) -> dict:
    """테스트용 Img 챌린지와 그에 대한 공유를 미리 생성하는 픽스처."""
    user = crud_user.get_user(db_session, authenticated_client["user_id"])
    challenge_in = ChallengeCreate(
        tag="img",
        level="Medium",
        title="Img Share Test Challenge",
        challenge_number=9002,
    )
    db_challenge = crud_challenge.create_img_challenge(db_session, challenge_in, [], user)

    share_in = ShareCreate(challenge_id=db_challenge.id)
    img_share_in = ImgShareCreate(img_url="/media/shares/img_shares/test.png")
    db_share = crud_share.create_img_share(db_session, share_in, img_share_in, user)

    return {"id": db_share.id, "challenge_id": db_challenge.id, "user_id": user.id}


@pytest.fixture(scope="function")
def created_video_share(db_session: Session, authenticated_client: dict) -> dict:
    """테스트용 Video 챌린지와 그에 대한 공유를 미리 생성하는 픽스처."""
    user = crud_user.get_user(db_session, authenticated_client["user_id"])
    challenge_in = ChallengeCreate(
        tag="video",
        level="Hard",
        title="Video Share Test Challenge",
        challenge_number=9003,
    )
    db_challenge = crud_challenge.create_video_challenge(
        db_session, challenge_in, [], user
    )

    share_in = ShareCreate(challenge_id=db_challenge.id)
    video_share_in = VideoShareCreate(video_url="/media/shares/video_shares/test.mp4")
    db_share = crud_share.create_video_share(
        db_session, share_in, video_share_in, user
    )

    return {"id": db_share.id, "challenge_id": db_challenge.id, "user_id": user.id}


# =================================================================
# 모킹 제어 픽스처
# =================================================================


@pytest.fixture(scope="function")
def gemini_api_mocker(request, mocker):
    """
    `--run-gemini-api` 옵션 여부에 따라 Gemini API 호출을 모킹하거나 실제 호출하도록 제어합니다.
    """
    if not request.config.getoption("--run-gemini-api"):
        # --- 모킹 모드 (기본값) ---
        mocker.patch(
            "app.routers.challenge.gemini.generate_code",
            return_value={"content": "mocked_code"},
        )
        mock_png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
        mocker.patch(
            "app.routers.challenge.gemini.generate_png_binary",
            return_value=mock_png_bytes,
        )
        mocker.patch(
            "app.routers.challenge.gemini.generate_mp4_binary",
            return_value=b"mocked_mp4_bytes",
        )
        # 파일 저장 함수도 모킹하여 예측 가능한 경로를 반환하도록 합니다.
        mocker.patch(
            "app.routers.challenge.save_png", return_value="mocked/path.png"
        )
        mocker.patch(
            "app.routers.challenge.save_mp4", return_value="mocked/path.mp4"
        )
        yield "mocked"
    else:
        # --- 실제 API 호출 모드 ---
        yield "live"

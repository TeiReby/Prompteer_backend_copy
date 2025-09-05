# tests/test_user_scenario.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_user_data():
    """사용자 시나리오 테스트에 일관되게 사용될 사용자 데이터를 제공하는 픽스처."""
    return {
        "nickname": "testuser_scenario",
        "email": "scenario@example.com",
        "password": "strongpassword123",
    }


def test_full_user_lifecycle_scenario(client: TestClient, test_user_data: dict):
    """
    사용자 생명주기 전체(회원가입 -> 정보 조회 -> 정보 수정 -> 탈퇴)를 테스트하는 시나리오.
    """
    # --- 1. 회원가입 ---
    response = client.post("/users/register", json=test_user_data)
    assert response.status_code == 201, f"회원가입 실패: {response.text}"
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # --- 2. 상세 정보 조회 (/me/details) ---
    response = client.get("/users/me/details", headers=headers)
    assert response.status_code == 200, "사용자 상세 정보 조회 실패"
    user_id = response.json()["id"]
    assert response.json()["nickname"] == test_user_data["nickname"]
    assert "profile" in response.json()

    # --- 3. 프로필 수정 ---
    profile_update_data = {
        "introduction": "FastAPI 전문가가 되고 싶습니다.",
        "interested_in": {"backend_developer": True, "ps": True},
    }
    response = client.put(
        "/users/me/profile", json=profile_update_data, headers=headers
    )
    assert response.status_code == 200, "프로필 수정 실패"
    assert response.json()["introduction"] == profile_update_data["introduction"]

    # --- 4. 사용자 정보 수정 ---
    user_update_data = {"email": "new_scenario@example.com"}
    response = client.put("/users/me", json=user_update_data, headers=headers)
    assert response.status_code == 200, "사용자 정보 수정 실패"
    assert response.json()["email"] == user_update_data["email"]

    # --- 5. 회원 탈퇴 ---
    response = client.delete("/users/unregister", headers=headers)
    assert response.status_code == 204, "회원 탈퇴 실패"

    # --- 6. 검증 ---
    login_credentials = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/users/login", data=login_credentials)
    assert response.status_code == 401, "탈퇴한 계정으로 로그인이 되어서는 안 됨"

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404, "탈퇴한 사용자의 정보가 조회되어서는 안 됨"


def test_read_current_user_me(authenticated_client: dict):
    """
    GET /users/me 엔드포인트가 현재 로그인된 사용자의 기본 정보를 정확히 반환하는지 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]
    user_id = authenticated_client["user_id"]

    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["nickname"] == "auth_user"
    assert "password" not in data
    assert "profile" not in data  # /me는 프로필을 포함하지 않음


def test_register_duplicate_user(client: TestClient, test_user_data: dict):
    """
    중복된 닉네임 또는 이메일로 회원가입을 시도할 때 400 에러가 발생하는지 테스트합니다.
    """
    client.post("/users/register", json=test_user_data)

    duplicate_nickname_data = test_user_data.copy()
    duplicate_nickname_data["email"] = "another@example.com"
    response = client.post("/users/register", json=duplicate_nickname_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Nickname already registered"

    duplicate_email_data = test_user_data.copy()
    duplicate_email_data["nickname"] = "another_user"
    response = client.post("/users/register", json=duplicate_email_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_authentication_failures(client: TestClient):
    """
    인증 실패 케이스들을 테스트합니다.
    """
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    invalid_headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/users/me", headers=invalid_headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_registration_validation_failures(client: TestClient):
    """
    회원가입 시 Pydantic 모델의 유효성 검사 실패 케이스를 테스트합니다.
    """
    invalid_email_data = {
        "nickname": "validation_user",
        "email": "not-an-email",
        "password": "password123",
    }
    response = client.post("/users/register", json=invalid_email_data)
    assert response.status_code == 422
    assert "value is not a valid email address" in response.text


def test_user_utility_endpoints(authenticated_client: dict):
    """
    닉네임 및 이메일 중복 확인 엔드포인트의 정상 및 실패 케이스를 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user_data = client.get("/users/me", headers=authenticated_client["headers"]).json()

    response = client.get(f"/users/check-nickname/{user_data['nickname']}")
    assert response.status_code == 409

    response = client.get(f"/users/check-email/{user_data['email']}")
    assert response.status_code == 409

    response = client.get("/users/check-nickname/available_nickname")
    assert response.status_code == 204

    response = client.get("/users/check-email/available@email.com")
    assert response.status_code == 204


def test_read_other_user_profile_and_auth(
    authenticated_client: dict, authenticated_client_2: dict
):
    """
    다른 사용자의 공개 프로필 조회 및 프로필 수정 권한을 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user1_id = authenticated_client["user_id"]
    user2_headers = authenticated_client_2["headers"]

    # --- 1. 사용자 2가 사용자 1의 프로필을 조회 ---
    response = client.get(f"/users/{user1_id}", headers=user2_headers)
    assert response.status_code == 200
    user1_data = response.json()
    assert user1_data["id"] == user1_id
    assert "profile" in user1_data
    assert "password" not in user1_data

    # --- 2. 사용자 2가 사용자 1의 프로필을 수정하려고 시도 (실패해야 함) ---
    # /users/me/profile 엔드포인트는 현재 로그인된 사용자 본인의 프로필만 수정 가능
    # 따라서 user2의 토큰으로 user1의 프로필을 직접 수정하는 API 경로는 존재하지 않음
    # 여기서는 user2가 자신의 프로필을 수정하는 것은 성공하는지 확인
    profile_update_data = {"introduction": "User 2's introduction"}
    response = client.put(
        "/users/me/profile", json=profile_update_data, headers=user2_headers
    )
    assert response.status_code == 200
    assert response.json()["introduction"] == profile_update_data["introduction"]

    # 사용자 1의 프로필은 변경되지 않았는지 다시 확인
    response = client.get(f"/users/{user1_id}", headers=user1_headers)
    assert (
        response.json()["profile"]["introduction"]
        != profile_update_data["introduction"]
    )

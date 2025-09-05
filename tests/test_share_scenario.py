# tests/test_share_scenario.py
from fastapi.testclient import TestClient


def test_read_shares_and_filter(
    client: TestClient,
    created_ps_share: dict,
    created_img_share: dict,
    created_video_share: dict,
):
    """
    다양한 타입의 Share 목록을 조회하고, 챌린지 ID로 필터링하는 기능을 테스트합니다.
    """
    # --- 1. 타입별 목록 조회 ---
    response_ps = client.get("/shares/ps/")
    assert response_ps.status_code == 200
    assert any(s["id"] == created_ps_share["id"] for s in response_ps.json())

    response_img = client.get("/shares/img/")
    assert response_img.status_code == 200
    assert any(s["id"] == created_img_share["id"] for s in response_img.json())

    response_video = client.get("/shares/video/")
    assert response_video.status_code == 200
    assert any(s["id"] == created_video_share["id"] for s in response_video.json())

    # --- 2. 챌린지 ID로 필터링 ---
    challenge_id = created_img_share["challenge_id"]
    response_filtered = client.get(f"/shares/img/?challenge_id={challenge_id}")
    assert response_filtered.status_code == 200
    assert len(response_filtered.json()) > 0
    assert all(
        s["challenge_id"] == challenge_id for s in response_filtered.json()
    ), "필터링된 모든 결과는 동일한 challenge_id를 가져야 합니다."


def test_read_single_share(client: TestClient, created_ps_share: dict):
    """ID로 특정 Share의 상세 정보를 조회하는 기능을 테스트합니다."""
    share_id = created_ps_share["id"]
    response = client.get(f"/shares/{share_id}")
    assert response.status_code == 200
    share_data = response.json()
    assert share_data["id"] == share_id
    assert share_data["prompt"] == created_ps_share["prompt"]
    assert "ps_share" in share_data
    assert share_data["ps_share"]["code"] is not None


def test_share_like_unlike_scenario(
    client: TestClient, authenticated_client_2: dict, created_ps_share: dict
):
    """Share에 대한 '좋아요' 및 '좋아요 취소' 기능을 테스트합니다."""
    user2_headers = authenticated_client_2["headers"]
    share_id = created_ps_share["id"]

    # --- 1. 좋아요 ---
    response = client.post(f"/shares/{share_id}/like", headers=user2_headers)
    assert response.status_code == 201, "좋아요 실패"

    response = client.get(f"/shares/{share_id}")
    assert response.json()["likes_count"] == 1, "좋아요 후 카운트가 1이어야 함"

    # --- 2. 중복 좋아요 시도 (실패) ---
    response = client.post(f"/shares/{share_id}/like", headers=user2_headers)
    assert response.status_code == 409, "중복 좋아요는 Conflict 에러를 발생시켜야 함"

    # --- 3. 좋아요 취소 ---
    response = client.delete(f"/shares/{share_id}/like", headers=user2_headers)
    assert response.status_code == 204, "좋아요 취소 실패"

    response = client.get(f"/shares/{share_id}")
    assert response.json()["likes_count"] == 0, "좋아요 취소 후 카운트가 0이어야 함"


def test_share_delete_authorization(
    client: TestClient, authenticated_client: dict, authenticated_client_2: dict, created_ps_share: dict
):
    """Share 삭제 시 소유권 및 권한을 테스트합니다."""
    owner_headers = authenticated_client["headers"]
    other_user_headers = authenticated_client_2["headers"]
    share_id = created_ps_share["id"]

    # --- 1. 다른 사용자가 삭제 시도 (실패) ---
    response = client.delete(f"/shares/{share_id}", headers=other_user_headers)
    assert response.status_code == 404, "다른 사용자는 공유를 삭제할 수 없어야 함"

    # --- 2. 소유자가 삭제 (성공) ---
    response = client.delete(f"/shares/{share_id}", headers=owner_headers)
    assert response.status_code == 204, "소유자의 공유 삭제 실패"

    # --- 3. 삭제 후 조회 (실패) ---
    response = client.get(f"/shares/{share_id}")
    assert response.status_code == 404, "삭제된 공유는 조회될 수 없어야 함"


def test_admin_can_manage_other_users_share(
    client: TestClient, authenticated_admin_client: dict, created_ps_share: dict
):
    """관리자가 다른 사용자의 공유를 삭제할 수 있는지 테스트합니다."""
    admin_headers = authenticated_admin_client["headers"]
    share_id = created_ps_share["id"]

    # --- 관리자가 해당 공유를 삭제 (204 No Content 예상) ---
    response = client.delete(f"/shares/{share_id}", headers=admin_headers)
    assert response.status_code == 204

    # 삭제 후 조회되지 않는지 확인
    response = client.get(f"/shares/{share_id}")
    assert response.status_code == 404

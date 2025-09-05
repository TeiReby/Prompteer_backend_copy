# tests/test_post_scenario.py
from fastapi.testclient import TestClient


def test_post_lifecycle(authenticated_client: dict):
    """게시글의 생성, 수정, 삭제 라이프사이클을 테스트합니다."""
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    # --- 1. 게시글 생성 (첨부파일 URL 포함) ---
    post_data = {
        "type": "share",
        "tag": "img",
        "title": "My First Post",
        "content": "Check out this image!",
        "attachment_urls": ["/media/posts/attachments/test_image.png"],
    }
    response = client.post("/posts/", json=post_data, headers=headers)
    assert response.status_code == 201, "게시글 생성 실패"
    post = response.json()
    post_id = post["id"]
    assert len(post["attachments"]) == 1, "첨부파일이 정상적으로 추가되지 않음"
    assert post["attachments"][0]["file_path"] == post_data["attachment_urls"][0]

    # --- 2. 게시글 단일 조회 ---
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["title"] == post_data["title"]

    # --- 3. 게시글 수정 ---
    update_data = {
        "title": "My Updated Post",
        "content": "This content has been updated.",
    }
    response = client.put(f"/posts/{post_id}", json=update_data, headers=headers)
    assert response.status_code == 200, "게시글 수정 실패"
    updated_post = response.json()
    assert updated_post["title"] == update_data["title"]

    # --- 4. 게시글 삭제 ---
    response = client.delete(f"/posts/{post_id}", headers=headers)
    assert response.status_code == 204, "게시글 삭제 실패"

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 404, "삭제된 게시글이 조회되어서는 안 됨"


def test_comment_lifecycle(authenticated_client: dict, authenticated_client_2: dict):
    """댓글의 생성, 수정, 삭제 라이프사이클을 테스트합니다."""
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # 게시글 생성
    post_res = client.post(
        "/posts/",
        json={"type": "question", "tag": "ps", "title": "Post for comments"},
        headers=user1_headers,
    )
    post_id = post_res.json()["id"]

    # --- 1. 댓글 생성 ---
    comment_data = {"post_id": post_id, "content": "Initial comment"}
    res_comment = client.post(
        f"/posts/{post_id}/comments", json=comment_data, headers=user2_headers
    )
    assert res_comment.status_code == 201, "댓글 생성 실패"
    comment_id = res_comment.json()["id"]

    # --- 2. 댓글 수정 ---
    client.put(
        f"/posts/comments/{comment_id}",
        json={"content": "Updated comment"},
        headers=user2_headers,
    )
    res_post = client.get(f"/posts/{post_id}")
    assert res_post.json()["comments"][0]["content"] == "Updated comment", "댓글 수정 실패"

    # --- 3. 댓글 삭제 ---
    client.delete(f"/posts/comments/{comment_id}", headers=user2_headers)
    res_post = client.get(f"/posts/{post_id}")
    assert len(res_post.json()["comments"]) == 0, "댓글 삭제 실패"


def test_post_and_comment_like_unlike(
    authenticated_client: dict, authenticated_client_2: dict
):
    """게시글과 댓글의 '좋아요' 및 '좋아요 취소' 기능을 테스트합니다."""
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # 게시글 및 댓글 생성
    post_res = client.post(
        "/posts/",
        json={"type": "question", "tag": "ps", "title": "Post for likes"},
        headers=user1_headers,
    )
    post_id = post_res.json()["id"]
    comment_res = client.post(
        f"/posts/{post_id}/comments",
        json={"post_id": post_id, "content": "Comment for likes"},
        headers=user2_headers,
    )
    comment_id = comment_res.json()["id"]

    # --- 1. 게시글 좋아요/취소 ---
    client.post(f"/posts/{post_id}/like", headers=user2_headers)
    response = client.get(f"/posts/{post_id}")
    assert response.json()["likes_count"] == 1
    client.delete(f"/posts/{post_id}/like", headers=user2_headers)
    response = client.get(f"/posts/{post_id}")
    assert response.json()["likes_count"] == 0

    # --- 2. 댓글 좋아요/취소 ---
    client.post(f"/posts/comments/{comment_id}/like", headers=user1_headers)
    response = client.get(f"/posts/{post_id}")
    assert response.json()["comments"][0]["likes_count"] == 1
    client.delete(f"/posts/comments/{comment_id}/like", headers=user1_headers)
    response = client.get(f"/posts/{post_id}")
    assert response.json()["comments"][0]["likes_count"] == 0


def test_post_list_and_filter_scenario(
    authenticated_client: dict, authenticated_client_2: dict
):
    """
    게시글 목록 조회 및 `type`, `tag` 필터링 기능을 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # --- 1. 테스트용 게시글 3개 생성 ---
    client.post(
        "/posts/",
        json={"type": "question", "tag": "ps", "title": "PS Question"},
        headers=user1_headers,
    )
    client.post(
        "/posts/",
        json={"type": "share", "tag": "img", "title": "Image Share"},
        headers=user2_headers,
    )
    client.post(
        "/posts/",
        json={"type": "share", "tag": "ps", "title": "PS Share"},
        headers=user1_headers,
    )

    # --- 2. 목록 조회 및 필터링 테스트 ---
    response = client.get("/posts/")
    assert response.status_code == 200
    assert len(response.json()) >= 3

    response = client.get("/posts/?types=question")
    assert all(p["type"] == "question" for p in response.json())

    response = client.get("/posts/?tags=ps")
    assert all(p["tag"] == "ps" for p in response.json())

    response = client.get("/posts/?types=share&tags=img")
    assert all(p["type"] == "share" and p["tag"] == "img" for p in response.json())


def test_post_authorization_and_failure_cases(
    authenticated_client: dict, authenticated_client_2: dict
):
    """
    게시글 기능의 권한 및 실패 케이스를 테스트합니다.
    - 다른 사용자의 게시글 수정/삭제 시도
    - 중복 '좋아요' 시도
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # --- 사용자 1이 게시글 생성 ---
    post_data = {
        "type": "question",
        "tag": "ps",
        "title": "User 1's Post",
        "content": "Help me!",
    }
    response = client.post("/posts/", json=post_data, headers=user1_headers)
    assert response.status_code == 201
    post_id = response.json()["id"]

    # --- 사용자 2가 수정/삭제 시도 (404 Not Found 예상) ---
    response = client.put(
        f"/posts/{post_id}", json={"title": "Updated by User 2"}, headers=user2_headers
    )
    assert response.status_code == 404
    response = client.delete(f"/posts/{post_id}", headers=user2_headers)
    assert response.status_code == 404

    # --- 중복 '좋아요' 시도 (409 Conflict 예상) ---
    client.post(f"/posts/{post_id}/like", headers=user1_headers)
    response = client.post(f"/posts/{post_id}/like", headers=user1_headers)
    assert response.status_code == 409


def test_admin_can_manage_other_users_post(
    authenticated_client: dict, authenticated_admin_client: dict
):
    """
    관리자가 다른 사용자의 게시글을 관리(수정, 삭제)할 수 있는지 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user_headers = authenticated_client["headers"]
    admin_headers = authenticated_admin_client["headers"]

    # --- 일반 사용자가 게시글 생성 ---
    post_data = {
        "type": "question",
        "tag": "ps",
        "title": "A User's Post for Admin Test",
        "content": "Content",
    }
    response = client.post("/posts/", json=post_data, headers=user_headers)
    assert response.status_code == 201
    post_id = response.json()["id"]

    # --- 관리자가 해당 게시글을 수정 (200 OK 예상) ---
    response = client.put(
        f"/posts/{post_id}", json={"title": "Updated by Admin"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated by Admin"

    # --- 관리자가 해당 게시글을 삭제 (204 No Content 예상) ---
    response = client.delete(f"/posts/{post_id}", headers=admin_headers)
    assert response.status_code == 204

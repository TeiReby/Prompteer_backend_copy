# tests/test_challenge_scenario.py
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.relations import PSShare, Share


def create_test_file(
    tmp_path: Path, filename: str, content: bytes = b"test content"
) -> Path:
    """테스트용 임시 파일을 생성하고 경로를 반환하는 헬퍼 함수."""
    file_path = tmp_path / filename
    file_path.write_bytes(content)
    return file_path


def test_ps_challenge_lifecycle(authenticated_client: dict):
    """PS Challenge의 생성, 조회, 수정, 삭제 라이프사이클을 테스트합니다."""
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    # --- 1. 챌린지 생성 ---
    challenge_data = {
        "tag": "ps",
        "level": "Medium",
        "title": "두 수의 합",
        "content": "정수 배열 `nums`와 정수 `target`이 주어졌을 때...",
        "challenge_number": 1001,
        "testcases": [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]"}
        ],
    }
    response = client.post("/challenges/ps", json=challenge_data, headers=headers)
    assert response.status_code == 201, "챌린지 생성 실패"
    challenge_id = response.json()["id"]

    # --- 2. 챌린지 상세 조회 ---
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == challenge_data["title"]

    # --- 3. 챌린지 내용 수정 ---
    update_data = {"title": "Updated Two Sum Title"}
    response = client.put(
        f"/challenges/{challenge_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200, "챌린지 수정 실패"
    assert response.json()["title"] == update_data["title"]

    # --- 4. 챌린지 삭제 ---
    response = client.delete(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 204, "챌린지 삭제 실패"
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 404, "삭제된 챌린지가 조회되어서는 안 됨"


def test_ps_testcase_lifecycle(authenticated_client: dict):
    """PS Challenge의 Testcase 추가, 수정, 삭제 라이프사이클을 테스트합니다."""
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    # 챌린지 생성
    challenge_res = client.post(
        "/challenges/ps",
        json={
            "tag": "ps",
            "level": "Easy",
            "title": "TC Test",
            "challenge_number": 1002,
            "testcases": [],
        },
        headers=headers,
    )
    challenge_id = challenge_res.json()["id"]

    # --- 1. 테스트케이스 추가 ---
    new_tc_data = {"input": "1", "output": "1"}
    response = client.post(
        f"/challenges/ps/{challenge_id}/testcases", json=new_tc_data, headers=headers
    )
    assert response.status_code == 201, "테스트케이스 추가 실패"
    tc_id = response.json()["id"]

    # --- 2. 테스트케이스 수정 ---
    updated_tc_data = {"output": "one"}
    response = client.put(
        f"/challenges/ps/{challenge_id}/testcases/{tc_id}",
        json=updated_tc_data,
        headers=headers,
    )
    assert response.status_code == 200, "테스트케이스 수정 실패"
    assert response.json()["output"] == updated_tc_data["output"]

    # --- 3. 테스트케이스 삭제 ---
    response = client.delete(
        f"/challenges/ps/{challenge_id}/testcases/{tc_id}", headers=headers
    )
    assert response.status_code == 204, "테스트케이스 삭제 실패"


def test_img_challenge_lifecycle_scenario(authenticated_client: dict, tmp_path: Path):
    """
    Image Challenge의 전체 생명주기(파일 업로드 포함 생성, 조회, 수정, 삭제)를 테��트하는 시나리오.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]
    test_file = create_test_file(tmp_path, "test_image.png")

    challenge_data = {
        "level": "Easy",
        "title": "Aesthetic Image",
        "content": "Generate an aesthetic image.",
        "challenge_number": 1003,
    }
    files = {"references": (test_file.name, test_file.open("rb"), "image/png")}
    response = client.post(
        "/challenges/img", data=challenge_data, files=files, headers=headers
    )
    assert response.status_code == 201, "이미지 챌린지 생성 실패"
    challenge = response.json()
    challenge_id = challenge["id"]
    assert challenge["title"] == challenge_data["title"]
    assert len(challenge["img_challenge"]["references"]) == 1

    # --- 2. 챌린지 조회 ---
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["tag"] == "img"

    # --- 3. 챌린지 수정 ---
    update_data = {"title": "Updated Aesthetic Image"}
    response = client.put(
        f"/challenges/{challenge_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == update_data["title"]

    # --- 4. 챌린지 삭제 ---
    response = client.delete(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 204
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 404


def test_video_challenge_lifecycle_scenario(
    authenticated_client: dict, tmp_path: Path
):
    """
    Video Challenge의 전체 생명주기(파일 업로드 포함 생성, 조회, 수정, 삭제)를 테스트하는 시나리오.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]
    test_file = create_test_file(tmp_path, "test_video.mp4")

    challenge_data = {
        "level": "Hard",
        "title": "Cool Video",
        "content": "Create a cool video.",
        "challenge_number": 1004,
    }
    files = {"references": (test_file.name, test_file.open("rb"), "video/mp4")}
    response = client.post(
        "/challenges/video", data=challenge_data, files=files, headers=headers
    )
    assert response.status_code == 201, "비디오 챌린지 생성 실패"
    challenge = response.json()
    challenge_id = challenge["id"]
    assert challenge["title"] == challenge_data["title"]
    assert len(challenge["video_challenge"]["references"]) == 1

    # --- 2. 챌린지 조회 ---
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["tag"] == "video"

    # --- 3. 챌린지 수정 ---
    update_data = {"title": "Updated Cool Video"}
    response = client.put(
        f"/challenges/{challenge_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == update_data["title"]

    # --- 4. 챌린지 삭제 ---
    response = client.delete(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 204
    response = client.get(f"/challenges/{challenge_id}", headers=headers)
    assert response.status_code == 404


def test_challenge_list_and_filter_scenario(
    authenticated_client: dict, authenticated_client_2: dict, tmp_path: Path
):
    """
    챌린지 목록 조회 및 타입별 필터링 기능을 테스트하는 시나리오.
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # --- 1. 테스트용 챌린지 3개 생성 (서로 다른 유저, 다른 태그) ---
    ps_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "PS List Test",
        "challenge_number": 1005,
        "testcases": [],
    }
    client.post("/challenges/ps", json=ps_data, headers=user1_headers)

    img_data = {"level": "Easy", "title": "Img List Test", "challenge_number": 1006}
    img_file = create_test_file(tmp_path, "list_test.png")
    client.post(
        "/challenges/img",
        data=img_data,
        files={"references": (img_file.name, img_file.open("rb"), "image/png")},
        headers=user2_headers,
    )

    video_data = {
        "level": "Medium",
        "title": "Video List Test",
        "challenge_number": 1007,
    }
    video_file = create_test_file(tmp_path, "list_test.mp4")
    client.post(
        "/challenges/video",
        data=video_data,
        files={"references": (video_file.name, video_file.open("rb"), "video/mp4")},
        headers=user1_headers,
    )

    # --- 2. 타입별 목록 조회 검증 ---
    response_ps = client.get("/challenges/ps/", headers=user1_headers)
    assert response_ps.status_code == 200
    assert len(response_ps.json()) >= 1
    assert all(c["tag"] == "ps" for c in response_ps.json())

    response_img = client.get("/challenges/img/", headers=user1_headers)
    assert response_img.status_code == 200
    assert len(response_img.json()) >= 1
    assert all(c["tag"] == "img" for c in response_img.json())

    response_video = client.get("/challenges/video/", headers=user1_headers)
    assert response_video.status_code == 200
    assert len(response_video.json()) >= 1
    assert all(c["tag"] == "video" for c in response_video.json())


def test_score_code_scenario(authenticated_client: dict):
    """
    코드 채점 엔드포인트의 다양한 시나리오(정답, 오답, 에러)를 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]
    # 채점용 챌린지 생성
    challenge_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "입력값 그대로 출력",
        "content": "입력으로 주어진 문자열을 그대로 출력하세요.",
        "challenge_number": 1008,
        "testcases": [{"input": "Hello, World!", "output": "Hello, World!"}],
    }
    response = client.post("/challenges/ps", json=challenge_data, headers=headers)
    challenge_id = response.json()["id"]

    # --- 다양한 코드 제출 및 결과 확인 ---
    codes = {
        "correct": "import sys\nprint(sys.stdin.read())",
        "wrong": "print('Wrong Answer')",
        "error": "import sys\nprint(sys.stdin.read(",  # Syntax Error
    }

    # 1. 정답 코드
    response = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": codes["correct"]},
        headers=headers,
    )
    assert response.json()[0]["status"] == "Accepted"

    # 2. 오답 코드
    response = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": codes["wrong"]},
        headers=headers,
    )
    assert response.json()[0]["status"] == "Wrong Answer"

    # 3. 에러 발생 코드
    response = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": codes["error"]},
        headers=headers,
    )
    assert response.json()[0]["status"] in ["Compilation Error", "Runtime Error"]

    # --- 테스트 종료 후 챌린지 삭제 ---
    client.delete(f"/challenges/{challenge_id}", headers=headers)


def test_challenge_authorization_failures(
    authenticated_client: dict, authenticated_client_2: dict
):
    """
    챌린지 기능의 권한 실패 케이스를 테스트합니다.
    - 다른 사용자가 생성한 챌린지를 수정/삭제할 수 없는지 확인합니다.
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # --- 사용자 1이 챌린지 생성 ---
    challenge_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "User 1's Challenge",
        "content": "Content",
        "challenge_number": 1009,
        "testcases": [{"input": "1", "output": "1"}],
    }
    response = client.post("/challenges/ps", json=challenge_data, headers=user1_headers)
    assert response.status_code == 201
    challenge_id = response.json()["id"]

    # --- 사용자 2가 사용자 1의 챌린지를 수정/삭제하려고 시도 (404 Not Found 예상) ---
    update_data = {"title": "Attempt to Update by User 2"}
    response = client.put(
        f"/challenges/{challenge_id}", json=update_data, headers=user2_headers
    )
    assert response.status_code == 404

    response = client.delete(f"/challenges/{challenge_id}", headers=user2_headers)
    assert response.status_code == 404


def test_admin_can_manage_other_users_challenge(
    authenticated_client: dict, authenticated_admin_client: dict
):
    """
    관리자가 다른 사용자의 챌린지를 관리(삭제)할 수 있는지 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user_headers = authenticated_client["headers"]
    admin_headers = authenticated_admin_client["headers"]

    # --- 일반 사용자가 챌린지 생성 ---
    challenge_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "User's Challenge for Admin Test",
        "content": "Content",
        "challenge_number": 1010,
        "testcases": [{"input": "1", "output": "1"}],
    }
    response = client.post("/challenges/ps", json=challenge_data, headers=user_headers)
    assert response.status_code == 201
    challenge_id = response.json()["id"]

    # --- 관리자가 해당 챌린지를 삭제 (204 No Content 예상) ---
    response = client.delete(f"/challenges/{challenge_id}", headers=admin_headers)
    assert response.status_code == 204


def test_img_challenge_reference_management_scenario(
    authenticated_client: dict, tmp_path: Path
):
    """
    이미지 챌린지의 참고자료(Reference) 관리(추가, 조회, 수정, 삭제)를 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    img_challenge_data = {
        "level": "Easy",
        "title": "Image Ref Test",
        "challenge_number": 1011,
    }
    img_file = create_test_file(tmp_path, "image.png")
    files = {"references": (img_file.name, img_file.open("rb"), "image/png")}
    res = client.post(
        "/challenges/img", data=img_challenge_data, files=files, headers=headers
    )
    challenge_id = res.json()["id"]
    initial_ref_id = res.json()["img_challenge"]["references"][0]["id"]

    # --- 2. 참고자료(Reference) 개별 조회 테스트 ---
    response = client.get(
        f"/challenges/img/{challenge_id}/references/{initial_ref_id}"
    )
    assert response.status_code == 200, "특정 참고자료 조회 실패"

    # --- 3. 참고자료 추가, 수정, 삭제 테스트 ---
    # 추가 (참고: 이 엔드포인트는 파일 경로를 JSON으로 받음)
    new_ref_data = {
        "file_path": "/media/challenges/img_references/new.png",
        "file_type": "image/png",
    }
    res_add = client.post(
        f"/challenges/img/{challenge_id}/references", json=new_ref_data, headers=headers
    )
    assert res_add.status_code == 201, "참고자료 추가 실패"
    added_ref_id = res_add.json()["id"]

    # 수정
    update_ref_data = {"file_path": "/media/challenges/img_references/updated.png"}
    res_update = client.put(
        f"/challenges/img/{challenge_id}/references/{added_ref_id}",
        json=update_ref_data,
        headers=headers,
    )
    assert res_update.status_code == 200, "참고자료 수정 실패"

    # 삭제
    res_delete = client.delete(
        f"/challenges/img/{challenge_id}/references/{added_ref_id}", headers=headers
    )
    assert res_delete.status_code == 204, "참고자료 삭제 실패"


def test_video_challenge_reference_management_scenario(
    authenticated_client: dict, tmp_path: Path
):
    """
    비디오 챌린지의 참고자료(Reference) 관리(추가, 조회, 수정, 삭제)를 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    # --- 1. 테스트용 비디오 챌린지 생성 ---
    video_challenge_data = {
        "level": "Medium",
        "title": "Video Ref Test",
        "challenge_number": 1012,
    }
    video_file = create_test_file(tmp_path, "video.mp4")
    files = {"references": (video_file.name, video_file.open("rb"), "video/mp4")}
    res = client.post(
        "/challenges/video", data=video_challenge_data, files=files, headers=headers
    )
    assert res.status_code == 201, "비디오 챌린지 생성 실패"
    challenge_id = res.json()["id"]
    initial_ref_id = res.json()["video_challenge"]["references"][0]["id"]

    # --- 2. 참고자료(Reference) 개별 조회 테스트 ---
    response = client.get(
        f"/challenges/video/{challenge_id}/references/{initial_ref_id}"
    )
    assert response.status_code == 200, "특정 비디오 참고자료 조회 실패"

    # --- 3. 참고자료 추가, 수정, 삭제 테스트 ---
    # 추가
    new_ref_data = {
        "file_path": "/media/challenges/video_references/new.mp4",
        "file_type": "video/mp4",
    }
    res_add = client.post(
        f"/challenges/video/{challenge_id}/references",
        json=new_ref_data,
        headers=headers,
    )
    assert res_add.status_code == 201, "비디오 참고자료 추가 실패"
    added_ref_id = res_add.json()["id"]

    # 수정
    update_ref_data = {"file_path": "/media/challenges/video_references/updated.mp4"}
    res_update = client.put(
        f"/challenges/video/{challenge_id}/references/{added_ref_id}",
        json=update_ref_data,
        headers=headers,
    )
    assert res_update.status_code == 200, "비디오 참고자료 수정 실패"

    # 삭제
    res_delete = client.delete(
        f"/challenges/video/{challenge_id}/references/{added_ref_id}", headers=headers
    )
    assert res_delete.status_code == 204, "비디오 참고자료 삭제 실패"


@pytest.mark.gemini_api
def test_gemini_generation_endpoints(
    authenticated_client: dict, tmp_path: Path, gemini_api_mocker: str
):
    """
    Gemini AI를 이용한 코드, 이미지, 비디오 생성 엔드포인트를 테스트합니다.
    `--run-gemini-api` 옵션에 따라 모킹 또는 실제 API 호출 모드로 실행됩니다.
    """
    client: TestClient = authenticated_client["client"]
    headers = authenticated_client["headers"]

    # --- 1. 테스트용 챌린지 생성 ---
    ps_challenge_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "PS Gen Test",
        "challenge_number": 1013,
        "testcases": [],
    }
    ps_res = client.post("/challenges/ps", json=ps_challenge_data, headers=headers)
    ps_challenge_id = ps_res.json()["id"]

    img_challenge_data = {
        "level": "Easy",
        "title": "Img Gen Test",
        "challenge_number": 1014,
    }
    img_file = create_test_file(tmp_path, "gen_test.png")
    img_res = client.post(
        "/challenges/img",
        data=img_challenge_data,
        files={"references": (img_file.name, img_file.open("rb"), "image/png")},
        headers=headers,
    )
    img_challenge_id = img_res.json()["id"]

    video_challenge_data = {
        "level": "Easy",
        "title": "Video Gen Test",
        "challenge_number": 1015,
    }
    video_file = create_test_file(tmp_path, "gen_test.mp4")
    video_res = client.post(
        "/challenges/video",
        data=video_challenge_data,
        files={"references": (video_file.name, video_file.open("rb"), "video/mp4")},
        headers=headers,
    )
    video_challenge_id = video_res.json()["id"]

    # --- 2. 생성 엔드포인트 호출 및 검증 ---
    # 코드 생성
    response_code = client.post(
        f"/challenges/ps/{ps_challenge_id}/generate",
        json={"prompt": "a function that returns 'hello world' in python"},
        headers=headers,
    )
    assert response_code.status_code == 200
    if gemini_api_mocker == "mocked":
        assert response_code.json()["content"] == "mocked_code"
    else:
        assert isinstance(response_code.json()["content"], str)
        assert len(response_code.json()["content"]) > 0

    # 이미지 생성
    response_img = client.post(
        f"/challenges/img/{img_challenge_id}/generate",
        json={"prompt": "a cute cat"},
        headers=headers,
    )
    assert response_img.status_code == 200
    if gemini_api_mocker == "mocked":
        assert response_img.json() == "mocked/path.png"
    else:
        # settings.MEDIA_ROOT가 임시 경로이므로, 전체 경로가 아닌 상대 경로 부분만 확인합니다.
        relative_path = os.path.join("shares", "img_shares")
        assert relative_path in response_img.json()
        assert response_img.json().endswith(".png")

    # 비디오 생성
    response_video = client.post(
        f"/challenges/video/{video_challenge_id}/generate",
        json={"prompt": "a running dog"},
        headers=headers,
    )
    assert response_video.status_code == 200
    if gemini_api_mocker == "mocked":
        assert response_video.json() == "mocked/path.mp4"
    else:
        relative_path = os.path.join("shares", "video_shares")
        assert relative_path in response_video.json()
        assert response_video.json().endswith(".mp4")


def test_ps_challenge_scoring_and_accuracy(
    db_session: Session, authenticated_client: dict, authenticated_client_2: dict
):
    """
    PS 챌린지 채점, is_correct/is_public 필드 설정, 정답률 계산의 전체 시나리오를 테스트합니다.
    """
    client: TestClient = authenticated_client["client"]
    user1_headers = authenticated_client["headers"]
    user2_headers = authenticated_client_2["headers"]

    # --- 1. 테스트용 챌린지 생성 ---
    challenge_data = {
        "tag": "ps",
        "level": "Easy",
        "title": "Accuracy Test Challenge",
        "content": "입력 문자열 'test'를 출력하세요.",
        "challenge_number": 1016,
        "testcases": [{"input": "ignored", "output": "test"}],
    }
    response = client.post("/challenges/ps", json=challenge_data, headers=user1_headers)
    assert response.status_code == 201
    challenge_id = response.json()["id"]

    correct_code = "print('test')"
    wrong_code = "print('wrong')"

    # --- 2. 사용자 1, 정답 제출 ---
    res_score1 = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": correct_code},
        headers=user1_headers,
    )
    assert res_score1.status_code == 200
    assert res_score1.json()[0]["status"] == "Accepted"

    # DB에서 직접 확인
    share1 = db_session.exec(select(Share).order_by(Share.id.desc())).first()
    assert share1 is not None
    assert share1.is_public is True
    assert share1.ps_share is not None
    assert share1.ps_share.is_correct is True

    # 정답률 확인 (1/1 = 1.0)
    res_read1 = client.get(f"/challenges/{challenge_id}")
    assert res_read1.status_code == 200
    assert res_read1.json()["ps_challenge"]["accuracy_rate"] == 1.0

    # --- 3. 사용자 2, 오답 제출 ---
    res_score2 = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": wrong_code},
        headers=user2_headers,
    )
    assert res_score2.status_code == 200
    assert res_score2.json()[0]["status"] == "Wrong Answer"

    # DB에서 직접 확인
    share2 = db_session.exec(select(Share).order_by(Share.id.desc())).first()
    assert share2 is not None
    assert share2.is_public is False
    assert share2.ps_share is not None
    assert share2.ps_share.is_correct is False

    # 정답률 확인 (1/2 = 0.5)
    res_read2 = client.get(f"/challenges/{challenge_id}")
    assert res_read2.status_code == 200
    assert res_read2.json()["ps_challenge"]["accuracy_rate"] == 0.5

    # --- 4. 사용자 1, 오답 제출 (정답률 변화 없어야 함) ---
    client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": wrong_code},
        headers=user1_headers,
    )
    res_read3 = client.get(f"/challenges/{challenge_id}")
    assert res_read3.status_code == 200
    assert res_read3.json()["ps_challenge"]["accuracy_rate"] == 0.5

    # --- 5. 사용자 2, 정답 제출 ---
    res_score3 = client.post(
        f"/challenges/ps/{challenge_id}/score",
        json={"code": correct_code},
        headers=user2_headers,
    )
    assert res_score3.status_code == 200
    assert res_score3.json()[0]["status"] == "Accepted"

    # DB에서 직접 확인
    share3 = db_session.exec(select(Share).order_by(Share.id.desc())).first()
    assert share3 is not None
    assert share3.is_public is True
    assert share3.ps_share is not None
    assert share3.ps_share.is_correct is True

    # 정답률 확인 (2/2 = 1.0)
    res_read4 = client.get(f"/challenges/{challenge_id}")
    assert res_read4.status_code == 200
    assert res_read4.json()["ps_challenge"]["accuracy_rate"] == 1.0

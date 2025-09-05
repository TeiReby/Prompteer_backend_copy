# tests/test_edge_cases.py
import pytest
from fastapi.testclient import TestClient

# 테스트할 엔드포인트 목록
ENDPOINTS_TO_TEST = [
    "/challenges/ps/",
    "/challenges/img/",
    "/challenges/video/",
    "/posts/",
    "/shares/ps/",
    "/shares/img/",
    "/shares/video/",
]

# 테스트할 쿼리 파라미터와 값
INVALID_QUERY_PARAMS = [
    ("skip", -1),
    ("limit", -1),
    ("limit", 200),  # 일반적으로 API는 최대 limit 값을 제한하는 것이 좋음
]


def test_read_root(client: TestClient):
    """루트 엔드포인트('/')가 정상적으로 응답하는지 테스트합니다."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Prompteer!"}


@pytest.mark.parametrize("endpoint", ENDPOINTS_TO_TEST)
@pytest.mark.parametrize("param, value", INVALID_QUERY_PARAMS)
def test_invalid_pagination_params(client: TestClient, endpoint, param, value):
    """
    목록 조회 엔드포인트에 유효하지 않은 페이지네이션 파라미터(skip, limit)를
    전달했을 때, FastAPI가 422 Unprocessable Entity 에러를 반환하는지 테스트합니다.
    """
    response = client.get(f"{endpoint}?{param}={value}")
    # FastAPI는 음수값이나 모델에 정의된 제약(예: ge=0)을 위반하는 경우
    # 자동으로 422 에러를 반환합니다.
    assert response.status_code == 422, f"Expected 422 for {endpoint}?{param}={value}"


def test_post_invalid_enum_query_params(client: TestClient):
    """
    Post 목록 조회 시 유효하지 않은 Enum 값을 쿼리 파라미터로 전달했을 때
    422 에러가 발생하는지 테스트합니다.
    """
    response = client.get("/posts/?tags=invalid_tag")
    assert response.status_code == 422
    assert "Input should be 'ps', 'img' or 'video'" in response.text

    response = client.get("/posts/?types=invalid_type")
    assert response.status_code == 422
    assert "Input should be 'question' or 'share'" in response.text

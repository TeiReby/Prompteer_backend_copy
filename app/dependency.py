# app/dependency.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.database import engine
from app.core.security import verify_token
from app.crud import user as crud_user
from app.models.relations import User

# =================================================================
# Database Dependency
# =================================================================


def get_db():
    """
    FastAPI 의존성(Dependency)으로, 각 API 요청마다 데이터베이스 세션을 제공합니다.

    - `with Session(engine)`: 요청이 시작될 때 새로운 DB 세션을 생성합니다.
    - `yield session`: 생성된 세션을 API 엔드포인트 함수에 주입합니다.
    - `with` 블록이 끝나면(요청 처리가 완료되면) 세션은 자동으로 닫힙니다.
      이를 통해 세션 관리를 자동화하고 리소스 누수를 방지합니다.
    """
    with Session(engine) as session:
        yield session


# =================================================================
# Authentication Dependencies
# =================================================================

# OAuth2PasswordBearer는 API 요청의 Authorization 헤더에서 Bearer 토큰을
# 추출하는 의존성을 생성합니다.
# `tokenUrl`은 클라이언트가 토큰을 얻기 위해 요청해야 하는 API 경로를 명시합니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    JWT 토큰을 검증하고 현재 로그인된 사용자 객체를 반환하는 의존성 함수.

    이 함수를 엔드포인트에 `Depends()`와 함께 주입하면, 해당 엔드포인트는
    요청의 `Authorization` 헤더에 유효한 Bearer 토큰이 포함되어야만 접근할 수 있습니다.

    Args:
        token: `oauth2_scheme`에 의해 HTTP 헤더에서 추출된 JWT 토큰.
        db: `get_db` 의존성에 의해 제공되는 데이터베이스 세션.

    Returns:
        인증된 사용자의 User 모델 객체.

    Raises:
        HTTPException:
            - 401 Unauthorized: 토큰이 유효하지 않거나 페이로드에 주체(sub)가 없는 경우.
            - 404 Not Found: 토큰은 유효하지만 해당 사용자가 DB에 존재하지 않는 경우.
    """
    # 1. 토큰의 유효성을 검증하고 페이로드(payload)를 추출합니다.
    #    - `verify_token` 함수는 토큰 만료, 서명 오류 등을 감지하여 예외를 발생시킵니다.
    payload = verify_token(token)

    # 2. 페이로드에서 주체(subject), 즉 사용자 ID를 추출합니다.
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials, malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 추출한 사용자 ID를 정수형으로 변환합니다.
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. 사용자 ID를 사용하여 데이터베이스에서 사용자 정보를 조회합니다.
    # 여기다가 비활성화 로직 추가함(2025.08.23)
    user = crud_user.get_user(db, user_id=user_id)
    if user is None or not user.is_active:
        # 토큰이 유효하더라도 해당 사용자가 DB에서 삭제되었거나 비활성화 상태일 수 있습니다.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# =================================================================
# Ownership Verification Dependencies
# =================================================================













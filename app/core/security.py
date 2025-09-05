# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


def create_access_token(subject: Union[str, Any]) -> str:
    """
    주어진 주체(subject)를 기반으로 JWT 액세스 토큰을 생성합니다.

    Args:
        subject: 토큰의 주체가 될 데이터. 보통 사용자의 고유 ID가 사용됩니다.

    Returns:
        생성된 JWT 액세스 토큰 문자열.
    """
    # 토큰 만료 시간을 현재 UTC 시간 기준으로 설정합니다.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    # JWT 페이로드(payload)를 구성합니다. 'exp'는 만료 시간, 'sub'는 주체(subject)를 나타냅니다.
    to_encode = {"exp": expire, "sub": str(subject)}
    # 구성된 페이로드를 비밀 키와 지정된 알고리즘을 사용하여 인코딩합니다.
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    JWT 토큰을 검증하고 페이로드(payload)를 반환합니다.

    Args:
        token: 검증할 JWT 토큰 문자열.

    Returns:
        토큰이 유효한 경우, 디코딩된 페이로드(dict).

    Raises:
        HTTPException:
            - 401 Unauthorized: 토큰이 만료되었거나, 유효하지 않은 경우.
    """
    try:
        # 토큰을 비밀 키와 알고리즘을 사용하여 디코딩하고, 유효성을 검증합니다.
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # 토큰의 유효 기간이 만료된 경우 예외 처리
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        # 토큰의 서명이 유효하지 않거나 형식이 잘못된 경우 예외 처리
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

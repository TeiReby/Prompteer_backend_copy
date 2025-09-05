# app/models/token.py
from sqlmodel import SQLModel


class Token(SQLModel):
    """
    JWT(JSON Web Token) 인증에 사용되는 액세스 토큰 정보를 정의하는 모델.

    사용자 로그인 시 이 형식으로 토큰이 발급됩니다.
    """

    access_token: str
    token_type: str

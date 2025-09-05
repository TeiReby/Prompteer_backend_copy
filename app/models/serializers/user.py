# app/models/serializers/user.py
from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel

from app.models.relations.user import Interests, ProfileBase, UserBase


# =================================================================
# User
# =================================================================
class UserCreate(UserBase):
    """사용자 생성을 위한 데이터 모델 (입력)."""

    password: str


class UserUpdate(SQLModel):
    """사용자 정보 수정을 위한 데이터 모델 (입력)."""

    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserRead(UserBase):
    """기본 사용자 정보 조회를 위한 데이터 모델 (출력)."""

    id: int


class UserReadWithProfile(UserRead):
    """프로필을 포함한 상세 사용자 정보 조회를 위한 데이터 모델 (출력)."""

    profile: Optional["ProfileRead"] = None


# =================================================================
# Profile
# =================================================================
class ProfileUpdate(SQLModel):
    """프로필 수정을 위한 데이터 모델 (입력)."""

    introduction: Optional[str] = None
    interested_in: Optional[Interests] = None


class ProfileRead(ProfileBase):
    """프로필 조회를 위한 데이터 모델 (출력)."""

    user_id: int
    modified_at: datetime


class UserPasswordCheck(SQLModel):
    """사용자 비밀번호 확인을 위한 데이터 모델 (입력)."""

    password: str
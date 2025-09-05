# app/models/relations/user.py
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import JSON, Column, TypeDecorator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.relations.challenge import Challenge
    from app.models.relations.post import Comment, Post, UserLikesComment, UserLikesPost
    from app.models.relations.share import Share, UserLikesShare


# =================================================================
# Helper Models & Types for User Profile
# =================================================================
class Interests(BaseModel):
    """
    사용자의 관심분야를 구조화하기 위한 Pydantic 모델.
    Profile 모델의 JSON 필드에 저장됩니다.
    """

    backend_developer: bool = Field(default=False, description="백엔드 개발자")
    frontend_developer: bool = Field(default=False, description="프론트엔드 개발자")
    ui_ux_designer: bool = Field(default=False, description="UI/UX 디자이너")
    prompt_engineer: bool = Field(default=False, description="프롬프트 엔지니어")
    planner_pm: bool = Field(default=False, description="기획/PM")
    ps: bool = Field(default=False, description="PS (Problem Solving)")
    etc: bool = Field(default=False, description="기타")


class InterestsType(TypeDecorator):
    """
    SQLAlchemy가 `Interests` Pydantic 모델을 데이터베이스의 JSON 타입과
    상호작용할 수 있도록 하는 커스텀 타입 데코레이터.

    - `process_bind_param`: Python 객체(Interests)를 DB에 저장될 JSON 형식으로 변환합니다.
    - `process_result_value`: DB에서 읽어온 JSON을 Python 객체(Interests)로 변환합니다.
    """

    impl = JSON

    def process_bind_param(
        self, value: Optional[Interests | dict], dialect: Any
    ) -> Optional[dict]:
        if isinstance(value, Interests):
            return value.model_dump()
        if isinstance(value, dict):
            return value
        return None

    def process_result_value(
        self, value: Optional[dict], dialect: Any
    ) -> Optional[Interests]:
        if value is not None:
            return Interests.model_validate(value)
        return None


# =================================================================
# User
# =================================================================
class UserBase(SQLModel):
    """사용자 정보의 공통 필드를 정의하는 기본 모델."""

    nickname: str = Field(
        max_length=50, unique=True, index=True, nullable=False, description="사용자 닉네임 (고유)"
    )
    email: EmailStr = Field(
        max_length=100, unique=True, index=True, nullable=False, description="사용자 이메일 (고유)"
    )
    is_admin: bool = Field(default=False, nullable=False, description="관리자 권한 여부")
    is_active: bool = Field(default=True, nullable=False, description="활성 사용자 여부")


class User(UserBase, table=True):
    """
    사용자 계정 정보를 나타내는 데이터베이스 테이블 모델.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    # TODO: 프로덕션 환경에서는 반드시 비밀번호를 해싱하여 저장해야 합니다.
    password: str = Field(max_length=255, nullable=False, description="사용자 비밀번호 (해싱 필요)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="계정 생성 시각 (UTC)",
    )
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        description="마지막 수정 시각 (UTC)",
    )

    # --- Relationships ---
    # User 모델과 다른 모델 간의 관계를 정의합니다.
    # `back_populates`는 양방향 관계를 설정하며,
    # `sa_relationship_kwargs`는 SQLAlchemy 레벨의 옵션(예: cascade)을 지정합니다.
    profile: Optional["Profile"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    challenges: List["Challenge"] = Relationship(back_populates="user")
    shares: List["Share"] = Relationship(back_populates="user")
    posts: List["Post"] = Relationship(back_populates="user")
    comments: List["Comment"] = Relationship(back_populates="user")
    liked_shares: List["UserLikesShare"] = Relationship(back_populates="user")
    liked_posts: List["UserLikesPost"] = Relationship(back_populates="user")
    liked_comments: List["UserLikesComment"] = Relationship(back_populates="user")


# =================================================================
# Profile
# =================================================================
class ProfileBase(SQLModel):
    """프로필 정보의 공통 필드를 정의하는 기본 모델."""

    introduction: Optional[str] = Field(
        default=None, max_length=255, description="자기소개"
    )
    interested_in: Optional[Interests] = Field(
        default_factory=Interests,
        sa_column=Column(InterestsType),
        description="관심분야 (JSON으로 저장)",
    )


class Profile(ProfileBase, table=True):
    """
    사용자 프로필 정보를 나타내는 데이터베이스 테이블 모델.
    User 모델과 일대일(one-to-one) 관계를 가집니다.
    """

    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,
        description="연결된 사용자의 ID (외래키, 기본키)",
    )
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        description="마지막 수정 시각 (UTC)",
    )

    # --- Relationships ---
    user: "User" = Relationship(back_populates="profile")

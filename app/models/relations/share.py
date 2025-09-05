# app/models/relations/share.py
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.relations.challenge import Challenge
    from app.models.relations.user import User


# =================================================================
# Share
# =================================================================
class ShareBase(SQLModel):
    """공유 모델의 공통 필드를 정의하는 기본 모델."""

    prompt: Optional[str] = Field(
        default=None, description="생성형 AI 사용 시 입력한 프롬프트"
    )
    is_public: bool = Field(default=True, description="공유 공개 여부")


class Share(ShareBase, table=True):
    """
    챌린지 결과물 공유 정보를 나타내는 메인 테이블 모델.
    연관된 챌린지의 종류에 따라 PS, Img, Video 공유 중 하나와
    일대일(one-to-one) 관계를 맺습니다.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: int = Field(
        foreign_key="challenge.id", nullable=False, description="연관된 챌린지 ID (외래키)"
    )
    user_id: int = Field(
        foreign_key="user.id", nullable=False, description="공유한 사용자 ID (외래키)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="공유 시각 (UTC)",
    )

    # --- Relationships ---
    challenge: "Challenge" = Relationship(back_populates="shares")
    user: "User" = Relationship(back_populates="shares")
    likes: List["UserLikesShare"] = Relationship(back_populates="share")
    ps_share: Optional["PSShare"] = Relationship(
        back_populates="share", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    img_share: Optional["ImgShare"] = Relationship(
        back_populates="share", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    video_share: Optional["VideoShare"] = Relationship(
        back_populates="share", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# =================================================================
# PS Share
# =================================================================
class PSShareBase(SQLModel):
    """PS 챌린지 공유 모델의 공통 필드를 정의하는 기본 모델."""

    code: Optional[str] = Field(default=None, description="제출 및 공유된 소스코드")
    is_correct: bool = Field(default=False, description="정답 여부")


class PSShare(PSShareBase, table=True):
    """PS 챌린지 결과물(코드)의 상세 정보를 나타내는 테이블 모델."""

    share_id: Optional[int] = Field(
        default=None,
        foreign_key="share.id",
        primary_key=True,
        description="연결된 공유 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    share: "Share" = Relationship(back_populates="ps_share")


# =================================================================
# Image Share
# =================================================================
class ImgShareBase(SQLModel):
    """이미지 챌린지 공유 모델의 공통 필드를 정의하는 기본 모델."""

    img_url: Optional[str] = Field(
        default=None, max_length=255, description="공유된 이미지의 URL 또는 파일 경로"
    )


class ImgShare(ImgShareBase, table=True):
    """이미지 챌린지 결과물(이미지 URL)의 상세 정보를 나타내는 테이블 모델."""

    share_id: Optional[int] = Field(
        default=None,
        foreign_key="share.id",
        primary_key=True,
        description="연결된 공유 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    share: "Share" = Relationship(back_populates="img_share")


# =================================================================
# Video Share
# =================================================================
class VideoShareBase(SQLModel):
    """비디오 챌린지 공유 모델의 공통 필드를 정의하는 기본 모델."""

    video_url: Optional[str] = Field(
        default=None, max_length=255, description="공유된 비디오의 URL 또는 파일 경로"
    )


class VideoShare(VideoShareBase, table=True):
    """비디오 챌린지 결과물(비디오 URL)의 상세 정보를 나타내는 테이블 모델."""

    share_id: Optional[int] = Field(
        default=None,
        foreign_key="share.id",
        primary_key=True,
        description="연결된 공유 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    share: "Share" = Relationship(back_populates="video_share")


# =================================================================
# Many-to-Many Link Model for Likes
# =================================================================
class UserLikesShareBase(SQLModel):
    """공유 좋아요 관계 모델의 기본 모델 (현재 추가 필드 없음)."""

    pass


class UserLikesShare(UserLikesShareBase, table=True):
    """
    사용자와 챌린지 공유 간의 '좋아요' 관계를 나타내는 다대다(many-to-many) 연결 테이블 모델.
    복합 기본키(share_id, user_id)를 사용합니다.
    """

    share_id: int = Field(
        foreign_key="share.id", primary_key=True, description="좋아요를 받은 챌린지 공유 ID"
    )
    user_id: int = Field(
        foreign_key="user.id", primary_key=True, description="좋아요를 누른 사용자 ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="좋아요를 누른 시각 (UTC)",
    )

    # --- Relationships ---
    user: "User" = Relationship(back_populates="liked_shares")
    share: "Share" = Relationship(back_populates="likes")

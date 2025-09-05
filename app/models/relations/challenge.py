# app/models/relations/challenge.py
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.relations.share import Share
    from app.models.relations.user import User
    from app.models.relations.post import Post


# =================================================================
# Enums
# =================================================================
class ChallengeTag(str, Enum):
    """챌린지의 유형을 나타내는 Enum."""

    ps = "ps"
    img = "img"
    video = "video"


class ChallengeLevel(str, Enum):
    """챌린지의 난이도를 나타내는 Enum."""

    easy = "Easy"
    medium = "Medium"
    hard = "Hard"


# =================================================================
# General Challenge
# =================================================================
class ChallengeBase(SQLModel):
    """챌린지 모델의 공통 필드를 정의하는 기본 모델."""

    tag: ChallengeTag = Field(nullable=False, description="챌린지 유형 태그 (ps, img, video)")
    level: ChallengeLevel = Field(nullable=False, description="난이도 (Easy, Medium, Hard)")
    title: str = Field(max_length=100, nullable=False, description="챌린지 제목")
    content: Optional[str] = Field(
        default=None, description="챌린지 설명 (Markdown 형식 지원)"
    )
    challenge_number: int = Field(
        unique=True, nullable=False, description="챌린지 번호 (중복 불가)"
    )


class Challenge(ChallengeBase, table=True):
    """
    모든 유형의 챌린지에 대한 공통 정보를 저장하는 메인 테이블 모델.
    챌린지의 종류(tag)에 따라 PS, Img, Video 챌린지 중 하나와
    일대일(one-to-one) 관계를 맺습니다.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="user.id", nullable=False, description="챌린지 생성자 ID (외래키)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="생성 시각 (UTC)",
    )
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        description="마지막 수정 시각 (UTC)",
    )

    # --- Relationships ---
    user: "User" = Relationship(back_populates="challenges")
    posts: List["Post"] = Relationship(back_populates="challenge")
    shares: List["Share"] = Relationship(
        back_populates="challenge", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # `cascade="all, delete-orphan"`: Challenge가 삭제될 때 관련된 하위 챌린지(PS, Img, Video)도 함께 삭제됩니다.
    ps_challenge: Optional["PSChallenge"] = Relationship(
        back_populates="challenge", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    img_challenge: Optional["ImgChallenge"] = Relationship(
        back_populates="challenge", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    video_challenge: Optional["VideoChallenge"] = Relationship(
        back_populates="challenge", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# =================================================================
# PS Challenge & Testcase
# =================================================================
class PSChallenge(SQLModel, table=True):
    """
    프로그래밍(PS) 챌린지의 상세 정보를 나타내는 테이블 모델.
    Challenge와 일대일 관계이며, 여러 개의 테스트케이스(PSTestcase)와 일대다 관계를 가집니다.
    """

    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="challenge.id",
        primary_key=True,
        description="연결된 챌린지 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    challenge: "Challenge" = Relationship(back_populates="ps_challenge")
    testcases: List["PSTestcase"] = Relationship(
        back_populates="ps_challenge",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class PSTestcaseBase(SQLModel):
    """PS 챌린지 테스트케이스의 공통 필드를 정의하는 기본 모델."""

    input: Optional[str] = Field(default=None, description="테스트케이스 입력값")
    output: Optional[str] = Field(default=None, description="테스트케이스 기대 출력값")
    time_limit: float = Field(default=2.0, description="실행 시간 제한 (초)")
    mem_limit: int = Field(default=128, description="메모리 사용량 제한 (MB)")


class PSTestcase(PSTestcaseBase, table=True):
    """PS 챌린지에 사용되는 테스트케이스 정보를 담는 테이블 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="pschallenge.challenge_id",
        nullable=False,
        description="연결된 PS 챌린지 ID (외래키)",
    )

    # --- Relationships ---
    ps_challenge: "PSChallenge" = Relationship(back_populates="testcases")


# =================================================================
# Image Challenge & Reference
# =================================================================
class ImgChallenge(SQLModel, table=True):
    """
    이미지(Img) 챌린지의 상세 정보를 나타내는 테이블 모델.
    Challenge와 일대일 관계이며, 여러 개의 참고 이미지(ImgReference)와 일대다 관계를 가집니다.
    """

    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="challenge.id",
        primary_key=True,
        description="연결된 챌린지 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    challenge: "Challenge" = Relationship(back_populates="img_challenge")
    references: List["ImgReference"] = Relationship(
        back_populates="img_challenge",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ImgReferenceBase(SQLModel):
    """이미지 챌린지 참고자료의 공통 필드를 정의하는 기본 모델."""

    file_path: Optional[str] = Field(
        default=None, max_length=255, description="서버에 저장된 파일 경로"
    )
    file_type: Optional[str] = Field(
        default=None, max_length=50, description="파일 MIME 타입 (예: 'image/jpeg')"
    )


class ImgReference(ImgReferenceBase, table=True):
    """이미지 챌린지에 사용되는 참고 이미지 정보를 담는 테이블 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="imgchallenge.challenge_id",
        nullable=False,
        description="연결된 이미지 챌린지 ID (외래키)",
    )

    # --- Relationships ---
    img_challenge: "ImgChallenge" = Relationship(back_populates="references")


# =================================================================
# Video Challenge & Reference
# =================================================================
class VideoChallenge(SQLModel, table=True):
    """
    비디오(Video) 챌린지의 상세 정보를 나타내는 테이블 모델.
    Challenge와 일대일 관계이며, 여러 개의 참고 비디오(VideoReference)와 일대다 관계를 가집니다.
    """

    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="challenge.id",
        primary_key=True,
        description="연결된 챌린지 ID (외래키, 기본키)",
    )

    # --- Relationships ---
    challenge: "Challenge" = Relationship(back_populates="video_challenge")
    references: List["VideoReference"] = Relationship(
        back_populates="video_challenge",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class VideoReferenceBase(SQLModel):
    """비디오 챌린지 참고자료의 공통 필드를 정의하는 기본 모델."""

    file_path: Optional[str] = Field(
        default=None, max_length=255, description="서버에 저장된 파일 경로"
    )
    file_type: Optional[str] = Field(
        default=None, max_length=50, description="파일 MIME 타입 (예: 'video/mp4')"
    )


class VideoReference(VideoReferenceBase, table=True):
    """비디오 챌린지에 사용되는 참고 비디오 정보를 담는 테이블 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: Optional[int] = Field(
        default=None,
        foreign_key="videochallenge.challenge_id",
        nullable=False,
        description="연결된 비디오 챌린지 ID (외래키)",
    )

    # --- Relationships ---
    video_challenge: "VideoChallenge" = Relationship(back_populates="references")

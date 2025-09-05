# app/models/relations/post.py
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.relations.user import User
    from app.models.relations.challenge import Challenge


# =================================================================
# Enums
# =================================================================
class PostType(str, Enum):
    """게시글의 종류를 나타내는 Enum."""

    question = "question"  # 질문 게시글
    share = "share"  # 정보 공유 게시글


class PostTag(str, Enum):
    """게시글이 관련된 챌린지의 유형을 나타내는 Enum."""

    ps = "ps"
    img = "img"
    video = "video"


# =================================================================
# Post
# =================================================================
class PostBase(SQLModel):
    """게시글 모델의 공통 필드를 정의하는 기본 모델."""

    type: PostType = Field(nullable=False, description="게시글 종류 (question, share)")
    tag: PostTag = Field(nullable=False, description="관련 챌린�� 유형 태그 (ps, img, video)")
    title: str = Field(max_length=100, nullable=False, description="게시글 제목")
    content: Optional[str] = Field(
        default=None, description="게시글 내용 (Markdown 형식 지원)"
    )


class Post(PostBase, table=True):
    """
    게시글 정보를 나타내는 데이터베이스 테이블 모델.
    사용자(User)가 작성하며, 여러 개의 첨부파일(Attachment)과 댓글(Comment)을 가질 수 있습니다.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="user.id", nullable=False, description="게시글 작성자 ID (외래키)"
    )
    challenge_id: Optional[int] = Field(
        default=None, foreign_key="challenge.id", description="연관된 챌린지 ID (외래키)"
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
    user: "User" = Relationship(back_populates="posts")
    challenge: Optional["Challenge"] = Relationship(back_populates="posts")
    attachments: List["Attachment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    comments: List["Comment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes: List["UserLikesPost"] = Relationship(back_populates="post")


# =================================================================
# Attachment
# =================================================================
class AttachmentBase(SQLModel):
    """첨부파일 모델의 공통 필드를 정의하는 기본 모델."""

    file_path: str = Field(
        max_length=255, nullable=False, description="서버에 저장된 파일의 전체 경로"
    )
    file_type: Optional[str] = Field(
        default=None, max_length=50, description="파일의 MIME 타입 (예: 'image/png')"
    )


class Attachment(AttachmentBase, table=True):
    """게시글에 첨부된 파일 정보를 나타내는 데이터베이스 테이블 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: Optional[int] = Field(
        default=None, foreign_key="post.id", nullable=False, description="소속된 게시글 ID (외래키)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="생성 시각 (UTC)",
    )

    # --- Relationships ---
    post: "Post" = Relationship(back_populates="attachments")


# =================================================================
# Comment
# =================================================================
class CommentBase(SQLModel):
    """댓글 모델의 공통 필드를 정의하는 기본 모델."""

    content: Optional[str] = Field(default=None, description="댓글 내용")


class Comment(CommentBase, table=True):
    """게시글에 달린 댓글 정보를 나타내는 데이터베이스 테이블 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="user.id", nullable=False, description="댓글 작성자 ID (외래키)"
    )
    post_id: int = Field(
        foreign_key="post.id", nullable=False, description="소속된 게시글 ID (외래키)"
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
    user: "User" = Relationship(back_populates="comments")
    post: "Post" = Relationship(back_populates="comments")
    likes: List["UserLikesComment"] = Relationship(back_populates="comment")


# =================================================================
# Many-to-Many Link Models for Likes
# =================================================================
class UserLikesPostBase(SQLModel):
    """게시글 좋아요 관계 모델의 기본 모델 (현재 추가 필드 없음)."""

    pass


class UserLikesPost(UserLikesPostBase, table=True):
    """
    사용자와 게시글 간의 '좋아요' 관계를 나타내는 다대다(many-to-many) 연결 테이블 모델.
    복합 기본키(user_id, post_id)를 사용하여 한 사용자가 한 게시글에 한 번만 '좋아요'를 누를 수 있도록 보장합니다.
    """

    user_id: int = Field(
        foreign_key="user.id", primary_key=True, description="좋아요를 누른 사용자 ID"
    )
    post_id: int = Field(
        foreign_key="post.id", primary_key=True, description="좋아요를 받은 게시글 ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="좋아요를 누른 시각 (UTC)",
    )

    # --- Relationships ---
    user: "User" = Relationship(back_populates="liked_posts")
    post: "Post" = Relationship(back_populates="likes")


class UserLikesCommentBase(SQLModel):
    """댓글 좋아요 관계 모델의 기본 모델 (현재 추가 필드 없음)."""

    pass


class UserLikesComment(UserLikesCommentBase, table=True):
    """
    사용자와 댓글 간의 '좋아요' 관계를 나타내는 다대다(many-to-many) 연결 테이블 모델.
    복합 기본키(user_id, comment_id)를 사용합니다.
    """

    user_id: int = Field(
        foreign_key="user.id", primary_key=True, description="좋아요를 누른 사용자 ID"
    )
    comment_id: int = Field(
        foreign_key="comment.id", primary_key=True, description="좋아요를 받은 댓글 ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="좋아요를 누른 시각 (UTC)",
    )

    # --- Relationships ---
    user: "User" = Relationship(back_populates="liked_comments")
    comment: "Comment" = Relationship(back_populates="likes")

# app/models/serializers/post.py
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import computed_field
from sqlmodel import SQLModel

from app.models.relations.post import (
    AttachmentBase,
    CommentBase,
    PostBase,
    PostTag,
    PostType,
    UserLikesCommentBase,
    UserLikesPostBase,
)

if TYPE_CHECKING:
    from app.models.serializers.user import UserRead
    from app.models.serializers.challenge import ChallengeNumberRead


# =================================================================
# Post
# =================================================================
class PostCreate(PostBase):
    """게시글 생성을 위한 데이터 모델 (입력)."""

    challenge_id: Optional[int] = None


class PostCreateWithURL(PostCreate):
    """게시글과 첨부파일 URL을 함께 생성을 위한 데이터 모델 (입력)."""

    attachment_urls: List[str] = []


class PostUpdate(SQLModel):
    """게시글 수정을 위한 데이터 모델 (입력)."""

    type: Optional[PostType] = None
    tag: Optional[PostTag] = None
    title: Optional[str] = None
    content: Optional[str] = None


class PostRead(PostBase):
    """
    게시글 정보 조회를 위한 메인 데이터 모델 (출력).
    작성자, 첨부파일, 댓글, 좋아요 목록/개수를 포함합니다.
    """

    id: int
    user_id: int
    challenge_id: Optional[int] = None
    created_at: datetime
    modified_at: datetime
    user: Optional["UserRead"] = None
    challenge: Optional["ChallengeNumberRead"] = None
    attachments: List["AttachmentRead"] = []
    comments: List["CommentRead"] = []
    likes: List["UserLikesPostRead"] = []

    @computed_field
    @property
    def likes_count(self) -> int:
        """좋아요 개수를 계산하여 반환하는 계산된 필드."""
        return len(self.likes)


# =================================================================
# Attachment
# =================================================================
class AttachmentCreate(AttachmentBase):
    """첨부파일 생성을 위한 데이터 모델 (입력)."""

    pass


class AttachmentRead(AttachmentBase):
    """첨부파일 조회를 위한 데이터 모델 (출력)."""

    id: int
    post_id: int
    created_at: datetime


# =================================================================
# Comment
# =================================================================
class CommentCreate(CommentBase):
    """댓글 생성을 위한 데이터 모델 (입력)."""

    post_id: int


class CommentUpdate(SQLModel):
    """댓글 수정을 위한 데이터 모델 (입력)."""

    content: Optional[str] = None


class CommentRead(CommentBase):
    """
    댓글 정보 조회를 위한 데이터 모델 (출력).
    작성자 정보와 좋아요 목록/개수를 포함합니다.
    """

    id: int
    user_id: int
    post_id: int
    created_at: datetime
    modified_at: datetime
    user: Optional["UserRead"] = None
    likes: List["UserLikesCommentRead"] = []

    @computed_field
    @property
    def likes_count(self) -> int:
        """좋아요 개수를 계산하여 반환하는 계산된 필드."""
        return len(self.likes)


# =================================================================
# Likes
# =================================================================
class UserLikesPostRead(UserLikesPostBase):
    """게시글 좋아요 정보 조회를 위한 데이터 모델 (출력)."""

    user_id: int
    post_id: int
    created_at: datetime


class UserLikesCommentRead(UserLikesCommentBase):
    """댓글 좋아요 정보 조회를 위한 데이터 모델 (출력)."""

    user_id: int
    comment_id: int
    created_at: datetime

# app/models/serializers/share.py
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import computed_field

from app.models.relations.share import (
    ImgShareBase,
    PSShareBase,
    ShareBase,
    UserLikesShareBase,
    VideoShareBase,
)

if TYPE_CHECKING:
    from app.models.serializers.user import UserRead


# =================================================================
# Share
# =================================================================
class ShareCreate(ShareBase):
    """공유 생성을 위한 데이터 모델 (입력)."""

    challenge_id: int


class ShareRead(ShareBase):
    """
    공유 정보 조회를 위한 기본 데이터 모델 (출력).
    타입별 상세 정보는 포함하지 않습니다.
    """

    id: int
    challenge_id: int
    user_id: int
    created_at: datetime
    user: Optional["UserRead"] = None
    likes: List["UserLikesShareRead"] = []

    @computed_field
    @property
    def likes_count(self) -> int:
        """좋아요 개수를 계산하여 반환하는 계산된 필드."""
        return len(self.likes)


class ShareReadWithDetails(ShareRead):
    """
    타입별 상세 정보를 모두 포함한 공유 정보 조회를 위한 데이터 모델 (출력).
    """

    ps_share: Optional["PSShareRead"] = None
    img_share: Optional["ImgShareRead"] = None
    video_share: Optional["VideoShareRead"] = None


class PSShareReadWithDetails(ShareRead):
    """PS 공유의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    ps_share: Optional["PSShareRead"] = None


class ImgShareReadWithDetails(ShareRead):
    """이미지 공유의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    img_share: Optional["ImgShareRead"] = None


class VideoShareReadWithDetails(ShareRead):
    """비디오 공유의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    video_share: Optional["VideoShareRead"] = None


# =================================================================
# PS Share
# =================================================================
class PSShareCreate(PSShareBase):
    """PS 챌린지 공유 생성을 위한 데이터 모델 (입력)."""

    pass


class PSShareRead(PSShareBase):
    """PS 챌린지 공유 조회를 위한 데이터 모델 (출력)."""

    share_id: int


# =================================================================
# Image Share
# =================================================================
class ImgShareCreate(ImgShareBase):
    """이미지 챌린지 공유 생성을 위한 데이터 모델 (입력)."""

    pass


class ImgShareRead(ImgShareBase):
    """이미지 챌린지 공유 조회를 위한 데이터 모델 (출력)."""

    share_id: int


# =================================================================
# Video Share
# =================================================================
class VideoShareCreate(VideoShareBase):
    """비디오 챌린지 공유 생성을 위한 데이터 모델 (입력)."""

    pass


class VideoShareRead(VideoShareBase):
    """비디오 챌린지 공유 조회를 위한 데이터 모델 (출력)."""

    share_id: int


# =================================================================
# Likes
# =================================================================
class UserLikesShareRead(UserLikesShareBase):
    """공유 좋아요 정보 조회를 위한 데이터 모델 (출력)."""

    share_id: int
    user_id: int
    created_at: datetime

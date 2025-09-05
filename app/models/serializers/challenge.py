# app/models/serializers/challenge.py
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import SQLModel

from app.models.relations.challenge import (
    ChallengeBase,
    ChallengeLevel,
    ChallengeTag,
    ImgReferenceBase,
    PSTestcaseBase,
    VideoReferenceBase,
)

if TYPE_CHECKING:
    from app.models.serializers.user import UserRead


# =================================================================
# General Challenge
# =================================================================
class ChallengeCreate(ChallengeBase):
    """챌린지 생성을 위한 데이터 모델 (입력)."""

    pass


class ChallengeUpdate(SQLModel):
    """챌린지 수정을 위한 데이터 모델 (입력)."""

    tag: Optional[ChallengeTag] = None
    level: Optional[ChallengeLevel] = None
    title: Optional[str] = None
    content: Optional[str] = None
    challenge_number: Optional[int] = None


class ChallengeRead(ChallengeBase):
    """
    챌린지 목록 등 기본 정보 조회를 위한 데이터 모델 (출력).
    상세 정보는 포함하지 않습니다.
    """

    id: int
    user_id: int
    created_at: datetime
    user: Optional["UserRead"] = None


# =================================================================
# PS Challenge & Testcases
# =================================================================
class PSChallengeCreate(ChallengeCreate):
    """PS 챌린지 생성을 위한 요청 모델. ChallengeCreate를 상속받아 테스트케이스 목록을 추가로 받습니다."""

    testcases: List["PSTestcaseCreate"]


class PSChallengeRead(SQLModel):
    """PS 챌린지 상세 정보 조회를 위한 데이터 모델 (출력)."""

    challenge_id: int
    testcases: List["PSTestcaseRead"] = []
    accuracy_rate: float = 0.0


class PSChallengeReadWithDetails(ChallengeRead):
    """PS 챌린지의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    ps_challenge: Optional["PSChallengeRead"] = None


class PSTestcaseCreate(PSTestcaseBase):
    """PS 챌린지 테스트케이스 생성을 위한 데이터 모델 (입력)."""

    pass


class PSTestcaseUpdate(SQLModel):
    """PS 챌린지 테스트케이스 수정을 위한 데이터 모델 (입력)."""

    input: Optional[str] = None
    output: Optional[str] = None
    time_limit: Optional[int] = None
    mem_limit: Optional[int] = None


class PSTestcaseRead(PSTestcaseBase):
    """PS 챌린지 테스트케이스 조회를 위한 데이터 모델 (출력)."""

    id: int
    challenge_id: int


# =================================================================
# Image Challenge & References
# =================================================================
class ImgChallengeRead(SQLModel):
    """이미지 챌린지 상세 정보 조회를 위한 데이터 모델 (출력)."""

    challenge_id: int
    references: List["ImgReferenceRead"] = []


class ImgChallengeReadWithDetails(ChallengeRead):
    """이미지 챌린지의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    img_challenge: Optional["ImgChallengeRead"] = None


class ImgReferenceCreate(ImgReferenceBase):
    """이미지 참고자료 생성을 위한 데이터 모델 (입력)."""

    pass


class ImgReferenceUpdate(SQLModel):
    """이미지 참고자료 수정을 위한 데이터 모델 (입력)."""

    file_path: Optional[str] = None
    file_type: Optional[str] = None


class ImgReferenceRead(ImgReferenceBase):
    """이미지 참고자료 조회를 위한 데이터 모델 (출력)."""

    id: int
    challenge_id: int


# =================================================================
# Video Challenge & References
# =================================================================
class VideoChallengeRead(SQLModel):
    """비디오 챌린지 상세 정보 조회를 위한 데이터 모델 (출력)."""

    challenge_id: int
    references: List["VideoReferenceRead"] = []


class VideoChallengeReadWithDetails(ChallengeRead):
    """비디오 챌린지의 상세 정보 조회를 위한 데이터 모델 (출력)."""

    video_challenge: Optional["VideoChallengeRead"] = None


class VideoReferenceCreate(VideoReferenceBase):
    """비디오 참고자료 생성을 위한 데이터 모델 (입력)."""

    pass


class VideoReferenceUpdate(SQLModel):
    """비디오 참고자료 수정을 위한 데이터 모델 (입력)."""

    file_path: Optional[str] = None
    file_type: Optional[str] = None


class VideoReferenceRead(VideoReferenceBase):
    """비디오 참고자료 조회를 위한 데이터 모델 (출력)."""

    id: int
    challenge_id: int


# =================================================================
# Union Read Serializer for Details
# =================================================================
class ChallengeReadWithDetails(ChallengeBase):
    """챌린지 상세 정보 조회를 위한 데이터 모델 (출력)."""

    ps_challenge: Optional["PSChallengeRead"] = None
    img_challenge: Optional["ImgChallengeRead"] = None
    video_challenge: Optional["VideoChallengeRead"] = None


class ChallengeNumberRead(SQLModel):
    """게시글 조회 시 챌린지 번호만 내려주기 위한 모델."""

    challenge_number: Optional[int] = None

# app/crud/share.py
from typing import List, Optional

from sqlmodel import Session, select

from app.models.relations import (
    Challenge,
    ImgShare,
    PSShare,
    Share,
    User,
    UserLikesShare,
    VideoShare,
)
from app.models.serializers import (
    ChallengeTag,
    ImgShareCreate,
    PSShareCreate,
    ShareCreate,
    VideoShareCreate,
)


def create_ps_share(
    db: Session, share_in: ShareCreate, ps_share_in: PSShareCreate, user: User
) -> Share:
    """
    새로운 PS 챌린지 결과물을 공유(생성)합니다.
    """
    db_share = Share.model_validate(share_in, update={"user_id": user.id})
    db_ps_share = PSShare.model_validate(ps_share_in)
    db_share.ps_share = db_ps_share
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def create_img_share(
    db: Session, share_in: ShareCreate, img_share_in: ImgShareCreate, user: User
) -> Share:
    """
    새로운 이미지 챌린지 결과물을 공유(생성)합니다.
    """
    db_share = Share.model_validate(share_in, update={"user_id": user.id})
    # 자식 객체 생성 시 부모 객체와의 관계를 명시적으로 설정합니다.
    db_img_share = ImgShare.model_validate(img_share_in, update={"share": db_share})
    db.add(db_img_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def create_video_share(
    db: Session, share_in: ShareCreate, video_share_in: VideoShareCreate, user: User
) -> Share:
    """
    새로운 비디오 챌린지 결과물을 공유(생성)합니다.
    """
    db_share = Share.model_validate(share_in, update={"user_id": user.id})
    # 자식 객체 생성 시 부모 객체와의 관계를 명시적으로 설정합니다.
    db_video_share = VideoShare.model_validate(
        video_share_in, update={"share": db_share}
    )
    db.add(db_video_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def get_share(db: Session, share_id: int) -> Optional[Share]:
    """
    ID를 기준으로 특정 공유를 조회합니다.
    """
    return db.get(Share, share_id)


def get_shares(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    challenge_id: Optional[int] = None,
    tag: Optional[ChallengeTag] = None,
) -> List[Share]:
    """
    조건에 맞는 '공개된' 공유 목록을 조회합니다.
    """
    statement = select(Share).where(Share.is_public).offset(skip).limit(limit)
    if challenge_id:
        statement = statement.where(Share.challenge_id == challenge_id)
    if tag:
        statement = statement.join(Challenge).where(Challenge.tag == tag)
    shares = db.exec(statement).all()
    return list(shares)


def delete_share(db: Session, share_id: int, user: User) -> Share | None:
    """
    공유를 삭제합니다.
    """
    db_share = db.get(Share, share_id)
    if not db_share:
        return None

    if db_share.user_id != user.id and not user.is_admin:
        return None

    db.delete(db_share)
    db.commit()
    return db_share


def like_share(db: Session, db_share: Share, user: User) -> UserLikesShare:
    """
    공유에 '좋아요'를 추가합니다.
    """
    if user.id is None:
        raise ValueError("User must have an ID to like a share")
    if db_share.id is None:
        raise ValueError("Share must have an ID to be liked")

    db_like = UserLikesShare(user_id=user.id, share_id=db_share.id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def unlike_share(db: Session, db_share: Share, user: User):
    """
    공유의 '좋아요'를 취소합니다.
    """
    statement = select(UserLikesShare).where(
        UserLikesShare.user_id == user.id, UserLikesShare.share_id == db_share.id
    )
    like_to_delete = db.exec(statement).first()
    if like_to_delete:
        db.delete(like_to_delete)
        db.commit()
    return

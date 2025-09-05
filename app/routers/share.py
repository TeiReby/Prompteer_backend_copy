# app/routers/share.py
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlmodel import Session

from app.crud import share as crud_share
from app.dependency import get_current_user, get_db
from app.models.relations import User
from app.models.serializers import (
    ChallengeTag,
    ImgShareReadWithDetails,
    PSShareReadWithDetails,
    ShareReadWithDetails,
    UserLikesShareRead,
    VideoShareReadWithDetails,
)

router = APIRouter(
    prefix="/shares",
    tags=["Shares"],
)

@router.get("/ps/", response_model=List[PSShareReadWithDetails])
async def read_ps_shares(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    challenge_id: Optional[int] = Query(None, description="필터링할 챌린지 ID"),
    db: Session = Depends(get_db),
):
    """
    PS 챌린지 결과물 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    - **필터링**: `challenge_id`로 특정 챌린지에 대한 결과물만 필터링할 수 있습니다.
    """
    return crud_share.get_shares(
        db=db, skip=skip, limit=limit, challenge_id=challenge_id, tag=ChallengeTag.ps
    )


@router.get("/img/", response_model=List[ImgShareReadWithDetails])
async def read_img_shares(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    challenge_id: Optional[int] = Query(None, description="필터링할 챌린지 ID"),
    db: Session = Depends(get_db),
):
    """
    이미지 챌린지 결과물 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    - **필터링**: `challenge_id`로 특정 챌린지에 대한 결과물만 필터링할 수 있습니다.
    """
    return crud_share.get_shares(
        db=db, skip=skip, limit=limit, challenge_id=challenge_id, tag=ChallengeTag.img
    )


@router.get("/video/", response_model=List[VideoShareReadWithDetails])
async def read_video_shares(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    challenge_id: Optional[int] = Query(None, description="필터링할 챌린지 ID"),
    db: Session = Depends(get_db),
):
    """
    비디오 챌린지 결과물 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    - **필터링**: `challenge_id`로 특정 챌린지에 대한 결과물만 필터링할 수 있습니다.
    """
    return crud_share.get_shares(
        db=db, skip=skip, limit=limit, challenge_id=challenge_id, tag=ChallengeTag.video
    )


@router.get("/{share_id}", response_model=ShareReadWithDetails)
async def read_share(share_id: int, db: Session = Depends(get_db)):
    """
    ID로 특정 챌린지 결과물을 조회합니다.

    - **오류**: 결과물을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_share = crud_share.get_share(db, share_id=share_id)
    if db_share is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )
    return db_share

@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    챌린지 결과물(공유)을 삭제합니다.

    - **권한**: 공유 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**: 공유를 찾을 수 없거나 권한이 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    deleted_share = crud_share.delete_share(
        db=db, share_id=share_id, user=current_user
    )
    if not deleted_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or permission denied",
        )
    return


@router.post(
    "/{share_id}/like",
    response_model=UserLikesShareRead,
    status_code=status.HTTP_201_CREATED,
)
async def like_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    챌린지 결과물(공유)에 '좋아요'를 누릅니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**:
        - 공유를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 이미 '좋아요'를 누른 경우 `409 Conflict` 에러를 반환합니다.
    """
    db_share = crud_share.get_share(db, share_id=share_id)
    if not db_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    existing_like = any(like.user_id == current_user.id for like in db_share.likes)
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already liked this share"
        )

    return crud_share.like_share(db=db, db_share=db_share, user=current_user)


@router.delete("/{share_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    챌린지 결과물(공유)의 '좋아요'를 취소합니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**: 공유를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_share = crud_share.get_share(db, share_id=share_id)
    if not db_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )
    crud_share.unlike_share(db=db, db_share=db_share, user=current_user)
    return

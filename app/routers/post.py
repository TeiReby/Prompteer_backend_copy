# app/routers/post.py
from typing import List, Optional, Set

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlmodel import Session

from app.crud import post as crud_post
from app.dependency import get_current_user, get_db
from app.models.relations import User
from app.models.serializers import (
    CommentCreate,
    CommentRead,
    CommentUpdate,
    PostCreate,
    PostCreateWithURL,
    PostRead,
    PostTag,
    PostType,
    PostUpdate,
    UserLikesCommentRead,
    UserLikesPostRead,
)

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)


# =================================================================
# Post Endpoints
# =================================================================


@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreateWithURL,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    새로운 게시글을 생성합니다.

    - **요청 형식**: `application/json`
    - 게시글 정보와 첨부파일 URL 목록을 JSON 본문으로 전달받아 처리합니다.
    - **권한**: 로그인된 사용자만 생성할 수 있습니다.
    """
    post_create_data = post_in.model_dump(exclude={"attachment_urls"})
    post_create = PostCreate.model_validate(post_create_data)

    return crud_post.create_post(
        db=db,
        post_in=post_create,
        user=current_user,
        attachment_urls=post_in.attachment_urls,
    )


@router.get("/", response_model=List[PostRead])
async def read_posts(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    types: Optional[Set[PostType]] = Query(
        default=None, description="필터링할 게시글 종류 (중복 가능)"
    ),
    tags: Optional[Set[PostTag]] = Query(
        default=None, description="필터링할 챌린지 태그 (중복 가능)"
    ),
    db: Session = Depends(get_db),
):
    """
    조건에 맞는 게시글 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    - **필터링**: `types`와 `tags` 쿼리 파라미터를 사용하여 다중 조건 필터링이 가능합니다.
    """
    return crud_post.get_posts(db=db, skip=skip, limit=limit, types=types, tags=tags)


@router.get("/{post_id}", response_model=PostRead)
async def read_post(post_id: int, db: Session = Depends(get_db)):
    """
    ID로 특정 게시글의 상세 정보를 조회합니다.

    - **오류**: 게시글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_post = crud_post.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return db_post


@router.put("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    게시글의 텍스트 정보를 수정합니다. (첨부파일 수정은 별도 엔드포인트 사용)

    - **권한**: 게시글 생성자 또는 관리자만 수정할 수 있습니다.
    - **오류**: 게시글을 찾을 수 없거나 권한이 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    updated_post = crud_post.update_post(
        db=db, post_id=post_id, post_in=post_in, user=current_user
    )
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or permission denied",
        )
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 ID의 게시글을 삭제합니다.

    - **권한**: 게시글 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**: 게시글을 찾을 수 없거나 권한이 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    deleted_post = crud_post.delete_post(db=db, post_id=post_id, user=current_user)
    if not deleted_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or permission denied",
        )
    return

# =================================================================
# Comment Endpoints
# =================================================================


@router.post(
    "/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 게시글에 새로운 댓글을 작성합니다.

    - **권한**: 로그인된 사용자만 작성할 수 있습니다.
    - **오류**:
        - 게시글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 요청 경로의 `post_id`와 요청 본문의 `post_id`가 일치하지 않는 경우
          `400 Bad Request` 에러를 반환합니다.
    """
    db_post = crud_post.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if comment_in.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path post_id and body post_id do not match",
        )

    return crud_post.create_comment(db=db, comment_in=comment_in, user=current_user)


@router.put(
    "/comments/{comment_id}",
    response_model=CommentRead,
)
async def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 ID의 댓글을 수정합니다.

    - **권한**: 댓글 작성자 또는 관리자만 수정할 수 있습니다.
    - **오류**: 댓글을 찾을 수 없거나 권한이 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    updated_comment = crud_post.update_comment(
        db=db, comment_id=comment_id, comment_in=comment_in, user=current_user
    )
    if not updated_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or permission denied",
        )
    return updated_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 ID의 댓글을 삭제합니다.

    - **권한**: 댓글 작성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**: 댓글을 찾을 수 없거나 권한이 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    deleted_comment = crud_post.delete_comment(
        db=db, comment_id=comment_id, user=current_user
    )
    if not deleted_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or permission denied",
        )
    return


# =================================================================
# Like Endpoints
# =================================================================


@router.post(
    "/{post_id}/like",
    response_model=UserLikesPostRead,
    status_code=status.HTTP_201_CREATED,
)
async def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 게시글에 '좋아요'를 누릅니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**:
        - 게시글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 이미 '좋아요'를 누른 경우 `409 Conflict` 에러를 반환합니다.
    """
    db_post = crud_post.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # 현재 사용자가 이미 '좋아요'를 눌렀는지 확인
    existing_like = any(like.user_id == current_user.id for like in db_post.likes)
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already liked this post"
        )

    return crud_post.like_post(db=db, db_post=db_post, user=current_user)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 게시글의 '좋아요'를 취소합니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**: 게시글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_post = crud_post.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    crud_post.unlike_post(db=db, db_post=db_post, user=current_user)
    return


@router.post(
    "/comments/{comment_id}/like",
    response_model=UserLikesCommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 댓글에 '좋아요'를 누릅니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**:
        - 댓글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 이미 '좋아요'를 누른 경우 `409 Conflict` 에러를 반환합니다.
    """
    db_comment = crud_post.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    existing_like = any(like.user_id == current_user.id for like in db_comment.likes)
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already liked this comment"
        )

    return crud_post.like_comment(db=db, db_comment=db_comment, user=current_user)


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 댓글의 '좋아요'를 취소합니다.

    - **권한**: 로그인된 사용자만 가능합니다.
    - **오류**: 댓글을 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_comment = crud_post.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    crud_post.unlike_comment(db=db, db_comment=db_comment, user=current_user)
    return

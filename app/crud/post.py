# app/crud/post.py
import os
from typing import List, Set

from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.models.relations import (
    Attachment,
    Comment,
    Post,
    User,
    UserLikesComment,
    UserLikesPost,
    Challenge,
)
from app.models.serializers import (
    AttachmentCreate,
    CommentCreate,
    CommentUpdate,
    PostCreate,
    PostTag,
    PostType,
    PostUpdate,
)

# =================================================================
# Attachment CRUD
# =================================================================


def get_attachment(db: Session, attachment_id: int) -> Attachment | None:
    """
    ID로 특정 첨부파일을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        attachment_id: 조회할 첨부파일의 ID.

    Returns:
        조회된 Attachment 객체. 없으면 None을 반환합니다.
    """
    return db.get(Attachment, attachment_id)


def create_attachment_for_post(
    db: Session, db_post: Post, attachment_in: AttachmentCreate
) -> Attachment:
    """
    특정 게시글에 새로운 첨부파일을 추가합니다.

    Args:
        db: SQLModel 세션 객체.
        db_post: 첨부파일을 추가할 Post 객체.
        attachment_in: 생성할 첨부파일의 데이터 모델.

    Returns:
        생성된 Attachment 객체.
    
    Raises:
        ValueError: Post 객체에 ID가 없을 경우 발생합니다.
    """
    if db_post.id is None:
        raise ValueError("Post must have an ID to add an attachment")

    db_attachment = Attachment.model_validate(
        attachment_in, update={"post_id": db_post.id}
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def delete_attachment(db: Session, db_attachment: Attachment):
    """
    첨부파일을 삭제합니다.
    - 데이터베이스 레코드와 파일 시스템의 실제 파일을 모두 삭제합니다.

    Args:
        db: SQLModel 세션 객체.
        db_attachment: 삭제할 Attachment 객체.
    """
    file_path = db_attachment.file_path
    db.delete(db_attachment)
    db.commit()

    # DB에서 삭제 성공 후, 파일 시스템에서 실제 파일 삭제
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return


# =================================================================
# Post CRUD
# =================================================================


def create_post(
    db: Session, post_in: PostCreate, user: User, attachment_urls: List[str]
) -> Post:
    """
    새로운 게시글을 생성하고, 제공된 URL 목록을 기반으로 첨부파일을 연결합니다.

    Args:
        db: SQLModel 세션 객체.
        post_in: 생성할 게시글의 데이터 모델.
        user: 게시글을 생성하는 사용자 객체.
        attachment_urls: 게시글에 포함될 첨부파일의 URL 목록.

    Returns:
        생성된 Post 객체.

    Raises:
        ValueError: User 객체에 ID가 없거나 존재하지 않는 Challenge ID가 제공된 경우.
    """
    if user.id is None:
        raise ValueError("User must have an ID to create a post")

    # `post_in`에서 `challenge_id`를 포함한 데이터를 추출합니다.
    post_data = post_in.model_dump()
    
    # challenge_id가 유효한지 확인합니다.
    challenge_id = post_data.get("challenge_id")
    if challenge_id:
        challenge = db.get(Challenge, challenge_id)
        if not challenge:
            raise ValueError(f"Challenge with id {challenge_id} not found")

    # user_id를 추가하여 Post 객체를 생성합니다.
    db_post = Post.model_validate(post_data, update={"user_id": user.id})

    for url in attachment_urls:
        # 각 URL에 대해 Attachment 객체를 생성하여 게시글에 추가합니다.
        attachment_in = AttachmentCreate(file_path=url, file_type=None)
        db_attachment = Attachment.model_validate(attachment_in)
        db_post.attachments.append(db_attachment)

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_post(db: Session, post_id: int) -> Post | None:
    """
    ID로 특정 게시글을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        post_id: 조회할 게시글의 ID.

    Returns:
        조회된 Post 객체. 없으면 None을 반환합니다.
    """
    statement = (
        select(Post).where(Post.id == post_id).options(joinedload(Post.challenge))
    )
    return db.exec(statement).first()


def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    types: Set[PostType] | None = None,
    tags: Set[PostTag] | None = None,
) -> List[Post]:
    """
    조건에 맞는 게시글 목록을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        skip: 건너뛸 레코드의 수 (페이지네이션).
        limit: 반환할 최대 레코드의 수 (페이지네이션).
        types: 필터링할 게시글 종류(PostType) 집합.
        tags: 필터링할 챌린지 태그(PostTag) 집합.

    Returns:
        조회된 Post 객체의 리스트.
    """
    statement = select(Post).options(joinedload(Post.challenge))
    if types:
        statement = statement.where(Post.type.in_(types))
    if tags:
        statement = statement.where(Post.tag.in_(tags))
        
    # 최신순으로 정렬 (created_at 기준 내림차순)
    statement = statement.order_by(Post.created_at.desc())
    statement = statement.offset(skip).limit(limit)
    posts = db.exec(statement).all()
    return list(posts)


def update_post(
    db: Session, post_id: int, post_in: PostUpdate, user: User
) -> Post | None:
    """
    게시글 정보를 수정합니다.

    - 게시글 소유자 또는 관리자만 수정할 수 있습니다.

    Args:
        db: SQLModel 세션 객체.
        post_id: 수정할 게시글의 ID.
        post_in: 수정할 데이터가 담긴 모델.
        user: 요청을 보낸 사용자 객체.

    Returns:
        수정된 Post 객체. 게시글이 없거나 권한이 없으면 None을 반환합니다.
    """
    db_post = db.get(Post, post_id)
    if not db_post:
        return None

    # 소유권 및 관리자 권한 검사
    if db_post.user_id != user.id and not user.is_admin:
        return None

    post_data = post_in.model_dump(exclude_unset=True)
    for key, value in post_data.items():
        setattr(db_post, key, value)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int, user: User) -> Post | None:
    """
    게시글을 삭제합니다.

    - 게시글 소유자 또는 관리자만 삭제할 수 있습니다.
    - `cascade` 설정에 따라 연결된 댓글, 첨부파일, 좋아요 정보가 함께 삭제됩니다.

    Args:
        db: SQLModel 세션 객체.
        post_id: 삭제할 게시글의 ID.
        user: 요청을 보낸 사용자 객체.

    Returns:
        삭제된 Post 객체. 게시글이 없거나 권한이 없으면 None을 반환합니다.
    """
    db_post = db.get(Post, post_id)
    if not db_post:
        return None

    # 소유권 및 관리자 권한 검사
    if db_post.user_id != user.id and not user.is_admin:
        return None

    db.delete(db_post)
    db.commit()
    return db_post


# =================================================================
# Comment CRUD
# =================================================================


def create_comment(
    db: Session, comment_in: CommentCreate, user: User
) -> Comment:
    """
    특정 게시글에 새로운 댓글을 생성합니다.

    Args:
        db: SQLModel 세션 객체.
        comment_in: 생성할 댓글의 데이터 모델.
        user: 댓글을 생성하는 사용자 객체.

    Returns:
        생성된 Comment 객체.
    """
    # `user.id`를 주입하여 댓글 작성자를 명시합니다.
    db_comment = Comment.model_validate(
        comment_in, update={"user_id": user.id}
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment(db: Session, comment_id: int) -> Comment | None:
    """
    ID로 특정 댓글을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        comment_id: 조회할 댓글의 ID.

    Returns:
        조회된 Comment 객체. 없으면 None을 반환합니다.
    """
    return db.get(Comment, comment_id)


def update_comment(
    db: Session, comment_id: int, comment_in: CommentUpdate, user: User
) -> Comment | None:
    """
    댓글 정보를 수정합니다.

    - 댓글 작성자 또는 관리자만 수정할 수 있습니다.

    Args:
        db: SQLModel 세션 객체.
        comment_id: 수정할 댓글의 ID.
        comment_in: 수정할 데이터가 담긴 모델.
        user: 요청을 보낸 사용자 객체.

    Returns:
        수정된 Comment 객체. 댓글이 없거나 권한이 없으면 None을 반환합니다.
    """
    db_comment = db.get(Comment, comment_id)
    if not db_comment:
        return None

    # 소유권 및 관리자 권한 검사
    if db_comment.user_id != user.id and not user.is_admin:
        return None

    comment_data = comment_in.model_dump(exclude_unset=True)
    for key, value in comment_data.items():
        setattr(db_comment, key, value)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: int, user: User) -> Comment | None:
    """
    댓글을 삭제합니다.

    - 댓글 작성자 또는 관리자만 삭제할 수 있습니다.

    Args:
        db: SQLModel 세션 객체.
        comment_id: 삭제할 댓글의 ID.
        user: 요청을 보낸 사용자 객체.

    Returns:
        삭제된 Comment 객체. 댓글이 없거나 권한이 없으면 None을 반환합니다.
    """
    db_comment = db.get(Comment, comment_id)
    if not db_comment:
        return None

    # 소유권 및 관리자 권한 검사
    if db_comment.user_id != user.id and not user.is_admin:
        return None

    db.delete(db_comment)
    db.commit()
    return db_comment


# =================================================================
# Like CRUD
# =================================================================


def like_post(db: Session, db_post: Post, user: User) -> UserLikesPost:
    """
    게시글에 '좋아요'를 추가합니다.

    Args:
        db: SQLModel 세션 객체.
        db_post: '좋아요'를 추가할 Post 객체.
        user: '좋아요'를 누르는 사용자 객체.

    Returns:
        생성된 UserLikesPost 연결 객체.
        
    Raises:
        ValueError: User 또는 Post 객체에 ID가 없을 경우 발생합니다.
    """
    if user.id is None:
        raise ValueError("User must have an ID to like a post")
    if db_post.id is None:
        raise ValueError("Post must have an ID to be liked")

    db_like = UserLikesPost(user_id=user.id, post_id=db_post.id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def unlike_post(db: Session, db_post: Post, user: User):
    """
    게시글의 '좋아요'를 취소합니다.

    Args:
        db: SQLModel 세션 객체.
        db_post: '좋아요'를 취소할 Post 객체.
        user: '좋아요'를 취소하는 사용자 객체.
    """
    statement = select(UserLikesPost).where(
        UserLikesPost.user_id == user.id, UserLikesPost.post_id == db_post.id
    )
    like_to_delete = db.exec(statement).first()
    if like_to_delete:
        db.delete(like_to_delete)
        db.commit()
    return


def like_comment(db: Session, db_comment: Comment, user: User) -> UserLikesComment:
    """
    댓글에 '좋아요'를 추가합니다.

    Args:
        db: SQLModel 세션 객체.
        db_comment: '좋아요'를 추가할 Comment 객체.
        user: '좋아요'를 누르는 사용자 객체.

    Returns:
        생성된 UserLikesComment 연결 객체.
        
    Raises:
        ValueError: User 또는 Comment 객체에 ID가 없을 경우 발생합니다.
    """
    if user.id is None:
        raise ValueError("User must have an ID to like a comment")
    if db_comment.id is None:
        raise ValueError("Comment must have an ID to be liked")

    db_like = UserLikesComment(user_id=user.id, comment_id=db_comment.id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def unlike_comment(db: Session, db_comment: Comment, user: User):
    """
    댓글의 '좋아요'를 취소합니다.

    Args:
        db: SQLModel 세션 객체.
        db_comment: '좋아요'를 취소할 Comment 객체.
        user: '좋아요'를 취소하는 사용자 객체.
    """
    statement = select(UserLikesComment).where(
        UserLikesComment.user_id == user.id,
        UserLikesComment.comment_id == db_comment.id,
    )
    like_to_delete = db.exec(statement).first()
    if like_to_delete:
        db.delete(like_to_delete)
        db.commit()
    return

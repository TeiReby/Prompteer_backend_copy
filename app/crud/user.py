# app/crud/user.py
from typing import List
from sqlmodel import Session, select

from app.models.relations import Challenge, Profile, Share, User
from app.models.serializers import ChallengeTag, ProfileUpdate, UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User | None:
    """
    ID를 기준으로 활성 상태인 사용자를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        user_id: 조회할 사용자의 ID.

    Returns:
        조회된 User 객체. 없거나 비활성 상태이면 None을 반환합니다.
    """
    statement = select(User).where(User.id == user_id, User.is_active == True)
    return db.exec(statement).first()


def get_user_by_nickname(db: Session, nickname: str) -> User | None:
    """
    닉네임을 기준으로 활성 상태인 사용자를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        nickname: 조회할 사용자의 닉네임.

    Returns:
        조회된 User 객체. 없거나 비활성 상태이면 None을 반환합니다.
    """
    statement = select(User).where(User.nickname == nickname, User.is_active == True)
    return db.exec(statement).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    이메일을 기준으로 활성 상태인 사용자를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        email: 조회할 사용자의 이메일.

    Returns:
        조회된 User 객체. 없거나 비활성 상태이면 None을 반환합니다.
    """
    statement = select(User).where(User.email == email, User.is_active == True)
    return db.exec(statement).first()


def create_user(db: Session, user: UserCreate) -> User:
    """
    새로운 사용자를 생성하고, 연관된 빈 프로필도 함께 생성합니다.

    - 참고: 현재 구현에서는 데모 및 테스트 편의를 위해 비밀번호를 해싱하지 않고
      그대로 데이터베이스에 저장합니다. 실제 프로덕션 환경에서는 반드시
      bcrypt와 같은 안전한 해싱 알고리즘을 사용해야 합니다.

    Args:
        db: SQLModel 세션 객체.
        user: 생성할 사용자의 데이터가 담긴 Pydantic 모델.

    Returns:
        데이터베이스에 저장된 새로운 User 객체.
    """
    db_user = User.model_validate(user)
    # 사용자 생성 시, 1:1 관계인 빈 프로필(Profile) 객체를 함께 생성하여 연결합니다.
    db_user.profile = Profile()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    """
    기존 사용자 정보를 업데이트합니다.

    - `user_in` 모델에 포함된 필드만 선택적으로 업데이트합니다.

    Args:
        db: SQLModel 세션 객체.
        db_user: 업데이트할 기존 User 객체.
        user_in: 업데이트할 데이터가 담긴 Pydantic 모델.

    Returns:
        업데이트된 User 객체.
    """
    user_data = user_in.model_dump(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_profile(
    db: Session, db_profile: Profile, profile_in: ProfileUpdate
) -> Profile:
    """
    사용자 프로필 정보를 업데이트합니다.

    - `profile_in` 모델에 포함된 필드만 선택적으로 업데이트합니다.

    Args:
        db: SQLModel 세션 객체.
        db_profile: 업데이트할 기존 Profile 객체.
        profile_in: 업데이트할 데이터가 담긴 Pydantic 모델.

    Returns:
        업데이트된 Profile 객체.
    """
    profile_data = profile_in.model_dump(exclude_unset=True)
    for key, value in profile_data.items():
        setattr(db_profile, key, value)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def soft_delete_user(db: Session, user: User):
    """
    사용자를 비활성 상태로 만들고 개인정보를 마스킹 처리합니다.

    - is_active를 False로 설정합니다.
    - 닉네임과 이메일은 다른 사용자가 사용할 수 있도록 접미사를 추가하여 변경합니다.
    - 비밀번호는 복구 불가능하도록 빈 값으로 설정합니다.

    Args:
        db: SQLModel 세션 객체.
        user: 비활성화할 User 객체.
    """
    user.is_active = False
    user.nickname = f"{user.nickname}(탈퇴한 유저)#{user.id}"
    user.email = f"deleted_user_#{user.id}_{user.email}"
    user.password = ""  # 패스워드 삭제해서 접근 차단.
    db.add(user)
    db.commit()


def get_user_public_shares(
    db: Session, user: User, tag: ChallengeTag
) -> List[Share]:
    """
    특정 사용자가 생성하고 특정 태그에 해당하는 '공개'된 공유 목록을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        user: 조회할 User 객체.
        tag: 필터링할 챌린지 태그 (ps, img, video).

    Returns:
        해당 사용자의 공개된 Share 객체 리스트.
    """
    statement = (
        select(Share)
        .join(Challenge)
        .where(Share.user_id == user.id)
        .where(Share.is_public)
        .where(Challenge.tag == tag)
    )
    shares = db.exec(statement).all()
    return list(shares)


def get_user_public_shares(
    db: Session, user: User, tag: ChallengeTag
) -> List[Share]:
    """
    특정 사용자가 생성하고 특정 태그에 해당하는 '공개'된 공유 목록을 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        user: 조회할 User 객체.
        tag: 필터링할 챌린지 태그 (ps, img, video).

    Returns:
        해당 사용자의 공개된 Share 객체 리스트.
    """
    statement = (
        select(Share)
        .join(Challenge)
        .where(Share.user_id == user.id)
        .where(Share.is_public)
        .where(Challenge.tag == tag)
    )
    shares = db.exec(statement).all()
    return list(shares)
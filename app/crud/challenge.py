# app/crud/challenge.py
from typing import List

from sqlmodel import Session, select, func

from app.models.relations import (
    Challenge,
    ImgChallenge,
    ImgReference,
    PSChallenge,
    PSTestcase,
    PSShare, 
    Share,
    User,
    VideoChallenge,
    VideoReference,
)
from app.models.serializers import (
    ChallengeCreate,
    ChallengeTag,
    ChallengeUpdate,
    ImgReferenceCreate,
    ImgReferenceUpdate,
    PSTestcaseCreate,
    PSTestcaseUpdate,
    VideoReferenceCreate,
    VideoReferenceUpdate,
)


def create_ps_challenge(
    db: Session,
    challenge_in: ChallengeCreate,
    testcases_in: List[PSTestcaseCreate],
    user: User,
) -> Challenge:
    """
    새로운 프로그래밍(PS) 챌린지를 데이터베이스에 생성합니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_in: 생성할 챌린지의 데이터 모델.
        testcases_in: 챌린지에 포함될 테스트케이스 데이터 목록.
        user: 챌린지를 생성하는 사용자 객체.

    Returns:
        생성된 Challenge 객체.
    """
    # Challenge 모델 기반으로 기본 챌린지 정보 생성
    db_challenge = Challenge.model_validate(challenge_in, update={"user_id": user.id})

    # PS 챌린지 상세 정보 및 테스트케이스 생성
    db_ps_challenge = PSChallenge()
    for testcase_in in testcases_in:
        db_testcase = PSTestcase.model_validate(testcase_in)
        db_ps_challenge.testcases.append(db_testcase)

    # 생성된 정보들을 Challenge 객체에 연결
    db_challenge.ps_challenge = db_ps_challenge

    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge


def get_challenge(db: Session, challenge_id: int) -> Challenge | None:
    """
    지정된 ID를 가진 챌린지를 데이터베이스에서 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_id: 조회할 챌린지의 ID.

    Returns:
        조회된 Challenge 객체. 해당 ID의 챌린지가 없으면 None을 반환합니다.
    """
    return db.get(Challenge, challenge_id)


def get_challenges(
    db: Session, skip: int = 0, limit: int = 100, tag: ChallengeTag | None = None
) -> List[Challenge]:
    """
    조건에 맞는 챌린지 목록을 데이터베이스에서 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        skip: 건너뛸 레코드의 수 (페이지네이션).
        limit: 반환할 최대 레코드의 수 (페이지네이션).
        tag: 필터링할 챌린지 태그 (ps, img, video).

    Returns:
        조회된 Challenge 객체의 리스트.
    """
    statement = select(Challenge).offset(skip).limit(limit)
    if tag:
        statement = statement.where(Challenge.tag == tag)
    challenges = db.exec(statement).all()
    return list(challenges)


def update_challenge(
    db: Session, challenge_id: int, challenge_in: ChallengeUpdate, user: User
) -> Challenge | None:
    """
    기존 챌린지의 정보를 업데이트합니다.

    - 챌린지 소유자 또는 관리자만 수정할 수 있습니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_id: 수정할 챌린지의 ID.
        challenge_in: 업데이트할 데이터가 담긴 모델.
        user: 요청을 보낸 사용자 객체.

    Returns:
        업데이트된 Challenge 객체. 챌린지가 없거나 권한이 없으면 None을 반환합니다.
    """
    db_challenge = db.get(Challenge, challenge_id)
    if not db_challenge:
        return None

    # 소유권 및 관리자 권한 검사
    if db_challenge.user_id != user.id and not user.is_admin:
        return None

    challenge_data = challenge_in.model_dump(exclude_unset=True)
    for key, value in challenge_data.items():
        setattr(db_challenge, key, value)
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge


def delete_challenge(db: Session, challenge_id: int, user: User) -> Challenge | None:
    """
    지정된 챌린지를 데이터베이스에서 삭제합니다.

    - 챌린지 소유자 또는 관리자만 삭제할 수 있습니다.
    - `cascade` 설정에 따라 관련된 모든 하위 데이터(테스트케이스 등)가 함께 삭제됩니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_id: 삭제할 챌린지의 ID.
        user: 요청을 보낸 사용자 객체.

    Returns:
        삭제된 Challenge 객체. 챌린지가 없거나 권한이 없으면 None을 반환합니다.
    """
    db_challenge = db.get(Challenge, challenge_id)
    if not db_challenge:
        return None

    # 소유권 및 관리자 권한 검사
    if db_challenge.user_id != user.id and not user.is_admin:
        return None

    db.delete(db_challenge)
    db.commit()
    return db_challenge


# =================================================================
# PS Testcase CRUD
# =================================================================


def get_testcase(db: Session, testcase_id: int) -> PSTestcase | None:
    """
    지정된 ID를 가진 테스트케이스를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        testcase_id: 조회할 테스트케이스의 ID.

    Returns:
        조회된 PSTestcase 객체. 없으면 None을 반환합니다.
    """
    return db.get(PSTestcase, testcase_id)


def create_testcase_for_challenge(
    db: Session, db_challenge: Challenge, testcase_in: PSTestcaseCreate
) -> PSTestcase:
    """
    특정 PS 챌린지에 새로운 테스트케이스를 추가합니다.

    Args:
        db: SQLModel 세션 객체.
        db_challenge: 테스트케이스를 추가할 Challenge 객체.
        testcase_in: 생성할 테스트케이스의 데이터 모델.

    Returns:
        생성된 PSTestcase 객체.
    """
    db_testcase = PSTestcase.model_validate(
        testcase_in, update={"challenge_id": db_challenge.id}
    )
    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase


def update_testcase(
    db: Session, db_testcase: PSTestcase, testcase_in: PSTestcaseUpdate
) -> PSTestcase:
    """
    기존 테스트케이스의 정보를 업데이트합니다.

    Args:
        db: SQLModel 세션 객체.
        db_testcase: 업데이트할 기존 PSTestcase 객체.
        testcase_in: 업데이트할 데이터가 담긴 모델.

    Returns:
        업데이트된 PSTestcase 객체.
    """
    testcase_data = testcase_in.model_dump(exclude_unset=True)
    for key, value in testcase_data.items():
        setattr(db_testcase, key, value)
    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase


def delete_testcase(db: Session, db_testcase: PSTestcase):
    """
    지정된 테스트케이스를 데이터베이스에서 삭제합니다.

    Args:
        db: SQLModel 세션 객체.
        db_testcase: 삭제할 PSTestcase 객체.
    """
    db.delete(db_testcase)
    db.commit()
    return


# =================================================================
# Img Challenge CRUD
# =================================================================

def create_img_challenge(
    db: Session,
    challenge_in: ChallengeCreate,
    references_in: List[ImgReferenceCreate],
    user: User,
) -> Challenge:
    """
    새로운 이미지(Img) 챌린지를 데이터베이스에 생성합니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_in: 생성할 챌린지의 데이터 모델.
        references_in: 챌린지에 포함될 참고 이미지 데이터 목록.
        user: 챌린지를 생성하는 사용자 객체.

    Returns:
        생성된 Challenge 객체.
    """
    db_challenge = Challenge.model_validate(challenge_in, update={"user_id": user.id})
    db_img_challenge = ImgChallenge()
    for reference_in in references_in:
        db_reference = ImgReference.model_validate(reference_in)
        db_img_challenge.references.append(db_reference)
    db_challenge.img_challenge = db_img_challenge
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge





# =================================================================
# Img Reference CRUD
# =================================================================


def get_img_reference(db: Session, reference_id: int) -> ImgReference | None:
    """
    지정된 ID를 가진 참고 이미지를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        reference_id: 조회할 참고 이미지의 ID.

    Returns:
        조회된 ImgReference 객체. 없으면 None을 반환합니다.
    """
    return db.get(ImgReference, reference_id)


def create_img_reference_for_challenge(
    db: Session, db_challenge: Challenge, reference_in: ImgReferenceCreate
) -> ImgReference:
    """
    특정 이미지 챌린지에 새로운 참고 이미지를 추가��니다.

    Args:
        db: SQLModel 세션 객체.
        db_challenge: 참고 이미지를 추가할 Challenge 객체.
        reference_in: 생성할 참고 이미지의 데이터 모델.

    Returns:
        생성된 ImgReference 객체.
    """
    db_reference = ImgReference.model_validate(
        reference_in, update={"challenge_id": db_challenge.id}
    )
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def update_img_reference(
    db: Session, db_reference: ImgReference, reference_in: ImgReferenceUpdate
) -> ImgReference:
    """
    기존 참고 이미지의 정보를 업데이트합니다.

    Args:
        db: SQLModel 세션 객체.
        db_reference: 업데이트할 기존 ImgReference 객체.
        reference_in: 업데이트할 데이터가 담긴 모델.

    Returns:
        업데이트된 ImgReference 객체.
    """
    reference_data = reference_in.model_dump(exclude_unset=True)
    for key, value in reference_data.items():
        setattr(db_reference, key, value)
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def delete_img_reference(db: Session, db_reference: ImgReference):
    """
    지정된 참고 이미지를 데이터베이스에서 삭제합니다.

    Args:
        db: SQLModel 세션 객체.
        db_reference: 삭제할 ImgReference 객체.
    """
    db.delete(db_reference)
    db.commit()
    return


# =================================================================
# Video Challenge CRUD
# =================================================================


def create_video_challenge(
    db: Session,
    challenge_in: ChallengeCreate,
    references_in: List[VideoReferenceCreate],
    user: User,
) -> Challenge:
    """
    새로운 비디오(Video) 챌린지를 데이터베이스에 생성합니다.

    Args:
        db: SQLModel 세션 객체.
        challenge_in: 생성할 챌린지의 데이터 모델.
        references_in: 챌린지에 포함될 참고 비디오 데이터 목록.
        user: 챌린지를 생성하는 사용자 객체.

    Returns:
        생성된 Challenge 객체.
    """
    db_challenge = Challenge.model_validate(challenge_in, update={"user_id": user.id})
    db_video_challenge = VideoChallenge()
    for reference_in in references_in:
        db_reference = VideoReference.model_validate(reference_in)
        db_video_challenge.references.append(db_reference)
    db_challenge.video_challenge = db_video_challenge
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge





# =================================================================
# Video Reference CRUD
# =================================================================


def get_video_reference(db: Session, reference_id: int) -> VideoReference | None:
    """
    지정된 ID를 가진 참고 비디오를 조회합니다.

    Args:
        db: SQLModel 세션 객체.
        reference_id: 조회할 참고 비디오의 ID.

    Returns:
        조회된 VideoReference 객체. 없으면 None을 반환합니다.
    """
    return db.get(VideoReference, reference_id)


def create_video_reference_for_challenge(
    db: Session, db_challenge: Challenge, reference_in: VideoReferenceCreate
) -> VideoReference:
    """
    특정 비디오 챌린지에 새로운 참고 비디오를 추가합니다.

    Args:
        db: SQLModel 세션 객체.
        db_challenge: 참고 비디오를 추가할 Challenge 객체.
        reference_in: 생성할 참고 비디오의 데이터 모델.

    Returns:
        생성된 VideoReference 객체.
    """
    db_reference = VideoReference.model_validate(
        reference_in, update={"challenge_id": db_challenge.id}
    )
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def update_video_reference(
    db: Session, db_reference: VideoReference, reference_in: VideoReferenceUpdate
) -> VideoReference:
    """
    기존 참고 비디오의 정보를 업데이트합니다.

    Args:
        db: SQLModel 세션 객체.
        db_reference: 업데이트할 기존 VideoReference 객체.
        reference_in: 업데이트할 데이터가 담긴 모델.

    Returns:
        업데이트된 VideoReference 객체.
    """
    reference_data = reference_in.model_dump(exclude_unset=True)
    for key, value in reference_data.items():
        setattr(db_reference, key, value)
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def delete_video_reference(db: Session, db_reference: VideoReference):
    """
    지정된 참고 비디오를 데이터베이스에서 삭제합니다.

    Args:
        db: SQLModel 세션 객체.
        db_reference: 삭제할 VideoReference 객체.
    """
    db.delete(db_reference)
    db.commit()
    return


def get_ps_challenge_accuracy_rate(db: Session, challenge_id: int) -> float:
    """
    특정 PS 챌린지의 정답률을 '사용자 기준'으로 계산합니다.

    - 정답률 = (정답을 맞춘 고유 사용자 수) / (해당 챌린지를 시도한 고유 사용자 수)

    Args:
        db: SQLModel 세션 객체.
        challenge_id: 정답률을 계산할 챌린지의 ID.

    Returns:
        계산된 정답률 (0.0에서 1.0 사이의 float).
        아무도 챌린지를 시도하지 않았으면 0.0을 반환합니다.
    """


    # 챌린지를 시도한 고유 사용자 수 계산
    total_users_stmt = (
        select(func.count(func.distinct(Share.user_id))).where(
            Share.challenge_id == challenge_id
        )
    )
    total_users_count = db.exec(total_users_stmt).one()

    if total_users_count == 0:
        return 0.0

    # 정답을 맞춘 고유 사용자 수 계산
    correct_users_stmt = (
        select(func.count(func.distinct(Share.user_id)))
        .join(PSShare, Share.id == PSShare.share_id)
        .where(Share.challenge_id == challenge_id)
        .where(PSShare.is_correct)
    )
    correct_users_count = db.exec(correct_users_stmt).one()

    return correct_users_count / total_users_count
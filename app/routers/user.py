# app/routers/user.py
from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.security import create_access_token
from app.crud import user as crud_user
from app.dependency import get_current_user, get_db
from app.models.relations import User
from app.models.serializers import (
    ChallengeTag,
    ImgShareReadWithDetails,
    PSShareReadWithDetails,
    VideoShareReadWithDetails,
    ProfileRead,
    ProfileUpdate,
    Token,
    UserCreate,
    UserPasswordCheck,
    UserRead,
    UserReadWithProfile,
    UserUpdate
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    새로운 사용자를 생성(회원가입)하고 즉시 로그인하여 토큰을 발급합니다.

    - **오류**: 닉네임 또는 이메일이 이미 존재하는 경우 `400 Bad Request` 에러를 반환합니다.
    """
    db_user_by_nickname = crud_user.get_user_by_nickname(db, nickname=user.nickname)
    if db_user_by_nickname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already registered",
        )
    db_user_by_email = crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    created_user = crud_user.create_user(db=db, user=user)
    access_token = create_access_token(subject=created_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    사용자 로그인 및 JWT 액세스 토큰 발급 (OAuth2 호환).

    - **인증**: `username`(이메일)과 `password`로 사용자를 인증합니다.
    - **오류**: 인증에 실패하면 `401 Unauthorized` 에러를 반환합니다.
    """
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    """
    사용자 로그아웃 (클라이언트 측 토큰 삭제 안내).

    - **중요**: 이 엔드포인트는 서버 측에서 토큰을 무효화하지 않습니다.
      JWT는 상태 비저장(stateless) 특성상 서버에서 개별 토큰을 소멸시키기 어렵습니다.
      실제 로그아웃 처리는 클라이언트(브라우저, 앱)에서 저장된 토큰을 안전하게
      삭제하는 방식으로 이루어져야 합니다.
    - **권한**: 로그인된 사용자만 호출할 수 있습니다.
    """
    return {"message": f"User {current_user.nickname} logged out successfully."}


@router.delete("/unregister", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_user(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    현재 로그인된 사용자를 탈퇴 처리합니다.

    - 데이터베이스에서 사용자 및 연관된 모든 정보(프로필, 게시글, 댓글 등)가
      `cascade` 설정에 따라 함께 삭제됩니다.
    - **권한**: 로그인된 사용자 본인만 탈퇴할 수 있습니다.
    """
    crud_user.soft_delete_user(db=db, user=current_user)
    return


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    현재 로그인된 사용자의 기본 정보를 반환합니다. (프로필 제외)

    - **권한**: 로그인된 사용자만 접근할 수 있습니다.
    """
    return current_user


@router.get("/me/details", response_model=UserReadWithProfile)
async def read_current_user_details(current_user: User = Depends(get_current_user)):
    """
    현재 로그인된 사용자의 상세 정보(프로필 포함)를 반환합니다.

    - **권한**: 로그인된 사용자만 접근할 수 있습니다.
    """
    return current_user


@router.put("/me", response_model=UserReadWithProfile)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자의 계정 정보(닉네임, 이메일, 비밀번호)를 수정합니다.

    - **권한**: 로그인된 사용자 본인만 수정할 수 있습니다.
    """
    return crud_user.update_user(db=db, db_user=current_user, user_in=user_in)


@router.put("/me/profile", response_model=ProfileRead)
async def update_current_user_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자의 프로필 정보(자기소개, 관심분야)를 수정합니다.

    - **권한**: 로그인된 사용자 본인만 수정할 수 있습니다.
    - **오류**: 프로필이 존재하지 않는 경우 `404 Not Found` 에러를 반환합니다.
      (정상적인 경우, 사용자 생성 시 프로필이 함께 생성되므로 발생하지 않음)
    """
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    return crud_user.update_profile(db=db, db_profile=profile, profile_in=profile_in)


@router.get("/me/completed-challenges/ps", response_model=List[PSShareReadWithDetails])
async def read_my_completed_ps_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자가 완료한 PS 챌린지 목록을 반환합니다.
    """
    return crud_user.get_user_public_shares(
        db=db, user=current_user, tag=ChallengeTag.ps
    )


@router.get("/me/completed-challenges/img", response_model=List[ImgShareReadWithDetails])
async def read_my_completed_img_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자가 완료한 이미지 챌린지 목록을 반환합니다.
    """
    return crud_user.get_user_public_shares(
        db=db, user=current_user, tag=ChallengeTag.img
    )


@router.get("/me/completed-challenges/video", response_model=List[VideoShareReadWithDetails])
async def read_my_completed_video_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인된 사용자가 완료한 비디오 챌린지 목록을 반환합니다.
    """
    return crud_user.get_user_public_shares(
        db=db, user=current_user, tag=ChallengeTag.video
    )


@router.get("/{user_id}", response_model=UserReadWithProfile)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    특정 ID를 가진 사용자의 공개 프로필 정보(프로필 포함)를 반환합니다.

    - **오류**: 사용자를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return db_user


@router.get("/check-nickname/{nickname}", status_code=status.HTTP_204_NO_CONTENT)
async def check_nickname_availability(nickname: str, db: Session = Depends(get_db)):
    """
    회원가입 시 닉네임 중복 여부를 확인합니다.

    - **성공**: 사용 가능한 닉네임인 경우 `204 No Content`를 반환합니다.
    - **오류**: 이미 사용 중인 닉네임인 경우 `409 Conflict` 에러를 반환합니다.
    """
    db_user = crud_user.get_user_by_nickname(db, nickname=nickname)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Nickname is already in use"
        )
    return


@router.get("/check-email/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def check_email_availability(email: str, db: Session = Depends(get_db)):
    """
    회원가입 시 이메일 중복 여부를 확인합니다.

    - **성공**: 사용 가능한 이메일인 경우 `204 No Content`를 반환합니다.
    - **오류**: 이미 사용 중인 이메일인 경우 `409 Conflict` 에러를 반환합니다.
    """
    db_user = crud_user.get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already in use"
        )
    return


@router.post("/check-password", status_code=status.HTTP_204_NO_CONTENT)
async def check_password(
    password_data: UserPasswordCheck,
    current_user: User = Depends(get_current_user),
):
    """
    현재 로그인된 사용자의 비밀번호를 확인합니다.

    - **성공**: 비밀번호가 일치하는 경우 `204 No Content` 상태 코드를 반환합니다.
    - **실패**: 비밀번호가 일치하지 않는 경우 `422 Unprocessable Entity` 에러를 반환합니다.
    """
    if current_user.password != password_data.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="비밀번호가 틀렸습니다.",
        )
    return


# app/routers/challenge.py
import asyncio
import os
from enum import Enum
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.crud import challenge as crud_challenge
from app.crud import share as crud_share
from app.dependency import get_current_user, get_db
from app.models.relations import User
from app.models.serializers import (
    ChallengeCreate,
    ChallengeLevel,
    ChallengeReadWithDetails,
    ChallengeTag,
    ChallengeUpdate,
    ImgChallengeReadWithDetails,
    ImgReferenceCreate,
    ImgReferenceRead,
    ImgReferenceUpdate,
    ImgShareCreate,
    PSChallengeCreate,
    PSChallengeReadWithDetails,
    PSShareCreate,
    PSTestcaseCreate,
    PSTestcaseRead,
    PSTestcaseUpdate,
    ShareCreate,
    VideoChallengeReadWithDetails,
    VideoReferenceCreate,
    VideoReferenceRead,
    VideoReferenceUpdate,
    VideoShareCreate,
)
from app.utils import gemini
from app.utils.file_handler import save_mp4, save_png, save_upload_file
from app.utils.sandbox.code_runner import score_code

# --- 임시 프롬프트 캐시 ---
# key: (user_id, challenge_id)
# value: 해당 챌린지에서 가장 마지막으로 생성 요청된 프롬프트 (str)
#
# 이 캐시는 /generate 엔드포인트에서 생성된 코드의 프롬프트를 임시 저장하고,
# /score 엔드포인트에서 채점 시 해당 프롬프트를 꺼내어 Share에 기록하는 데 사용됩니다.
# 사용자가 동일한 챌린지에 대해 generate를 여러 번 호출하면 마지막 프롬프트로 덮어쓰여집니다.
prompt_cache_for_ps_challenge: dict[tuple[int, int], str] = {}


router = APIRouter(
    prefix="/challenges",
    tags=["Challenges"],
)


# ——— 챌린지 엔드포인트 ———


@router.post(
    "/ps",
    response_model=PSChallengeReadWithDetails,
    status_code=status.HTTP_201_CREATED,
)
async def create_ps_challenge(
    request: PSChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    새로운 프로그래밍(PS) 챌린지를 생성합니다.

    - **요청 본문**: 챌린지 기본 정보와 테스트케이스 목록을 포함해야 합니다.
    - **권한**: 로그인된 사용자만 생성할 수 있습니다.
    """
    challenge_in = ChallengeCreate.model_validate(request)
    testcases_in = request.testcases
    if challenge_in.tag != ChallengeTag.ps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag must be 'ps' for a PS Challenge.",
        )
    return crud_challenge.create_ps_challenge(
        db=db,
        challenge_in=challenge_in,
        testcases_in=testcases_in,
        user=current_user,
    )


@router.post(
    "/img",
    response_model=ImgChallengeReadWithDetails,
    status_code=status.HTTP_201_CREATED,
)
async def create_img_challenge(
    level: ChallengeLevel = Form(...),
    title: str = Form(...),
    challenge_number: int = Form(...),
    content: Optional[str] = Form(None),
    references: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    새로운 이미지(Img) 챌린지를 생성합니다.

    - **요청 형식**: `multipart/form-data`
    - 챌린지 정보는 Form 데이터 필드로, 참고 이미지는 파일 업로드로 전달받습니다.
    - **권한**: 로그인된 사용자만 생성할 수 있습니다.
    """
    challenge_in = ChallengeCreate(
        tag=ChallengeTag.img,
        level=level,
        title=title,
        content=content,
        challenge_number=challenge_number,
    )

    reference_create_list: List[ImgReferenceCreate] = []
    for file in references:
        if not file.filename:
            continue
        file_path = await save_upload_file(
            upload_file=file,
            filename=file.filename,
            destination="challenges/img_references",
        )
        reference_create_list.append(
            ImgReferenceCreate(file_path=file_path, file_type=file.content_type)
        )

    return crud_challenge.create_img_challenge(
        db=db,
        challenge_in=challenge_in,
        references_in=reference_create_list,
        user=current_user,
    )


@router.post(
    "/video",
    response_model=VideoChallengeReadWithDetails,
    status_code=status.HTTP_201_CREATED,
)
async def create_video_challenge(
    level: ChallengeLevel = Form(...),
    title: str = Form(...),
    challenge_number: int = Form(...),
    content: Optional[str] = Form(None),
    references: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    새로운 비디오(Video) 챌린지를 생성합니다.

    - **요청 형식**: `multipart/form-data`
    - 챌린지 정보는 Form 데이터 필드로, 참고 비디오는 파일 업로드로 전달받습니다.
    - **권한**: 로그인된 사용자만 생성할 수 있습니다.
    """
    challenge_in = ChallengeCreate(
        tag=ChallengeTag.video,
        level=level,
        title=title,
        content=content,
        challenge_number=challenge_number,
    )

    reference_create_list: List[VideoReferenceCreate] = []
    for file in references:
        if not file.filename:
            continue
        file_path = await save_upload_file(
            upload_file=file,
            filename=file.filename,
            destination="challenges/video_references",
        )
        reference_create_list.append(
            VideoReferenceCreate(file_path=file_path, file_type=file.content_type)
        )

    return crud_challenge.create_video_challenge(
        db=db,
        challenge_in=challenge_in,
        references_in=reference_create_list,
        user=current_user,
    )


@router.get("/ps/", response_model=List[PSChallengeReadWithDetails])
async def read_ps_challenges(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    db: Session = Depends(get_db),
):
    """
    프로그래밍(PS) 챌린지 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    """
    return crud_challenge.get_challenges(
        db=db, skip=skip, limit=limit, tag=ChallengeTag.ps
    )


@router.get("/img/", response_model=List[ImgChallengeReadWithDetails])
async def read_img_challenges(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    db: Session = Depends(get_db),
):
    """
    이미지(Img) 챌린지 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    """
    return crud_challenge.get_challenges(
        db=db, skip=skip, limit=limit, tag=ChallengeTag.img
    )


@router.get("/video/", response_model=List[VideoChallengeReadWithDetails])
async def read_video_challenges(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=0, le=100, description="반환할 최대 항목 수"),
    db: Session = Depends(get_db),
):
    """
    비디오(Video) 챌린지 목록을 조회합니다.

    - **페이지네이션**: `skip`과 `limit` 쿼리 파라미터를 사용하여 페이지네이션을 지원합니다.
    """
    return crud_challenge.get_challenges(
        db=db, skip=skip, limit=limit, tag=ChallengeTag.video
    )


@router.get(
    "/{challenge_id}",
    response_model=ChallengeReadWithDetails,
)
async def read_challenge(challenge_id: int, db: Session = Depends(get_db)):
    """
    ID를 기준으로 특정 챌린지의 상세 정보를 조회합니다.

    - PS 챌린지의 경우, 정답률(accuracy_rate)을 추가로 계산하여 반환합니다.
    - **오류**: 챌린지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if db_challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found"
        )

    # 최종 응답으로 사용할 Pydantic 모델을 생성합니다.
    response_data = ChallengeReadWithDetails.model_validate(db_challenge)

    # PS 챌린지인 경우, 응답 모델의 ps_challenge 부분에 정답률을 추가합니다.
    if response_data.ps_challenge:
        accuracy_rate = crud_challenge.get_ps_challenge_accuracy_rate(
            db, challenge_id=challenge_id
        )
        response_data.ps_challenge.accuracy_rate = accuracy_rate

    return response_data


@router.put(
    "/{challenge_id}",
    response_model=ChallengeReadWithDetails,
)
async def update_challenge(
    challenge_id: int,
    challenge_in: ChallengeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    챌린지 정보를 수정합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 수정할 수 있습니다.
    - **오류**: 챌린지를 찾을 수 없거나 권한이 없는 경우 `404 Not Found`를 반환합니다.
    """
    updated_challenge = crud_challenge.update_challenge(
        db=db,
        challenge_id=challenge_id,
        challenge_in=challenge_in,
        user=current_user,
    )
    if not updated_challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found or permission denied",
        )
    return updated_challenge


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 ID의 챌린지를 삭제합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**: 챌린지를 찾을 수 없거나 권한이 없는 경우 `404 Not Found`를 반환합니다.
    """
    deleted_challenge = crud_challenge.delete_challenge(
        db=db, challenge_id=challenge_id, user=current_user
    )
    if not deleted_challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found or permission denied",
        )
    return


# ——— PS 챌린지 테스트케이스 엔드포인트 ———


@router.post(
    "/ps/{challenge_id}/testcases",
    response_model=PSTestcaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_testcase(
    challenge_id: int,
    testcase_in: PSTestcaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 PS 챌린지에 새로운 테스트케이스를 추가합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 추가할 수 있습니다.
    - **오류**:
        - PS 챌린지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or db_challenge.tag != ChallengeTag.ps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PS Challenge not found.",
        )
    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add testcases to this challenge",
        )
    return crud_challenge.create_testcase_for_challenge(
        db=db, db_challenge=db_challenge, testcase_in=testcase_in
    )


@router.put(
    "/ps/{challenge_id}/testcases/{testcase_id}", response_model=PSTestcaseRead
)
async def update_testcase(
    challenge_id: int,
    testcase_id: int,
    testcase_in: PSTestcaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 테스트케이스를 수정합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 수정할 수 있습니다.
    - **오류**:
        - 챌린지 또는 테스트케이스를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update testcases in this challenge",
        )

    db_testcase = crud_challenge.get_testcase(db, testcase_id=testcase_id)
    if not db_testcase or db_testcase.challenge_id != db_challenge.id:
        raise HTTPException(
            status_code=404, detail="Testcase not found in this challenge"
        )

    return crud_challenge.update_testcase(
        db=db, db_testcase=db_testcase, testcase_in=testcase_in
    )


@router.delete(
    "/ps/{challenge_id}/testcases/{testcase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_testcase(
    challenge_id: int,
    testcase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 테스트케이스를 삭제합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**:
        - 챌린지 또는 테스트케이스를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete testcases from this challenge",
        )

    db_testcase = crud_challenge.get_testcase(db, testcase_id=testcase_id)
    if not db_testcase or db_testcase.challenge_id != db_challenge.id:
        raise HTTPException(
            status_code=404, detail="Testcase not found in this challenge"
        )

    crud_challenge.delete_testcase(db=db, db_testcase=db_testcase)
    return


# ——— 이미지 챌린지 참고자료 엔드포인트 ———


@router.post(
    "/img/{challenge_id}/references",
    response_model=ImgReferenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_img_reference(
    challenge_id: int,
    reference_in: ImgReferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 이미지 챌린지에 새로운 참고 이미지를 추가합니다.

    - **참고**: 이 엔드포인트는 파일 경로를 JSON으로 받습니다.
      일반적으로는 파일 업로드를 통해 참고 자료를 추가하는 것이 더 직관적일 수 있습니다.
    - **권한**: 챌린지 생성자 또는 관리자만 추가할 수 있습니다.
    - **오류**:
        - 이미지 챌린지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or db_challenge.tag != ChallengeTag.img:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image Challenge not found.",
        )
    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add references to this challenge",
        )
    return crud_challenge.create_img_reference_for_challenge(
        db=db, db_challenge=db_challenge, reference_in=reference_in
    )


@router.get(
    "/img/{challenge_id}/references/{reference_id}",
    response_model=ImgReferenceRead,
)
async def read_img_reference(
    challenge_id: int,
    reference_id: int,
    db: Session = Depends(get_db),
):
    """
    ID를 기준으로 특정 참고 이미지의 상세 정보를 조회합니다.

    - **오류**: 참고 이미지가 해당 챌린지에 속하지 않거나 찾을 수 없는 경우
      `404 Not Found` 에러를 반환합니다.
    """
    db_reference = crud_challenge.get_img_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != challenge_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image Reference not found in this challenge",
        )
    return db_reference


@router.put(
    "/img/{challenge_id}/references/{reference_id}", response_model=ImgReferenceRead
)
async def update_img_reference(
    challenge_id: int,
    reference_id: int,
    reference_in: ImgReferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 참고 이미지를 수정합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 수정할 수 있습니다.
    - **오류**:
        - 챌린지 또는 참고 이미지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update references in this challenge",
        )

    db_reference = crud_challenge.get_img_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != db_challenge.id:
        raise HTTPException(status_code=404, detail="Image Reference not found")

    return crud_challenge.update_img_reference(
        db=db, db_reference=db_reference, reference_in=reference_in
    )


@router.delete(
    "/img/{challenge_id}/references/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_img_reference(
    challenge_id: int,
    reference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 참고 이미지를 삭제합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**:
        - 챌린지 또는 참고 이미지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete references from this challenge",
        )

    db_reference = crud_challenge.get_img_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != db_challenge.id:
        raise HTTPException(status_code=404, detail="Image Reference not found")

    crud_challenge.delete_img_reference(db=db, db_reference=db_reference)
    return


# ——— 비디오 챌린지 참고자료 엔드포인트 ———
@router.post(
    "/video/{challenge_id}/references",
    response_model=VideoReferenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_video_reference(
    challenge_id: int,
    reference_in: VideoReferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 비디오 챌린지에 새로운 참고 비디오를 추가합니다.

    - **참고**: 이 엔드포인트는 파일 경로를 JSON으로 받습니다.
    - **권한**: 챌린지 생성자 또는 관리자만 추가할 수 있습니다.
    - **오류**:
        - 비디오 챌린지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or db_challenge.tag != ChallengeTag.video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video Challenge not found.",
        )
    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add references to this challenge",
        )
    return crud_challenge.create_video_reference_for_challenge(
        db=db, db_challenge=db_challenge, reference_in=reference_in
    )


@router.get(
    "/video/{challenge_id}/references/{reference_id}",
    response_model=VideoReferenceRead,
)
async def read_video_reference(
    challenge_id: int,
    reference_id: int,
    db: Session = Depends(get_db),
):
    """
    ID를 기준으로 특정 참고 비디오의 상세 정보를 조회합니다.

    - **오류**: 참고 비디오가 해당 챌린지에 속하지 않거나 찾을 수 없는 경우
      `404 Not Found` 에러를 반환합니다.
    """
    db_reference = crud_challenge.get_video_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != challenge_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video Reference not found in this challenge",
        )
    return db_reference


@router.put(
    "/video/{challenge_id}/references/{reference_id}",
    response_model=VideoReferenceRead,
)
async def update_video_reference(
    challenge_id: int,
    reference_id: int,
    reference_in: VideoReferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 참고 비디오를 수정합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 수정할 수 있습니다.
    - **오류**:
        - 챌린지 또는 참고 비디오를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update references in this challenge",
        )

    db_reference = crud_challenge.get_video_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != db_challenge.id:
        raise HTTPException(status_code=404, detail="Video Reference not found")

    return crud_challenge.update_video_reference(
        db=db, db_reference=db_reference, reference_in=reference_in
    )


@router.delete(
    "/video/{challenge_id}/references/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_video_reference(
    challenge_id: int,
    reference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ID를 기준으로 특정 참고 비디오를 삭제합니다.

    - **권한**: 챌린지 생성자 또는 관리자만 삭제할 수 있습니다.
    - **오류**:
        - 챌린지 또는 참고 비디오를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
        - 권한이 없는 경우 `403 Forbidden` 에러를 반환합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if db_challenge.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete references from this challenge",
        )

    db_reference = crud_challenge.get_video_reference(db, reference_id=reference_id)
    if not db_reference or db_reference.challenge_id != db_challenge.id:
        raise HTTPException(status_code=404, detail="Video Reference not found")

    crud_challenge.delete_video_reference(db=db, db_reference=db_reference)
    return


@router.post("/ps/{challenge_id}/generate", response_model=dict)
async def generate_code(
    challenge_id: int,
    prompt: Annotated[str, Body(embed=True, description="코드 생성을 위한 프롬프트")],
    current_user: User = Depends(get_current_user),
):
    """
    주어진 프롬프트를 기반으로 특정 PS 챌린지에 대한 코드를 생성합니다.

    - **권한**: 로그인된 사용자만 코드를 생성할 수 있습니다.
    - **반환 형식**: `{"content": "생성된 코드 내용"}`
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID not found.",
        )
    try:
        response = await gemini.generate_code(prompt)
        # 생성된 코드에 대한 프롬프트를 캐시에 저장
        prompt_cache_for_ps_challenge[(current_user.id, challenge_id)] = prompt
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during code generation: {str(e)}",
        )


# ——— 코드 채점 엔드포인트 ———


class ScoringStatus(str, Enum):
    """코드 채점 결과의 상태를 나타내는 Enum."""

    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    COMPILATION_ERROR = "Compilation Error"
    RUNTIME_ERROR = "Runtime Error"
    TIMEOUT = "Timeout"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"


class ScoringResult(BaseModel):
    """개별 테스트케이스에 대한 채점 결과를 담는 모델."""

    testcase_id: int
    status: ScoringStatus
    stdout: str
    stderr: str
    elapsed_time: float
    max_memory_kb: int | None


@router.post("/ps/{challenge_id}/score", response_model=List[ScoringResult])
async def score_code_and_create_share(
    challenge_id: int,
    code: Annotated[str, Body(embed=True, description="채점할 Python 코드")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    제출된 Python 코드를 PS 챌린지의 모든 테스트케이스에 대해 채점하고, 그 결과를 공유(저장)합니다.

    - 코드는 Docker 샌드박스 환경에서 비동기적으로 실행됩니다.
    - 각 테스트케이스에 대한 실행 결과(성공, 실패, 시간 초과 등)를 리스트로 반환합니다.
    - 채점 후에는 성공 여부와 관계없이 항상 `Share` 및 `PSShare` 레코드를 생성하여 제출 기록을 남깁니다.
    - 모든 테스트케이스를 통과한 경우에만 `is_correct` 필드가 `True`로 설정됩니다.
    - **권한**: 로그인된 사용자만 채점 및 공유가 가능합니다.
    - **오류**: PS 챌린지를 찾을 수 없는 경우 `404 Not Found` 에러를 반환합니다.
    """
    if not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID not found.",
        )

    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or not db_challenge.ps_challenge:
        raise HTTPException(status_code=404, detail="PS Challenge not found")

    testcases = db_challenge.ps_challenge.testcases

    # 각 테스트케이스에 대해 코드 실행을 비동기 태스크로 생성합니다.
    tasks = [
        score_code(
            code=code,
            stdin_data=tc.input or "",
            timeout_seconds=tc.time_limit,
            memory_limit_mb=tc.mem_limit,
        )
        for tc in testcases
    ]
    # 생성된 모든 태스크를 동시에 실행하고 결과를 기다립니다.
    execution_results = await asyncio.gather(*tasks)

    scoring_results = []
    for tc, result in zip(testcases, execution_results):
        if tc.id is None:
            # 정상적인 경우 발생하지 않아야 하는 내부 서버 오류
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: Testcase for input '{tc.input}' is missing an ID.",
            )

        # 코드 실행 결과(error, success)와 정답(tc.output)을 비교하여 채점 상태를 결정합니다.
        status_val = ScoringStatus.WRONG_ANSWER
        if result["error"]:
            try:
                # `run_python_code`에서 반환된 에러 타입(Timeout 등)을 ScoringStatus로 변환
                status_val = ScoringStatus(result["error"])
            except ValueError:
                # 정의되지 않은 에러 타입인 경우 일반적인 런타임 에러로 처리
                status_val = ScoringStatus.RUNTIME_ERROR
        elif result["success"] and result["stdout"].strip() == (
            tc.output or ""
        ).strip():
            status_val = ScoringStatus.ACCEPTED

        scoring_results.append(
            ScoringResult(
                testcase_id=tc.id,
                status=status_val,
                stdout=result["stdout"],
                stderr=result["stderr"],
                elapsed_time=result["elapsed_time"],
                max_memory_kb=result["max_memory_kb"],
            )
        )

    # 모든 테스트케이스를 통과했는지 확인
    all_accepted = all(
        result.status == ScoringStatus.ACCEPTED for result in scoring_results
    )

    # 프롬프트 변수 초기화
    prompt = None
    # 모든 테스트케이스를 통과한 경우에만 캐시에서 프롬프트를 가져옵니다.
    if all_accepted:
        prompt = prompt_cache_for_ps_challenge.pop(
            (current_user.id, challenge_id), None
        )

    # 채점 결과를 데이터베이스에 기록합니다.
    # 정답일 경우에만 공개(is_public=True) 처리합니다.
    # ShareBase 모델에는 is_public을 두어 공개 여부를 결정하고,
    # PSShareBase 모델에는 is_correct를 두어 정답 여부를 결정한다.
    # 이렇게 하면 PSShareBase는 사실상 정/오답 기록용, ShareBase는 공유용으로 분리됨.
    share_in = ShareCreate(
        challenge_id=challenge_id, is_public=all_accepted, prompt=prompt
    )
    ps_share_in = PSShareCreate(code=code, is_correct=all_accepted)
    crud_share.create_ps_share(
        db=db, share_in=share_in, ps_share_in=ps_share_in, user=current_user
    )

    return scoring_results


@router.post(
    "/img/{challenge_id}/generate", response_model=Annotated[str, "생성된 이미지 URL"]
)
async def generate_image_and_create_share(
    challenge_id: int,
    prompt: Annotated[str, Body(embed=True, description="이미지 생성을 위한 프롬프트")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gemini를 사용하여 이미지를 생성하고, 그 결과물을 즉시 공유합니다.

    - 생성된 이미지는 서버에 저장되며, 해당 이미지의 URL이 반환됩니다.
    - **권한**: 로그인된 사용자만 생성이 가능합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or db_challenge.tag != ChallengeTag.img:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This challenge is not an image challenge.",
        )
    try:
        # 1. 이미지 생성 및 저장
        generated_image = await gemini.generate_png_binary(prompt)
        img_url = await save_png(
            image_binary=generated_image,
            filename=f"{current_user.id}_generated_image",
            destination="shares/img_shares",
        )

        # 2. 공유 생성
        share_in = ShareCreate(challenge_id=challenge_id, prompt=prompt)
        img_share_in = ImgShareCreate(img_url=img_url)
        crud_share.create_img_share(
            db=db, share_in=share_in, img_share_in=img_share_in, user=current_user
        )

        return img_url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during image generation or sharing: {str(e)}",
        )


@router.post(
    "/video/{challenge_id}/generate", response_model=Annotated[str, "생성된 비디오 URL"]
)
async def generate_video_and_create_share(
    challenge_id: int,
    prompt: Annotated[str, Body(embed=True, description="비디오 생성을 위한 프롬프트")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gemini를 사용하여 비디오를 생성하고, 그 결과물을 즉시 공유합니다.

    - 생성된 비디오는 서버에 저장되며, 해당 비디오의 URL이 반환됩니다.
    - **권한**: 로그인된 사용자만 생성이 가능합니다.
    """
    db_challenge = crud_challenge.get_challenge(db, challenge_id=challenge_id)
    if not db_challenge or db_challenge.tag != ChallengeTag.video:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This challenge is not a video challenge.",
        )
    try:
        # 1. 비디오 생성 밑 저장
        generated_video = await gemini.generate_mp4_binary(prompt)
        video_url = await save_mp4(
            video_bytes=generated_video,
            filename=f"{current_user.id}_generated_video",
            destination="shares/video_shares",
        )

        # 2. 공유 생성
        share_in = ShareCreate(challenge_id=challenge_id, prompt=prompt)
        video_share_in = VideoShareCreate(video_url=video_url)
        crud_share.create_video_share(
            db=db, share_in=share_in, video_share_in=video_share_in, user=current_user
        )

        return video_url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during video generation or sharing: {str(e)}",
        )

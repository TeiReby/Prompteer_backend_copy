import os
import requests
import json
from pathlib import Path
import time
import random
import re

# --- 설정 ---
BASE_URL = "http://localhost:8000"
INITIALIZER_DIR = Path(__file__).parent
USERS_TO_CREATE = [
    {"nickname": "admin_user1", "email": "admin1@example.com", "password": "adminpassword1", "is_admin": True},
    {"nickname": "admin_user2", "email": "admin2@example.com", "password": "adminpassword2", "is_admin": True},
    {"nickname": "normal_user1", "email": "user1@example.com", "password": "userpassword1"},
    {"nickname": "normal_user2", "email": "user2@example.com", "password": "userpassword2"},
]

from typing import Dict, Any

# --- 도우미 함수 ---

def print_status(message, response):
    """API 응답을 기반으로 성공/실패 메시지를 출력합니다."""
    if 200 <= response.status_code < 300:
        status = "✅ SUCCESS"
        print(f"{message}... {status}")
        return True
    else:
        status = "❌ FAILED"
        error_details = response.text
        print(f"{message}... {status} (Code: {response.status_code})")
        print(f"  - Error: {error_details}")
        return False

def print_verification_result(title: str, data: Any):
    """Verification 결과를 예쁘게 출력합니다."""
    print(f"\n--- ✅ {title} ---")
    if isinstance(data, list):
        for item in data:
            print(json.dumps(item, indent=2, ensure_ascii=False))
    elif isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)



def check_server_status():
    """서버가 실행 중인지 확인"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("🚀 FastAPI 서버가 실행 중입니다. 초기화를 시작합니다.")
            return True
        else:
            print(f"🚨 서버 응답 코드: {response.status_code}. 서버가 정상적으로 실행되고 있는지 확인해주세요.")
            return False
    except requests.ConnectionError:
        print("🚨 서버에 연결할 수 없습니다. FastAPI 서버를 먼저 실행해주세요: uvicorn app.main:app --reload")
        return False

# --- 초기화 단계별 함수 ---

def create_users():
    """초기 사용자 생성 및 토큰 반환"""
    print("\n--- 1. 사용자 생성 시작 ---")
    auth_tokens = {}
    for user_data in USERS_TO_CREATE:
        try:
            response = requests.post(f"{BASE_URL}/users/register", json=user_data)
            is_success = print_status(f"  - 사용자 '{user_data['nickname']}' 생성", response)
            if is_success:
                # 회원가입 시 바로 토큰이 발급되므로 저장
                token = response.json()["access_token"]
                auth_tokens[user_data['nickname']] = token
        except requests.RequestException as e:
            print(f"  - 사용자 '{user_data['nickname']}' 생성 중 예외 발생: {e}")
    return auth_tokens


def create_ps_challenges(token):
    """PS 챌린지 생성"""
    print("\n--- 2. PS 챌린지 생성 시작 ---")
    headers = {"Authorization": f"Bearer {token}"}
    ps_data_path = INITIALIZER_DIR / "PSChallengeData"
    challenge_number = 1
    created_challenge_ids = []

    for challenge_dir in sorted(ps_data_path.iterdir()):
        if not challenge_dir.is_dir():
            continue

        try:
            content_file = next(challenge_dir.glob("ps*.txt"))
            with open(content_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                title = lines[0].strip()
                # PS 문제 제목에서 # 기호와 이모티콘 제거
                if title.startswith('#'):
                    # '#'와 공백들을 제거
                    title = title.lstrip('# ').strip()
                    # 이모티콘 패턴 제거 (유니코드 이모티콘 범위)
                    title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F000-\U0001F02F\U0001F0A0-\U0001F0FF\U0001F100-\U0001F1FF\U0001F200-\U0001F2FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U0001F900-\U0001F9FF]+', '', title).strip()
                content = "".join(lines[1:]).strip()

            testcase_file = next(challenge_dir.glob("testcases*.txt"))
            with open(testcase_file, 'r', encoding='utf-8') as f:
                testcases_raw = f.read().split('---')

            testcases = []
            for tc_raw in testcases_raw:
                if not tc_raw.strip():
                    continue
                parts = tc_raw.strip().split('[OUTPUT]')
                if len(parts) < 2:
                    continue
                input_data = parts[0].replace('[INPUT]', '').strip()
                output_data = parts[1].strip()
                testcases.append({
                    "input": input_data,
                    "output": output_data,
                    "is_hidden": False,
                    "time_limit": 15.0,
                    "mem_limit": 5120,
                })

            payload = {
                "tag": "ps",
                "level": random.choice(["Easy", "Medium", "Hard"]),
                "title": title,
                "content": content,
                "challenge_number": challenge_number,
                "testcases": testcases,
            }

            response = requests.post(f"{BASE_URL}/challenges/ps", headers=headers, json=payload)
            is_success = print_status(f"  - PS 챌린지 '{title}' 생성", response)
            if is_success:
                created_challenge_ids.append(response.json()["id"])
            challenge_number += 1
        except Exception as e:
            print(f"  - PS 챌린지 '{challenge_dir.name}' 생성 중 예외 발생: {e}")
    return created_challenge_ids, challenge_number


def create_media_challenges(token, start_challenge_number):
    """이미지 및 비디오 챌린지 생성"""
    print("\n--- 3. 이미지 & 비디오 챌린지 생성 시작 ---")
    headers = {"Authorization": f"Bearer {token}"}
    challenge_number = start_challenge_number
    created_challenge_ids = {"img": [], "video": []}

    media_types = [
        {"name": "이미지", "tag": "img", "path": "ImgChallengeData"},
        {"name": "비디오", "tag": "video", "path": "VideoChallengeData"},
    ]

    for media_type in media_types:
        media_data_path = INITIALIZER_DIR / media_type["path"]
        for challenge_dir in sorted(media_data_path.iterdir()):
            if not challenge_dir.is_dir():
                continue

            try:
                content_file = challenge_dir / "content.txt"
                with open(content_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 콘텐츠 내용에 맞는 적절한 제목으로 변경
                    if "img1" in str(challenge_dir):
                        title = "공유 오피스 메인 배너 이미지 프롬프트 작성"
                    elif "img2" in str(challenge_dir):
                        title = "파머스 마켓 로컬푸드 매거진용 이미지 프롬프트 작성"  
                    elif "img3" in str(challenge_dir):
                        title = "전기 SUV 광고 Key Visual 이미지 프롬프트 작성"
                    elif "vid1" in str(challenge_dir):
                        title = "사이버펑크 세계관 네오-베리디아 암시장 일러스트 프롬프트 작성"
                    elif "vid2" in str(challenge_dir):
                        title = "사이버펑크 해태 수호신 디지털 아트 프롬프트 작성"
                    elif "vid3" in str(challenge_dir):
                        title = "감성적인 북카페 창가 풍경 일러스트 프롬프트 작성"
                    else:
                        title = lines[0].strip()  # 기본값으로 첫 번째 줄 사용
                    content = "".join(lines[1:]).strip()

                media_file = next(f for f in challenge_dir.iterdir() if f.suffix in ['.png', '.mp4'])

                form_data = {
                    "level": random.choice(["Easy", "Medium", "Hard"]),
                    "title": title,
                    "challenge_number": challenge_number,
                    "content": content,
                }

                with open(media_file, 'rb') as f_media:
                    files = {'references': (media_file.name, f_media, f'image/{media_file.suffix[1:]}' if media_type["tag"] == "img" else f'video/{media_file.suffix[1:]}')}
                    response = requests.post(f"{BASE_URL}/challenges/{media_type['tag']}", headers=headers, data=form_data, files=files)

                is_success = print_status(f"  - {media_type['name']} 챌린지 '{title}' 생성", response)
                if is_success:
                    created_challenge_ids[media_type['tag']].append(response.json()["id"])
                challenge_number += 1
            except Exception as e:
                print(f"  - {media_type['name']} 챌린지 '{challenge_dir.name}' 생성 중 예외 발생: {e}")
    return created_challenge_ids


def create_shares_and_posts(tokens, challenge_ids):
    """챌린지 결과 공유 및 게시글/댓글 생성"""
    print("\n--- 4. 공유, 게시글, 댓글 생성 시작 ---")

    if not all([tokens.get('normal_user1'), tokens.get('normal_user2')]):
        print("  - ⚠️ 일반 사용자 토큰이 없어 이 단계를 건너뜁니다.")
        return

    user1_token = tokens['normal_user1']
    user2_token = tokens['normal_user2']

    # 1. PS 챌린지 정답 제출 -> Share 생성
    if challenge_ids["ps"]:
        try:
            ps_challenge_id = challenge_ids["ps"][0]
            headers = {"Authorization": f"Bearer {user1_token}"}
            solution_code = "a, b = map(int, input().split())\nprint(a + b)"
            payload = {"code": solution_code}
            response = requests.post(f"{BASE_URL}/challenges/ps/{ps_challenge_id}/score", headers=headers, json=payload)
            print_status(f"  - PS 챌린지(ID:{ps_challenge_id}) 결과 공유 생성", response)
        except Exception as e:
            print(f"  - PS 챌린지 결과 공유 생성 중 예외 발생: {e}")

    # 2. 이미지 챌린지 프롬프트 제출 -> Share 생성
    if challenge_ids["img"]:
        try:
            img_challenge_id = challenge_ids["img"][0]
            headers = {"Authorization": f"Bearer {user2_token}"}
            payload = {"prompt": "A cute cat programming on a laptop, digital art"}
            response = requests.post(f"{BASE_URL}/challenges/img/{img_challenge_id}/generate", headers=headers, json=payload)
            print_status(f"  - 이미지 챌린지(ID:{img_challenge_id}) 결과 공유 생성", response)
        except Exception as e:
            print(f"  - 이미지 챌린지 결과 공유 생성 중 예외 발생: {e}")

    # 3. 게시글 생성
    post_id = None
    try:
        headers = {"Authorization": f"Bearer {user1_token}"}
        post_data = {
            "title": "PS 챌린지 질문 있습니다!",
            "content": "1번 문제 시간 초과가 계속 나는데 팁 좀 알려주세요.",
            "type": "question",
            "tag": "ps",
            "attachment_urls": []
        }
        response = requests.post(f"{BASE_URL}/posts/", headers=headers, json=post_data)
        is_success = print_status("  - Q&A 게시글 생성", response)
        if is_success:
            post_id = response.json()["id"]
    except Exception as e:
        print(f"  - 게시글 생성 중 예외 발생: {e}")

    # 4. 댓글 생성
    if post_id:
        try:
            headers = {"Authorization": f"Bearer {user2_token}"}
            comment_data = {
                "content": "입력 방식을 sys.stdin.readline으로 바꿔보시는 건 어떨까요?",
                "post_id": post_id
            }
            response = requests.post(f"{BASE_URL}/posts/{post_id}/comments", headers=headers, json=comment_data)
            print_status(f"  - 게시글(ID:{post_id})에 댓글 생성", response)
        except Exception as e:
            print(f"  - 댓글 생성 중 예외 발생: {e}")


# --- 메인 실행 ---
def main():
    """초기화 스크립트 메인 함수"""
    if not check_server_status():
        return

    # 1. 사용자 생성 및 토큰 획득
    auth_tokens = create_users()
    if not auth_tokens.get("admin_user1"):
        print("\n🚨 관리자 계정 생성에 실패하여 초기화를 중단합니다.")
        return

    admin_token = auth_tokens["admin_user1"]
    time.sleep(1)

    # 2. 챌린지 생성
    ps_challenge_ids, next_challenge_num = create_ps_challenges(admin_token)
    media_challenge_ids = create_media_challenges(admin_token, next_challenge_num)
    all_challenge_ids = {
        "ps": ps_challenge_ids,
        "img": media_challenge_ids.get("img", []),
        "video": media_challenge_ids.get("video", [])
    }

    # 3. 공유 및 게시글 생성
    create_shares_and_posts(auth_tokens, all_challenge_ids)

    print("\n🎉 모든 초기화 작업이 완료되었습니다.")

    # 5. 생성된 정보 검증
    verify_creation(auth_tokens, all_challenge_ids)


def verify_creation(tokens: Dict[str, str], challenge_ids: Dict[str, Any]):
    """생성된 데이터가 API를 통해 정상적으로 조회되는지 검증합니다."""
    print("\n--- 5. 생성된 정보 검증 시작 ---")

    # 검증에 사용할 일반 사용자 토큰
    normal_user_token = tokens.get("normal_user1")
    if not normal_user_token:
        print("  - ⚠️ 일반 사용자 토큰이 없어 검증을 건너뜁니다.")
        return
    
    headers = {"Authorization": f"Bearer {normal_user_token}"}

    # 1. PS 챌린지 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/challenges/ps/", headers=headers)
        if response.status_code == 200:
            print_verification_result("PS 챌린지 목록 조회", response.json())
    except Exception as e:
        print(f"  - PS 챌린지 목록 조회 중 예외 발생: {e}")

    # 2. 첫 번째 PS 챌린지 상세 조회
    if challenge_ids["ps"]:
        try:
            ps_challenge_id = challenge_ids["ps"][0]
            response = requests.get(f"{BASE_URL}/challenges/{ps_challenge_id}", headers=headers)
            if response.status_code == 200:
                print_verification_result(f"PS 챌린지(ID:{ps_challenge_id}) 상세 조회", response.json())
        except Exception as e:
            print(f"  - PS 챌린지 상세 조회 중 예외 발생: {e}")

    # 3. 첫 번째 게시글 및 댓글 조회
    try:
        # 게시글은 1개만 생성되므로 ID 1로 가정
        post_id = 1
        response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=headers)
        if response.status_code == 200:
            print_verification_result(f"게시글(ID:{post_id}) 및 댓글 조회", response.json())
    except Exception as e:
        print(f"  - 게시글 조회 중 예외 발생: {e}")

    # 4. PS 챌린지 공유 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/shares/ps/", headers=headers)
        if response.status_code == 200:
            print_verification_result("PS 챌린지 공유 목록 조회", response.json())
    except Exception as e:
        print(f"  - PS 챌린지 공유 목록 조회 중 예외 발생: {e}")

    print("\n✅ 모든 검증 작업이 완료되었습니다.")


if __name__ == "__main__":
    main()

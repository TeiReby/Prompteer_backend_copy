import sqlite3
from datetime import datetime

def create_video_challenges(db_path='/Users/byunmingyu/Desktop/해커톤/2508Hackathon/run.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        challenges = [
            (
                'video',
                'Easy',
                '1분짜리 브이로그 영상 만들기',
                '일상의 한 순간을 포착하여 1분 길이의 브이로그 스타일 영상을 만드는 프롬프트를 작성해주세요. 예를 들어, 아침 커피를 내리는 과정, 반려견과의 산책, 창 밖의 풍경 등을 담을 수 있습니다.',
                202,
                202,
                1,
                datetime.now(),
                datetime.now(),
            ),
            (
                'video',
                'Medium',
                '영화 예고편 스타일 영상 제작',
                '존재하지 않는 영화의 예고편을 만드는 프롬프트를 작성해주세요. 장르는 자유롭게 선택할 수 있으며 (예: SF, 로맨스, 스릴러), 긴장감 넘치는 장면 전환, 인상적인 대사, 배경 음악에 대한 묘사가 포함되어야 합니다.',
                203,
                203,
                1,
                datetime.now(),
                datetime.now(),
            ),
            (
                'video',
                'Hard',
                '자연 다큐멘터리 오프닝 시퀀스',
                '특정 생태계(예: 아마존 열대우림, 심해, 아프리카 사바나)의 모습을 담은 자연 다큐멘터리의 오프닝 시퀀스 영상을 만드는 프롬프트를 작성해주세요. 웅장한 배경 음악과 함께 다양한 동식물의 모습, 생태계의 역동성을 생생하게 묘사해야 합니다.',
                204,
                204,
                1,
                datetime.now(),
                datetime.now(),
            ),
        ]

        insert_sql = """INSERT INTO challenge (tag, level, title, content, challenge_number, id, user_id, created_at, modified_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        cursor.executemany(insert_sql, challenges)
        conn.commit()

        print(f"{cursor.rowcount}개의 비디오 챌린지를 성공적으로 추가했습니다.")

    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_video_challenges()

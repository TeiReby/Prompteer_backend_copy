import sqlite3

def fix_video_challenge_levels(db_path='/Users/byunmingyu/Desktop/해커톤/2508Hackathon/run.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        updates = {
            202: 'easy',
            203: 'medium',
            204: 'hard'
        }

        for challenge_id, level in updates.items():
            cursor.execute("UPDATE challenge SET level = ? WHERE id = ?", (level, challenge_id))

        conn.commit()
        print(f"{cursor.rowcount}개의 비디오 챌린지 레벨을 성공적으로 수정했습니다.")

    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    fix_video_challenge_levels()

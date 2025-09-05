import sqlite3
import sys

def migrate_specific_challenge(challenge_title, source_db_path='2508Hackathon/run3.db', dest_db_path='2508Hackathon/run.db'):
    """
    특정 챌린지와 그에 연결된 PS 챌린지 및 테스트케이스를
    source_db_path에서 dest_db_path로 마이그레이션합니다.
    """
    source_conn = None
    dest_conn = None
    try:
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()

        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        print(f"'{source_db_path}'와 '{dest_db_path}'에 연결되었습니다.")

        # 1. Challenge 테이블에서 특정 챌린지 찾기
        source_cursor.execute(
            "SELECT id, tag, level, title, content, challenge_number, user_id, created_at, modified_at FROM challenge WHERE title = ?",
            (challenge_title,)
        )
        challenge_data = list(source_cursor.fetchone()) # Convert to list to modify

        if not challenge_data:
            print(f"오류: '{challenge_title}' 챌린지를 '{source_db_path}'에서 찾을 수 없습니다.")
            return

        challenge_id = challenge_data[0]
        challenge_number = challenge_data[5]

        # Handle case where challenge_number is None
        if challenge_number is None:
            challenge_data[5] = challenge_id # Assign challenge_id as challenge_number
            challenge_number = challenge_id
            print(f"경고: 챌린지 '{challenge_title}'의 challenge_number가 None입니다. challenge_id ({challenge_id})로 설정합니다.")

        print(f"'{challenge_title}' (ID: {challenge_id}, Number: {challenge_number}) 챌린지 데이터를 찾았습니다.")

        # Check if Challenge already exists in destination
        dest_cursor.execute(
            "SELECT id FROM challenge WHERE id = ? OR challenge_number = ?",
            (challenge_id, challenge_number)
        )
        existing_challenge = dest_cursor.fetchone()
        if existing_challenge:
            print(f"경고: Challenge (ID: {challenge_id} or Number: {challenge_number})가 '{dest_db_path}'에 이미 존재합니다. 이 챌린지 및 관련 데이터를 건너뜁니다.")
            return

        # 2. PSChallenge 테이블에서 연결된 PS 챌린지 찾기
        source_cursor.execute(
            "SELECT challenge_id FROM pschallenge WHERE challenge_id = ?",
            (challenge_id,)
        )
        ps_challenge_data = source_cursor.fetchone()

        if not ps_challenge_data:
            print(f"경고: '{challenge_title}' 챌린지에 연결된 PSChallenge 데이터가 없습니다. PSChallenge 및 PSTestcase 마이그레이션을 건너뜁니다.")
            # Still try to insert Challenge data if PSChallenge is missing
            try:
                dest_cursor.execute(
                    "INSERT INTO challenge (id, tag, level, title, content, challenge_number, user_id, created_at, modified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    challenge_data
                )
                print(f"Challenge '{challenge_title}' 데이터가 '{dest_db_path}'에 성공적으로 마이그레이션되었습니다.")
                dest_conn.commit()
            except sqlite3.IntegrityError as e:
                print(f"오류: Challenge '{challenge_title}' 데이터 마이그레이션 중 충돌 발생 (이미 존재할 수 있음): {e}", file=sys.stderr)
                dest_conn.rollback()
            return

        print(f"PSChallenge 데이터 (challenge_id: {ps_challenge_data[0]})를 찾았습니다.")

        # 3. PSTestcase 테이블에서 연결된 테스트케이스 찾기
        source_cursor.execute(
            "SELECT id, input, output, time_limit, mem_limit, challenge_id FROM pstestcase WHERE challenge_id = ?",
            (challenge_id,)
        )
        pstestcase_data = source_cursor.fetchall()

        print(f"PSTestcase 데이터 {len(pstestcase_data)}개를 찾았습니다.")

        # 4. 대상 데이터베이스에 데이터 삽입
        # Challenge 데이터 삽입
        dest_cursor.execute(
            "INSERT INTO challenge (id, tag, level, title, content, challenge_number, user_id, created_at, modified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            challenge_data
        )
        print(f"Challenge '{challenge_title}' 데이터가 '{dest_db_path}'에 성공적으로 마이그레이션되었습니다.")

        # PSChallenge 데이터 삽입
        dest_cursor.execute(
            "INSERT INTO pschallenge (challenge_id) VALUES (?)",
            ps_challenge_data
        )
        print(f"PSChallenge 데이터가 '{dest_db_path}'에 성공적으로 마이그레이션되었습니다.")

        # PSTestcase 데이터 삽입
        if pstestcase_data:
            dest_cursor.executemany(
                "INSERT INTO pstestcase (id, input, output, time_limit, mem_limit, challenge_id) VALUES (?, ?, ?, ?, ?, ?)",
                pstestcase_data
            )
            print(f"PSTestcase 데이터 {len(pstestcase_data)}개가 '{dest_db_path}'에 성공적으로 마이그레이션되었습니다.")
        else:
            print("마이그레이션할 PSTestcase 데이터가 없습니다.")

        dest_conn.commit()
        print("마이그레이션 완료. 모든 변경사항이 커밋되었습니다.")

    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}", file=sys.stderr)
        if dest_conn:
            dest_conn.rollback()
            print("모든 변경사항이 롤백되었습니다.", file=sys.stderr)
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()
        print("데이터베이스 연결이 닫혔습니다.")

if __name__ == '__main__':
    # 사용 예시:
    migrate_specific_challenge("두 수의 합 구하기")

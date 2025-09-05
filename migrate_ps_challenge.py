import sqlite3
import sys

def migrate_specific_ps_challenge(source_db_path='run3.db', dest_db_path='run.db'):
    """
    run3.db에서 '두 수의 합 구하기' PS 챌린지와 관련 데이터를 run.db로 마이그레이션합니다.
    - challenge, pschallenge, pstestcase 테이블의 데이터를 이전합니다.
    - challenge_number 충돌을 피하기 위해 새로운 번호를 부여합니다.
    - 이미 존재하는 챌린지인 경우 건너뜁니다.
    """
    source_conn = None
    dest_conn = None
    challenge_title = "두 수의 합 구하기"

    try:
        # 데이터베이스 연결
        source_conn = sqlite3.connect(source_db_path)
        source_conn.row_factory = sqlite3.Row # 컬럼 이름으로 접근 가능하도록 설정
        source_cursor = source_conn.cursor()

        dest_conn = sqlite3.connect(dest_db_path)
        dest_conn.row_factory = sqlite3.Row
        dest_cursor = dest_conn.cursor()

        print(f"소스 DB '{source_db_path}'와 대상 DB '{dest_db_path}'에 연결되었습니다.")
        print(f"'{challenge_title}' PS 챌린지 마이그레이션을 시작합니다.")

        # 1. 대상 DB에 이미 챌린지가 있는지 확인
        dest_cursor.execute("SELECT id FROM challenge WHERE title = ?", (challenge_title,))
        existing_challenge = dest_cursor.fetchone()
        if existing_challenge:
            print(f"  - '{challenge_title}' 챌린지는 대상 DB에 이미 존재하므로 건너뜁니다.")
            # 이미 추가된 챌린지 데이터가 있다면 롤백하지 않고 종료
            dest_conn.commit()
            return

        # 2. 소스 DB에서 해당 챌린지 정보 가져오기
        source_cursor.execute("SELECT * FROM challenge WHERE title = ? AND tag = 'ps'", (challenge_title,))
        challenge_data = source_cursor.fetchone()

        if not challenge_data:
            print(f"  - 소스 DB에서 '{challenge_title}' 챌린지를 찾을 수 없습니다.")
            return
        
        original_challenge_id = challenge_data['id']
        print(f"  - 소스 DB에서 챌린지를 찾았습니다 (원본 ID: {original_challenge_id}).")

        # 3. 대상 DB에서 새로운 challenge_number 결정
        dest_cursor.execute("SELECT MAX(challenge_number) FROM challenge")
        max_num_result = dest_cursor.fetchone()
        max_num = max_num_result[0] if max_num_result and max_num_result[0] is not None else 0
        new_challenge_number = max_num + 1
        print(f"  - 새로운 challenge_number를 {new_challenge_number}로 할당합니다.")

        # 4. challenge 테이블에 데이터 삽입
        challenge_cols = [key for key in challenge_data.keys() if key != 'id']
        challenge_values = list(dict(challenge_data).values())[1:] # id 제외
        challenge_values[challenge_cols.index('challenge_number')] = new_challenge_number

        insert_sql = f"INSERT INTO challenge ({', '.join(challenge_cols)}) VALUES ({', '.join(['?'] * len(challenge_cols))})"
        dest_cursor.execute(insert_sql, challenge_values)
        new_challenge_id = dest_cursor.lastrowid
        print(f"  - 'challenge' 테이블에 데이터 추가 완료 (새 ID: {new_challenge_id}).")

        # 5. pschallenge 데이터 마이그레이션
        source_cursor.execute("SELECT * FROM pschallenge WHERE challenge_id = ?", (original_challenge_id,))
        pschallenge_data = source_cursor.fetchone()
        if pschallenge_data:
            # pschallenge 테이블은 challenge_id 컬럼만 가짐
            dest_cursor.execute("INSERT INTO pschallenge (challenge_id) VALUES (?)", (new_challenge_id,))
            print("  - 'pschallenge' 테이블에 데이터 추가 완료.")

        # 6. pstestcase 데이터 마이그레이션
        source_cursor.execute("SELECT * FROM pstestcase WHERE challenge_id = ?", (original_challenge_id,))
        pstestcase_rows = source_cursor.fetchall()
        if pstestcase_rows:
            testcase_cols = [key for key in pstestcase_rows[0].keys() if key != 'id']
            
            new_testcases = []
            for row in pstestcase_rows:
                new_row_values = list(dict(row).values())[1:] # id 제외
                new_row_values[testcase_cols.index('challenge_id')] = new_challenge_id
                new_testcases.append(tuple(new_row_values))

            insert_sql = f"INSERT INTO pstestcase ({', '.join(testcase_cols)}) VALUES ({', '.join(['?'] * len(testcase_cols))})"
            dest_cursor.executemany(insert_sql, new_testcases)
            print(f"  - 'pstestcase' 테이블에 {len(new_testcases)}개 데이터 추가 완료.")

        # 7. 변경사항 커밋
        dest_conn.commit()
        print("\n마이그레이션 완료. 모든 관련 데이터가 성공적으로 추가되었습니다.")

    except sqlite3.Error as e:
        print(f"데이터베이스 오류가 발생했습니다: {e}", file=sys.stderr)
        if dest_conn:
            dest_conn.rollback()
            print("변경사항이 롤백되었습니다.", file=sys.stderr)
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()
        print("데이터베이스 연결이 닫혔습니다.")

if __name__ == '__main__':
    migrate_specific_ps_challenge()
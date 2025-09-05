import sqlite3
import sys

def migrate_img_challenges(source_db_path='run3.db', dest_db_path='run.db'):
    """
    run3.db에서 tag가 'img'인 챌린지를 run.db로 마이그레이션합니다.
    challenge_number 충돌을 피하기 위해 새로운 번호를 부여합니다.
    """
    source_conn = None
    dest_conn = None
    try:
        # 데이터베이스 연결
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()

        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        print(f"소스 DB '{source_db_path}'와 대상 DB '{dest_db_path}'에 연결되었습니다.")
        print("tag='img'인 챌린지 마이그레이션을 시작합니다.")

        # 1. 대상 DB에서 현재 가장 큰 challenge_number 찾기
        dest_cursor.execute("SELECT MAX(challenge_number) FROM challenge")
        max_num_result = dest_cursor.fetchone()
        # 데이터가 없는 경우를 대비하여 0으로 기본값 설정
        max_num = max_num_result[0] if max_num_result and max_num_result[0] is not None else 0
        print(f"  - 대상 DB의 현재 최대 challenge_number: {max_num}")

        # 2. 소스 DB에서 'img' 태그 챌린지 가져오기
        source_cursor.execute("SELECT * FROM challenge WHERE tag = 'img'")
        img_challenges = source_cursor.fetchall()

        if not img_challenges:
            print("  - 소스 DB에서 'img' 태그를 가진 챌린지를 찾을 수 없습니다.")
            return

        print(f"  - 소스 DB에서 {len(img_challenges)}개의 'img' 챌린지를 찾았습니다. 새로운 번호를 부여하여 추가합니다.")

        # 3. 컬럼 정보 가져오기 (id와 challenge_number를 수정하기 위함)
        source_cursor.execute("PRAGMA table_info('challenge')")
        columns_info = source_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        try:
            id_index = column_names.index('id')
            challenge_number_index = column_names.index('challenge_number')
            title_index = column_names.index('title')
        except ValueError as e:
            print(f"오류: 'challenge' 테이블에서 필수 컬럼({e})을 찾을 수 없습니다.", file=sys.stderr)
            return

        # 4. 새로운 챌린지 데이터 준비
        new_challenges_to_insert = []
        next_challenge_num = max_num + 1

        for row in img_challenges:
            new_row = list(row)
            original_challenge_num = new_row[challenge_number_index]
            
            # 기본 키(id)는 자동으로 생성되도록 None으로 설정
            new_row[id_index] = None
            # 새로운 challenge_number 할당
            new_row[challenge_number_index] = next_challenge_num
            
            new_challenges_to_insert.append(tuple(new_row))
            print(f"  - 준비: '{new_row[title_index]}' (원본 번호: {original_challenge_num}) -> 새 번호: {next_challenge_num}")
            next_challenge_num += 1

        # 5. 데이터 삽입
        insert_columns = [f'"{c}"' for c in column_names]
        placeholders = ', '.join(['?'] * len(column_names))
        insert_sql = f"INSERT INTO challenge ({', '.join(insert_columns)}) VALUES ({placeholders})"
        
        dest_cursor.executemany(insert_sql, new_challenges_to_insert)
        dest_conn.commit()

        print(f"\n마이그레이션 완료. {dest_cursor.rowcount}개의 'img' 챌린지를 성공적으로 추가했습니다.")

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
    migrate_img_challenges()

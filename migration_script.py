import sqlite3
import sys

def migrate_database(source_db_path='run3.db', dest_db_path='run.db'):
    """
    run3.db에서 run.db로 데이터를 마이그레이션합니다.
    'post' 테이블에는 'challenge_id' 컬럼에 기본값 1을 추가합니다.
    마이그레이션 전에 대상 테이블의 모든 데이터를 삭제합니다.
    """
    try:
        # 소스 및 대상 데이터베이스에 연결
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()

        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        print(f"'{source_db_path}'와 '{dest_db_path}'에 연결되었습니다.")

        # 소스 데이터베이스에서 모든 테이블 목록 가져오기 (sqlite 시스템 테이블 제외)
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in source_cursor.fetchall()]
        print(f"마이그레이션할 테이블: {tables}")

        # 각 테이블을 순회하며 데이터 마이그레이션
        for table_name in tables:
            print(f"'{table_name}' 테이블 데이터 마이그레이션 시작...")
            try:
                # 대상 테이블의 기존 데이터 삭제
                print(f"  - '{table_name}' 테이블의 기존 데이터를 삭제합니다.")
                dest_cursor.execute(f"DELETE FROM \"{table_name}\"")
                
                # 소스 테이블에서 모든 데이터 가져오기
                source_cursor.execute(f"SELECT * FROM \"{table_name}\"")
                data_to_migrate = source_cursor.fetchall()

                if not data_to_migrate:
                    print(f"  - '{table_name}' 테이블이 비어있어 건너뜁니다.")
                    continue

                # 소스 테이블의 컬럼 이름 가져오기
                source_cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                source_columns = [col[1] for col in source_cursor.fetchall()]
                
                # 'post' 테이블 특별 처리
                if table_name == 'post':
                    # 새로운 'challenge_id' 컬럼 추가 및 데이터 준비
                    dest_columns = source_columns + ['challenge_id']
                    # 각 행에 기본값 (1) 추가
                    data_with_challenge_id = [row + (1,) for row in data_to_migrate]
                    
                    placeholders = ', '.join(['?'] * len(dest_columns))
                    insert_sql = f"INSERT INTO \"{table_name}\" ({', '.join(dest_columns)}) VALUES ({placeholders})"
                    
                    dest_cursor.executemany(insert_sql, data_with_challenge_id)
                else:
                    # 다른 모든 테이블은 스키마가 동일하다고 가정
                    placeholders = ', '.join(['?'] * len(source_columns))
                    insert_sql = f"INSERT INTO \"{table_name}\" ({', '.join(source_columns)}) VALUES ({placeholders})"
                    
                    dest_cursor.executemany(insert_sql, data_to_migrate)

                print(f"  - '{table_name}'에 {dest_cursor.rowcount}개 행을 성공적으로 마이그레이션했습니다.")

            except sqlite3.Error as e:
                print(f"  - '{table_name}' 테이블 마이그레이션 중 오류 발생: {e}", file=sys.stderr)
                dest_conn.rollback() # 오류 발생 시 해당 테이블의 변경사항 롤백
                continue # 다음 테이블로 계속 진행

        # 대상 데이터베이스에 변경사항 커밋
        dest_conn.commit()
        print("마이그레이션 완료. 모든 변경사항이 커밋되었습니다.")

    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}", file=sys.stderr)
        if 'dest_conn' in locals():
            dest_conn.rollback()
            print("모든 변경사항이 롤백되었습니다.", file=sys.stderr)
    finally:
        # 연결 종료
        if 'source_conn' in locals():
            source_conn.close()
        if 'dest_conn' in locals():
            dest_conn.close()
        print("데이터베이스 연결이 닫혔습니다.")

if __name__ == '__main__':
    # run3.db와 run.db 파일이 스크립트와 동일한 디렉토리에 있는지 확인하세요.
    migrate_database()
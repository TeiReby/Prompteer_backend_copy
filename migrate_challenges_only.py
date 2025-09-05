import sqlite3
import sys

def migrate_challenges_only(source_db_path='run3.db', dest_db_path='run.db'):
    """
    run3.db의 'challenge' 테이블 데이터만 run.db로 마이그레이션합니다.
    UNIQUE 제약 조건 충돌이 발생하면 해당 행의 삽입을 무시합니다.
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

        table_name = 'challenge'
        print(f"'{table_name}' 테이블 마이그레이션을 시작합니다.")

        # 1. 소스 테이블에서 데이터 가져오기
        source_cursor.execute(f"SELECT * FROM \"{table_name}\"")
        data_to_migrate = source_cursor.fetchall()

        if not data_to_migrate:
            print(f"  - 소스 테이블 '{table_name}'이 비어있습니다. 마이그레이션할 데이터가 없습니다.")
            return

        print(f"  - 소스에서 {len(data_to_migrate)}개의 행을 찾았습니다.")

        # 2. 컬럼 이름 가져오기
        source_cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
        columns = [col[1] for col in source_cursor.fetchall()]
        column_str = ', '.join([f'\"{c}\"' for c in columns])
        placeholders = ', '.join(['?'] * len(columns))

        # 3. INSERT OR IGNORE를 사용하여 중복 데이터는 무시하고 삽입
        insert_sql = f"INSERT OR IGNORE INTO \"{table_name}\" ({column_str}) VALUES ({placeholders})"
        
        # 4. 마이그레이션 실행
        dest_cursor.executemany(insert_sql, data_to_migrate)
        
        # 5. 변경사항 커밋 및 결과 보고
        dest_conn.commit()
        
        print(f"  - 마이그레이션 완료. {dest_cursor.rowcount}개의 새로운 행이 삽입되었습니다.")
        print("  - (삽입된 행의 수가 소스 행의 수보다 적다면, 중복된 데이터는 무시된 것입니다.)")

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
    migrate_challenges_only()

# app/core/database.py
from sqlmodel import SQLModel, create_engine

from app.core.config import settings

# 데이터베이스 엔진을 생성합니다.
# create_engine은 애플리케이션 전체에서 한 번만 호출되어야 합니다.
# - `settings.DATABASE_URL`: .env 파일에서 읽어온 데이터베이스 연결 문자열.
# - `echo=True`: 실행되는 SQL 쿼리를 콘솔에 출력하여 디버깅에 용이하게 합니다.
# - `connect_args={"check_same_thread": False}`:
#   SQLite를 사용할 때 필요하며, FastAPI가 여러 스레드에서 데이터베이스와
#   상호작용할 수 있도록 허용합니다. 다른 데이터베이스(예: PostgreSQL)에서는 필요하지 않습니다.
engine = create_engine(
    settings.DATABASE_URL, echo=True, connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """
    SQLModel 모델 메타데이터를 기반으로 데이터베이스에 모든 테이블을 생성합니다.

    이 함수는 애플리케이션 시작 시 호출되어야 합니다.
    `app/models` 디렉터리에서 SQLModel을 상속받는 모든 모델 클래스를 찾아
    그에 해당하는 테이블이 데이터베이스에 존재하지 않으면 생성합니다.
    """
    # `app.models` 모듈이 임포트되는 시점에 SQLModel.metadata에
    # 모든 테이블 정보가 등록되므로, 여기서는 create_all만 호출하면 됩니다.
    SQLModel.metadata.create_all(engine)

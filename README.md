uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh 

데모 run하는 방법
1. 기존 *.db 파일 삭제

2. .env 파일 만들어서 입력
DATABASE_URL=sqlite:///./run.db
GEMINI_API_KEY="google cloud에서 발급받은 키"
SECRET_KEY="openssl rand -base64 32 명령어로 생성한 키"

3. utils/sandbox/로 이동하여 dockerfile 기반 이미지 생성(당연히 docker cli가 있어야겠죠)
docker build -t python-with-time .

4. terminal에 다음 커맨드 입력
uv run uvicorn app.main:app --port 8000 --reload

5. uv run python3 initializer/init.py으로 초기 데이터 생성

6. http://127.0.0.1:8000/docs 에서 문서 조회되는지 확인

pytest 명령어
mocking test
uv run pytest
non-mocking test (비용 발생 주의)
uv run pytest --run-gemini-api

해커톤 이후 TODO
1. SSO 로그인 구현 OR clerk api 활용
2. int id에서 uuid 도입
3. sqlite에서 aws rds로 확장
4. alembic 도입
5. Redis dram 캐싱 설정

### 도움 되는 명령어들

import 관계 정리 명령어
uv run ruff check --fix --extend-select I .

심심할때 해보기
git ls-files | xargs wc -l
git ls-files | xargs wc -c

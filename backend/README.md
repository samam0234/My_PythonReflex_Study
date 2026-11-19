# FastAPI 백엔드

공통 게시판 API의 진입점은 [main.py](main.py)다. 독립 SQLite에 계정·글·댓글을 저장한다. Reflex 화면은 서버 이벤트에서 이 API에 HTTP 요청을 보낸다.

저장소 루트에서 가상환경을 활성화한 뒤 첫 번째 터미널에서 FastAPI를 실행한다.

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8011
```

두 번째 터미널에서는 [루트 README](../README.md)의 Reflex 의존성을 설치한 환경으로 다음을 실행한다.

```powershell
cd demo
reflex db migrate
reflex run
```

[Reflex 게시판](http://localhost:3000/study6/api-board)에서 가입·로그인·글·댓글을 실습한다. [FastAPI API 문서](http://127.0.0.1:8011/api-docs)에서 요청과 응답을 확인할 수 있다.

SQLite 기본 경로는 `backend/board-v1.sqlite3`다. 다른 파일을 쓰려면 FastAPI 프로세스에 `BOARD_V1_DB`를 설정한다. FastAPI 주소를 바꾸면 Reflex 프로세스의 `BOARD_V1_API_URL`도 맞춘다. 이전 경로의 DB를 계속 쓰려면 `BOARD_V1_DB`에 기존 파일의 절대경로를 지정한다.

루트에서 `python -m pytest tests/test_board_v1.py -q`와 `python tools/verify_board_v1.py`로 API 계약과 Chromium 연동을 검증한다. 검증 도구는 임시 DB를 사용한다.

과일 조회 예제도 이 디렉터리에 있다. 루트에서 `python -m uvicorn backend.fruit_api:app --port 8001`로 따로 실행한다.

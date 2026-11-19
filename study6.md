# study6 — SQLModel·Alembic으로 DB CRUD

목표: Reflex 이벤트에서 DB의 생성·조회·수정·삭제를 수행하고 새로고침 후에도 데이터를 보존한다.

실제 구현: [demo/demo/lessons/db_state.py](demo/demo/lessons/db_state.py), [demo/demo/lessons/models.py](demo/demo/lessons/models.py). `demo/`에서 실행 후 `/study6`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

기초 실습은 **DB에 직접 읽고 쓰는 Reflex 이벤트**로 시작한다. 아래 응용에서는 같은 게시판 흐름을 별도 FastAPI 공통 API에 연결한다. 노션의 `rx.Model` 사용 중단 권고(deprecated) 메모를 반영해 `sqlmodel.SQLModel`을 직접 상속한다. `rx.session()`은 요청마다 열고 닫는 DB 작업 범위다.

DB가 원본이고 State 목록은 화면 표시용 사본이다. 쓰기는 `commit`, 갱신된 ID 읽기는 `refresh`, 화면 재조회는 `load_posts`로 처리한다. 세션을 State 필드나 전역 변수로 보관하지 않는다. 스키마 변경은 Alembic 이력으로 관리한다.

## 🛠️ 실기(코드·줄별 설명)

study0의 독립 실습 앱에서 실행할 명령이다.

```powershell
python -m pip install "reflex[db]==0.9.11"
```

`rxconfig.py`의 최소 설정:

```python
import reflex as rx
config = rx.Config(app_name="reflex_lab", db_url="sqlite:///reflex.db")
```

`reflex_lab/models.py`:

```python
from datetime import datetime, timezone
import sqlmodel

class Post(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    created_at: datetime = sqlmodel.Field(default_factory=lambda: datetime.now(timezone.utc))
```

- `datetime`, `timezone`는 UTC 작성 시각을 만든다.
- `sqlmodel`은 모델·필드·쿼리를 제공한다.
- `table=True`는 클래스가 실제 테이블임을 선언한다.
- `id`의 `None`은 저장 전 상태이며 DB가 기본키를 할당한다.
- `title`, `content`, `author`는 문자열 컬럼이다.
- `default_factory`는 각 행을 생성할 때 새 시각을 계산한다.

`reflex_lab/state.py`의 전체 로컬 CRUD 예제다. **인증 전 학습용**이며 다음 단원 전에는 외부에 공개하지 않는다.

```python
from typing import Any
import reflex as rx
from sqlmodel import select
from .models import Post

class DbState(rx.State):
    posts: list[dict[str, str]] = []
    error: str = ""

    @rx.event
    def load_posts(self):
        with rx.session() as session:
            rows = session.exec(select(Post).order_by(Post.created_at.desc(), Post.id.desc())).all()
            self.posts = [
                {"id": str(p.id), "title": p.title, "content": p.content,
                 "author": p.author, "created_at": p.created_at.isoformat()}
                for p in rows
            ]

    @rx.event
    def create_post(self, data: dict[str, Any]):
        title, content = data.get("title", "").strip(), data.get("content", "").strip()
        if not 1 <= len(title) <= 50 or not 1 <= len(content) <= 5000:
            self.error = "제목·본문 길이를 확인하세요."
            return
        with rx.session() as session:
            post = Post(title=title, content=content, author="learner")
            session.add(post)
            session.commit()
            session.refresh(post)
        self.error = ""
        self.load_posts()

    @rx.event
    def rename_post(self, raw_id: str, title: str):
        if not raw_id.isdecimal() or not 1 <= len(title.strip()) <= 50:
            self.error = "ID·제목을 확인하세요."
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None:
                self.error = "없는 글입니다."
                return
            row.title = title.strip()
            session.add(row)
            session.commit()
        self.load_posts()

    @rx.event
    def delete_post(self, raw_id: str):
        if not raw_id.isdecimal():
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is not None:
                session.delete(row)
                session.commit()
        self.load_posts()
```

| 구간 | 줄별 역할 |
|---|---|
| import 3줄 | 상태 API·쿼리·모델을 연결한다. |
| `posts`, `error` | 직렬화 가능한 화면 데이터와 오류를 선언한다. |
| `load_posts`, `with`, `select` | 세션을 열고 최신순·ID순으로 조회한다. |
| dict 각 키 / comprehension | ID·날짜를 문자열로 바꿔 세션 밖에서 쓸 데이터를 만든다. |
| `create_post` 입력·조건 | 저장 전 서버 길이 검증을 한다. |
| `Post`, `add`, `commit`, `refresh` | 새 행을 저장하고 DB 생성 값을 읽는다. |
| `error`, `load_posts` | 성공 표시와 목록을 갱신한다. |
| `rename_post` 조건 / `get` | ID·제목을 검사하고 대상 한 행을 찾는다. |
| `None` 분기 / 대입 / `commit` | 없는 행은 중단하고 있는 행의 제목을 변경한다. |
| `delete_post` / `get` / `delete` | ID를 검증해 대상 행을 삭제한다. |
| 두 메서드의 `load_posts` | 쓰기 후 오래된 화면 사본을 새로 읽는다. |

진입점 `reflex_lab/reflex_lab.py`:

```python
import reflex as rx
from .state import DbState

def index() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.input(name="title", placeholder="제목"),
            rx.input(name="content", placeholder="본문"),
            rx.button("등록", type="submit"),
            on_submit=DbState.create_post,
        ),
        rx.text(DbState.error, role="alert"),
        rx.foreach(DbState.posts, lambda p: rx.hstack(
            rx.text(p["title"]),
            rx.button("제목 수정", on_click=DbState.rename_post(p["id"], "수정한 제목")),
            rx.button("삭제", on_click=DbState.delete_post(p["id"])),
        )),
    )

app = rx.App()
app.add_page(index, on_load=DbState.load_posts)
```

import는 상태를 연결하고, `form`은 생성 데이터를 제출한다. `foreach`는 조회 결과를 표시하며 각 행 버튼이 해당 ID의 수정·삭제 이벤트를 보낸다. 마지막 줄은 최초 조회를 등록한다.

모델이 앱 import 경로에서 읽히는 상태에서 실행한다.

```powershell
reflex db init
reflex db makemigrations --message "create post"
reflex db migrate
reflex run
```

첫 줄은 **Alembic 폴더가 없는 새 앱에서만** 실행한다. 둘째 줄은 변경 파일을 생성하고, 셋째 줄은 이력을 적용한다. 기존 `project/alembic/`를 재초기화하지 않는다. 생성 → 목록 조회 → 제목 수정 → 삭제를 수행하고, 삭제하지 않은 글은 서버 재시작 후에도 남는지 확인한다.

### 공통 게시판 API v1 연동

별도 FastAPI가 SQLite를 소유하고, Reflex 이벤트가 HTTP로 호출하는 응용 실습이다. 기존 과일 API는 별도로 실행할 수 있다. API 구현·화면·검증은 다음 파일에 있다. [FastAPI](backend/main.py) · [Reflex 화면](demo/demo/lessons/api_board.py) · [계약 테스트](tests/test_board_v1.py)

```powershell
python -m pip install -r backend/requirements.txt
python -m pytest tests/test_board_v1.py -q
python tools/verify_board_v1.py
```

첫 줄은 이번 응용에 필요한 서버만 추가한다. 둘째 줄은 임시 DB에서 API 계약을 검사한다. 셋째 줄은 FastAPI와 Reflex를 별도 프로세스로 띄우고 8001번 Reflex 백엔드와 임시 API 포트로 브라우저 연동을 검사한 뒤 종료한다.

직접 사용하려면 저장소 루트에서 `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8011`을 실행한다. 다른 터미널에서 `demo/`로 이동한 뒤 `reflex db migrate`와 `reflex run`을 실행한다. 화면은 `http://localhost:3000/study6/api-board`, OpenAPI 문서는 `http://127.0.0.1:8011/api-docs`다. 기본 DB 파일은 `backend/board-v1.sqlite3`이며 `BOARD_V1_DB`로 바꿀 수 있다. Reflex는 `BOARD_V1_API_URL`로 API 주소를 읽는다.

```python
result = await self._request(
    "GET", "/api/posts", params={"q": self.query, "page": self.page, "limit": 10}
)
if result is not None:
    self.rows = result["data"]
    self.total_pages = result["meta"]["totalPages"]
```

첫 호출은 검색어와 1부터 시작하는 페이지를 보낸다. 성공하면 `data`로 목록을 그리고 `meta.totalPages`로 이동 범위를 정한다. 글 수정은 `PATCH`, 삭제는 본문 없는 204, 글 생성은 201과 `Location`을 사용한다. 로그인은 한 시간짜리 Bearer 토큰을 받고 Reflex의 서버 전용 State에 둔다. API가 토큰·작성자를 다시 확인하므로 비로그인 작성은 401, 타인 글 변경은 403이다. 오류 본문의 `requestId`와 응답 헤더 `X-Request-Id`도 대조한다. [공통 API 명세](https://app.notion.com/p/3d6d7dec5e2e8139adbfd36dd506c65e)

현재 실습의 FastAPI는 이 저장소에서 독립 실행하는 v1 서버다. 기존 FastAPI 학습 저장소의 `/posts`·`PUT`·폼 로그인 API는 별도 구현으로 유지한다. 이 실습 서버는 루프백에서 공부용으로 실행하며 최종 운영 게시판은 `project/`에 있다.

## 오류 노트

- `no such table`: 모델 import 여부, migration 생성·적용 여부, DB 상대 경로를 확인한다.
- 날짜 직렬화 오류: ORM 객체 자체를 State로 넘기지 않고 `isoformat()` 등으로 변환한다.
- `database is locked`: 긴 트랜잭션·동시 쓰기를 확인한다. 네트워크 대기 중 DB 세션을 잡아두지 않는다.
- 실패한 트랜잭션을 계속 재사용하지 않는다. 컨텍스트 종료로 정리하고 사용자 오류와 서버 로그를 분리한다.

## ☐ 체크리스트

- ☐ [노션 설치 메모] `rx.Model` 대신 `SQLModel`을 직접 상속한다.
- ☐ [노션 코드 2] `rx.session`, 최신순 조회, 날짜 문자열 변환을 확인한다.
- ☐ [노션 학습 목표] 이벤트 핸들러로 CRUD 네 동작을 수행한다.
- ☐ [노션 학습 기록] Alembic 이력을 생성·검토·적용한다.
- ☐ 서버 재시작 뒤 DB 데이터가 유지되는지 확인한다.
- ☐ [노션 조합 과제] FastAPI의 가입·로그인·목록·상세·작성·수정·삭제·댓글을 Reflex 화면에서 연결하고 401·403과 1부터 시작하는 페이지를 검증한다.

## 다음 단계 연결

[study7](study7.md)에서 CRUD 이벤트마다 로그인·작성자 권한을 검사한다.

참고: [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/), [Reflex DB 개요](https://reflex.dev/docs/database/overview/).

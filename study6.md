# study6 — SQLModel·Alembic으로 DB CRUD

목표: Reflex 이벤트에서 DB의 생성·조회·수정·삭제를 수행하고 새로고침 후에도 데이터를 보존한다.

실제 구현: [demo/demo/lessons/db_state.py](demo/demo/lessons/db_state.py), [demo/demo/lessons/models.py](demo/demo/lessons/models.py). `demo/`에서 실행 후 `/study6`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

이 단원은 사용자 요청의 “DB 또는 외부 API” 중 **DB**를 선택한다. 별도 웹 프레임워크를 만들지 않는다. 노션의 `rx.Model` 사용 중단 권고(deprecated) 메모를 반영해 `sqlmodel.SQLModel`을 직접 상속한다. `rx.session()`은 요청마다 열고 닫는 DB 작업 범위다.

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
- ☐ 노션의 외부 프레임워크 API 연결 과제는 [README 범위 기록](README.md#노션-요구사항-대응표)에서 제외 사유를 확인한다.

## 다음 단계 연결

[study7](study7.md)에서 CRUD 이벤트마다 로그인·작성자 권한을 검사한다.

참고: [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/), [Reflex DB 개요](https://reflex.dev/docs/database/overview/).

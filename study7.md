# study7 — 로그인·세션·권한의 기초

목표: 학습용 로그인을 만들고 페이지 진입과 DB 변경 양쪽에 권한 검사를 둔다.

실제 구현: [demo/demo/lessons/auth.py](demo/demo/lessons/auth.py), [demo/demo/lessons/auth_page.py](demo/demo/lessons/auth_page.py). `demo/`에서 실행 후 `/study7`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

인증은 누구인지 확인하고, 인가는 그 사용자가 해당 글을 바꿔도 되는지 확인한다. 수정 버튼 숨기기는 UI 처리이며 서버 권한 검사를 대신하지 않는다. 작성자 이름은 입력 폼에서 받지 않고 서버가 확인한 사용자에서 정한다.

Reflex 연결 식별자는 사용자 인증 토큰과 같지 않다. 아래는 서버 State에만 로그인 이름을 둔 **학습용 세션**이다. 재시작·상태 만료 시 다시 로그인한다. 노션·기존 `project/`도 데모 계정 딕셔너리 방식이다. 운영용 DB 사용자·비밀번호 해시·만료·폐기는 study16에서 구현한다.

## 🛠️ 실기(코드·줄별 설명)

study6의 인증 전 `DbState`를 아래 **독립된 AuthState로 교체**하는 학습 예제다. 이전의 무인증 CRUD State를 함께 import·등록해 두지 않는다. 진입점도 `DbState` 대신 `AuthState`를 사용한다. 아래 코드는 `state.py` 전체 예제다.

```python
from typing import Any
import reflex as rx
from .models import Post
from sqlmodel import select

DEMO_USERS = {"demo": "reflex123", "guest": "guest123"}

class AuthState(rx.State):
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

    _username: str = ""
    login_error: str = ""

    @rx.var
    def username(self) -> str:
        return self._username

    @rx.event
    def login(self, data: dict[str, Any]):
        name, password = data.get("username", "").strip(), data.get("password", "")
        if name not in DEMO_USERS or DEMO_USERS[name] != password:
            self.login_error = "아이디 또는 비밀번호를 확인하세요."
            return
        self._username = name
        self.login_error = ""
        return rx.redirect("/")

    @rx.event
    def logout(self):
        self._username = ""
        return rx.redirect("/login")

    @rx.event
    def require_login(self):
        if not self._username:
            return rx.redirect("/login")

    @rx.event
    def create_post(self, data: dict[str, Any]):
        if not self._username:
            return rx.redirect("/login")
        title, content = data.get("title", "").strip(), data.get("content", "").strip()
        if not 1 <= len(title) <= 50 or not 1 <= len(content) <= 5000:
            self.error = "제목·본문 길이를 확인하세요."
            return
        with rx.session() as session:
            session.add(Post(title=title, content=content, author=self._username))
            session.commit()
        self.load_posts()

    @rx.event
    def rename_post(self, raw_id: str, title: str):
        if not self._username:
            return rx.redirect("/login")
        if not raw_id.isdecimal() or not 1 <= len(title.strip()) <= 50:
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None or row.author != self._username:
                self.error = "수정할 수 없습니다."
                return
            row.title = title.strip()
            session.add(row)
            session.commit()
        self.load_posts()

    @rx.event
    def delete_post(self, raw_id: str):
        if not self._username:
            return rx.redirect("/login")
        if not raw_id.isdecimal():
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None or row.author != self._username:
                self.error = "삭제할 수 없습니다."
                return
            session.delete(row)
            session.commit()
        self.load_posts()
```

로그인은 데모 계정을 비교하며 비밀번호를 공개 State에 저장하지 않는다.

| 코드 구간 | 줄별 설명 |
|---|---|
| import / 데모 dict | 기존 모델·조회 쿼리를 사용하고 로컬 테스트 계정을 정의한다. |
| `posts`, `error`, `load_posts` | DB 조회 결과를 화면용 문자열 dict로 만든다. |
| `_username`, `login_error` | 서버 전용 인증 상태와 사용자 오류를 분리한다. |
| `@rx.var`, `username` | 표시할 이름만 공개 파생 값으로 제공한다. |
| `login` 입력 / 조건 / 대입 | 자격을 검증한 뒤 서버 상태를 변경한다. |
| `logout` | 서버 인증 상태를 폐기한다. |
| `require_login` | 보호 페이지의 진입을 제한한다. |
| CRUD 첫 조건 | 이벤트 직접 호출에도 로그인을 재확인한다. |
| `author=self._username` | 작성자를 서버에서 결정한다. |
| `get`, `row.author` 조건 | DB 원본으로 소유권을 확인한다. |
| `commit`, `load_posts` | 승인된 변경만 저장하고 화면을 갱신한다. |

로그인 페이지 함수와 등록 예제는 진입점에서 `AuthState` import 후 추가한다.

```python
def login_page() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.input(name="username", placeholder="아이디"),
            rx.input(name="password", type="password", placeholder="비밀번호"),
            rx.button("로그인", type="submit"),
            on_submit=AuthState.login,
            reset_on_submit=True,
        ),
        rx.text(AuthState.login_error, role="alert"),
    )

app.add_page(login_page, route="/login")
```

`name` 두 개가 제출 키를 정하고 `type="password"`는 화면 표시만 가린다. TLS가 전송 보호를 담당한다. `on_submit`으로 로그인하고 제출 후 입력을 비운다. 보호 페이지 등록 시에는 `on_load=AuthState.require_login`을 지정한다.

## 오류 노트

- 이름만 일치한다고 로그인시키면 안 된다. 비밀번호가 틀리거나 없는 계정이면 동일한 일반 오류를 표시한다.
- `on_load` 가드만 두면 이벤트 직접 호출이 남는다. 세 변경 이벤트에 모두 가드가 있어야 한다.
- 운영에서 평문 데모 dict를 사용하지 않는다. 실제 계정은 study16의 DB·해시·만료 세션으로 전환한다.
- `rx.Cookie`나 LocalStorage의 임의 사용자 ID를 신뢰하지 않는다. HttpOnly 쿠키로 자동 간주하지도 않는다.

## ☐ 체크리스트

- ☐ [노션 로그인 메모] 데모 로그인과 실제 서비스의 DB·비밀번호 해시 요구를 구분한다.
- ☐ [노션 코드 3] 수정·삭제 전 DB에서 작성자를 다시 확인한다.
- ☐ [노션 보호 페이지] 비로그인 URL 직접 접근과 이벤트 직접 호출을 차단한다.
- ☐ demo 계정 글을 guest가 수정·삭제하지 못하는지 확인한다.
- ☐ 로그아웃 후 이전 수정 이벤트도 거부되는지 확인한다.
- ☐ 로그인 자격증명을 공개 State·로그에 저장하지 않는다.

## 다음 단계 연결

[study8](study8.md)에서 인증·DB·UI 책임과 환경설정을 분리한다.

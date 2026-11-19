# studyMidpoint — 기초 로그인 게시판 완성

목표: study0~10 기능만으로 로그인·페이지 분리·SQLModel CRUD를 완성한다.

## 📖 이론

### 기능 목록

| 기능 | 경로 | 단원 |
|---|---|---|
| 목록·빈 목록·최신순 | `/` | study2·3·6 |
| 데모 로그인·로그아웃 | `/login` | study5·7 |
| 상세 | `/post/[post_id]` | study4 |
| 작성 | `/post/new` | study5·6·7 |
| 작성자만 수정·삭제 | `/post/[post_id]/edit` | study6·7 |
| DB·설정·실행 | SQLite·Alembic·rxconfig | study6·8·10 |

구현 위치는 [midpoint/](midpoint/)다. 고급 계정·AI·캐시·CI를 끌어오지 않고 기초 구간의 서버 전용 데모 로그인·일반 검증·SQLModel 세션을 사용한다.

### 폴더 구조

```text
midpoint/
├── rxconfig.py
├── requirements.txt
├── alembic/versions/
└── midpoint/
    ├── midpoint.py
    ├── models.py
    ├── validation.py
    ├── state.py
    ├── components/post_card.py, post_form.py
    └── pages/index.py, login.py, post_detail.py, post_new.py, post_edit.py
```

## 🛠️ 실기(코드·줄별 설명)

### 구현 순서

1. [모델](midpoint/midpoint/models.py)에 Post와 UTC 작성 시각을 정의한다.
2. [validation.py](midpoint/midpoint/validation.py)에서 제목 1~50자·본문 1~5000자를 검사한다.
3. [State](midpoint/midpoint/state.py)에 서버 전용 `_username`과 로그인 제출 이벤트를 둔다.
4. DB를 조회해 화면용 dict로 바꾸고 `rx.cond`·`rx.foreach`로 그린다.
5. 아래 다섯 페이지를 등록한다.
6. 작성·수정·삭제마다 서버에서 로그인·DB 작성자를 다시 확인한다.
7. 기본 테스트와 prod 브라우저 흐름을 실행한다.

실제 진입점:

```python
import reflex as rx

from .pages.index import index
from .pages.login import login_page
from .pages.post_detail import post_detail
from .pages.post_edit import post_edit_page
from .pages.post_new import post_new_page
from .state import State

app = rx.App()
app.add_page(index, route="/", on_load=State.load_posts)
app.add_page(login_page, route="/login")
app.add_page(post_detail, route="/post/[post_id]", on_load=State.load_posts)
app.add_page(post_new_page, route="/post/new", on_load=State.prepare_new_post)
app.add_page(post_edit_page, route="/post/[post_id]/edit", on_load=State.prepare_edit_post)
```

import는 페이지와 State를 연결한다. `App` 하나를 만들고 목록·상세에는 조회 이벤트, 작성·수정에는 인증·폼 준비 이벤트를 등록한다.

State 내부의 수정·삭제 메서드 발췌:

```python
@rx.event
def update_post(self):
    if not self._username:
        return rx.redirect("/login")
    if not self._validate_form():
        return
    post_id = self._id()
    if post_id is None:
        return
    with rx.session() as session:
        post = session.get(Post, post_id)
        if post is None or post.author != self._username:
            self.form_error = "수정할 수 없습니다."
            return
        post.title, post.content = self.form_title.strip(), self.form_content.strip()
        session.add(post)
        session.commit()
    self.load_posts()
    return rx.redirect(f"/post/{post_id}")

@rx.event
def delete_post(self, post_id: int):
    if not self._username:
        return rx.redirect("/login")
    with rx.session() as session:
        post = session.get(Post, post_id)
        if post is None or post.author != self._username:
            self.form_error = "삭제할 수 없습니다."
            return
        session.delete(post)
        session.commit()
    self.load_posts()
    return rx.redirect("/")
```

- 첫 조건은 UI를 우회한 이벤트에도 로그인을 다시 요구한다.
- 수정은 공통 검증과 URL ID 변환을 먼저 수행한다.
- `session.get` 뒤 DB 원본 작성자와 backend 사용자 이름을 비교한다.
- 승인한 행만 변경·commit하며 목록 갱신 후 알맞은 URL로 이동한다.
- 비밀번호는 제출 인자로만 받고 공개 State에 보관하지 않는다.

```powershell
cd midpoint
python -m pip install -r requirements.txt
reflex db migrate
reflex run
```

`http://localhost:3000/login`에서 `demo / reflex123`, `guest / guest123`으로 시험한다. 실제 구현의 로그인을 확인하는 **로컬 학습용 계정**이다. 운영용 계정·해시는 study16과 `project/`에 있다.

저장소 루트의 검증 명령:

```powershell
python -m pytest tests/test_midpoint_validation.py -q
python tools/verify_app.py --app midpoint --mode prod
```

격리 도구는 실제 DB를 건드리지 않고 새 DB와 포트를 준비한다. 브라우저에서 익명 접근 차단→오답 로그인→정상 로그인→작성→새로고침→guest 직접 수정 접근 거부→소유자 수정·삭제→로그아웃을 확인한다.

## 오류 노트

- 기존 인증 전 State를 함께 import해 무인증 CRUD 경로를 남기지 않는다.
- 수정 버튼 숨김만으로 권한 검사를 끝내지 않는다.
- 잘못된 URL 숫자는 `_id()`로 처리하고 예외를 화면에 노출하지 않는다.
- State 재시작 후 재로그인은 허용되지만 DB 글 유실은 허용되지 않는다.

## ☐ 체크리스트

- ☐ [노션 예제] Reflex 단독 게시판의 다섯 페이지·CRUD·로그인을 완성한다.
- ☐ [노션 코드 1~4] on_load·SQLModel·작성자 확인·cond/foreach를 코드에서 찾는다.
- ☐ 공백·경계값·비정상 ID·없는 글을 처리한다.
- ☐ guest·비로그인·로그아웃 뒤의 변경을 거부한다.
- ☐ DB 저장·새로고침·기초 테스트·prod 브라우저 검증 결과를 기록한다.
- ☐ 회고: State/Var 오류의 원인과 서버 권한 검사 위치를 적는다.
- ☐ 회고: 데모 인증의 한계와 study16에서 바꿀 항목을 설명한다.

## 다음 단계 연결

[study11](study11.md)부터 이 구조의 심화 기능을 익히고 [studyFinal](studyFinal.md)의 `project/`에 적용한다.

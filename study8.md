# study8 — 구조화·재사용·환경변수 분리

목표: 실제 게시판에서 페이지·State·모델·공통 컴포넌트·설정을 분리한다.

실제 구현: [midpoint/](midpoint/), [심화 설정](project/project/settings.py), [최종 rxconfig](project/rxconfig.py). 설치·실행은 [README](README.md)를 따른다.

## 📖 이론

페이지는 표시, State는 입력·이벤트·화면 상태, 모델은 저장 구조, 공통 컴포넌트는 반복 UI를 담당한다. 같은 폼을 복사하면 검증·오류·권한 처리가 달라질 수 있으므로 작성·수정에서 재사용한다.

기초 앱은 다음 실제 구조를 사용한다. 심화 구간은 `project/project/services/`, `schemas.py`, `settings.py`로 책임을 더 나눈다.

```text
midpoint/
├── rxconfig.py
├── requirements.txt
├── .env.example
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

실제 기초 앱 설정:

```python
import os

import reflex as rx
from reflex.constants import StateManagerMode

config = rx.Config(
    state_manager_mode=StateManagerMode.MEMORY,
    app_name="midpoint",
    db_url=os.getenv("REFLEX_DB_URL", "sqlite:///midpoint.db"),
    api_url=os.getenv("REFLEX_API_URL", "http://localhost:8000"),
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
```

- `os`는 앱의 DB·API 환경변수를 읽는다.
- `app_name`은 패키지와 진입점 이름 `midpoint`를 선택한다.
- `state_manager_mode`는 MEMORY를 명시해 서버 상태와 영속 DB를 구분한다.
- `db_url`은 SQLite 파일을, `api_url`은 브라우저의 서버 접속 주소를 정한다.
- `cors_allowed_origins`는 허용 출처다. 운영의 `*` 허용을 사용하지 않는다.
- 플러그인은 Sitemap·Tailwind·Radix 스타일을 생성한다. 생성된 `.web/`를 직접 편집하지 않는다.

앱 루트 PowerShell에서 환경변수를 주입한다.

```powershell
$env:REFLEX_DB_URL = "sqlite:///midpoint.db"
$env:REFLEX_API_URL = "http://localhost:8000"
reflex run
```

두 대입은 현재 프로세스와 자식에게 적용하고 run이 읽는다. 포트를 바꾸면 API URL·허용 화면 origin도 맞춘다. `REFLEX_CORS_ALLOWED_ORIGINS`는 쉼표 구분 문자열이며 JSON 배열 문자열을 넣지 않는다.

실제 공통 폼:

```python
import reflex as rx

from ..state import State


def post_form(submit_label: str, on_submit) -> rx.Component:
    """새 글 작성/수정 페이지가 공유하는 폼. study5·8에서 배운 컴포넌트
    분리 + 서버 측 검증 패턴을 그대로 적용했다."""
    return rx.vstack(
        rx.input(
            placeholder="제목 (최대 50자)",
            name="title",
            max_length=50,
            value=State.form_title,
            on_change=State.set_form_title,
            width="100%",
        ),
        rx.text_area(
            placeholder="내용",
            name="content",
            max_length=5000,
            value=State.form_content,
            on_change=State.set_form_content,
            width="100%",
            rows="10",
        ),
        rx.cond(
            State.form_error != "",
            rx.text(State.form_error, color="red", size="2"),
        ),
        rx.button(submit_label, on_click=on_submit),
        spacing="3",
        width="100%",
        max_width="480px",
    )
```

- import는 UI와 State를 연결한다. 컴포넌트에서 App을 import하지 않는다.
- `submit_label`, `on_submit`은 호출자가 전달하는 버튼 문구와 저장 콜백이다.
- 제목·본문은 State의 입력 필드와 명시적 setter에 연결한다.
- `name`, 길이 제한은 필드 식별·입력 보조다. 서버는 별도 검증을 수행한다.
- `form_error`는 같은 오류 영역에 표시한다.
- `rx.button(..., on_click=on_submit)`은 저장 이벤트를 연결한다. 여기서 `on_submit`은 함수 인자 이름이며 `rx.form`의 제출 이벤트와 구분한다.
- 작성·수정 페이지는 `post_form("작성 완료", State.create_post)`, `post_form("수정 완료", State.update_post)`로 같은 함수를 사용한다.

심화 앱의 [settings.py](project/project/settings.py)는 `.env`를 명시적으로 로드하고 APP_* 변수를 해석한다. 운영에서는 HTTPS·origin을 검사한다. 실제 `.env`는 git 제외하고 예시 파일에는 가짜 값·변수명만 둔다.

## 오류 노트

- `pages → state → services/models` 방향을 지킨다. 하위 컴포넌트에서 App을 import하면 순환 참조가 생긴다.
- 개발 localhost를 외부 빌드에 넣으면 사용자 컴퓨터를 가리킨다. 배포 URL로 재빌드한다.
- `.env.example` 복사만으로 모든 임의 변수가 자동 로드되는 것은 아니다. 실제 설정 로더를 확인한다.
- 설정·플러그인 변경 후 프로세스를 재시작하고 필요한 프론트 자산을 재빌드한다.
- DB URL·키 원문을 디버그 로그로 출력하지 않는다.

## ☐ 체크리스트

- ☐ [노션 페이지 분리] 목록·로그인·작성·수정과 공통 폼의 책임을 구분한다.
- ☐ 작성·수정이 같은 검증 함수와 공통 폼을 사용한다.
- ☐ [노션 환경변수] DB·브라우저 API URL·허용 origin을 환경별로 분리한다.
- ☐ [노션 포트 경험] 포트 충돌 시 서버 포트와 접속 주소를 함께 수정한다.
- ☐ MEMORY State·영속 DB·공개 설정·비밀 값을 구분한다.
- ☐ 실제 환경 파일·비밀번호·토큰을 git·이미지·로그에서 제외한다.

## 다음 단계 연결

[study9](study9.md)에서 분리한 순수 검증 함수와 실제 사용자 흐름을 테스트한다.

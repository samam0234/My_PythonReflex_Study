# study2 — 컴포넌트·모듈·앱의 핵심 구조

목표: 재사용 컴포넌트를 모듈로 분리하고 App의 페이지 등록까지 연결한다.

실제 구현: [demo/demo/components/notice.py](demo/demo/components/notice.py), [demo/demo/lessons/structure.py](demo/demo/lessons/structure.py). `demo/`에서 실행 후 `/study2`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

Reflex의 기본 UI 단위는 컴포넌트다. Python 함수로 여러 컴포넌트를 조합하면 재사용 단위가 된다. 모듈은 `.py` 파일, 패키지는 `__init__.py`를 가진 디렉터리, 앱은 `rx.App` 객체다. 페이지도 컴포넌트를 반환하는 함수지만 URL 등록이라는 역할이 추가된다.

컴포넌트는 필요한 값만 인자로 받게 한다. 데이터 조회·저장과 로그인 여부 판단은 State·서비스에서 수행한다. 고정 Python 데이터에 대한 `if`·`for`와 State Var에 대한 `rx.cond`·`rx.foreach`는 실행 시점이 다르다.

## 🛠️ 실기(코드·줄별 설명)

실습 앱에 다음 구조를 설계한다.

```text
reflex_lab/
├── __init__.py
├── reflex_lab.py
└── components/
    ├── __init__.py
    └── notice.py
```

`components/notice.py`:

```python
import reflex as rx

def notice(title: str, *children: rx.Component) -> rx.Component:
    return rx.box(
        rx.heading(title, size="4"),
        *children,
        border="1px solid #ddd",
        padding="1rem",
        width="100%",
    )
```

- `import`는 컴포넌트 생성 함수를 불러온다.
- `def`의 `title`은 제목 값, `*children`은 가변 개수 자식이다.
- `return`은 하나의 최상위 컨테이너를 반환한다.
- `rx.heading`은 함수 인자로 받은 제목을 사용한다.
- `*children`은 받은 요소를 컨테이너 자식으로 펼친다.
- `border`, `padding`, `width`는 공통 디자인을 한곳에 둔다.

`reflex_lab.py` 전체 예제:

```python
import reflex as rx
from .components.notice import notice

def index() -> rx.Component:
    return rx.vstack(
        notice("안내", rx.text("읽기 전용 컴포넌트입니다.")),
        notice("다음 학습", rx.link("데이터", href="/data")),
        padding="2rem",
    )

def data_page() -> rx.Component:
    return rx.text("study3에서 상태를 연결합니다.")

app = rx.App()
app.add_page(index, route="/")
app.add_page(data_page, route="/data")
```

- 첫 줄은 UI API를, 두 번째 줄은 같은 패키지의 모듈을 가져온다.
- `index`는 같은 함수에 다른 제목·자식을 전달해 두 화면 조각을 만든다.
- `data_page`는 링크 도착 화면이다.
- 마지막 세 줄은 앱을 생성하고 두 URL을 등록한다.

실행 후 두 안내 상자가 서로 다른 내용으로 보이고 `/data` 링크가 동작하는지 확인한다. `notice`의 여백 한 줄을 바꾸면 두 상자에 함께 반영되어야 한다.

## 오류 노트

- 상대 import를 쓰는 모듈을 `python reflex_lab.py`로 직접 실행하면 패키지 문맥이 없다. `rxconfig.py`가 있는 위치에서 `reflex run`을 쓴다.
- `notice`가 진입점의 `app`을 import하고 진입점이 다시 `notice`를 import하면 순환 참조다. 하위 모듈은 App을 가져오지 않는다.
- `*children` 대신 `children` 자체를 넘기면 튜플을 한 요소처럼 전달할 수 있다.

## ☐ 체크리스트

- ☐ 컴포넌트·페이지·모듈·패키지·App의 책임을 구분한다.
- ☐ [노션 학습 기록] 페이지와 공통 컴포넌트를 별도 파일로 나눈다.
- ☐ 제목과 자식을 인자로 받는 컴포넌트를 두 번 사용한다.
- ☐ 하위 컴포넌트가 진입점 App을 import하지 않는지 확인한다.

## 다음 단계 연결

[study3](study3.md)에서 고정 UI에 State, 파생 값, 목록 변경 이벤트를 연결한다.

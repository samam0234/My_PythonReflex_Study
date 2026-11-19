# study1 — Hello World와 기본 문법

목표: Python 함수 호출로 첫 화면을 만들고 자식·속성·이벤트 문법을 익힌다.

실제 구현: [demo/demo/lessons/hello.py](demo/demo/lessons/hello.py), [demo/demo/demo.py](demo/demo/demo.py). `demo/`에서 실행 후 `/study1`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

컴포넌트의 위치 인자는 자식 요소, 키워드 인자는 속성이다. `rx.vstack`은 세로 배치, `rx.hstack`은 가로 배치, `rx.text`는 본문, `rx.heading`은 제목이다. 함수가 반환하는 트리를 `app.add_page`에 등록하면 URL과 연결된다.

컴포넌트 함수는 화면 구조를 정의하는 단계에서 실행된다. 여기서 파일 쓰기·DB 변경을 수행하지 않는다. 사용자 클릭 시 실행할 동작은 State 이벤트로 분리한다. `on_click=State.increment`처럼 핸들러를 연결하고, 컴포넌트를 만들면서 `State.increment()`를 일반 Python 함수처럼 실행하려 하지 않는다.

## 🛠️ 실기(코드·줄별 설명)

별도 실습 앱의 `reflex_lab/reflex_lab.py` 전체 예제다.

```python
import reflex as rx

class HelloState(rx.State):
    count: int = 0

    @rx.event
    def increment(self):
        self.count += 1

def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Hello, Reflex!", size="7"),
        rx.text("Python으로 만든 첫 화면"),
        rx.text("클릭 수: ", HelloState.count),
        rx.button("증가", on_click=HelloState.increment),
        spacing="4",
        padding="2rem",
    )

app = rx.App()
app.add_page(index, route="/", title="Reflex 학습")
```

| 코드 순서 | 줄별 역할 |
|---|---|
| `import` | Reflex를 `rx` 이름으로 불러온다. |
| `class` / `count` | 서버 상태와 초기 정수를 정의한다. |
| `@rx.event` / `increment` / `+=` | 클릭 이벤트를 등록하고 서버 상태를 1 증가시킨다. |
| `def index` / `return` / `rx.vstack` | 페이지가 세로 배치 컴포넌트를 반환한다. |
| `heading` / 첫 `text` | 고정 문자열과 제목 크기를 지정한다. |
| 두 번째 `text` | 상태 표현식을 자식 인자로 전달한다. |
| `button` | 클릭을 서버 핸들러에 연결한다. |
| `spacing` / `padding` | 자식 간격과 내부 여백을 설정한다. |
| `rx.App` / `add_page` | 앱을 만들고 루트 URL과 페이지 제목을 등록한다. |

1. `reflex run`으로 시작해 제목과 본문을 확인한다.
2. 버튼을 세 번 눌러 클릭 수가 3인지 확인한다.
3. 문구를 바꾸고 저장해 개발 모드 화면 반영을 확인한다.
4. 다른 브라우저 세션을 열어 사용자 상태가 분리되는지 확인한다.

기본 템플릿은 `import → State(필요할 때) → 페이지 함수 → App → add_page` 순서다. 반환 타입 `-> rx.Component`와 문자열 속성 `size="7"`을 함께 익힌다.

## 오류 노트

- 제목 크기 등 문자열 enum 속성에 정수를 넣으면 컴파일 검증에 실패할 수 있다. 해당 컴포넌트의 허용 값을 확인한다.
- 버튼이 보이지만 증가하지 않으면 백엔드 터미널과 개발자 도구 Network의 WebSocket 연결을 확인한다.
- `on_click` 이름 오타, 이벤트 데코레이터 누락, 다른 State 클래스 참조를 확인한다.
- 자동 setter가 생긴다고 가정하지 않는다. 0.9 계열은 필요한 setter를 명시적으로 정의한다.

## ☐ 체크리스트

- ☐ 첫 화면과 클릭 이벤트를 실행한다.
- ☐ 위치 인자·키워드 인자·반환 타입을 각각 설명한다.
- ☐ [노션 상태 흐름] 클릭 → WebSocket → Python 이벤트 → delta → 화면 갱신을 추적한다.
- ☐ 고정 문자열 수정과 사용자 상태 변경의 실행 시점을 구분한다.

## 다음 단계 연결

[study2](study2.md)에서 화면을 작은 컴포넌트와 모듈로 나눈다.

참고: [Reflex 기본 문법](https://reflex.dev/docs/getting-started/basics/).

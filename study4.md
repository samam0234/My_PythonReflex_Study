# study4 — 라우팅과 요청·응답 흐름

목표: 정적·동적 URL을 등록하고 페이지 진입 시 데이터를 준비한다.

실제 구현: [demo/demo/lessons/routing.py](demo/demo/lessons/routing.py), [demo/demo/demo.py](demo/demo/demo.py). `demo/`에서 실행 후 `/study4/post/1`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

`app.add_page`의 `route`로 페이지를 등록한다. `/post/[post_id]`의 대괄호 이름은 동적 문자열 값이다. 등록 후 State에서 `self.post_id`로 읽을 수 있다. `on_load`는 페이지 진입 시 실행할 이벤트다.

브라우저의 URL 이동은 페이지 선택과 초기 로드를 일으킨다. 이후 사용자 이벤트는 WebSocket을 통해 서버에서 처리된다. 페이지 라우트 자체를 임의의 JSON REST 엔드포인트처럼 간주하지 않는다. 이 코스는 Reflex 앱 안의 페이지·이벤트만 구현한다.

URL은 외부 입력이다. 숫자 변환 실패, 없는 ID, 권한 부족을 구분하고 보호 페이지는 `on_load`와 실제 변경 이벤트 모두에서 검증한다.

## 🛠️ 실기(코드·줄별 설명)

실습 앱 진입점 전체 예제:

```python
import reflex as rx

class RouteState(rx.State):
    title: str = ""
    error: str = ""

    @rx.event
    def load_post(self):
        self.title = ""
        self.error = ""
        try:
            selected = int(self.post_id)
        except ValueError:
            self.error = "올바른 글 번호가 아닙니다."
            return
        if selected != 1:
            self.error = "글을 찾을 수 없습니다."
            return
        self.title = "첫 번째 글"

def index() -> rx.Component:
    return rx.link("첫 글 보기", href="/post/1")

def detail() -> rx.Component:
    return rx.vstack(
        rx.cond(RouteState.error != "", rx.text(RouteState.error), rx.heading(RouteState.title)),
        rx.link("목록", href="/"),
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(detail, route="/post/[post_id]", on_load=RouteState.load_post)
```

- `title`, `error`는 화면 결과와 사용자용 오류를 담는다.
- `load_post` 시작 두 줄은 이전 페이지의 표시 값을 비운다.
- `int(self.post_id)`는 등록된 동적 라우트의 문자열을 숫자로 변환한다.
- `except`, `error`, `return`은 잘못된 형식을 처리한다.
- `selected != 1` 분기는 없는 글을 처리한다.
- 마지막 대입은 정상 글 제목을 만든다.
- `index`는 동적 URL에 실제 ID를 넣은 링크를 반환한다.
- `detail`의 `rx.cond`는 오류와 정상 화면을 분기한다.
- 마지막 세 줄은 루트·상세 URL과 진입 이벤트를 등록한다.

`/post/1`, `/post/abc`, `/post/999`를 직접 열고 새로고침한다. 이전 글 제목이 오류 화면에 남지 않아야 한다. 기존 [`project/project/project.py`](project/project/project.py)에는 목록·로그인·상세·작성·수정 경로가 등록되어 있다.

## 오류 노트

- `post_id` 속성이 없으면 동적 페이지가 앱에 등록되었는지, 이름이 일치하는지 확인한다. 같은 이름의 일반 State 필드를 중복 선언하지 않는다.
- 클라이언트 이동만 정상이고 새로고침은 404면 배포 프론트의 경로 처리를 점검한다.
- 페이지를 숨겨도 변경 이벤트가 자동으로 보호되지는 않는다. study7에서 서버 권한 검사를 추가한다.

## ☐ 체크리스트

- ☐ [노션 학습 목표] 라우팅과 페이지 분리를 구현한다.
- ☐ [노션 코드 1] `add_page`와 `on_load`의 연결을 설명한다.
- ☐ [노션 코드 3] `/post/[post_id]` 값을 읽고 유효한 숫자로 검사한다.
- ☐ 잘못된 ID·없는 ID·직접 URL 접근·새로고침을 확인한다.

## 다음 단계 연결

[study5](study5.md)에서 작성·수정 페이지에 사용할 입력과 검증을 만든다.

참고: [동적 라우팅](https://reflex.dev/docs/pages/dynamic-routing/).

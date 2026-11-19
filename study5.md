# study5 — 폼·입력·유효성 검사

목표: 입력을 서버에서 검증하고 실패 메시지와 성공 결과를 화면에 표시한다.

실제 구현: [demo/demo/lessons/form.py](demo/demo/lessons/form.py), [midpoint/midpoint/validation.py](midpoint/midpoint/validation.py). `demo/`에서 실행 후 `/study5`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

`rx.form`은 `name`이 있는 필드 값을 딕셔너리로 모아 `on_submit`에 전달한다. 입력마다 State에 동기화하는 controlled 방식도 있지만 제출 시에만 검증하는 방식은 이벤트 수를 줄이기 쉽다.

브라우저의 `required`와 `max_length`는 사용성을 위한 보조 기능이다. 서버는 공백 제거 후 필수·길이·타입을 다시 검사한다. 이 과정의 게시판 규칙은 제목 1~50자, 본문 1~5000자다. 실패하면 입력을 지우지 않고 오류를 표시한다.

## 🛠️ 실기(코드·줄별 설명)

실습 앱 진입점 전체 예제:

```python
from typing import Any
import reflex as rx

def validate_post(title: str, content: str) -> str:
    if not 1 <= len(title.strip()) <= 50:
        return "제목은 1~50자로 입력하세요."
    if not 1 <= len(content.strip()) <= 5000:
        return "본문은 1~5000자로 입력하세요."
    return ""

class FormState(rx.State):
    error: str = ""
    saved_title: str = ""

    @rx.event
    def submit(self, data: dict[str, Any]):
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        self.error = validate_post(title, content)
        if self.error:
            return
        self.saved_title = title

def index() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.vstack(
                rx.text("제목"),
                rx.input(name="title", placeholder="제목", required=True, max_length=50),
                rx.text("본문"),
                rx.text_area(name="content", placeholder="본문", required=True, max_length=5000),
                rx.button("저장", type="submit"),
            ),
            on_submit=FormState.submit,
            reset_on_submit=False,
        ),
        rx.text(FormState.error, color="red", role="alert"),
        rx.text("저장된 제목: ", FormState.saved_title),
    )

app = rx.App()
app.add_page(index)
```

| 코드 | 줄별 설명 |
|---|---|
| `validate_post`의 두 `if` | 공백을 제거한 길이를 확인한다. |
| 오류 문자열 / 마지막 빈 문자열 | 실패 사유 또는 성공을 나타낸다. |
| `error`, `saved_title` | 화면용 상태를 선언한다. |
| `data.get`, `strip` 두 줄 | 누락된 키를 처리하고 입력을 정규화한다. |
| `self.error`, `if`, `return` | 실패하면 저장 단계로 내려가지 않는다. |
| `self.saved_title` | 검증 통과 후에만 결과를 변경한다. |
| `rx.form`, `name` | 입력의 서버 전달 키를 정한다. |
| `type="submit"`, `on_submit` | 제출 버튼과 이벤트를 연결한다. |
| `reset_on_submit=False` | 실패 시에도 입력을 유지한다. |
| `role="alert"` | 오류 메시지를 보조 기술에 알린다. |

빈 값, 공백만, 제목 50자·51자, 본문 5000자·5001자를 시험한다. 브라우저 제한을 우회한 데이터도 `validate_post`에서 거절되어야 한다. 비문자열 등 신뢰할 수 없는 원시 이벤트 입력에 대한 엄격한 검증은 study14에서 확장한다.

## 오류 노트

- 제출 데이터가 비어 있으면 `name` 누락을 확인한다.
- 오류 때 입력이 사라지면 `reset_on_submit` 설정을 확인한다.
- 버튼이 눌러도 제출되지 않으면 form 밖 배치 또는 `type` 설정을 확인한다.
- 공개 State에 비밀번호를 넣어 보관하지 않는다. 로그인 제출값은 검증 후 유지하지 않는다.

## ☐ 체크리스트

- ☐ [노션 학습 기록] 폼 컴포넌트를 작성·수정 화면에서 재사용할 수 있게 설계한다.
- ☐ 제목 필수·50자 제한·본문 필수를 서버에서도 확인한다.
- ☐ 경계값과 공백 입력에서 오류 문구를 확인한다.
- ☐ 입력 유지와 오류 알림의 접근성을 확인한다.

## 다음 단계 연결

[study6](study6.md)에서 검증된 값을 DB에 저장해 CRUD로 확장한다.

참고: [Reflex 폼 레시피](https://reflex.dev/docs/recipes/content/forms/).

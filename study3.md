# study3 — State·Var·모델로 데이터 다루기

목표: 서버 상태를 변경하고 파생 값·조건·반복을 화면에 안전하게 연결한다.

실제 구현: [demo/demo/lessons/data.py](demo/demo/lessons/data.py), [demo/demo/demo.py](demo/demo/demo.py). `demo/`에서 실행 후 `/study3`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

`rx.State`의 공개 필드는 화면으로 전달될 수 있는 데이터다. 밑줄로 시작하는 backend var는 서버에만 보관한다. API 키·세션 자격증명은 공개 State에 넣지 않는다. State는 기본 메모리 관리 시 서버 재시작으로 사라질 수 있으며 영속 데이터는 DB에 둔다. 별도 상태 저장소 구성은 study11에서 다룬다.

`State.names`는 컴포넌트 함수 안에서 실제 리스트가 아닌 Var다. 따라서 `len(State.names)`·`if State.names`·`for name in State.names` 대신 Var 연산과 `rx.cond`·`rx.foreach`를 사용한다. 이벤트의 `self.names`와 computed var 내부는 실제 서버 값이므로 일반 Python 문법을 사용할 수 있다.

상태에 리스트·딕셔너리를 대입하면 변경이 감지된다. 노션에 기록된 것처럼 `append` 등의 직접 변경도 추적된다. 중첩 데이터는 새 값을 대입하는 방식도 연습해 변경 지점을 명확히 한다.

이 저장소는 세 앱의 `rxconfig.py`에 `StateManagerMode.MEMORY`를 명시했다. Reflex 0.9.11 자체의 기본값은 DISK이므로, 노션의 재시작 시 초기화 실습을 이 명시적 설정으로 재현한다.

## 🛠️ 실기(코드·줄별 설명)

실습 앱 진입점 전체 예제:

```python
import reflex as rx

class DataState(rx.State):
    names: list[str] = []
    show_list: bool = True

    @rx.event
    def add_name(self):
        self.names.append(f"항목 {len(self.names) + 1}")

    @rx.event
    def toggle(self):
        self.show_list = not self.show_list

    @rx.var
    def total(self) -> int:
        return len(self.names)

def index() -> rx.Component:
    return rx.vstack(
        rx.text("개수: ", DataState.total),
        rx.button("추가", on_click=DataState.add_name),
        rx.button("표시 전환", on_click=DataState.toggle),
        rx.cond(
            DataState.show_list,
            rx.vstack(rx.foreach(DataState.names, lambda name: rx.text(name))),
            rx.text("목록 숨김"),
        ),
        rx.text(rx.cond(~DataState.show_list, "숨김 상태", "표시 상태")),
    )

app = rx.App()
app.add_page(index)
```

| 코드 | 줄별 설명 |
|---|---|
| `names`, `show_list` | 요소 타입과 초기값을 선언한다. |
| `add_name`, `append` | 서버 이벤트 안에서 실제 리스트를 변경한다. |
| `toggle`, `not` | 실제 Python bool을 반전한다. |
| `@rx.var`, `total`, `len` | 상태로부터 정수를 계산한다. 반환 타입을 명시한다. |
| `rx.text`, 버튼 두 개 | 파생 값을 표시하고 이벤트를 연결한다. |
| `rx.cond` | Var 조건으로 두 화면 중 하나를 표시한다. |
| `rx.foreach`, `lambda` | 각 Var 항목을 텍스트로 렌더링한다. |
| `~DataState.show_list` | 컴포넌트 표현식에서 bool Var를 반전한다. |
| `App`, `add_page` | 페이지를 등록한다. |

추가 버튼 세 번 → 개수 3, 표시 전환 → 목록 숨김, 다시 전환 → 기존 세 항목 유지가 기대 결과다. 프로세스를 완전히 재시작한 뒤 목록이 초기화되는 것도 확인한다.

### 노션의 Todo 예제

`demo/` 실행 후 `/study3/todo`로 이동한다. 빈 입력을 제출해 오류를 확인하고 할 일을 추가·완료 전환·삭제한다. 완료 전환으로 남은 항목 수가 즉시 바뀌며, 서버를 재시작하면 메모리 목록이 초기화된다. [실제 Todo 코드](demo/demo/lessons/todo.py)

```python
@rx.event
def toggle(self, item_id: int):
    for item in self.items:
        if item["id"] == item_id:
            item["done"] = not item["done"]
            return
```

이벤트의 `item_id`는 행 인덱스 대신 안정적인 ID다. 서버의 Python 반복문에서 일치하는 딕셔너리를 찾고 bool을 반전한다. Reflex가 중첩 변경을 감지하면 `remaining`이 다시 계산된다. 화면은 `rx.foreach`로 행을 만들고 `rx.cond`로 상태를 표시한다.

## 오류 노트

- `Cannot convert Var to bool`: 컴포넌트 안의 Python `if`, `and`, `not` 사용 위치를 확인한다. Var에는 `rx.cond`, `&`, `~`를 사용한다.
- 목록 요소 타입을 알 수 없는 오류: `list` 대신 `list[str]`처럼 명확한 타입을 선언한다.
- 날짜·ORM 객체 직렬화 문제: 화면에 필요한 필드를 dict·DTO로 변환하고 날짜는 UTC ISO 문자열로 변환한다.
- State를 전역 변수와 동일하게 생각하면 사용자 간 데이터 공유를 잘못 설계할 수 있다. 공동 게시물 원본은 DB로 관리한다.

## ☐ 체크리스트

- ☐ [노션 학습 목표] State 클래스로 화면 상태를 관리한다.
- ☐ [노션 상태 흐름] 대입과 list/dict 직접 변경의 감지를 확인한다.
- ☐ [노션 제약] State Var에 `rx.cond`, `rx.foreach`, `~`를 사용한다.
- ☐ [노션 제약] 재시작 시 State 초기화와 DB 영속성의 필요를 설명한다.
- ☐ [노션 예제] Todo 빈 입력·추가·완료 전환·삭제와 남은 개수 갱신을 실행한다.
- ☐ 공개 상태에 비밀 값이 없는지 확인한다.

## 다음 단계 연결

[study4](study4.md)에서 URL의 동적 값과 페이지 진입 이벤트로 데이터를 선택한다.

참고: [computed var](https://reflex.dev/docs/vars/computed-vars/), [조건부 렌더링](https://reflex.dev/docs/library/dynamic-rendering/cond/).

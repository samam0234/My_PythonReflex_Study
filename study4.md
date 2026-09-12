# study4 — 컴포넌트 분리 + 폼 검증 (실습4)

study3까지는 `fruit_list.py` 한 파일에 입력 폼, 검증, 목록 조립이 다 섞여 있었습니다. 이번 단계에서 **폼을 독립 컴포넌트로 분리**하고, **서버 측 검증**을 제대로 갖춥니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [ ] 라우팅 / 페이지 분리                (study5 예정)
```

대응하는 실습 프로젝트: [`demo/`](./demo) (신규: [`components/fruit_form.py`](./demo/demo/components/fruit_form.py) / 변경: [`state.py`](./demo/demo/state.py), [`components/fruit_list.py`](./demo/demo/components/fruit_list.py))

---

## 1. 컴포넌트 분리 — `fruit_form.py`

```python
# components/fruit_form.py
def fruit_form() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.input(
                placeholder="새 과일 이름",
                value=State.new_fruit_name,
                on_change=State.set_new_fruit_name,
                width="100%",
            ),
            rx.button("추가", on_click=State.add_fruit),
            width="100%",
        ),
        rx.cond(
            State.form_error != "",
            rx.text(State.form_error, color="red", size="2"),
        ),
        align="start",
        width="100%",
        spacing="1",
    )
```

- `fruit_list.py`는 이제 `fruit_form()`을 호출하기만 하면 됩니다 — Vue/React에서 "화면이 커지면 컴포넌트를 쪼갠다"는 원칙이 Reflex에서는 **"함수를 하나 더 만들고 호출한다"**로 그대로 적용됩니다. 클래스나 특수 문법이 필요 없다는 점이 오히려 Vue/React보다 단순합니다.
- `rx.cond(State.form_error != "", rx.text(...))`: **두 번째 분기(else)를 생략**하면 조건이 거짓일 때 아무것도 렌더링하지 않습니다. `v-if`(else 없는)와 같은 용법입니다.

## 2. 서버 측 검증 3종

```python
# state.py
@rx.event
def add_fruit(self):
    name = self.new_fruit_name.strip()
    if not name:
        self.form_error = "이름을 입력하세요."
        return
    if len(name) > 10:
        self.form_error = "이름은 10자 이내로 입력하세요."
        return
    if any(f["name"] == name for f in self.fruits):
        self.form_error = f"'{name}'은(는) 이미 목록에 있습니다."
        return
    ...
```

- 빈 값, 길이 제한, 중복 이름 세 가지를 검사합니다. **모두 `add_fruit` 이벤트 핸들러(서버) 안에서** 검사한다는 점이 핵심입니다 — 브라우저의 `required`/`maxlength` 같은 HTML 속성에 의존하지 않고, 서버가 최종 문지기 역할을 합니다.
- `set_new_fruit_name`에서 타이핑할 때마다 `self.form_error = ""`로 에러를 지워줍니다. 그래야 사용자가 다시 입력을 시작하면 이전 에러 메시지가 즉시 사라집니다 (좋은 폼 UX의 기본 패턴).

## 3. 참고 — `rx.form`을 쓰는 대안 패턴

지금 방식(입력마다 `on_change`로 서버에 값 동기화)은 이해하기 쉽지만, 입력 필드가 많아지면 이벤트 핸들러가 많아집니다. Reflex는 "제출할 때 한 번에 폼 전체 값을 딕셔너리로 받는" `rx.form`도 제공합니다.

```python
def fruit_form_alt() -> rx.Component:
    return rx.form(
        rx.input(name="fruit_name", placeholder="새 과일 이름"),
        rx.button("추가", type="submit"),
        on_submit=State.handle_submit,   # handle_submit(self, form_data: dict)
        reset_on_submit=True,
    )

# state.py
@rx.event
def handle_submit(self, form_data: dict):
    name = form_data.get("fruit_name", "").strip()
    ...
```

- `on_submit`으로 넘어오는 `form_data`는 폼 안의 모든 `name=` 속성을 가진 입력값을 모은 dict입니다. 필드가 여러 개인 폼(예: 이름+수량+카테고리)일 때 이 방식이 `on_change`를 각각 다는 것보다 간결합니다.
- 이 저장소에서는 지금까지처럼 **입력마다 상태를 즉시 동기화하는 방식을 계속 씁니다** (실시간 미리보기 같은 기능을 붙이기 쉬워서). `studyFinal`의 게시판 프로젝트에서 필드가 많은 폼(제목+내용)을 만들 때 `rx.form` 방식도 실제로 적용해봅니다.

## 4. 실행 확인

```bash
cd demo
reflex run
```

- 빈 입력으로 "추가" → "이름을 입력하세요." 에러가 뜨는지 확인
- "사과"(이미 있는 이름)를 입력하고 "추가" → 중복 에러가 뜨는지 확인
- 아무 키나 입력하면 에러 메시지가 바로 사라지는지 확인
- 11자 이상 입력 시 길이 제한 에러가 뜨는지 확인
- 정상적인 새 이름 입력 시 추가되고 에러 메시지 영역이 비는지 확인

## 5. 다음 단계 (study5 예정)

- 지금은 페이지가 `index` 하나뿐입니다. **라우팅**을 도입해 "목록 페이지"와 "과일 상세 페이지"로 화면을 나눕니다.
- URL 파라미터(동적 라우트)로 특정 과일의 id를 받아오는 방법을 다룹니다.

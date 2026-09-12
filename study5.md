# study5 — 라우팅 / 페이지 분리 (실습5)

지금까지는 화면이 `index` 하나였습니다. 이번 단계에서 **목록 페이지**와 **상세 페이지**로 화면을 나누고, URL에 담긴 id로 특정 과일을 보여줍니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [ ] FastAPI/Django 연동 가능성 확인      (study6 예정)
```

대응하는 실습 프로젝트: [`demo/`](./demo) (신규: [`pages/fruit_detail.py`](./demo/demo/pages/fruit_detail.py) / 변경: [`state.py`](./demo/demo/state.py), [`components/fruit_card.py`](./demo/demo/components/fruit_card.py), [`demo.py`](./demo/demo/demo.py))

---

## 1. 여러 페이지 등록하기

```python
# demo.py
app = rx.App()
app.add_page(index, route="/")
app.add_page(fruit_detail, route="/fruit/[fruit_id]")
```

- `app.add_page(컴포넌트_함수, route=경로)`: Vue Router의 `routes: [{ path, component }]`, React Router의 `<Route path element>`에 대응합니다. 다른 점은 **라우터 설정 파일이 따로 없고, `app.add_page`를 호출하는 것 자체가 라우트 등록**이라는 점입니다.
- `[fruit_id]`처럼 대괄호로 감싼 세그먼트가 **동적 라우트 파라미터**입니다. Next.js의 파일 기반 라우팅 문법(`[id].jsx`)에서 따온 표기법을 그대로 문자열로 씁니다.

## 2. 동적 라우트 파라미터 → State 속성으로 자동 주입

`/fruit/[fruit_id]`로 페이지를 등록하면, Reflex는 **`fruit_id`라는 이름의 문자열 속성을 State에 자동으로 추가**합니다. 우리가 직접 선언한 적이 없어도 `self.fruit_id`로 접근할 수 있습니다.

```python
# state.py
@rx.var
def current_fruit(self) -> dict:
    for fruit in self.fruits:
        if str(fruit["id"]) == self.fruit_id:
            return fruit
    return {"id": 0, "name": "", "in_stock": False}
```

| Vue Router | React Router | Reflex |
|---|---|---|
| `useRoute().params.id` | `useParams().id` | `self.fruit_id` (State 안에서, 자동 주입) |

- 라우트 파라미터는 항상 **문자열**이므로, `self.fruits`의 `id`(정수)와 비교하려면 `str(fruit["id"])`로 맞춰줘야 합니다. 이 실수(타입 불일치)는 Vue/React에서도 흔한 버그이니 낯설지 않을 것입니다.
- "찾지 못했을 때"를 위해 `{"id": 0, "name": "", "in_stock": False}`라는 **빈 값(sentinel)**을 반환합니다. Reflex의 ComputedVar는 반환 타입이 고정되어야 하므로(`dict`), Python처럼 `None`과 `dict`를 섞어 반환하기보다 **항상 같은 모양의 값**을 반환하는 편이 다루기 쉽습니다.

## 3. 상세 페이지 컴포넌트

```python
# pages/fruit_detail.py
def fruit_detail() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.cond(
                State.current_fruit["name"] != "",
                rx.vstack(
                    rx.heading(State.current_fruit["name"], size="8"),
                    rx.badge(
                        rx.cond(State.current_fruit["in_stock"], "재고 있음", "품절"),
                        color_scheme=rx.cond(State.current_fruit["in_stock"], "green", "red"),
                    ),
                ),
                rx.text("해당 id의 과일을 찾을 수 없습니다."),
            ),
            rx.link(rx.button("← 목록으로"), href="/"),
        ),
    )
```

- `State.current_fruit["name"] != ""`로 "찾았는지"를 판단합니다 — study0~4에서 계속 강조한 "Var 조건은 `rx.cond`로"라는 원칙이 여기서도 그대로 적용됩니다.
- `rx.link(..., href="/")`: Vue의 `<router-link to="/">`, React Router의 `<Link to="/">`에 대응합니다. 일반 `<a>` 태그처럼 보이지만, 클릭 시 페이지 전체를 새로고침하지 않고 클라이언트 라우팅으로 이동합니다.

## 4. 목록 → 상세로 이동하는 링크

```python
# components/fruit_card.py
rx.link(
    rx.button("상세", size="1", variant="soft"),
    href="/fruit/" + fruit["id"].to_string(),
),
```

- `fruit["id"]`는 정수 Var이므로 문자열과 `+`로 이어붙이려면 `.to_string()`으로 먼저 문자열 Var로 변환해야 합니다. Var끼리는 이렇게 **명시적으로 타입을 맞춰야** 연산할 수 있습니다 (JS의 암묵적 타입 변환에 의존하지 않도록 Reflex가 강제하는 부분).

## 5. 실행 확인

```bash
cd demo
reflex run
```

- `http://localhost:3000/` → 과일 카드마다 "상세" 버튼이 보이는지 확인
- "상세" 버튼 클릭 → `http://localhost:3000/fruit/1` 같은 주소로 이동하고, 해당 과일의 이름과 재고 배지가 크게 보이는지 확인
- 주소창에 직접 `http://localhost:3000/fruit/999`(존재하지 않는 id) 입력 → "해당 id의 과일을 찾을 수 없습니다." 문구가 보이는지 확인
- "← 목록으로" 클릭 → 목록 페이지로 돌아오고, 방금까지의 CRUD 상태(추가/삭제 결과)가 그대로 유지되는지 확인 (같은 서버 세션이므로 State가 공유됨)

## 6. 다음 단계 (study6, 고급1 예정)

- 지금까지 Reflex 자체 기능만 썼습니다. Reflex 백엔드는 사실 **FastAPI 위에서 동작**한다는 것을 study0에서 짚었는데, study6에서 이 구조를 직접 확인하고 **외부 API(또는 별도 FastAPI/Django 서버)와 연동**하는 방법을 다룹니다.

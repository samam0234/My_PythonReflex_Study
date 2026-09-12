# study3 — 이벤트 핸들러로 CRUD (실습3)

study2에서 "토글(Update의 일종)"까지 구현했습니다. 이번 단계에서 **추가(Create)**와 **삭제(Delete)**를 더해 CRUD를 완성합니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [ ] 라우팅 / 페이지 분리                (study5 예정)
```

대응하는 실습 프로젝트: [`demo/`](./demo) (변경 파일: [`state.py`](./demo/demo/state.py), [`components/fruit_card.py`](./demo/demo/components/fruit_card.py), [`components/fruit_list.py`](./demo/demo/components/fruit_list.py))

---

## 1. Create — Controlled Input + 이벤트 핸들러

```python
# state.py
new_fruit_name: str = ""

@rx.event
def set_new_fruit_name(self, value: str):
    self.new_fruit_name = value

@rx.event
def add_fruit(self):
    name = self.new_fruit_name.strip()
    if not name:
        return
    next_id = max((f["id"] for f in self.fruits), default=0) + 1
    self.fruits.append({"id": next_id, "name": name, "in_stock": True})
    self.new_fruit_name = ""
```

```python
# fruit_list.py
rx.input(
    placeholder="새 과일 이름",
    value=State.new_fruit_name,
    on_change=State.set_new_fruit_name,
),
rx.button("추가", on_click=State.add_fruit),
```

- `rx.input`의 `value` + `on_change` 조합은 React study0/4에서 배운 **Controlled Component**와 정확히 같은 패턴입니다. 다만 값을 들고 있는 곳이 브라우저 컴포넌트 로컬 상태가 아니라 **서버의 State**라는 점이 다릅니다 — 키를 한 글자 칠 때마다 WebSocket으로 서버에 값이 전달되고, 서버가 `new_fruit_name`을 갱신해 다시 내려보냅니다.
- `add_fruit`에서 `self.fruits.append(...)`처럼 **리스트를 직접 변경(mutate)**해도 됩니다. study2에서 확인한 "State 안의 list/dict는 직접 수정해도 변경이 감지된다"는 원칙이 추가에도 그대로 적용됩니다.
- 빈 문자열 검증(`if not name: return`)처럼 **서버 쪽에서 최종 검증**을 하는 습관을 들입니다. 프론트만 믿으면 안 된다는 원칙은 Vue/React와 동일하지만, Reflex는 애초에 폼 값이 서버에 있으므로 이 검증이 훨씬 자연스럽게 붙습니다.

## 2. Delete — id를 인자로 받는 이벤트 핸들러

```python
@rx.event
def remove_fruit(self, fruit_id: int):
    self.fruits = [f for f in self.fruits if f["id"] != fruit_id]
```

```python
rx.button(
    "삭제",
    color_scheme="red",
    on_click=State.remove_fruit(fruit["id"]),
),
```

- 여기서는 리스트를 직접 수정하는 대신 **새 리스트를 만들어 통째로 대입**했습니다. 둘 다 가능하지만("추가"는 append, "삭제"는 필터링) 상황에 맞는 방식을 씁니다.
- `on_click=State.remove_fruit(fruit["id"])`: 이벤트 핸들러를 **인자와 함께 미리 호출한 것처럼 적는** Reflex 특유의 문법입니다. 실제로는 클릭 즉시 실행되는 게 아니라, "클릭하면 `remove_fruit(그때의 fruit_id)`를 실행해라"라는 **이벤트 명세(EventSpec)**를 만드는 것입니다. `fruit["id"]`가 `rx.foreach`로 반복되는 시점의 Var이기 때문에, 카드마다 서로 다른 `fruit_id`가 정확히 바인딩됩니다.

## 3. Update(토글)까지 합친 카드 컴포넌트

```python
rx.hstack(
    rx.button("토글", on_click=State.toggle_stock(fruit["id"])),
    rx.button("삭제", color_scheme="red", on_click=State.remove_fruit(fruit["id"])),
    spacing="2",
),
```

이제 과일 카드 하나에 **읽기(카드 표시) + 수정(토글) + 삭제** 세 가지가 다 있고, 목록 상단에는 **생성(입력창+추가 버튼)**이 있습니다. CRUD 네 가지가 한 화면에 모였습니다.

## 4. 실행 확인

```bash
cd demo
reflex run
```

- 입력창에 "딸기"를 입력하고 "추가"를 누르면 목록 맨 아래에 "딸기"(재고 있음)가 추가되는지 확인
- 입력창을 비운 채 "추가"를 눌러도 아무 일도 일어나지 않는지 확인 (서버 검증)
- 아무 과일이나 "삭제"를 누르면 목록에서 사라지고, 상단 "재고 있는 과일" 개수도 같이 줄어드는지 확인
- 새로고침 후에도 추가/삭제한 결과가 유지되는지 확인 (서버 프로세스가 살아있는 동안 State가 유지됨 — study0에서 다룬 "상시 실행되는 서버" 구조)

## 5. 다음 단계 (study4 예정)

- 지금은 `fruit_list.py` 한 파일에 입력 폼, 목록, 카드 조립이 다 섞여 있습니다 — **컴포넌트를 더 잘게 분리**합니다 (입력 폼을 `fruit_form.py`로 독립).
- 이름 중복/길이 제한 같은 **폼 검증**을 추가하고, 에러 메시지를 화면에 보여줍니다.
- `rx.form`을 이용한 정식 폼 제출 패턴도 함께 살펴봅니다.

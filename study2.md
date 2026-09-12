# study2 — State 클래스로 화면 상태 관리 (실습2)

study1의 과일 목록은 "그려지기만 하는 고정 데이터"였습니다. 이번 단계에서 그 데이터를 **State 클래스** 안으로 옮겨서 진짜 상태로 만들고, 버튼으로 값을 바꿔봅니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [ ] 이벤트 핸들러로 CRUD               (study3 예정)
- [ ] 라우팅 / 페이지 분리                (study5 예정)
```

대응하는 실습 프로젝트: [`demo/`](./demo) (변경 파일: [`state.py`](./demo/demo/state.py), [`components/fruit_card.py`](./demo/demo/components/fruit_card.py), [`components/fruit_badge.py`](./demo/demo/components/fruit_badge.py), [`components/fruit_list.py`](./demo/demo/components/fruit_list.py))

---

## 1. State 클래스 정의

```python
# demo/state.py
import reflex as rx

class State(rx.State):
    fruits: list[dict] = [
        {"id": 1, "name": "사과", "in_stock": True},
        {"id": 2, "name": "바나나", "in_stock": False},
        {"id": 3, "name": "포도", "in_stock": True},
    ]
```

- `rx.State`를 상속한 클래스의 **타입 어노테이션이 붙은 클래스 속성**은 전부 "상태"로 취급됩니다. (Vue의 `data()`/`ref` 모음, React의 여러 `useState` 호출을 한 클래스로 합쳐놓은 형태)
- study1에서 모듈 최상단에 있던 `initial_fruits` 리스트가 그대로 `State.fruits`의 기본값이 되었습니다. **모양은 똑같은데 위치만 바뀐 것**이 핵심입니다.

## 2. 이벤트 핸들러 — `self.속성 = 값`이 곧 리렌더링 트리거

```python
@rx.event
def toggle_stock(self, fruit_id: int):
    for fruit in self.fruits:
        if fruit["id"] == fruit_id:
            fruit["in_stock"] = not fruit["in_stock"]
```

- `@rx.event` 데코레이터가 붙은 메서드만 `on_click` 등에 연결할 수 있는 "이벤트 핸들러"가 됩니다.
- 메서드 본문은 **평범한 Python 코드**입니다. `self.fruits`는 이 시점엔 진짜 Python list이므로 `for`/`if`를 그대로 씁니다 — study0에서 강조한 "`rx.cond`/`rx.foreach`가 필요한 건 컴포넌트 함수 쪽이지, State 내부 로직이 아니다"라는 원칙이 여기서 확인됩니다.
- 리스트 안의 dict를 직접 수정(`fruit["in_stock"] = ...`)해도 Reflex가 변경을 감지합니다. Vue의 반응형 배열/객체를 직접 수정해도 화면이 갱신되는 것과 같은 감각입니다 (React처럼 `setFruits([...])`으로 새 배열을 통째로 만들어줄 필요가 없습니다).

## 3. ComputedVar — 파생 값

```python
@rx.var
def in_stock_count(self) -> int:
    return len([f for f in self.fruits if f["in_stock"]])
```

- `@rx.var`가 붙으면 "다른 상태로부터 계산되는 값"이 됩니다. Vue의 `computed`, React에서 렌더링 중 계산하는 파생값과 같은 역할입니다.
- `self.fruits`가 바뀔 때마다 자동으로 다시 계산되어 화면에 반영됩니다. 화면 쪽에서는 그냥 `State.in_stock_count`를 값처럼 쓰면 됩니다 (`rx.text("재고 있는 과일: ", State.in_stock_count, "개")`).

## 4. `rx.foreach`가 진짜 필요해지는 순간

study1에서는 `[fruit_card(f) for f in initial_fruits]`처럼 파이썬 for로 반복해도 됐습니다. `initial_fruits`가 **컴포넌트 트리를 만드는 시점에 이미 확정된 값**이었기 때문입니다.

`State.fruits`는 다릅니다. 컴포넌트 함수(`fruit_list_practice`)가 실행되는 시점은 "서버가 이 페이지의 화면 구조를 준비하는 시점"이고, 그때는 **어떤 브라우저 세션이 접속해서 fruits 값이 어떻게 바뀌어 있을지 알 수 없습니다.** 그래서:

```python
rx.foreach(State.fruits, fruit_card)
```

로 "이 리스트는 나중에(브라우저에서) 실제 값이 정해지면, 각 항목마다 `fruit_card`를 호출해서 반복 렌더링해라"라고 **선언**만 해둡니다. 이때 `fruit_card`에 전달되는 `fruit`은 진짜 dict가 아니라 **아직 값이 없는 Var(자리표시자)** 입니다.

## 5. Var가 되면서 바뀌는 것 — `rx.cond`

`fruit`이 Var가 되면 `fruit["in_stock"]`으로 값을 꺼내는 문법은 study1과 똑같지만, 그 결과 역시 Var이기 때문에 **Python의 `if`로 직접 분기할 수 없습니다.** (`if fruit["in_stock"]: ...`을 쓰면 "아직 정해지지 않은 값에 대해 지금 당장 참/거짓을 판단하라"는 모순된 요청이 되어 에러가 납니다.)

```python
# study1 (fruit이 진짜 dict일 때) — 지금 당장 판단 가능
text_decoration = "none" if fruit["in_stock"] else "line-through"

# study2 (fruit이 Var일 때) — "나중에 정해지면 둘 중 하나를 써라"고 선언
text_decoration = rx.cond(fruit["in_stock"], "none", "line-through")
```

같은 이유로 `fruit_badge`의 `soldout` 판정도 `rx.cond`로 바꿨고, 값을 반대로 뒤집을 때도 Python의 `not` 대신 Var 연산자인 `~`(`~fruit["in_stock"]`)을 씁니다.

> **정리**: "값이 dict냐 Var냐"에 따라 **같은 문법(`[]`로 꺼내기)이 다른 도구(`if`/`not` vs `rx.cond`/`~`)를 요구**한다는 것이 Reflex 초반 최대 함정입니다. 헷갈리면 "이 컴포넌트 함수가 State 값을 다루고 있는가?"를 먼저 확인하세요.

## 6. 실행 확인

```bash
cd demo
reflex run
```

- `http://localhost:3000` 접속 → "재고 있는 과일: 2개"가 보이는지 확인 (사과, 포도)
- 바나나 카드의 "토글" 버튼을 누르면 배지가 초록/재고 있음으로 바뀌고, 상단 카운트가 "3개"로 바뀌는지 확인
- 다시 눌러서 "2개"로 돌아오는지 확인 (State가 서버에 유지되므로 새로고침해도 값이 남아있는지도 확인)

`reflex run`으로 프론트(3000)/백엔드(8000) 서버가 모두 에러 없이 뜨는지, `curl -s http://localhost:8000/ping`이 정상 응답하는지 확인했습니다.

## 7. 다음 단계 (study3 예정)

- 폼 입력으로 새 과일을 **추가**하는 이벤트 핸들러 (Create)
- 과일을 **삭제**하는 이벤트 핸들러 (Delete)
- 이름을 수정하는 이벤트 핸들러 (Update) — 지금까지의 "토글"과 합쳐 CRUD 완성

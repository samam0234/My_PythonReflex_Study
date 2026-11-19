# study11 — 상태·캐시·비동기 데이터 흐름 심화

목표: 계산 캐시와 조회 캐시를 구분하고 긴 작업 중에도 안전하게 상태를 갱신한다.

실제 구현: [demo/demo/lessons/async_lab.py](demo/demo/lessons/async_lab.py), [project/project/state.py](project/project/state.py). `demo/`에서 실행 후 `/study11`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

`@rx.var`는 기본적으로 의존 State가 바뀔 때 재계산하는 캐시를 사용한다. DB 행이 외부에서 바뀌는 것만으로 의존성 변경이 감지되지는 않는다. 명시적 재조회·무효화가 필요하다. 사용자별 조회 캐시와 여러 사용자 사이에 공유하는 캐시는 범위가 다르다.

일반 async 이벤트에서 `yield`는 중간 상태를 화면으로 내보낸다. 이것만으로 동일 세션의 모든 이벤트가 병렬 처리되지는 않는다. `@rx.event(background=True)`는 다른 이벤트와 함께 실행될 수 있지만 State를 읽고 변경할 때 `async with self`로 최신 상태와 잠금을 확보해야 한다. 네트워크 대기는 잠금 밖에 둔다.

노션의 실제 활용 기록은 중복 요청 방지 → 로딩 true → `yield` → API 대기 → 결과·실패 처리 흐름이다. 특정 외부 프레임워크 연결 없이 이 패턴만 연습한다.

## 🛠️ 실기(코드·줄별 설명)

독립 실습 진입점 전체 예제다. 외부 API 대신 지연을 가진 모의 함수를 써서 비용 없이 동시성을 확인한다.

```python
import asyncio
import time
import reflex as rx

async def fetch_label() -> str:
    await asyncio.sleep(1)
    return "조회 완료"

class AsyncState(rx.State):
    result: str = ""
    busy: bool = False
    error: str = ""
    _cached: str = ""
    _expires: float = 0.0

    @rx.var(cache=True)
    def result_length(self) -> int:
        return len(self.result)

    @rx.event(background=True)
    async def reload(self):
        async with self:
            if self.busy:
                return
            if self._cached and time.monotonic() < self._expires:
                self.result = self._cached
                return
            self.busy = True
            self.error = ""
        try:
            value = await asyncio.wait_for(fetch_label(), timeout=5)
            async with self:
                self.result = value
                self._cached = value
                self._expires = time.monotonic() + 30
        except TimeoutError:
            async with self:
                self.error = "조회 시간이 초과되었습니다."
        finally:
            async with self:
                self.busy = False

    @rx.event
    def invalidate(self):
        self._cached = ""
        self._expires = 0.0

def index() -> rx.Component:
    return rx.vstack(
        rx.button("조회", on_click=AsyncState.reload, loading=AsyncState.busy),
        rx.button("캐시 비우기", on_click=AsyncState.invalidate),
        rx.text(AsyncState.result),
        rx.text(AsyncState.error, role="alert"),
        rx.text("결과 길이: ", AsyncState.result_length),
    )

app = rx.App()
app.add_page(index)
```

| 구간 | 줄별 설명 |
|---|---|
| import / `fetch_label` | 비동기 지연·단조 시계·UI를 준비한다. |
| 공개 필드 3개 / backend 필드 2개 | 표시 결과와 서버 캐시를 구분한다. |
| `result_length` | `result` 의존성의 계산 캐시다. TTL 캐시와 다르다. |
| 첫 `async with self` | 최신 상태를 잠근 뒤 중복·유효 캐시를 확인한다. |
| `busy`, `error` | 작업 시작 표시를 저장한다. 잠금을 놓을 때 화면에 반영된다. |
| `wait_for` | 잠금 밖에서 5초 한도로 외부 작업을 기다린다. |
| 두 번째 잠금 / 대입 3줄 | 결과와 30초 TTL을 함께 갱신한다. |
| `except` | 시간 초과를 사용자 오류로 바꾼다. |
| `finally` | 실패·취소 시에도 로딩 상태를 정리한다. |
| `invalidate` | 쓰기 이후 조회 캐시를 만료시킨다. |
| 페이지의 버튼·텍스트 | 작업·무효화 이벤트와 표시 필드를 연결한다. |

일반 async 이벤트의 중간 표시도 별도로 비교한다. 같은 클래스에 아래 메서드를 추가하고 버튼을 이 이벤트에 연결해 본다.

```python
@rx.event
async def reload_with_yield(self):
    if self.busy:
        return
    self.busy = True
    yield
    try:
        self.result = await asyncio.wait_for(fetch_label(), timeout=5)
    finally:
        self.busy = False
```

가드는 중복 호출을 막고 `yield`는 로딩을 먼저 보낸다. `try`의 await는 작업 완료를 기다리고 `finally`는 플래그를 되돌린다. background 이벤트의 잠금 규칙과 혼용하지 않는다.

검증: 첫 조회 약 1초 → TTL 내 즉시 결과 → 무효화 후 다시 지연을 관찰한다. 대기 시간을 6초로 바꾸면 5초 timeout 후 busy가 꺼져야 한다. 게시글 쓰기 뒤 목록 캐시도 무효화하도록 연결한다.

## 오류 노트

- `ImmutableStateError`: background에서 잠금 밖의 State 변경을 찾는다.
- 오래된 결과가 최신 검색을 덮으면 요청 번호·검색 키를 캡처하고 결과 적용 때 재확인한다.
- 개인화 결과의 공유 캐시는 사용자·권한·검색 조건이 키에 포함되어야 한다.
- 비동기 함수 안의 동기 DB·CPU 작업도 이벤트 루프를 막을 수 있다. study12에서 측정하고 `to_thread` 등으로 분리한다.
- 노션의 401 재시도 경험은 외부 인증 API를 쓰는 경우에만 해당한다. 재시도는 한 번으로 제한하고 실패하면 세션을 폐기한다. 이 코스의 단독 DB 인증에는 refresh API를 새로 만들지 않는다.

## ☐ 체크리스트

- ☐ [노션 비동기 경험] 중복 방지·로딩·`yield`·완료 정리를 재현한다.
- ☐ computed 캐시와 TTL 조회 캐시의 무효화 조건을 구분한다.
- ☐ background의 상태 접근을 잠금으로 보호한다.
- ☐ timeout 후 로딩이 복구되고 후속 조회가 가능한지 확인한다.
- ☐ [노션 401 경험] 한 번 재시도·세션 만료 원칙을 설명하고 단독 앱 적용 범위를 기록한다.

## 다음 단계 연결

[study12](study12.md)에서 상태 크기·쿼리·UI 비용을 측정해 최적화한다.

참고: [background 이벤트](https://reflex.dev/docs/events/background-events/), [computed 캐시](https://reflex.dev/docs/vars/computed-vars/).

# study6 (고급1) — Reflex의 FastAPI 기반 구조와 외부 API 연동

Notion 학습 목표의 "FastAPI 또는 Django API와 연동 가능성 확인"을 다룹니다. 두 가지를 봅니다: (1) Reflex 백엔드 자체가 FastAPI라는 사실, (2) **완전히 별도로 떠 있는** FastAPI/Django 서버를 이벤트 핸들러에서 호출하는 방법.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [ ] 배포 (도커 또는 Reflex 클라우드)     (study9~10 예정)
```

대응 실습: [`demo/demo/state.py`](./demo/demo/state.py)의 `load_fruit_fact`, 신규 [`demo/external_api/`](./demo/external_api) (별도 FastAPI 서버)

---

## 1. Reflex 백엔드는 이미 FastAPI다

study0에서 짚었듯, `reflex run`을 실행하면 `http://localhost:8000`에 **백엔드**가 뜹니다. 이건 Reflex가 직접 구현한 서버가 아니라 **FastAPI 앱**입니다. 실제로 `app = rx.App()`으로 만든 `app` 객체는 내부에 `app.api`라는 FastAPI 인스턴스를 들고 있어서, 필요하면 일반 FastAPI 라우트를 직접 추가할 수도 있습니다.

```python
# 참고: Reflex 앱에 직접 REST 엔드포인트를 추가하는 방법 (필요할 때만)
app = rx.App()
app.add_page(index)

@app.api.get("/api/health")
def health():
    return {"status": "ok"}
```

이 방식은 "Reflex 앱과 완전히 한 몸으로 배포되는 작은 API"가 필요할 때 유용합니다. 하지만 실무에서는 **이미 존재하는 별도의 FastAPI/Django 백엔드**를 Reflex 프론트엔드가 호출하는 경우가 더 흔합니다. 아래에서는 그 시나리오를 실습합니다.

## 2. 별도 FastAPI 서버 — `external_api/`

Reflex 앱과 완전히 무관한, 그냥 평범한 FastAPI 프로젝트입니다.

```python
# demo/external_api/main.py
from fastapi import FastAPI

app = FastAPI()

FRUIT_FACTS = {
    "사과": "사과는 장미과 식물로, 배와 가까운 친척이다.",
    ...
}

@app.get("/api/fruit-fact/{name}")
def get_fruit_fact(name: str) -> dict:
    fact = FRUIT_FACTS.get(name, f"'{name}'에 대한 정보가 아직 등록되지 않았습니다.")
    return {"name": name, "fact": fact}
```

```bash
cd demo
pip install -r external_api/requirements.txt
uvicorn external_api.main:app --port 8001
```

Django라도 URL만 다를 뿐 아래에서 다룰 "Reflex → HTTP 요청 → JSON 응답" 흐름은 동일합니다.

## 3. Reflex 이벤트 핸들러에서 호출하기 — `httpx` + `async`/`yield`

```python
# state.py
import httpx

EXTERNAL_API_BASE_URL = "http://127.0.0.1:8001"

fruit_fact: str = ""
fruit_fact_loading: bool = False

@rx.event
async def load_fruit_fact(self):
    self.fruit_fact_loading = True
    self.fruit_fact = ""
    yield  # ① 여기까지의 상태(로딩중)를 먼저 브라우저로 보낸다

    name = self.current_fruit["name"]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EXTERNAL_API_BASE_URL}/api/fruit-fact/{name}", timeout=5
            )
            response.raise_for_status()
            self.fruit_fact = response.json()["fact"]   # ② 완료 후 다시 갱신
    except httpx.HTTPError:
        self.fruit_fact = "정보를 가져오지 못했습니다. external_api 서버가 실행 중인지 확인하세요."
    finally:
        self.fruit_fact_loading = False
```

- **왜 `async def` + `yield`인가?** 이벤트 핸들러가 평범한 `def`이면, "로딩중" 상태로 바꿔도 함수가 끝날 때까지(HTTP 응답이 올 때까지) 브라우저에 아무것도 전송되지 않습니다. `yield`를 쓰면 그 지점까지의 변경사항을 **중간 스냅샷으로 즉시 전송**하고, 이후 코드(HTTP 요청)를 계속 진행합니다. Vue/React에서 `isLoading = true` → `await axios.get(...)` → `isLoading = false`를 쓰던 것과 목적은 같지만, Reflex는 "중간 전송 시점"을 `yield`로 명시적으로 표시해야 합니다.
- `httpx.AsyncClient`: Reflex 백엔드가 비동기(async) 서버이므로, 여기서 블로킹 방식(`requests` 라이브러리)을 쓰면 그동안 서버 전체가 다른 요청을 처리하지 못합니다. 그래서 비동기 HTTP 클라이언트(`httpx`)를 씁니다.
- `try`/`except`/`finally`로 **로딩 상태를 항상 정리**합니다. 요청이 실패해도 `fruit_fact_loading`이 `True`로 멈춰있지 않도록 하는, Vue/React에서도 익숙한 패턴입니다.

## 4. 화면에 연결하기

```python
# pages/fruit_detail.py
rx.button(
    "재미있는 사실 보기 (외부 API 호출)",
    on_click=State.load_fruit_fact,
    loading=State.fruit_fact_loading,   # rx.button이 로딩 상태를 알아서 스피너로 표시
),
rx.cond(State.fruit_fact != "", rx.text(State.fruit_fact)),
```

- `rx.button`의 `loading` prop에 Var를 연결하면, 값이 `True`인 동안 버튼이 자동으로 스피너+비활성 상태로 바뀝니다. 로딩 UI를 직접 조립할 필요가 없습니다.

## 5. 실행 확인 (두 개의 서버를 동시에 띄움)

```bash
# 터미널 1
cd demo
uvicorn external_api.main:app --port 8001

# 터미널 2
cd demo
reflex run
```

- `http://localhost:3000/fruit/1`(사과) 접속 → "재미있는 사실 보기" 클릭 → 버튼이 잠깐 로딩 상태였다가 "사과는 장미과 식물로..." 문구가 나타나는지 확인
- 터미널 1(외부 API)을 끈 상태에서 다시 클릭 → "정보를 가져오지 못했습니다..." 에러 문구가 나타나는지 확인 (예외 처리 확인)
- 두 서버 모두 각자 다른 포트(`8000` Reflex 백엔드, `8001` 외부 API)에서 독립적으로 떠 있다는 것을 `curl http://localhost:8001/api/fruit-fact/사과`로 직접 확인

## 6. 다음 단계 (study7, 고급2 예정)

- 지금까지 `self.fruits`는 서버 프로세스가 재시작되면 초기값으로 리셋되는 **메모리 상의 데이터**였습니다. study7에서 Reflex 내장 ORM(`rx.Model`)으로 진짜 데이터베이스에 저장합니다.

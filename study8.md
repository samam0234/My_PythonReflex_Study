# study8 (고급3) — 로그인 상태 관리 (보호된 페이지)

지금까지는 모든 방문자가 같은 화면을 봤습니다. 이번 단계에서 **로그인 상태**를 State로 관리하고, 로그인한 사용자만 볼 수 있는 페이지를 만듭니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [ ] 배포 (도커 또는 Reflex 클라우드)     (study9~10 예정)
```

> ⚠ **주의**: 이 실습은 "State로 로그인 여부를 표현하고 페이지를 보호한다"는 **개념**을 보여주는 데모입니다. 비밀번호를 코드에 평문으로 두거나(`DEMO_USERS = {"demo": "reflex123"}`) 해시 없이 비교하는 것은 실제 서비스에서는 절대 안 됩니다. 진짜 서비스라면 `passlib`/`bcrypt`로 비밀번호를 해시하고, 사용자 정보를 study7에서 배운 DB에 저장해야 합니다.

대응 실습: 신규 [`pages/login.py`](./demo/demo/pages/login.py), [`pages/admin.py`](./demo/demo/pages/admin.py) / 변경 [`state.py`](./demo/demo/state.py), [`demo.py`](./demo/demo/demo.py)

---

## 1. 로그인 상태를 State로 표현하기

```python
# state.py
DEMO_USERS = {"demo": "reflex123"}  # 데모용. 실서비스는 DB + 해시 필수

username_input: str = ""
password_input: str = ""
login_error: str = ""
is_logged_in: bool = False
current_username: str = ""

@rx.event
def login(self):
    username = self.username_input.strip()
    if DEMO_USERS.get(username) != self.password_input:
        self.login_error = "아이디 또는 비밀번호가 올바르지 않습니다."
        return
    self.is_logged_in = True
    self.current_username = username
    self.password_input = ""
    return rx.redirect("/admin")
```

- `is_logged_in`은 그냥 `bool` 타입 State 값입니다. Vue의 Pinia 스토어, React의 `Context`/`Zustand`로 로그인 상태를 전역 관리하던 것과 원리는 같습니다 — Reflex에서는 **State 클래스 자체가 이미 전역 스토어**이므로 별도 라이브러리가 필요 없습니다.
- 이벤트 핸들러가 `return rx.redirect("/admin")`을 반환하면, "이 이벤트가 끝난 뒤 `/admin`으로 이동해라"는 또 다른 이벤트가 이어서 실행됩니다. 로그인 성공 후 리다이렉트하는 흔한 패턴입니다.

## 2. 보호된 페이지 — `on_load`로 접근을 막기

```python
@rx.event
def require_login(self):
    if not self.is_logged_in:
        return rx.redirect("/login")
```

```python
# demo.py
app.add_page(admin_page, route="/admin", on_load=State.require_login)
```

| Vue Router | React Router | Reflex |
|---|---|---|
| `beforeEnter` 네비게이션 가드 | Protected Route 컴포넌트 / `loader` | 페이지의 `on_load` 이벤트 핸들러 |

- 로그인 안 한 사용자가 주소창에 `/admin`을 직접 입력해도, 페이지가 로드되자마자 `require_login`이 실행되어 `/login`으로 돌려보냅니다.
- **주의**: 이 방식은 "화면을 보여줄지 말지"를 서버 로직으로 막는 것이지, `/admin` 페이지 자체가 애초에 클라이언트에 전송되지 않는 것은 아닙니다(Reflex 컴파일 구조상 모든 페이지의 컴포넌트 트리는 정적으로 빌드됩니다). 정말 민감한 데이터라면 **화면에 보여줄지 여부뿐 아니라, 그 데이터를 담은 이벤트 핸들러 자체도** `if not self.is_logged_in: return`으로 한 번 더 막아야 합니다.

## 3. 로그인 폼 / 관리자 페이지

```python
# pages/login.py (핵심)
rx.input(placeholder="아이디", value=State.username_input, on_change=State.set_username_input),
rx.input(placeholder="비밀번호", type="password", value=State.password_input, on_change=State.set_password_input),
rx.button("로그인", on_click=State.login),
rx.cond(State.login_error != "", rx.text(State.login_error, color="red")),
```

- study3~4에서 만든 폼 패턴(Controlled Input + 서버 검증 + 에러 메시지)이 로그인 폼에도 **그대로** 재사용됩니다. "새로운 문법"이 아니라 "이미 배운 패턴의 또 다른 사례"라는 점이 중요합니다.
- `type="password"`: 일반 HTML `<input type="password">`와 동일하게 입력값을 가려줍니다.

## 4. 상태 지속(persist)에 대한 참고

새로고침해도 `is_logged_in`이 유지되는지 궁금할 수 있습니다. Reflex는 브라우저에 토큰(클라이언트 id)을 저장해두고, 같은 토큰으로 재접속하면 서버에 남아있는 State를 이어서 씁니다 — study2에서 확인한 "새로고침해도 과일 목록이 유지된다"와 같은 원리로, 로그인 상태도 **서버 프로세스가 살아있는 동안은** 유지됩니다.

다만 이건 "탭을 껐다 켜도 로그인 유지"나 "여러 기기에서 로그인 공유" 같은 실제 서비스의 요구사항과는 다릅니다. 실제 서비스는 보통 서버 재시작에도 살아남는 **JWT/세션 쿠키**를 씁니다. Reflex는 `rx.Cookie`, `rx.LocalStorage` 타입으로 State 값을 브라우저 쿠키/로컬스토리지에 자동 동기화하는 기능을 제공하므로, 진짜 인증을 구현할 때는 이 타입을 사용하는 것을 검토합니다.

## 5. 실행 확인

```bash
cd demo
reflex run
```

- `http://localhost:3000/admin` 직접 접속 → 로그인 안 한 상태라면 자동으로 `/login`으로 이동하는지 확인
- 틀린 비밀번호로 로그인 시도 → 에러 메시지가 뜨는지 확인
- `demo` / `reflex123`으로 로그인 → `/admin`으로 이동하고 "환영합니다, demo님"이 보이는지 확인
- "로그아웃" 클릭 → `/login`으로 돌아오는지, 이후 다시 `/admin`에 직접 접속하면 또 `/login`으로 튕기는지 확인
- 홈 화면(`/`) 우측 상단의 "관리자 페이지" 버튼으로도 진입 가능한지 확인

## 6. 다음 단계 (study9, 고급4 예정)

- 지금까지는 전부 `reflex run`(개발 모드)으로만 확인했습니다. study9에서 **프로덕션 배포를 위한 설정**(환경변수, `reflex export`)을 다룹니다.

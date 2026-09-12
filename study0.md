# study0 — Reflex 시작 전 React 기초 이론

이 문서는 실습(코드 작성) 이전에, Reflex를 이해하는 데 필요한 최소한의 React 개념을 정리한 문서입니다.
[Vue.js 학습](../vue.js/study0.md), [React 학습](../react/study0.md)을 먼저 마친 상태를 전제로 합니다.

```
- [ ] Reflex 프로젝트 생성과 실행
- [ ] State 클래스로 화면 상태 관리
- [ ] 이벤트 핸들러로 CRUD
- [ ] 라우팅 / 페이지 분리
- [ ] FastAPI 또는 Django API와 연동 가능성 확인
- [ ] 배포 (도커 또는 Reflex 클라우드)
```

(출처: [Notion — Python Reflex](https://app.notion.com/p/Python-Reflex-3d6d7dec5e2e817a836dd23576cb2e1e) 학습 목표)

---

## 0. Reflex는 "Python으로 React 앱을 만드는 컴파일러"다

Notion 정리 메모의 비교표를 다시 보면:

| 항목 | Reflex | Vue / React |
|---|---|---|
| 언어 | Python | JS / TS |
| 상태 | State 클래스 | ref / useState |
| 생태계 | Python 중심 팀 | 기업 표준 프론트 |

여기서 중요한 사실 하나가 빠져 있습니다: **Reflex로 짠 Python 코드는 실제로는 React(정확히는 Next.js) 프로젝트로 컴파일되어 브라우저에서 실행됩니다.**

```bash
reflex init   # 프로젝트를 만들면
```

을 실행하면 프로젝트 폴더 안에 `.web/`이라는 숨은 폴더가 생기는데, 이 안에 **진짜 Next.js(React) 프로젝트**가 들어 있습니다. `reflex run`을 실행하면:

1. 우리가 짠 Python 코드(컴포넌트 함수, State 클래스)를 읽어서
2. `.web/` 안에 **React 컴포넌트(.js/.tsx) 코드를 자동 생성**하고
3. Next.js 개발 서버로 그 코드를 실행합니다.

즉 우리는 Python만 쓰지만, 브라우저에 실제로 도달하는 것은 여전히 **Virtual DOM, 컴포넌트 트리, props, 이벤트 핸들러**로 이루어진 React 앱입니다. 그래서 Reflex를 제대로 이해하려면 "이 Python 코드가 어떤 React 개념으로 변환되는가"를 알아야 하고, 그게 이 문서의 목적입니다. (Vue/React를 먼저 배운 이유가 여기 있습니다 — 새 개념이 아니라 **번역**입니다.)

## 1. Virtual DOM — 개념은 동일, 주체만 다르다

> 상태가 바뀌면, 실제 DOM을 직접 조작하지 않고 "가상의 DOM"을 새로 만들어 이전 것과 비교(diffing)한 뒤, 달라진 부분만 실제 DOM에 반영한다.

Vue/React에서는 **브라우저(클라이언트)** 에서 이 diffing이 일어났습니다. Reflex는 조금 다릅니다.

- Reflex 앱은 **서버 프로세스**가 Python으로 State를 들고 있습니다.
- 브라우저는 이벤트(클릭 등)가 발생하면 **WebSocket으로 서버에 이벤트를 전송**합니다.
- 서버는 Python 이벤트 핸들러를 실행해 State를 바꾸고, **바뀐 부분(delta)만 WebSocket으로 브라우저에 다시 전송**합니다.
- 브라우저 쪽 React 코드가 이 delta를 받아서 평소처럼 Virtual DOM diffing을 하고 실제 DOM에 반영합니다.

정리하면: **"상태 → 화면 갱신" 파이프라인의 앞부분(상태 계산)이 서버로 옮겨갔을 뿐, 뒷부분(Virtual DOM diffing)은 여전히 브라우저의 React가 담당**합니다. 이 구조 때문에 Reflex 앱은 기본적으로 **서버와 연결이 유지되는(stateful) 앱**입니다 — REST API처럼 매 요청이 독립적이지 않습니다.

## 2. 컴포넌트 = 함수 (JSX 자리에 Python 함수 호출)

React의 핵심 아이디어를 다시 떠올려 봅니다.

> 컴포넌트 = JSX를 반환하는 함수. 이름은 대문자로 시작.

Reflex도 원칙은 같습니다: **컴포넌트 = `rx.Component`를 반환하는 Python 함수**입니다. 다른 점은 "반환값을 어떻게 표현하는가"입니다.

```jsx
// React (JSX)
function FruitCard({ fruit }) {
  return (
    <li className="fruit-card">
      <span>{fruit.name}</span>
    </li>
  )
}
```

```python
# Reflex (Python 함수 호출로 트리를 구성)
def fruit_card(fruit: dict) -> rx.Component:
    return rx.list_item(
        rx.text(fruit["name"]),
        class_name="fruit-card",
    )
```

JSX가 "HTML처럼 생긴 문법"이었다면, Reflex는 **HTML 태그 하나하나가 Python 함수(`rx.text`, `rx.button`, `rx.vstack`...)** 입니다. 자식 요소는 함수의 위치 인자로, 속성(HTML의 attribute, React의 props)은 키워드 인자로 전달합니다.

| React JSX | Reflex Python | 비고 |
|---|---|---|
| `<div>...</div>` | `rx.box(...)` | 자식은 위치 인자로 나열 |
| `<p className="x">{msg}</p>` | `rx.text(msg, class_name="x")` | 속성은 키워드 인자 |
| `{items.map(i => <Card key={i.id} item={i}/>)}` | `rx.foreach(items, lambda i: card(i))` | 리스트 렌더링 전용 함수 |
| `{cond ? <A/> : <B/>}` | `rx.cond(cond, a(), b())` | 조건부 렌더링 전용 함수 |
| `<Card item={i} />` (props) | `def card(item): ...` 호출 시 인자로 전달 | 함수 파라미터 = props |
| `{children}` | 함수의 위치 인자로 받은 `*children` | 같은 역할 |

**왜 `rx.foreach`/`rx.cond` 같은 전용 함수가 필요한가?** Python의 `if`/`for`는 "지금 이 순간" 값을 보고 한 번 실행되는 일반 코드입니다. 하지만 Reflex의 State 값은 **아직 값이 정해지지 않은 심볼(`Var`)**일 수 있습니다(브라우저에서 실행 중 서버 상태에 따라 달라짐). 그래서 일반 Python `if item in items`처럼 쓰면 안 되고, "이 조건/리스트는 나중에 서버 상태에 따라 평가된다"는 것을 Reflex 컴파일러에게 알려주는 **전용 컴포넌트 함수**를 대신 씁니다. 이 부분이 Vue/React와 가장 다르면서 Reflex 학습 초반에 가장 헷갈리는 지점이라, study2~study3에서 실습으로 다시 다룹니다.

## 3. State — `useState`/`ref`가 파이썬 클래스가 되다

| Vue | React | Reflex |
|---|---|---|
| `const count = ref(0)` | `const [count, setCount] = useState(0)` | `class State(rx.State): count: int = 0` |
| 읽기 | `count` / `count.value` | `count` |
| 쓰기 | `count.value = 1` | `setCount(1)` | `self.count = 1` (이벤트 핸들러 메서드 안에서) |

React에서 "왜 `count = 1`처럼 직접 대입하면 안 되고 `setCount`를 불러야 하는가"를 배웠다면, Reflex의 답은 오히려 Vue와 비슷합니다: **Reflex의 State 클래스는 속성에 값을 대입하는 순간(`self.count = 1`) 자동으로 변경을 감지**해서 브라우저에 delta를 보냅니다. 별도의 setter 함수가 없습니다. 대신 그 대입은 **반드시 State 클래스에 정의된 메서드(이벤트 핸들러) 안에서만** 일어나야 하고, 그 메서드는 버튼의 `on_click` 같은 곳에 연결되어야 실제로 호출됩니다. (자세한 내용은 study2에서.)

## 4. 단방향 데이터 흐름 — 원칙은 동일

Reflex도 "부모 → 자식은 인자(props)로, 자식 → 부모는 콜백으로"라는 원칙을 그대로 따릅니다. 다만 이벤트 핸들러 자체가 State 클래스의 메서드이기 때문에, "콜백을 내려준다"기보다는 **"버튼에 State의 메서드 이름을 연결한다"**는 감각에 가깝습니다.

```python
class State(rx.State):
    liked: bool = False

    @rx.event
    def like(self):
        self.liked = True

def like_button() -> rx.Component:
    return rx.button("좋아요", on_click=State.like)
```

## 5. Node.js / npm — 여전히 필요하다

Reflex는 "JS를 안 써도 된다"는 프레임워크이지, "JS 런타임이 필요 없다"는 뜻이 아닙니다. `reflex init`/`reflex run`은 내부적으로 **Node.js(및 번들러)를 다운로드하고 사용**해서 `.web/` 폴더의 Next.js 앱을 빌드·실행합니다.

**실습 전 확인할 것**:

```bash
python --version   # 3.10 이상 (가능하면 3.11+, Reflex가 3.10을 곧 지원 종료 예정)
node --version     # Reflex가 내부적으로 요구하는 버전 이상
```

## 6. 아키텍처 한 장 요약

```
브라우저 (React/Next.js, .web/ 에서 생성됨)
   │  이벤트 발생(클릭 등) → WebSocket으로 전송
   ▼
Reflex 백엔드 (Python, FastAPI 기반)
   │  이벤트 핸들러 실행 → State 변경 → 바뀐 값(delta)만 계산
   ▼
브라우저로 delta 전송 → React가 Virtual DOM diffing → 실제 DOM 갱신
```

이 구조 때문에 Reflex 앱은 배포할 때 **정적 사이트 하나**가 아니라 **프론트엔드(정적 빌드) + 백엔드(상시 실행되는 Python 서버)** 두 부분을 함께 운영해야 합니다 (study9~study10 배포 파트에서 다룸).

## 7. 학습 로드맵 (전체 목차)

| 문서 | 내용 |
|---|---|
| study0 (이 문서) | Reflex 이해에 필요한 React 기초 이론 |
| study1 | Reflex 프로젝트 생성, 명령어, 기본 컴포넌트 실습 |
| study2 | State 클래스로 화면 상태 관리 |
| study3 | 이벤트 핸들러로 CRUD (추가/수정/삭제) |
| study4 | 컴포넌트 분리, 폼 상태 + 검증 |
| study5 | 라우팅 / 페이지 분리 |
| study6 (고급1) | Reflex의 FastAPI 기반 구조와 외부 API 연동 |
| study7 (고급2) | 데이터베이스 연동 (`rx.Model`, 마이그레이션) |
| study8 (고급3) | 로그인/인증 상태 관리 (보호된 페이지) |
| study9 (고급4) | 배포 준비 (환경설정, 프로덕션 빌드) |
| study10 (고급5) | Docker / Reflex Cloud 배포 |
| studyFinal | 지금까지 배운 것을 합쳐 미니 게시판 웹사이트 제작 |

---

## 부록: 용어 미니 사전 (React 대비 Reflex 용어)

| 용어 | 한 줄 설명 |
|---|---|
| `rx.Component` | 화면의 한 조각. Python 함수가 반환하는 값 (React 컴포넌트에 대응) |
| `rx.State` | 상태를 담는 Python 클래스 (useState/ref들의 모음에 대응) |
| `Var` | State 속성이 프론트엔드로 컴파일될 때 갖는 "아직 확정 안 된 값"을 나타내는 심볼 |
| `ComputedVar` (`@rx.var`) | 다른 상태값으로부터 계산되는 파생 값 (Vue의 `computed`, React의 파생 state에 대응) |
| `event handler` | State 클래스의 메서드. `on_click` 등에 연결하면 클릭 시 서버에서 실행됨 |
| `rx.foreach` | 리스트를 반복 렌더링하는 전용 컴포넌트 (`v-for`/`.map()`에 대응) |
| `rx.cond` | 조건부 렌더링 전용 컴포넌트 (`v-if`/삼항연산자에 대응) |
| `.web/` | Reflex가 자동 생성하는 실제 Next.js(React) 프로젝트 폴더 |
| `rxconfig.py` | 프로젝트 전역 설정 파일 (Vite `vite.config.js`에 대응) |

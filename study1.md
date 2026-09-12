# study1 — Reflex 프로젝트 생성 & 컴포넌트 함수 실습

study0에서 이론을 훑었으니, 실제로 프로젝트를 만들고 화면에 뭔가 그려봅니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [ ] State 클래스로 화면 상태 관리        (study2 예정)
- [ ] 이벤트 핸들러로 CRUD               (study3 예정)
- [ ] 라우팅 / 페이지 분리                (study5 예정)
- [ ] FastAPI/Django 연동 가능성 확인      (study6 예정)
- [ ] 배포 (도커 또는 Reflex 클라우드)     (study9~10 예정)
```

대응하는 실습 프로젝트: [`demo/`](./demo)

---

## 1. 설치 및 프로젝트 생성 명령어

Reflex는 Python 패키지이므로 프로젝트마다 **독립된 가상환경**을 만드는 것을 권장합니다.

```bash
cd demo                      # 프로젝트를 만들 폴더로 이동 (빈 폴더여야 함)
python -m venv .venv         # 가상환경 생성 (Python 3.11+ 권장, 3.10은 지원 종료 예정)
source .venv/Scripts/activate  # Windows(Git Bash) 기준. PowerShell은 .venv\Scripts\Activate.ps1
pip install reflex           # Reflex 설치

reflex init                  # 현재 폴더를 Reflex 프로젝트로 초기화
```

- `reflex init`: Vue/React의 `npm create vite@latest`에 대응하는 스캐폴딩 명령어. 폴더 이름을 앱 이름으로 사용합니다.
- `--template blank`: 빈 템플릿(기본값에 가까움). 그 외 `--template` 목록은 `reflex init --help`로 확인 가능합니다.

> **Windows 참고**: `reflex init`/`reflex run`이 한글이 섞인 파일(자동 생성 `AGENTS.md` 등)을 쓰다가 콘솔 코드페이지(cp949) 때문에 `UnicodeEncodeError`가 날 수 있습니다. 아래처럼 UTF-8을 강제하면 해결됩니다.
> ```bash
> export PYTHONUTF8=1
> export PYTHONIOENCODING=utf-8
> ```

```bash
reflex run    # 개발 서버 실행 (프론트 http://localhost:3000, 백엔드 http://localhost:8000)
reflex export # 프로덕션 빌드 (study9~10에서 다룸)
```

## 2. 생성된 폴더 구조 (핵심만)

```
demo/
├─ rxconfig.py         # 프로젝트 전역 설정. Vite의 vite.config.js에 대응
├─ requirements.txt    # pip 의존성 목록 (package.json의 dependencies에 대응)
├─ assets/             # 정적 파일(파비콘, 이미지 등). public/에 대응
├─ demo/               # 앱 이름과 같은 이름의 Python 패키지. 실제 코드는 여기
│  ├─ __init__.py
│  └─ demo.py          # 진입점. App 인스턴스와 페이지를 정의
└─ .web/               # ⚠ 자동 생성되는 진짜 Next.js(React) 프로젝트 (건드리지 않음, .gitignore 대상)
```

`rxconfig.py`:

```python
import reflex as rx

config = rx.Config(
    app_name="demo",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),   # Tailwind CSS 유틸리티 클래스 사용 가능
        rx.plugins.RadixThemesPlugin(),  # 기본 UI 컴포넌트 테마(Radix Themes)
    ],
)
```

- `app_name`: `demo/demo.py`처럼 "패키지명/패키지명.py" 규칙으로 진입점 파일을 찾는 데 쓰입니다.
- `plugins`: Vue/React 생태계의 "Vite 플러그인"과 같은 개념. Reflex는 기본적으로 Radix Themes(디자인 시스템)와 Tailwind가 세팅되어 있어서 별도 CSS 없이 바로 스타일이 적용된 컴포넌트를 쓸 수 있습니다.

## 3. 컴포넌트 함수 실습 — 인자(props)와 자식 요소(children)

study0에서 배운 개념을 실제 코드로 확인하기 위해 "과일 재고 목록"을 3개의 컴포넌트 함수로 나눠서 만들었습니다 (Vue/React 학습의 과일 목록 실습과 같은 소재로 비교하기 쉽게 구성).

파일: [`demo/demo/components/`](./demo/demo/components)

### 3.1 `fruit_list.py` — 목록을 구성하는 최상위 함수

```python
from .fruit_card import fruit_card

initial_fruits = [
    {"id": 1, "name": "사과", "in_stock": True},
    {"id": 2, "name": "바나나", "in_stock": False},
    {"id": 3, "name": "포도", "in_stock": True},
]

def fruit_list_practice() -> rx.Component:
    return rx.vstack(
        rx.heading("실습1: 과일 재고 목록", size="5"),
        rx.list(
            *[fruit_card(fruit) for fruit in initial_fruits],
            list_style_type="none",
            width="100%",
        ),
        align="start",
        width="100%",
        max_width="480px",
    )
```

- `initial_fruits`는 그냥 평범한 Python list — study0에서 말한 "Reflex도 결국 Python 함수 호출"이라는 게 여기서 체감됩니다.
- `*[fruit_card(fruit) for fruit in initial_fruits]`: Vue의 `v-for`, React의 `.map()`에 대응하는 자리입니다. **아직 State가 아니므로** 일반 Python 리스트 컴프리헨션을 그대로 써도 됩니다. study2에서 이 리스트가 State 안으로 들어가면 왜 `rx.foreach`로 바꿔야 하는지 확인합니다.
- `rx.list(*[...])`: 별표(`*`)는 리스트를 풀어서 각 요소를 `rx.list`의 개별 위치 인자(=자식)로 전달하는 Python 문법입니다. JSX의 "여러 자식 엘리먼트를 나열"하는 것과 같은 결과를 만듭니다.

### 3.2 `fruit_card.py` — 인자(props)를 받는 컴포넌트 함수

```python
from .fruit_badge import fruit_badge

def fruit_card(fruit: dict) -> rx.Component:
    return rx.list_item(
        rx.hstack(
            rx.text(
                fruit["name"],
                text_decoration="line-through" if not fruit["in_stock"] else "none",
            ),
            fruit_badge(
                "재고 있음" if fruit["in_stock"] else "품절",
                soldout=not fruit["in_stock"],
            ),
            justify="between",
            width="100%",
        ),
        padding="0.5em 0",
    )
```

- `def fruit_card(fruit: dict)`: 함수의 매개변수가 곧 **props**입니다. Vue의 `defineProps`, React의 구조분해 매개변수와 같은 역할을 "그냥 평범한 Python 함수 매개변수"가 대신합니다.
- 조건에 따라 다른 스타일/문구를 계산하는 부분(`if not fruit["in_stock"] else ...`)은 지금은 **컴포넌트 트리를 만드는 시점(빌드 타임)에 한 번 실행되는 일반 Python 코드**라서 삼항연산자를 그대로 써도 됩니다.

### 3.3 `fruit_badge.py` — `*children` 실습

```python
def fruit_badge(*children, soldout: bool = False) -> rx.Component:
    return rx.badge(
        *children,
        color_scheme="red" if soldout else "green",
        variant="solid",
    )
```

- `*children`은 **React의 `children` prop을 파이썬 함수의 가변 인자로 그대로 흉내 낸 것**입니다. Reflex에는 JSX의 "태그 사이 내용" 같은 문법이 없으므로, "이 함수에 넘긴 위치 인자들을 그대로 하위 컴포넌트에 전달한다"는 관례로 같은 효과를 냅니다.
- Vue의 `<slot />`과 목적이 같습니다: "이 컴포넌트를 감싸 쓰는 쪽에서 내용물을 채워 넣는다."

### 3.4 컴포넌트 트리로 정리

```
index (demo.py)
└─ fruit_list_practice   (고정 리스트를 갖고 있음, 파이썬 for로 반복)
   └─ fruit_card × 3      (fruit dict 하나를 인자로 받음)
      └─ fruit_badge       (soldout 인자 + *children으로 문구를 받음)
```

데이터는 위에서 아래로만 흐릅니다 (study0에서 다룬 단방향 데이터 흐름). 지금은 콜백(자식→부모 통신)이 없어서 화살표가 한 방향뿐이지만, study3에서 이벤트 핸들러로 자식이 부모(State)에 변경을 요청하는 패턴을 추가합니다.

## 4. 실행 확인

```bash
cd demo
reflex run
```

- `http://localhost:3000` 접속 → "실습1: 과일 재고 목록" 섹션이 보이는지 확인
- 사과/포도는 초록색 "재고 있음" 배지, 바나나는 취소선 + 빨간색 "품절" 배지로 보이는지 확인
- 브라우저 개발자 도구 콘솔에 에러가 없는지 확인

터미널에서는 개발 서버를 띄운 뒤 `curl -s http://localhost:3000/`로 200 응답(HTML 셸)을 받는지, `curl -s http://localhost:8000/ping`으로 백엔드가 살아있는지, `reflex export`가 에러 없이 빌드되는지까지 확인했습니다. Reflex 앱은 React/Vite 앱과 달리 **정적 HTML만으로는 실제 화면 내용을 확인할 수 없다는 점**(study0의 아키텍처 설명 참고 — 초기 HTML은 빈 셸이고 브라우저 JS + WebSocket이 실제 내용을 채움)에 유의합니다.

## 5. 다음 단계 (study2 예정)

- `fruit_list_practice`의 고정 리스트를 **State 클래스 안으로 이동**시켜 "진짜 상태"로 바꾸기
- 상태가 된 리스트를 화면에 그릴 때 `rx.foreach`가 왜 필요한지 확인하기
- 이벤트 핸들러(`on_click`)로 재고 토글 버튼 추가하기

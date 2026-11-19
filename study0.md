# study0 — Reflex 환경 설정

목표: 독립된 Reflex 학습 앱을 생성하고 폴더·실행 포트·핵심 용어를 설명한다.

실제 구현: [demo/rxconfig.py](demo/rxconfig.py), [demo/requirements.txt](demo/requirements.txt). `demo/`에서 실행 후 `/`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

Reflex는 Python으로 UI, 서버 상태, 이벤트를 정의한다. 컴포넌트 함수는 화면 구조를 만들고 `rx.App`은 페이지를 등록한다. 브라우저 이벤트는 WebSocket으로 서버에 전달되고, 서버가 State를 변경하면 변경분(delta)이 화면에 전달된다.

이 과정에서 프론트 자산과 Python 백엔드가 모두 필요하다. 개발 기본 포트는 화면 3000, 백엔드 8000이다. 0.9 계열 프로덕션은 단일 포트 운영을 지원하므로 개발 포트 두 개를 반드시 외부에 공개하는 것은 아니다.

이 과정은 저장소와 같은 **Reflex 0.9.11 / Python 3.12**를 기준으로 한다. 노션의 Python 3.11+ 권장 사항을 따른다. 최신 버전으로 임의 업그레이드하지 않는다. Bun 등 프론트 빌드 도구는 Reflex가 관리하므로 Node.js 수동 설치를 선행 조건으로 두지 않는다.

| 용어 | 의미 |
|---|---|
| Component | `rx.text`, `rx.button` 등 화면 요소 |
| State | 서버에서 관리하는 사용자별 상태 클래스 |
| Var | 컴포넌트를 만들 때 사용하는 상태 표현식 |
| event | 입력·클릭에 반응하는 서버 메서드 |
| computed var | `@rx.var`로 정의한 파생 값 |
| `.web/` | 자동 생성 프론트 자산·빌드 디렉터리 |
| `rxconfig.py` | 앱 이름·DB·포트·배포 주소 설정 |

## 🛠️ 실기(코드·줄별 설명)

이하 명령은 처음부터 빈 앱을 생성하는 연습이다. 저장소에는 같은 개념을 `demo/demo/lessons/`의 별도 모듈·URL로 구현했다. 완성된 예제를 바로 실행하려면 README의 `demo/` 절차를 사용한다.

PowerShell:

```powershell
mkdir reflex_lab
cd reflex_lab
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
python -m pip install "reflex[db]==0.9.11"
reflex init --name reflex_lab --template blank
reflex run
```

1. `mkdir`는 기존 앱을 덮어쓰지 않을 빈 폴더를 만든다.
2. `cd`는 이후 모든 명령의 기준 디렉터리를 바꾼다.
3. `py`는 Python 3.12 가상환경을 만든다.
4. `Activate.ps1`은 해당 환경의 Python·CLI를 선택한다.
5. `PYTHONUTF8`은 Python 파일 처리 기본 인코딩을 UTF-8로 맞춘다.
6. `PYTHONIOENCODING`은 표준 입출력을 UTF-8로 맞춘다.
7. `pip install`은 DB 기능에 필요한 extra를 포함해 버전을 고정한다.
8. `init`은 `reflex_lab/reflex_lab.py` 진입점을 생성한다.
9. `run`은 개발 서버를 실행한다. 중지는 `Ctrl+C`다.

```text
reflex_lab/
├── rxconfig.py
├── requirements.txt
├── assets/
├── reflex_lab/
│   ├── __init__.py
│   └── reflex_lab.py
└── .web/                 # 자동 생성, 직접 편집하지 않음
```

재시작 실습을 위해 새 앱의 `rxconfig.py`에도 메모리 모드를 명시한다. 0.9.11 기본값 DISK와 구분한다.

```python
import reflex as rx
from reflex.constants import StateManagerMode

config = rx.Config(
    app_name="reflex_lab",
    state_manager_mode=StateManagerMode.MEMORY,
    db_url="sqlite:///reflex.db",
    plugins=[rx.plugins.SitemapPlugin(), rx.plugins.TailwindV4Plugin(), rx.plugins.RadixThemesPlugin()],
)
```

import 두 줄은 설정과 State 저장 방식 상수를 가져온다. `app_name`은 패키지·진입점 이름, `state_manager_mode`는 재시작 시 사라지는 메모리 상태, `db_url`은 study6에서 사용할 영속 DB다. 플러그인은 빌드·스타일 구성을 생성하며 생성된 `.web/`를 직접 고치지 않는다.

브라우저에서 `http://localhost:3000`을 열어 초기 화면을 확인한다. 다른 터미널의 `Invoke-WebRequest http://localhost:8000/ping`은 백엔드 생존 확인이다. 화면 표시와 WebSocket 연결 성공도 별도로 확인한다.

## 오류 노트

| 증상 | 확인·해결 |
|---|---|
| 한글 파일에서 UnicodeEncodeError | UTF-8 환경변수를 설정하고 새 프로세스로 재실행 |
| 스크립트 실행 정책으로 활성화 실패 | 전역 정책을 바꾸기보다 `.venv/Scripts/python.exe -m reflex run`으로 실행 |
| 포트 사용 중 | 터미널 오류를 확인하고 `reflex run --backend-port 8001`로 변경 |
| 모듈을 찾지 못함 | 현재 디렉터리, `app_name`, 패키지·진입점 이름 일치 확인 |
| Bun 다운로드 실패 | 네트워크·프록시·백신 로그 확인, 생성 폴더를 임의 삭제하지 않기 |

## ☐ 체크리스트

- ☐ [노션 학습 목표] Reflex 설치 → 프로젝트 생성 → 실행 확인을 직접 수행한다.
- ☐ [노션 설치 메모] Python 3.11+ 권장을 반영하고 사용 버전을 기록한다.
- ☐ [노션 설치 메모] Windows UTF-8 변수 두 개의 역할을 설명한다.
- ☐ [노션 설치 메모] Reflex가 관리하는 Bun과 수동 Node.js 설치를 구분한다.
- ☐ [노션 포트 경험] 기본 8000 충돌 시 8001로 분리하고 화면 연결을 재확인한다.
- ☐ 핵심 용어와 자동 생성 `.web/`의 역할을 설명한다.

## 다음 단계 연결

[study1](study1.md)에서 초기 화면을 Hello World로 교체한다. 전체 출처·범위는 [README](README.md)에 있다.

참고: [공식 설치 문서](https://reflex.dev/docs/getting-started/installation/), [0.8→0.9 변경 사항](https://reflex.dev/blog/upgrading-reflex-0-8-to-0-9/).

# Python Reflex 학습 과정과 실행 코드

[노션 Python Reflex](https://app.notion.com/p/Python-Reflex-3d6d7dec5e2e817a836dd23576cb2e1e)을 바탕으로 **Reflex 하나만** 학습하는 과정이다. 문서 21개와 실행 코드·테스트·배포 설정을 연결했다. 기준은 Python 3.12 / Reflex 0.9.11 / SQLModel 0.0.42다.

| 앱 | 용도 | 실행 화면 |
|---|---|---|
| [demo/](demo/) | 독립된 단원별 UI·DB·인증·비동기·차트 실습 | `/study1`~`/study7`, `/study11`, `/study13` |
| [midpoint/](midpoint/) | study0~10 기능만 사용하는 기초 게시판 | 목록·로그인·상세·작성·수정 |
| [project/](project/) | 심화 게시판 | DB 인증·권한·검색·페이지네이션·AI·MCP·운영 지표 |

앱은 한 번에 하나씩 실행하면 기본 포트 3000/8000을 사용할 수 있다. `demo`와 `midpoint`는 로컬 학습용 계정·권한 예제다. 최종 앱은 DB 계정·비밀번호 해시·만료 세션을 사용한다.

## 빠른 시작 — PowerShell

첫 가상환경이 없다면 `py -3.12 -m venv .venv`로 만든다. 저장소 루트에서:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
```

최종 앱:

```powershell
cd project
reflex db migrate
python -m project.manage seed-demo
reflex run
```

`http://localhost:3000`에서 `demo / demo-password-123`, `guest / guest-password-123`으로 시험한다. `seed-demo`는 로컬에서 명시적으로 실행하는 관리 명령이며 운영 환경에서는 거부한다. 운영 계정은 `python -m project.manage create-user 계정 --admin`으로 만들고 비밀번호는 콘솔에서 입력한다. import·서버 시작만으로 계정을 만들지 않는다.

기초 게시판은 저장소 루트에서 `cd midpoint` 후 `reflex db migrate`, `reflex run`으로 실행한다. 계정은 `demo / reflex123`, `guest / guest123`이다. 단원 실습은 `cd demo` 후 같은 두 명령을 실행하고 `/`의 목차에서 이동한다. 앱별 독립 환경은 각 `requirements.txt`로 설치할 수 있다.

기존 `project/reflex.db`의 글은 새 migration이 보존한다. 작성자 이름이 새 계정과 같아도 소유권을 자동 귀속시키지 않는다. 확인한 글에만 `python -m project.manage assign-owner 글번호 계정`을 적용한다. 테스트 도구는 기존 DB 대신 임시 DB를 사용한다.

세 앱의 `rxconfig.py`에 MEMORY State 모드를 명시했다. 설치 버전의 기본값 DISK와 구분하며, State 유실 시 재로그인하고 글·계정은 DB로 보존한다.

실제 키 없이 AI 버튼은 비활성이며, MCP는 `/dashboard`에서 바로 확인할 수 있다. AI를 사용하려면 서버 전용 환경에 `OPENAI_API_KEY`, `AI_MODEL`을 설정하고 재시작한다. 키·원문 토큰·비밀번호를 공개 State·문서·로그·이미지에 넣지 않는다.

## 학습 순서와 실제 코드

| 문서 | 주제 | 구현 |
|---|---|---|
| [study0](study0.md) | 환경·폴더·실행 | [demo/rxconfig.py](demo/rxconfig.py) |
| [study1](study1.md) | Hello World | [demo/demo/lessons/hello.py](demo/demo/lessons/hello.py) |
| [study2](study2.md) | 컴포넌트·모듈 | [demo/demo/lessons/structure.py](demo/demo/lessons/structure.py) |
| [study3](study3.md) | State·Var | [demo/demo/lessons/data.py](demo/demo/lessons/data.py) |
| [study4](study4.md) | 동적 라우팅 | [demo/demo/lessons/routing.py](demo/demo/lessons/routing.py) |
| [study5](study5.md) | 폼·검증 | [demo/demo/lessons/form.py](demo/demo/lessons/form.py) |
| [study6](study6.md) | DB CRUD | [demo/demo/lessons/db_state.py](demo/demo/lessons/db_state.py) |
| [study7](study7.md) | 학습용 인증 | [demo/demo/lessons/auth.py](demo/demo/lessons/auth.py) |
| [study8](study8.md) | 구조·환경변수 | [project/project/settings.py](project/project/settings.py) |
| [study9](study9.md) | 기초 테스트 | [tests/test_midpoint_validation.py](tests/test_midpoint_validation.py) |
| [study10](study10.md) | 빌드·기초 복습 | [tools/verify_app.py](tools/verify_app.py) |
| [studyMidpoint](studyMidpoint.md) | 기초 로그인 게시판 | [midpoint/](midpoint/) |
| [study11](study11.md) | 캐시·비동기 | [demo/demo/lessons/async_lab.py](demo/demo/lessons/async_lab.py) |
| [study12](study12.md) | 성능 측정 | [tools/benchmark.py](tools/benchmark.py) |
| [study13](study13.md) | UI·날짜 유틸 | [demo/demo/lessons/charts.py](demo/demo/lessons/charts.py) |
| [study14](study14.md) | 타입·스키마 | [project/project/schemas.py](project/project/schemas.py) |
| [study15](study15.md) | 테스트·CI | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| [study16](study16.md) | 운영 인증·로그 | [project/project/services/auth.py](project/project/services/auth.py) |
| [study17](study17.md) | Docker·배포 | [deploy/README.md](deploy/README.md) |
| [study18](study18.md) | AI·MCP | [project/project/services/ai.py](project/project/services/ai.py) |
| [studyFinal](studyFinal.md) | 최종 게시판 | [project/](project/) |

각 문서는 **목표 한 줄 → 📖 이론 → 🛠️ 실기(코드·줄별 설명) → 오류 노트 → ☐ 체크리스트 → 다음 단계 연결** 순서다. 모든 학습 파일명은 `study`로 시작한다. 체크리스트는 학습자가 직접 재현할 항목이므로 일괄 완료 표시하지 않았다.

기초 단원의 단일 파일 예제는 개념을 처음 작성하는 최소 예제다. 저장소는 그 코드를 `demo/demo/lessons/` 모듈과 공통 진입점으로 나눠 동시에 실행한다. study14~18·final의 예제는 실제 `project/` 함수·설정과 연결되어 있다. 기초 앱과 심화 앱의 Post 테이블·인증은 별개다.

## 검증 명령과 결과

저장소 루트에서:

```powershell
python -m ruff check .
python -m ruff format --check .
pyright
python -m pytest tests --ignore=tests/e2e -q
python tools/verify_app.py --app demo --mode prod
python tools/verify_app.py --app midpoint --mode prod
python tools/verify_app.py --app project --mode prod
python tools/benchmark.py
python tools/check_deploy.py
```

`verify_app.py`는 임시 DB·새 포트·유료 API 키가 없는 환경에서 migration→필요한 로컬 계정→prod export→단일 포트 서버→Chromium→프로세스 정리를 수행한다. E2E를 직접 실행하면 `REFLEX_E2E_URL`이 없을 때 의도적으로 건너뛴다.

2026-11-19 검증 기록:

| 검사 | 결과 |
|---|---|
| 단위·DB·동시성·AI mock·실제 MCP·migration·복원·State 직렬화 | 59개 통과 |
| demo prod 빌드·브라우저 | 2개 통과 |
| midpoint prod 빌드·브라우저 | 1개 통과 |
| project prod 빌드·브라우저 | 4개 통과 |
| Ruff·포맷·Pyright | 로컬 통과 |
| Compose 해석·배포 셸·CI 의존성 | 로컬 통과 |
| 성능 1,000행, 예열 3회·30회 측정 | [study12](study12.md)의 p95·JSON 크기 표 |

브라우저는 로그인·CRUD·타인 수정 URL·로그아웃·잘못된 ID·페이지네이션·검색·단원 State/폼/DB/캐시·차트 필터·실제 MCP를 확인했다. 토큰 직렬화 제외·만료/폐기·경쟁 요청량·이전 revision·백업 복원은 서비스 테스트로 검증한다. 로그·스크린샷·성능 JSON은 git 제외 `artifacts/`에 저장한다.

GitHub Actions **파일**과 로컬 동등 검사를 구현했다. 원격 Actions 실행은 아직 하지 않았다. Docker CLI는 있지만 엔진이 꺼져 있어 이미지 실행을 검증하지 않았다. 외부 VM·TLS·GHCR 게시·SSH 배포·롤백과 실제 모델 API 호출도 미실행이다. 배포 설정과 준비물은 [deploy/README](deploy/README.md)에 있다.

## 배포·설정·의존성

- 로컬 prod는 공개 API URL을 단일 포트에 맞춘 뒤 빌드한다. `APP_API_URL=http://localhost:3000`, `REFLEX_API_URL=http://localhost:3000`을 설정하고 `reflex run --env prod --single-port`로 실행한다.
- `APP_ENV=production`에서는 명시적인 HTTPS API·화면 origin을 요구한다. Docker·Compose가 이 값을 주입한다.
- `REFLEX_CORS_ALLOWED_ORIGINS`는 쉼표 구분 문자열이다. 0.9.11에서는 JSON 배열 문자열을 넣지 않는다.
- 개발 Windows 환경은 `requirements-dev.txt`, Linux CI·Docker는 전이 의존성과 해시를 고정한 `requirements-dev.lock`, `project/requirements.lock`을 사용한다.
- 모델 API와 MCP SDK는 실제 `project/requirements.txt` 버전으로 고정했다. MCP는 1.30.0 v1 API다.
- Reflex가 생성하는 `.web/`는 직접 편집하지 않는다. npm 의존성은 생성된 `reflex.lock/`으로 추적한다.
- 실제 키·DB·`.env.runtime`·생성 파일은 git·Docker context에서 제외한다.

## 노션 요구사항 대응표

원문 본문 전체를 읽고 설치 메모·학습 목표·제약·학습 기록 표·코드 스니펫 4개·조합 체크 항목·저장소 정보·실제 활용 기록까지 검토했다. 원문에는 별도 `[FW]` 하위 페이지가 없으며 해당 Python Reflex 페이지 자체를 프레임워크 페이지로 해석했다. 필요한 항목은 각 번호의 `☐` 체크리스트에 넣었다.

| 원문 항목 | 새 문서·체크 항목 |
|---|---|
| Python으로 UI·상태·이벤트, 내부 도구 용도 | study0·1·2 |
| 설치→init→run, 3000/8000 포트 | study0 |
| Python 3.11+ 권장 | study0 |
| Windows UTF-8 변수 두 개 | study0·9 |
| Bun 자동 관리·Node 별도 선행 설치 불필요 | study0 |
| rx.Model deprecated, SQLModel 직접 상속 | study6·final |
| 이벤트→WebSocket→Python→delta→화면 | study1·3·12 |
| list/dict 대입·직접 변경 감지 | study3 |
| Var에 Python if/for/not 대신 전용 표현 | study3·4·midpoint |
| 기본 State 재시작 초기화, DB 영속성 | study3·6·midpoint |
| 프론트 자산과 상시 백엔드의 배포 책임 | study10·17 |
| 학습 목표의 생성·State·CRUD·페이지 분리 | study0·3·4·6·midpoint·final |
| 코드 1: 5개 페이지·on_load | study4·midpoint |
| 코드 2: Post 모델·세션·최신순·날짜 변환 | study6·12 |
| 코드 3: 동적 ID·current_post·작성자 재확인 | study4·7·midpoint·16 |
| 코드 4: 로그인 메뉴·빈 목록·foreach | study3·midpoint |
| 데모 로그인과 실제 DB·해시 필요 | study7·16·final |
| Dockerfile·migration 후 실행, Cloud 선택 경로 | study10·17 |
| 실제 활용: 기본 8000 충돌을 8001로 분리 | study0·8 |
| 실제 활용: 중복 가드·yield 로딩·비동기 대기 | study11·18 |
| 실제 활용: 401 refresh 한 번 재시도·세션 만료 | study11 오류 노트·체크리스트, 단독 앱 적용 범위 표시 |
| demo·midpoint·project·GitHub 위치 | 이 문서의 구현 경로·과거 기록 안내 |
| 비교표·다른 프레임워크 선행 학습·비교 과제 | 사용자 “비교하지 말기”에 따라 미포함 |
| 외부 공통 게시판 API 연결·조합 코스·특정 외부 앱 통합 | 사용자 “통합하지 말기”에 따라 미포함, DB CRUD로 선택 |

범위 충돌은 다음과 같이 처리했다. 원문의 체크 과제 “같은 게시판을 공통 API 스펙 v1의 FastAPI에 연결해 보기”와 “코드 줄 수와 화면 전환 방식을 Vue·React 게시판과 비교”는 이 코스의 실행 체크리스트로 가져오지 않는다. 노션의 조합 페이지·외부 앱·공통 API 링크는 독립된 코스이므로 따라가서 범위를 확대하지 않았다. 실제 활용 사례의 포트·로딩·오류 복구 원리는 Reflex 단독 예제로 반영했다. 따라서 비교·통합 금지 조건과 양립하는 원문 항목은 모두 대응하며, 충돌 항목은 숨기지 않고 여기에 기록했다.

노션의 기존 학습 기록과 체크 완료 상태는 **과거 기록**이다. 새 문서의 `☐`는 앞으로 학습자가 검증할 항목이며 기존 완료 표시를 복사하지 않았다. 원문 내용을 그대로 전사하거나 외부 페이지 전체를 구현했다고 주장하지 않는다.

## 과거 기록과 변경 범위

과거의 study 번호·`demo/external_api/`·과일 단일 화면 예제는 이전 학습 자료다. 새 `demo/demo/demo.py`는 외부 프레임워크 서버를 import·실행하지 않는다. 다른 프레임워크 비교·통합은 새 과정의 실행 대상으로 삼지 않았다.

기존 `study0~10.md`와 `studyFinal.md`는 새 목차로 덮어썼고, `study11~18.md`, `studyMidpoint.md`를 추가했다. 이후 코드 작성 요청에 따라 세 앱·테스트·배포 설정과 설명을 구현 상태에 맞췄다. 커밋·푸시는 수행하지 않았다. 연결된 노션의 학습 기록·설치/State/배포 메모·구성 목록을 실제 코드와 검증 결과로 갱신했다. 기존 비교·조합·활용 기록은 보존하고, 미실행 외부 항목은 완료로 표시하지 않았다.

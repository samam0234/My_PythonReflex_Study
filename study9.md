# study9 (고급4) — 배포 준비 (환경설정, 프로덕션 빌드)

지금까지는 전부 `reflex run`(개발 모드)으로만 실행했습니다. 이번 단계에서 **환경변수로 설정을 분리**하고, **프로덕션 빌드(`reflex export`)** 를 만들어 봅니다. 실제 배포(Docker)는 study10에서 이어집니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [~] 배포 (도커 또는 Reflex 클라우드) — 환경설정/빌드까지, Docker는 study10
```

대응 실습: [`rxconfig.py`](./demo/rxconfig.py), [`.env.example`](./demo/.env.example), [`state.py`](./demo/demo/state.py)의 `EXTERNAL_API_BASE_URL`

---

## 1. `rx.Config` 필드는 `REFLEX_*` 환경변수로 자동 덮어써진다

Reflex는 `rxconfig.py`에 쓴 어떤 설정값이든, **`REFLEX_` + 필드명(대문자)** 환경변수로 실행 시점에 덮어쓸 수 있게 이미 만들어놨습니다. 코드를 고치지 않고도 배포 환경마다 다른 값을 줄 수 있습니다.

```bash
REFLEX_DB_URL="postgresql://user:pass@localhost/db" reflex run
REFLEX_CORS_ALLOWED_ORIGINS="https://my-app.com" reflex run
```

## 2. `.env` 파일로 관리하기 — `env_file`

매번 커맨드라인에 환경변수를 나열하는 대신, `rxconfig.py`에 `env_file`을 지정하면 `.env` 파일을 자동으로 읽습니다 (`python-dotenv` 필요).

```python
# rxconfig.py
config = rx.Config(
    app_name="demo",
    db_url="sqlite:///reflex.db",
    env_file=".env",
    cors_allowed_origins=["*"],   # 운영에서는 실제 도메인만 허용
    ...
)
```

```bash
# .env.example (커밋 O — 값 없는 템플릿)
REFLEX_DB_URL=sqlite:///reflex.db
REFLEX_CORS_ALLOWED_ORIGINS=*
EXTERNAL_API_BASE_URL=http://127.0.0.1:8001
```

- `.env.example`은 "어떤 환경변수가 필요한지" 보여주는 **템플릿**이라 커밋합니다. 실제 값이 든 `.env`는 `.gitignore`에 추가해서 **절대 커밋하지 않습니다** (Vue/React 프로젝트에서 `.env`를 깃에 올리면 안 되는 것과 같은 이유 — 비밀번호/키가 노출됩니다).
- `cors_allowed_origins`: 프론트엔드(정적 파일)와 백엔드(API)가 **다른 도메인**에서 서빙될 때, 백엔드가 어떤 출처(origin)의 요청을 허용할지 정합니다. Django의 `CORS_ALLOWED_ORIGINS`, FastAPI의 `CORSMiddleware`와 정확히 같은 개념입니다. 개발 중엔 `"*"`로 편하게 두고, **운영에서는 반드시 실제 프론트 도메인만 명시**해야 합니다.

## 3. "우리 앱만의" 값은 `os.environ`으로 직접

`REFLEX_*` 자동 덮어쓰기는 `rx.Config`의 필드에만 적용됩니다. study6에서 만든 `EXTERNAL_API_BASE_URL`처럼 **우리가 직접 정의한 상수**는 평범하게 `os.environ.get(...)`으로 읽습니다.

```python
# state.py
import os

EXTERNAL_API_BASE_URL = os.environ.get("EXTERNAL_API_BASE_URL", "http://127.0.0.1:8001")
```

`env_file`이 로드해둔 값은 프로세스의 환경변수(`os.environ`)에 그대로 들어가므로, `rx.Config`가 아닌 값도 `.env` 파일 하나로 함께 관리할 수 있습니다.

## 4. 프로덕션 빌드 — `reflex export`

```bash
reflex export --loglevel info
```

이 명령은:

1. 앱을 **프로덕션 모드**로 컴파일하고 (`reflex run`의 dev 모드는 코드 변경 감지, hot reload 등 개발 편의 기능이 켜져 있어 더 느립니다)
2. 프론트엔드를 **정적 파일**로 빌드하고 (`frontend.zip`)
3. 백엔드(Python 앱) 코드를 별도로 묶습니다 (`backend.zip`)

| 산출물 | 내용물 | 배포 방법 |
|---|---|---|
| `frontend.zip` | 순수 HTML/JS/CSS (Next.js 정적 빌드) | Nginx, S3+CloudFront, Vercel 등 **아무 정적 호스팅**에 올리면 끝 |
| `backend.zip` | Reflex 백엔드(FastAPI) Python 코드 | Python이 실행 가능한 서버에서 `reflex run --env prod --backend-only`(또는 study10의 Docker) |

- `--frontend-only`, `--backend-only` 옵션으로 둘 중 하나만 뽑을 수도 있습니다.
- 프론트/백엔드를 **분리 배포**할 경우, 정적 파일 안의 API 호출 주소를 백엔드의 실제 공개 URL로 맞춰야 합니다 — `rxconfig.py`의 `api_url` 필드(역시 `REFLEX_API_URL` 환경변수로 덮어쓰기 가능)가 이 역할을 합니다.

## 5. 실행 확인

```bash
cd demo
reflex export --loglevel info
```

- `frontend.zip`, `backend.zip`이 생성되는지, 에러 없이 끝나는지 확인 (본 저장소에서는 두 파일 모두 `.gitignore`의 `*.zip` 규칙으로 커밋되지 않습니다 — 배포 산출물이지 소스가 아니므로)
- `.env`(예시 값 채운 것)를 만들고 `reflex run`으로 실행 → `REFLEX_CORS_ALLOWED_ORIGINS`를 바꿔보고 실제로 값이 반영되는지 Python REPL에서 `from rxconfig import config; print(config.cors_allowed_origins)`로 확인

## 6. 다음 단계 (study10, 고급5 예정)

- `reflex export`로 만든 산출물을 실제로 **Docker 이미지**에 담아 실행하는 방법을 다룹니다.
- Reflex 팀이 제공하는 **Reflex Cloud** 배포도 간단히 살펴봅니다.

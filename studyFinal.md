# studyFinal — 운영 가능한 Reflex 게시판 완성

목표: midpoint의 기본 기능에 study11~18의 성능·인증·테스트·배포·AI/MCP를 실제 코드로 연결하고 운영 인수 조건을 확인한다.

## 📖 이론

### 기능 확장

| 범위 | 기초 구현 | 최종 구현 | 경로 |
|---|---|---|---|
| 목록 | 전체 dict 조회 | 본문 없는 20개 DTO·검색·정렬 인덱스 | `services/posts.py` |
| 상태 | State·일반 이벤트 | TTL·명시적 무효화·background 잠금·화면 세대 | `state.py` |
| 계정 | 데모 dict | DB 계정·scrypt·만료/폐기 세션·owner_id | `services/auth.py` |
| 보안 | 작성자 재확인 | 로그인 제한·동시 해시 상한·revision 충돌 방지 | `services/auth.py`, `posts.py` |
| UI | 공통 카드·폼 | 테마·집계 차트·MCP 화면·관리자 지표 | `pages/`, `components/` |
| AI | 없음 | 본인 글 요약·하루 10회·시간/출력 제한 | `services/ai.py`, `quota.py` |
| 품질 | 기본 검증 | DB·경쟁 요청·비동기·migration·Chromium·CI | `tests/`, `.github/` |
| 운영 | 수동 실행 | Docker·TLS Compose·백업·배포·롤백 스크립트 | `deploy/` |

앱은 [project/](project/)에 구현했다. 다른 웹 프레임워크와 비교하거나 공통 게시판 API를 통합하지 않는다. 운영 대상은 VM 한 대·앱 한 인스턴스·영속 SQLite이며, 세 앱은 MEMORY State를 명시하며 서버 State 유실 시 재로그인한다. 무중단 다중 인스턴스와 영구 로그인은 제공 범위에 포함하지 않는다.

## 🛠️ 실기(코드·줄별 설명)

### 구현 순서와 구조

```text
project/
├── rxconfig.py, requirements.txt, requirements.lock
├── Dockerfile, docker-entrypoint.sh, .dockerignore
├── alembic/versions/
├── mcp_readonly_server.py
└── project/
    ├── project.py, state.py, models.py, schemas.py
    ├── settings.py, health.py, manage.py, observability.py
    ├── services/auth.py, database.py, posts.py, quota.py, ai.py, mcp_client.py
    ├── components/
    ├── pages/
    └── utils/dates.py
```

1. [studyMidpoint](studyMidpoint.md)의 기초 게시판을 먼저 확인한다.
2. 엄격한 입력 스키마와 목록용 DTO를 적용하고 20행 조회·검색·복합 인덱스를 연결한다.
3. User·LoginSession·요청 카운터를 추가하는 migration을 적용한다. 기존 Post는 owner_id=NULL로 보존한다.
4. 모든 보호 서비스에서 DB 세션·활성 사용자·소유권을 확인하고 수정에는 revision 조건을 둔다.
5. 쓰기 성공 뒤 목록 캐시를 무효화하고 화면 이동·로그아웃 뒤 오래된 AI 결과를 버린다.
6. 공개 집계 차트·실제 read-only MCP·관리자 지표와 readiness를 연결한다.
7. 아래 테스트를 통과한 코드를 prod 빌드하고 외부 운영 조건을 준비한다.

실제 AI 일일 한도 예약:

```python
"""final: 동시에 요청해도 사용자별 하루 10회를 넘지 않는 예약."""

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import CursorResult
from sqlmodel import col

from ..models import AiDaily
from ..settings import get_settings
from .auth import require_user
from .database import open_session
from .errors import LimitExceeded


def reserve_ai_call(raw_token: str) -> None:
    day = datetime.now(timezone.utc).date().isoformat()
    with open_session() as session:
        user = require_user(session, raw_token)
        session.execute(
            insert(AiDaily).values(user_id=user.id, day=day, calls=0).on_conflict_do_nothing()
        )
        result = session.execute(
            update(AiDaily)
            .where(
                col(AiDaily.user_id) == user.id,
                col(AiDaily.day) == day,
                col(AiDaily.calls) < get_settings().ai_daily_limit,
            )
            .values(calls=col(AiDaily.calls) + 1)
        )
        assert isinstance(result, CursorResult)
        if result.rowcount != 1:
            raise LimitExceeded("오늘의 AI 요청 한도를 초과했습니다.")
        session.commit()
```

- 날짜는 서버 UTC를 기준으로 한다.
- 사용자 ID는 폼·공개 State 대신 DB 세션에서 확인한다.
- 첫 요청에 카운터를 만들고 `calls < 10`일 때만 원자적으로 증가시킨다.
- 증가한 행이 없으면 중단한다. 실제 AI 네트워크 호출 **전** commit한다.
- 실패·timeout도 보수적으로 횟수를 소비한다. 10회가 고정 금액을 뜻하지 않으므로 실제 모델 비용도 외부에서 관찰한다.

로컬 실행:

```powershell
cd project
python -m pip install -r requirements.txt
reflex db migrate
python -m project.manage seed-demo
reflex run
```

각 줄은 앱 위치·고정 런타임 설치·이력 적용·명시적 로컬 계정 준비·개발 서버 실행이다. `http://localhost:3000`에서 `demo / demo-password-123`, `guest / guest-password-123`으로 시험한다. 운영에서는 `APP_ENV=production`과 `create-user`를 사용하며 데모 시드는 거부된다.

기존 글은 새 계정과 이름이 같아도 자동 소유권을 부여하지 않는다. 관리자가 검토한 글만 `python -m project.manage assign-owner 글번호 계정`으로 지정한다.

### 성능·보안 점검

| 항목 | 구현·검증 |
|---|---|
| 목록 | 20행·본문 미전송·안정 정렬·literal 검색·별도 DB 읽기 |
| 캐시 | TTL 10초·새로 조회·쓰기 후 무효화·backend 필드 |
| 인증 | 비밀번호 해시·토큰 해시·1시간 만료·폐기·비활성 검사 |
| 권한 | DB owner_id 검사·타인/빈/만료 세션의 DB 불변성 |
| 로그인 제한 | 계정별 5회/분·해시 동시 2개·경쟁 요청 검사 |
| AI | 하루 10회·경쟁 요청 제한·본인 글·timeout·변경 후 결과 거부 |
| 비밀 | backend 토큰의 State 직렬화 제외·로그 필드 제한·이미지 제외 |
| 운영 | 스키마 readiness·관리자 `/ops`·온라인 백업·복원 무결성 |

성능 결과와 측정 한계는 [study12](study12.md)에 있다. JSON 크기는 실제 압축 WS 전송량이 아니며, 차트 도입 전후 번들 전송량은 별도 측정 항목이다.

### Docker·외부 배포

[study17](study17.md)과 [deploy/README](deploy/README.md)를 따른다. 실제 스크립트는 이미지 검증·pull→온라인 백업→앱 중지→migration 1회→readiness 대기 순서다. CI는 모든 앱의 prod E2E 성공 후에만 production 배포 job을 허용한다.

운영에 필요한 것은 보유 도메인·VM·DNS·GHCR 읽기 자격·서버 runtime 비밀 값·검증한 SSH 호스트 키다. 현재 Docker engine이 실행 중이 아니므로 이미지 실행·외부 TLS·SSH 배포·이미지 롤백은 미실행이다. 파일 작성과 로컬 prod 검증을 외부 배포 성공으로 표시하지 않는다.

### 테스트 결과

검증 기준일: 2026-11-19. 실제 DB와 API 키를 사용하지 않고 격리했다.

| 검사 | 결과 | 근거 |
|---|---|---|
| 입력·DB·인증·경쟁 요청·AI mock·MCP·migration·복원 | 로컬 pytest 통과, 59개 | `tests/` |
| backend 토큰 직렬화 제외·캐시 무효화 | 통과 | `tests/test_state.py` |
| final prod 빌드·단일 포트·Chromium | 4개 통과 | `tools/verify_app.py --app project --mode prod` |
| midpoint prod 빌드·Chromium | 1개 통과 | `--app midpoint --mode prod` |
| demo prod 빌드·단원 이벤트·인증·차트 | 2개 통과 | `--app demo --mode prod` |
| Ruff·포맷·Pyright | 로컬 통과 | 루트 품질 명령 |
| Compose 해석·배포 셸·CI gates | 통과 | `tools/check_deploy.py` |
| GitHub Actions 원격 실행 | 설정 구현, 원격 미실행 | `.github/workflows/ci.yml` |
| 실제 모델 API | 미실행, 서버 키·모델 필요 | `services/ai.py` |
| 외부 Docker/TLS/SSH/롤백 | 미실행, 운영 환경 필요 | `deploy/` |

프로덕션 브라우저는 로그인·작성·새로고침·수정·삭제·guest 직접 수정 접근 차단·로그아웃·잘못된 ID·관리자 접근 거부·MCP·페이지네이션·검색을 확인했다. AI는 공급자 mock과 권한/timeout/오래된 결과를 검증했으며 실제 과금 호출은 하지 않았다.

```powershell
python -m ruff check .
python -m ruff format --check .
pyright
python -m pytest tests --ignore=tests/e2e -q
python tools/benchmark.py
python tools/check_deploy.py
```

모든 명령은 저장소 루트 기준이다. 브라우저 도구가 만든 로그·스크린샷과 성능 원본은 git 제외 `artifacts/`에 있다.

## 오류 노트

- 공개 이름·UI 버튼을 권한 근거로 사용하지 않는다.
- 기본 앱의 DB 작성자 이름과 final의 불변 owner_id를 혼동하지 않는다.
- `REFLEX_CORS_ALLOWED_ORIGINS`에 JSON 배열을 넣으면 0.9.11에서 출처가 잘못 해석된다. 쉼표 구분 문자열을 쓴다.
- Tailwind 플러그인을 제거한 기존 생성 폴더에 PostCSS 설정만 남으면 빌드가 실패할 수 있다. 원본 rxconfig의 플러그인과 의존성을 일치시킨다.
- 단일 포트에 서로 다른 두 포트를 명시하지 않는다.
- 파괴적 스키마 변경은 이전 이미지 선택만으로 복구되지 않는다.

## ☐ 체크리스트

- ☐ [노션 학습 목표] 생성·State·CRUD·페이지 분리·배포 코드의 경로를 확인한다.
- ☐ [노션 SQLModel] 모델·세션·Alembic·날짜 직렬화를 확인한다.
- ☐ [노션 권한] 생성·수정·삭제의 DB 세션·owner_id 검사를 설명한다.
- ☐ [노션 비동기] 로딩·중복 방지·잠금·실패 복구·오래된 결과 거부를 확인한다.
- ☐ 기본 게시판과 최종 게시판의 prod E2E 회귀를 확인한다.
- ☐ 성능 측정과 보안·backup 복원 검증을 재현한다.
- ☐ 실제 키와 운영 환경 준비 후 외부 API·TLS·배포·롤백 결과를 추가한다.
- ☐ 최종 회고: 같은 Reflex 앱 내부에서 바뀐 구조·권한·성능을 설명한다.
- ☐ 최종 회고: 측정 사실·가정·운영 규모·중단/재로그인 정책을 구분한다.
- ☐ 최종 회고: 다음 개선의 우선순위와 재발 방지 테스트를 기록한다.

## 다음 단계 연결

학습 과정은 여기까지다. 외부 운영 준비 후 미실행 항목을 검증하고 같은 Reflex 서비스의 결함 수정·의존성 갱신·용량 측정을 이어간다. 전체 경로는 [README](README.md)에 있다.

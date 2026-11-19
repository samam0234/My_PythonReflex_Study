# study16 — 운영 인증·보안·로그·모니터링

목표: DB 사용자·만료 세션·소유권·요청 제한과 운영 증거를 확인한다.

실제 구현: [project/project/services/auth.py](project/project/services/auth.py), [project/project/observability.py](project/project/observability.py). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

노션의 “실제 서비스는 DB와 비밀번호 해시 필요”를 [auth.py](project/project/services/auth.py)에 구현했다. 토큰 원문은 backend State에만, DB에는 토큰 해시만 보관한다. 공개 이름·버튼 표시로 권한을 판단하지 않는다.

기본 한도는 계정별 로그인 5회/분·동시 해시 계산 2개, 세션 1시간이다. 이 예제는 서버 State 유실 시 재로그인하는 정책이며 영구 쿠키 로그인은 제공하지 않는다. 외부 gateway의 접속원별 과부하 방어는 별도 운영 정책으로 설정한다.

## 🛠️ 실기(코드·줄별 설명)

```python
"""study7·16: scrypt, backend 전용 토큰, DB 만료·폐기, 원자적 로그인 제한."""

import hashlib
import hmac
import secrets
import threading
import time
from functools import lru_cache

from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import CursorResult
from sqlmodel import Session, col, select

from ..models import LoginSession, RateWindow, User
from ..schemas import LoginInput
from ..settings import get_settings
from .database import open_session
from .errors import AccessDenied, LimitExceeded

SCRYPT_N = 2**17
_HASH_SLOTS = threading.BoundedSemaphore(2)


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 128:
        raise ValueError("비밀번호는 12~128자여야 합니다.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=8, p=1, maxmem=256 * 1024 * 1024
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    if not 12 <= len(password) <= 128:
        return False
    try:
        scheme, salt_hex, expected = encoded.split("$")
        if scheme != "scrypt" or len(salt_hex) != 32 or len(expected) != 128:
            return False
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=SCRYPT_N,
            r=8,
            p=1,
            maxmem=256 * 1024 * 1024,
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password("unavailable-account-placeholder")


def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def reserve_login_attempt(username: str) -> None:
    subject = token_hash("login:" + username)
    window = int(time.time()) // 60
    with open_session() as session:
        session.execute(
            insert(RateWindow)
            .values(subject=subject, window=window, attempts=0)
            .on_conflict_do_nothing()
        )
        result = session.execute(
            update(RateWindow)
            .where(
                col(RateWindow.subject) == subject,
                col(RateWindow.window) == window,
                col(RateWindow.attempts) < get_settings().login_limit,
            )
            .values(attempts=col(RateWindow.attempts) + 1)
        )
        assert isinstance(result, CursorResult)
        if result.rowcount != 1:
            raise LimitExceeded("로그인 시도가 많습니다. 잠시 후 다시 시도하세요.")
        session.commit()


def authenticate(data: LoginInput) -> tuple[str, int, str, bool]:
    reserve_login_attempt(data.username)
    if not _HASH_SLOTS.acquire(blocking=False):
        raise LimitExceeded("로그인 처리가 많습니다. 잠시 후 다시 시도하세요.")
    try:
        with open_session() as session:
            user = session.exec(select(User).where(User.username == data.username)).first()
            candidate = user.password_hash if user else _dummy_hash()
            valid = verify_password(data.password, candidate)
            if user is None or user.id is None or not user.active or not valid:
                raise AccessDenied("아이디 또는 비밀번호가 올바르지 않습니다.")
            raw = secrets.token_urlsafe(32)
            session.add(
                LoginSession(
                    token_hash=token_hash(raw),
                    user_id=user.id,
                    expires_at=int(time.time()) + get_settings().session_seconds,
                )
            )
            session.commit()
            return raw, user.id, user.username, user.is_admin
    finally:
        _HASH_SLOTS.release()


def require_user(session: Session, raw: str) -> User:
    if not raw or len(raw) > 128:
        raise AccessDenied("로그인이 필요합니다.")
    record = session.get(LoginSession, token_hash(raw))
    if record is None or record.expires_at <= int(time.time()):
        raise AccessDenied("로그인이 만료되었습니다. 다시 로그인하세요.")
    user = session.get(User, record.user_id)
    if user is None or user.id is None or not user.active:
        raise AccessDenied("로그인이 필요합니다.")
    return user


def check_identity(raw: str) -> tuple[int, str, bool]:
    with open_session() as session:
        user = require_user(session, raw)
        assert user.id is not None
        return user.id, user.username, user.is_admin


def revoke(raw: str) -> None:
    with open_session() as session:
        record = session.get(LoginSession, token_hash(raw))
        if record is not None:
            session.delete(record)
            session.commit()


def create_user(username: str, password: str, *, admin: bool = False) -> int:
    data = LoginInput(username=username, password=password)
    encoded = hash_password(data.password)
    with open_session() as session:
        if session.exec(select(User).where(User.username == data.username)).first():
            raise ValueError("이미 있는 사용자입니다.")
        user = User(username=data.username, password_hash=encoded, is_admin=admin)
        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.id is not None
        return user.id
```

| 코드 구간 | 줄별 역할 |
|---|---|
| `hash_password` | 12~128자 검사, 무작위 salt, scrypt n=2^17/r=8/p=1, 알고리즘·salt·해시 저장 |
| `verify_password` | 저장 형식 검사, 같은 비용으로 재계산, 상수 시간 비교 |
| `_dummy_hash` | 없는 계정도 검증 경로를 거치도록 한다. |
| `reserve_login_attempt` | 분 단위 복합키를 생성하고 허용량 미만인 행만 원자 증가한다. |
| `authenticate` | 요청 제한→전역 동시성 상한→해시 검증→활성 사용자→만료 세션 발급 순서다. |
| `require_user` | 보호 작업마다 토큰·만료·활성 사용자를 DB에서 다시 확인한다. |
| `revoke` | 로그아웃 시 DB 세션을 삭제한다. |
| `create_user` | 관리 명령에서만 계정을 명시적으로 만든다. import 시 계정을 만들지 않는다. |

scrypt의 메모리 비용은 호출당 대략 128MiB 이상이다. 메모리 예산과 최대 동시성을 함께 측정한다. 보호 CRUD는 [posts.py](project/project/services/posts.py)에서 `require_user`와 `Post.owner_id`를 확인하고, 수정에는 revision 조건을 추가한다.

관리 명령:

```powershell
cd project
reflex db migrate
python -m project.manage create-user operator --admin
python -m project.manage backup ../artifacts/board-backup.db
python -m project.manage cleanup
```

각 줄은 앱 위치→기존 이력 적용→콘솔 비밀번호 입력으로 관리자 생성→SQLite 온라인 백업과 무결성/행 수 확인→만료 세션·오래된 요청 기록 정리다. 백업 경로는 기존 파일을 덮어쓰지 않는다. 기존 글은 owner_id=NULL로 보존하며 확인한 글만 `assign-owner 글번호 계정`으로 명시적으로 귀속시킨다.

로그 구현은 [observability.py](project/project/observability.py)다. 시각·작업·결과·내부 사용자 ID·측정한 지연만 JSON으로 기록한다. `/ops`는 서버에서 관리자 권한을 재확인하며, 시간 측정이 있는 작업만 p95 집계에 포함한다. 프로세스 지표는 재시작 시 초기화되므로 외부 수집기가 stdout·메모리·WebSocket 재연결 등을 수집하도록 확장한다.

`/health/ready`는 [api_transformer](project/project/health.py)로 추가하며 실제 post·session 스키마 질의를 확인한다. 0.9.11에서 `app.api`를 사용하지 않는다.

## 오류 노트

- UI 입력 검증 오류의 원문을 로그에 남기지 않는다. 자격증명과 본문이 섞일 수 있다.
- 같은 작성자 이름의 기존 글을 새 사용자에게 자동 귀속시키지 않는다.
- 로그아웃은 화면 초기화와 DB 세션 폐기를 모두 수행한다.
- 이미지 롤백과 DB 복원은 다르다. 별도 DB에서 백업 복원·무결성·행 수를 확인한다.

## ☐ 체크리스트

- ☐ [노션 실제 인증 요구] 데모 dict를 DB·비밀번호 해시로 대체한다.
- ☐ 만료·폐기·비활성 세션과 타인 글 변경을 모두 거부한다.
- ☐ [노션 작성자 확인] 불변 사용자 ID와 DB 원본으로 생성·수정·삭제를 보호한다.
- ☐ 로그인 시도·해시 동시성 상한과 AI 한도를 확인한다.
- ☐ 일반 로그·이미지·공개 State에 비밀번호·원문 토큰·키가 없는지 확인한다.
- ☐ readiness·관리자 지표·백업 복원과 외부 경보 설정을 구분한다.

## 다음 단계 연결

[study17](study17.md)에서 Docker·외부 VM 배포·롤백을 구성한다.

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

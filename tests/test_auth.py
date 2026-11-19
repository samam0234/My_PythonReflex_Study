from concurrent.futures import ThreadPoolExecutor

import pytest
from project.models import LoginSession, User
from project.schemas import LoginInput
from project.services import auth
from project.services.database import open_session
from project.services.errors import AccessDenied, LimitExceeded


def test_password_hash(password_hashes):
    encoded = password_hashes[0]
    assert "demo-password-123" not in encoded
    assert auth.verify_password("demo-password-123", encoded)
    assert not auth.verify_password("wrong-password-123", encoded)
    assert not auth.verify_password("demo-password-123", "bad-encoding")


def test_login_wrong_and_unknown(accounts):
    for name in ("demo", "unknown"):
        with pytest.raises(AccessDenied):
            auth.authenticate(LoginInput(username=name, password="wrong-password-123"))


def test_session_expiry_revoke_inactive(accounts):
    owner, other = accounts
    with open_session() as session:
        record = session.get(LoginSession, auth.token_hash(owner))
        assert record is not None and record.token_hash != owner
        record.expires_at = 0
        session.add(record)
        session.commit()
    with open_session() as session, pytest.raises(AccessDenied):
        auth.require_user(session, owner)
    auth.revoke(other)
    with open_session() as session, pytest.raises(AccessDenied):
        auth.require_user(session, other)


def test_inactive_user_is_rejected(accounts):
    owner, _ = accounts
    user_id = auth.check_identity(owner)[0]
    with open_session() as session:
        user = session.get(User, user_id)
        user.active = False
        session.add(user)
        session.commit()
    with open_session() as session, pytest.raises(AccessDenied):
        auth.require_user(session, owner)


def test_login_limit_concurrent_and_next_window(database, monkeypatch):
    moment = 1_000_000
    monkeypatch.setattr(auth.time, "time", lambda: moment)

    def attempt(_):
        try:
            auth.reserve_login_attempt("demo")
            return True
        except LimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(12))) == 5
    moment += 60
    auth.reserve_login_attempt("demo")


def test_hash_concurrency_limit(accounts, monkeypatch):
    class Busy:
        def acquire(self, **kwargs):
            return False

    monkeypatch.setattr(auth, "_HASH_SLOTS", Busy())
    with pytest.raises(LimitExceeded):
        auth.authenticate(LoginInput(username="demo", password="demo-password-123"))

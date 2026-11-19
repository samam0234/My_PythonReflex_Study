import os
from pathlib import Path

import pytest
from project.models import User
from project.schemas import LoginInput
from project.services import auth
from project.services.database import open_session
from reflex.model import get_engine
from sqlmodel import SQLModel

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def password_hashes():
    return (auth.hash_password("demo-password-123"), auth.hash_password("guest-password-123"))


@pytest.fixture
def database(monkeypatch, tmp_path):
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    monkeypatch.setenv("APP_DB_URL", url)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_FRONTEND_ORIGIN", "http://localhost:3000")
    engine = get_engine(url)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def accounts(database, password_hashes):
    with open_session() as session:
        session.add_all(
            [
                User(username="demo", password_hash=password_hashes[0], is_admin=True),
                User(username="guest", password_hash=password_hashes[1]),
            ]
        )
        session.commit()
    owner = auth.authenticate(LoginInput(username="demo", password="demo-password-123"))[0]
    other = auth.authenticate(LoginInput(username="guest", password="guest-password-123"))[0]
    return owner, other


@pytest.fixture(scope="session")
def app_url():
    url = os.getenv("REFLEX_E2E_URL")
    if not url:
        pytest.skip("tools/verify_app.py로 실제 서버를 시작하거나 REFLEX_E2E_URL을 지정하세요.")
    return url.rstrip("/")

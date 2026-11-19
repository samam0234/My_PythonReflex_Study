"""Reflex 설정과 같은 URL로 짧은 DB 세션을 열고 SQLite 제약을 활성화."""

import reflex as rx
from sqlalchemy import text
from sqlmodel import Session

from ..settings import get_settings


def open_session() -> Session:
    session = rx.session(url=get_settings().db_url)
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.execute(text("PRAGMA busy_timeout=5000"))
    return session

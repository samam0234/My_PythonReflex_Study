"""study6·16·final: SQLModel 직접 상속, 기존 게시물은 소유자 미지정으로 보존."""

from datetime import datetime, timezone

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    active: bool = True
    is_admin: bool = False


class Post(SQLModel, table=True):
    __table_args__ = (Index("ix_post_created_id", "created_at", "id"),)
    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    revision: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LoginSession(SQLModel, table=True):
    token_hash: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    expires_at: int = Field(index=True)


class RateWindow(SQLModel, table=True):
    subject: str = Field(primary_key=True)
    window: int = Field(primary_key=True)
    attempts: int = 0


class AiDaily(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    day: str = Field(primary_key=True)
    calls: int = 0

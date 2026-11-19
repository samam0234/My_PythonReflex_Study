from datetime import datetime, timezone

import sqlmodel


class LessonPost(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    created_at: datetime = sqlmodel.Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthPost(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    created_at: datetime = sqlmodel.Field(default_factory=lambda: datetime.now(timezone.utc))

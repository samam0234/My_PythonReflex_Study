from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Post(SQLModel, table=True):
    __tablename__ = "midpoint_post"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

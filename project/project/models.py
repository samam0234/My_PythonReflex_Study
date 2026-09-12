from datetime import datetime, timezone

import sqlmodel


class Post(sqlmodel.SQLModel, table=True):
    """게시글 테이블. study7에서 배운 대로 `sqlmodel.SQLModel`을 직접 상속한다."""

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    title: str
    content: str
    author: str
    created_at: datetime = sqlmodel.Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

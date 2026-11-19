from typing import Any

import reflex as rx
from sqlmodel import select

from .models import LessonPost as Post


class DbState(rx.State):
    posts: list[dict[str, str]] = []
    error: str = ""

    @rx.event
    def load_posts(self):
        with rx.session() as session:
            rows = session.exec(select(Post).order_by(Post.created_at.desc(), Post.id.desc())).all()
            self.posts = [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "content": p.content,
                    "author": p.author,
                    "created_at": p.created_at.isoformat(),
                }
                for p in rows
            ]

    @rx.event
    def create_post(self, data: dict[str, Any]):
        title, content = data.get("title", "").strip(), data.get("content", "").strip()
        if not 1 <= len(title) <= 50 or not 1 <= len(content) <= 5000:
            self.error = "제목·본문 길이를 확인하세요."
            return
        with rx.session() as session:
            post = Post(title=title, content=content, author="learner")
            session.add(post)
            session.commit()
            session.refresh(post)
        self.error = ""
        self.load_posts()

    @rx.event
    def rename_post(self, raw_id: str, title: str):
        if not raw_id.isdecimal() or not 1 <= len(title.strip()) <= 50:
            self.error = "ID·제목을 확인하세요."
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None:
                self.error = "없는 글입니다."
                return
            row.title = title.strip()
            session.add(row)
            session.commit()
        self.load_posts()

    @rx.event
    def delete_post(self, raw_id: str):
        if not raw_id.isdecimal():
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is not None:
                session.delete(row)
                session.commit()
        self.load_posts()

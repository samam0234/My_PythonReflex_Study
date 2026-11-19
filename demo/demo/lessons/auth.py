from typing import Any

import reflex as rx
from sqlmodel import select

from .models import AuthPost as Post

DEMO_USERS = {"demo": "reflex123", "guest": "guest123"}


class AuthState(rx.State):
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

    _username: str = ""
    login_error: str = ""

    @rx.var
    def username(self) -> str:
        return self._username

    @rx.event
    def login(self, data: dict[str, Any]):
        name, password = data.get("username", "").strip(), data.get("password", "")
        if name not in DEMO_USERS or DEMO_USERS[name] != password:
            self.login_error = "아이디 또는 비밀번호를 확인하세요."
            return
        self._username = name
        self.login_error = ""
        return rx.redirect("/study7")

    @rx.event
    def logout(self):
        self._username = ""
        return rx.redirect("/study7/login")

    @rx.event
    def require_login(self):
        if not self._username:
            return rx.redirect("/study7/login")

    @rx.event
    def create_post(self, data: dict[str, Any]):
        if not self._username:
            return rx.redirect("/study7/login")
        title, content = data.get("title", "").strip(), data.get("content", "").strip()
        if not 1 <= len(title) <= 50 or not 1 <= len(content) <= 5000:
            self.error = "제목·본문 길이를 확인하세요."
            return
        with rx.session() as session:
            session.add(Post(title=title, content=content, author=self._username))
            session.commit()
        self.load_posts()

    @rx.event
    def rename_post(self, raw_id: str, title: str):
        if not self._username:
            return rx.redirect("/study7/login")
        if not raw_id.isdecimal() or not 1 <= len(title.strip()) <= 50:
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None or row.author != self._username:
                self.error = "수정할 수 없습니다."
                return
            row.title = title.strip()
            session.add(row)
            session.commit()
        self.load_posts()

    @rx.event
    def delete_post(self, raw_id: str):
        if not self._username:
            return rx.redirect("/study7/login")
        if not raw_id.isdecimal():
            return
        with rx.session() as session:
            row = session.get(Post, int(raw_id))
            if row is None or row.author != self._username:
                self.error = "삭제할 수 없습니다."
                return
            session.delete(row)
            session.commit()
        self.load_posts()


def login_page() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.input(name="username", placeholder="아이디"),
            rx.input(name="password", type="password", placeholder="비밀번호"),
            rx.button("로그인", type="submit"),
            on_submit=AuthState.login,
            reset_on_submit=True,
        ),
        rx.text(AuthState.login_error, role="alert"),
    )

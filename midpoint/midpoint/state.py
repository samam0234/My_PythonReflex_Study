"""study0~10만 사용하는 학습용 게시판. 데모 자격증명은 운영에서 사용하지 않는다."""

from typing import Any

import reflex as rx
from sqlmodel import select

from .models import Post
from .validation import validate_post

DEMO_USERS = {"demo": "reflex123", "guest": "guest123"}


class State(rx.State):
    posts: list[dict] = []
    form_title: str = ""
    form_content: str = ""
    form_error: str = ""
    login_error: str = ""
    _username: str = ""

    @rx.var
    def current_username(self) -> str:
        return self._username

    @rx.var
    def is_logged_in(self) -> bool:
        return bool(self._username)

    @rx.event
    def login(self, data: dict[str, Any]):
        name, password = data.get("username", ""), data.get("password", "")
        if (
            not isinstance(name, str)
            or not isinstance(password, str)
            or DEMO_USERS.get(name.strip()) != password
        ):
            self.login_error = "아이디 또는 비밀번호가 올바르지 않습니다."
            return
        self._username = name.strip()
        self.login_error = ""
        return rx.redirect("/")

    @rx.event
    def logout(self):
        self._username = ""
        return rx.redirect("/login")

    @rx.event
    def load_posts(self):
        with rx.session() as session:
            records = session.exec(
                select(Post).order_by(Post.created_at.desc(), Post.id.desc())
            ).all()
            self.posts = [
                {
                    "id": p.id,
                    "title": p.title,
                    "content": p.content,
                    "author": p.author,
                    "created_at": p.created_at.isoformat(),
                }
                for p in records
            ]

    @rx.event
    def set_form_title(self, value: str):
        self.form_title = value
        self.form_error = ""

    @rx.event
    def set_form_content(self, value: str):
        self.form_content = value
        self.form_error = ""

    def _validate_form(self) -> bool:
        self.form_error = validate_post(self.form_title, self.form_content)
        return not self.form_error

    def _id(self) -> int | None:
        raw = self.post_id
        if not raw.isascii() or not raw.isdecimal() or len(raw) > 10:
            self.form_error = "글 번호를 확인하세요."
            return None
        return int(raw)

    @rx.event
    def prepare_new_post(self):
        if not self._username:
            return rx.redirect("/login")
        self.form_title = ""
        self.form_content = ""
        self.form_error = ""

    @rx.event
    def create_post(self):
        if not self._username:
            return rx.redirect("/login")
        if not self._validate_form():
            return
        with rx.session() as session:
            post = Post(
                title=self.form_title.strip(),
                content=self.form_content.strip(),
                author=self._username,
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            post_id = post.id
        self.load_posts()
        return rx.redirect(f"/post/{post_id}")

    @rx.event
    def prepare_edit_post(self):
        self.form_title = ""
        self.form_content = ""
        if not self._username:
            return rx.redirect("/login")
        self.load_posts()
        if not self.can_edit_current_post:
            return rx.redirect("/")
        self.form_title = self.current_post["title"]
        self.form_content = self.current_post["content"]

    @rx.event
    def update_post(self):
        if not self._username:
            return rx.redirect("/login")
        if not self._validate_form():
            return
        post_id = self._id()
        if post_id is None:
            return
        with rx.session() as session:
            post = session.get(Post, post_id)
            if post is None or post.author != self._username:
                self.form_error = "수정할 수 없습니다."
                return
            post.title, post.content = self.form_title.strip(), self.form_content.strip()
            session.add(post)
            session.commit()
        self.load_posts()
        return rx.redirect(f"/post/{post_id}")

    @rx.event
    def delete_post(self, post_id: int):
        if not self._username:
            return rx.redirect("/login")
        with rx.session() as session:
            post = session.get(Post, post_id)
            if post is None or post.author != self._username:
                self.form_error = "삭제할 수 없습니다."
                return
            session.delete(post)
            session.commit()
        self.load_posts()
        return rx.redirect("/")

    @rx.var
    def current_post(self) -> dict:
        for post in self.posts:
            if str(post["id"]) == self.post_id:
                return post
        return {"id": 0, "title": "", "content": "", "author": "", "created_at": ""}

    @rx.var
    def can_edit_current_post(self) -> bool:
        return (
            bool(self._username)
            and self.current_post["id"] != 0
            and self.current_post["author"] == self._username
        )

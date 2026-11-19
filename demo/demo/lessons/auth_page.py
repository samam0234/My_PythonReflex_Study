import reflex as rx

from .auth import AuthState as DbState


def index() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.input(name="title", placeholder="제목"),
            rx.input(name="content", placeholder="본문"),
            rx.button("등록", type="submit"),
            on_submit=DbState.create_post,
        ),
        rx.text(DbState.error, role="alert"),
        rx.foreach(
            DbState.posts,
            lambda p: rx.hstack(
                rx.text(p["title"]),
                rx.button("제목 수정", on_click=DbState.rename_post(p["id"], "수정한 제목")),
                rx.button("삭제", on_click=DbState.delete_post(p["id"])),
            ),
        ),
    )

import reflex as rx

from ..state import State


def header() -> rx.Component:
    return rx.hstack(
        rx.link(rx.heading("Reflex Study Board", size="6"), href="/", color="inherit"),
        rx.spacer(),
        rx.link("통계 · MCP", href="/dashboard"),
        rx.cond(State.is_admin, rx.link("운영", href="/ops")),
        rx.cond(
            State.is_logged_in,
            rx.hstack(
                rx.text(State.current_username),
                rx.link("새 글 작성", href="/post/new"),
                rx.button("로그아웃", on_click=State.logout, variant="soft"),
            ),
            rx.link("로그인", href="/login"),
        ),
        align="center",
        wrap="wrap",
        gap="4",
        width="100%",
        padding_y="1rem",
    )


def layout(*children: rx.Component) -> rx.Component:
    return rx.container(
        header(),
        rx.separator(),
        rx.box(*children, padding_y="2rem", width="100%"),
        rx.text("Python · Reflex · SQLModel", size="1", color="gray", padding_y="1rem"),
        size="3",
        min_height="100vh",
    )


def error_message() -> rx.Component:
    return rx.text(State.form_error, color="red", role="alert", id="form-error")

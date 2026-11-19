import reflex as rx

from ..state import State


def login_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("기초 게시판 로그인"),
            rx.text("로컬 학습용: demo / reflex123, guest / guest123", size="2"),
            rx.form(
                rx.vstack(
                    rx.input(name="username", placeholder="아이디"),
                    rx.input(name="password", placeholder="비밀번호", type="password"),
                    rx.button("로그인", type="submit"),
                ),
                on_submit=State.login,
                reset_on_submit=True,
            ),
            rx.text(State.login_error, role="alert", color="red"),
            rx.link("목록", href="/"),
            max_width="420px",
            margin="4rem auto",
            spacing="4",
        )
    )

import reflex as rx

from ..components.layout import layout
from ..state import State


def login_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("로그인", size="7"),
            rx.text("관리자가 발급한 계정으로 로그인하세요.", color="gray"),
            rx.form(
                rx.vstack(
                    rx.text("아이디", as_="label", html_for="username"),
                    rx.input(
                        id="username",
                        name="username",
                        placeholder="아이디",
                        custom_attrs={"autoComplete": "username"},
                        max_length=32,
                        required=True,
                        width="100%",
                    ),
                    rx.text("비밀번호", as_="label", html_for="password"),
                    rx.input(
                        id="password",
                        name="password",
                        placeholder="비밀번호",
                        type="password",
                        custom_attrs={"autoComplete": "current-password"},
                        max_length=128,
                        required=True,
                        width="100%",
                    ),
                    rx.button("로그인", type="submit", loading=State.login_busy, width="100%"),
                    align="start",
                    spacing="3",
                    width="100%",
                ),
                on_submit=State.login,
                reset_on_submit=True,
                width="100%",
            ),
            rx.text(State.login_error, role="alert", color="red", id="login-error"),
            rx.link("목록으로", href="/"),
            align="start",
            spacing="4",
            max_width="400px",
            margin="2rem auto",
        )
    )

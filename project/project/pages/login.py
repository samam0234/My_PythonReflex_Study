import reflex as rx

from ..state import State


def login_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("로그인", size="7"),
            rx.text(
                "데모 계정: demo / reflex123 (또는 guest / guest123)",
                size="2",
                color="gray",
            ),
            rx.input(
                placeholder="아이디",
                value=State.username_input,
                on_change=State.set_username_input,
                width="100%",
            ),
            rx.input(
                placeholder="비밀번호",
                type="password",
                value=State.password_input,
                on_change=State.set_password_input,
                width="100%",
            ),
            rx.button("로그인", on_click=State.login, width="100%"),
            rx.cond(
                State.login_error != "",
                rx.text(State.login_error, color="red", size="2"),
            ),
            rx.link(rx.button("← 목록으로", variant="soft"), href="/"),
            spacing="3",
            justify="center",
            min_height="85vh",
            max_width="320px",
            margin="0 auto",
        ),
    )

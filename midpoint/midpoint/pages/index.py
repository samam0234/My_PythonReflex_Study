import reflex as rx

from ..components.post_card import post_card
from ..state import State


def index() -> rx.Component:
    return rx.container(
        rx.hstack(
            rx.heading("Reflex 게시판", size="8"),
            rx.spacer(),
            rx.color_mode.button(),
            rx.cond(
                State.is_logged_in,
                rx.hstack(
                    rx.text("반갑습니다, ", State.current_username, "님", size="3"),
                    rx.link(rx.button("새 글 작성"), href="/post/new"),
                    rx.button("로그아웃", on_click=State.logout, variant="soft"),
                    spacing="3",
                    align="center",
                ),
                rx.link(rx.button("로그인"), href="/login"),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            State.posts.length() == 0,
            rx.text("아직 게시글이 없습니다.", color="gray", margin_top="2em"),
            rx.vstack(
                rx.foreach(State.posts, post_card),
                width="100%",
                spacing="3",
                margin_top="1.5em",
            ),
        ),
        padding_y="2em",
    )

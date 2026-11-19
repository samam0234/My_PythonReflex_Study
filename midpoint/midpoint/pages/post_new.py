import reflex as rx

from ..components.post_form import post_form
from ..state import State


def post_new_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("새 글 작성", size="7"),
            post_form("작성 완료", State.create_post),
            rx.link(rx.button("← 취소", variant="soft"), href="/"),
            spacing="4",
        ),
        padding_y="2em",
    )

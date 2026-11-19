import reflex as rx

from ..components.post_form import post_form
from ..state import State


def post_edit_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("글 수정", size="7"),
            post_form("수정 완료", State.update_post),
            rx.link(
                rx.button("← 취소", variant="soft"),
                href="/post/" + State.current_post["id"].to_string(),
            ),
            spacing="4",
        ),
        padding_y="2em",
    )

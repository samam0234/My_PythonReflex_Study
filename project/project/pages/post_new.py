import reflex as rx

from ..components.layout import layout
from ..components.post_form import post_form
from ..state import State


def post_new_page() -> rx.Component:
    return layout(
        rx.heading("새 글 작성", size="7", margin_bottom="1rem"),
        rx.cond(
            State.is_logged_in,
            post_form("작성 완료", State.create_post),
            rx.link("로그인이 필요합니다.", href="/login"),
        ),
    )

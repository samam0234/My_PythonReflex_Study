import reflex as rx

from ..components.layout import error_message, layout
from ..components.post_form import post_form
from ..state import State


def post_edit_page() -> rx.Component:
    return layout(
        rx.heading("글 수정", size="7", margin_bottom="1rem"),
        rx.cond(
            State.can_edit_current_post,
            post_form("수정 완료", State.update_post),
            rx.vstack(error_message(), rx.link("목록으로", href="/")),
        ),
    )

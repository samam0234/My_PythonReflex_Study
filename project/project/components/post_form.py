import reflex as rx

from ..state import State
from .layout import error_message


def post_form(submit_label: str, on_submit) -> rx.Component:
    return rx.vstack(
        rx.text("제목", as_="label", html_for="post-title"),
        rx.input(
            id="post-title",
            name="title",
            placeholder="제목 (최대 50자)",
            value=State.form_title,
            on_change=State.set_form_title,
            max_length=50,
            width="100%",
        ),
        rx.text("본문", as_="label", html_for="post-content"),
        rx.text_area(
            id="post-content",
            name="content",
            placeholder="본문 (최대 5000자)",
            value=State.form_content,
            on_change=State.set_form_content,
            max_length=5000,
            rows="12",
            width="100%",
        ),
        error_message(),
        rx.button(submit_label, on_click=on_submit),
        align="start",
        spacing="3",
        width="100%",
    )

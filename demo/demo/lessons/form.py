from typing import Any

import reflex as rx


def validate_post(title: str, content: str) -> str:
    if not 1 <= len(title.strip()) <= 50:
        return "제목은 1~50자로 입력하세요."
    if not 1 <= len(content.strip()) <= 5000:
        return "본문은 1~5000자로 입력하세요."
    return ""


class FormState(rx.State):
    error: str = ""
    saved_title: str = ""

    @rx.event
    def submit(self, data: dict[str, Any]):
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        self.error = validate_post(title, content)
        if self.error:
            return
        self.saved_title = title


def index() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.vstack(
                rx.text("제목"),
                rx.input(name="title", placeholder="제목", required=True, max_length=50),
                rx.text("본문"),
                rx.text_area(name="content", placeholder="본문", required=True, max_length=5000),
                rx.button("저장", type="submit"),
            ),
            on_submit=FormState.submit,
            reset_on_submit=False,
        ),
        rx.text(FormState.error, color="red", role="alert"),
        rx.text("저장된 제목: ", FormState.saved_title),
    )

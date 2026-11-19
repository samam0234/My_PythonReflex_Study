import reflex as rx

from ..state import State


def post_form(submit_label: str, on_submit) -> rx.Component:
    """새 글 작성/수정 페이지가 공유하는 폼. study5·8에서 배운 컴포넌트
    분리 + 서버 측 검증 패턴을 그대로 적용했다."""
    return rx.vstack(
        rx.input(
            placeholder="제목 (최대 50자)",
            name="title",
            max_length=50,
            value=State.form_title,
            on_change=State.set_form_title,
            width="100%",
        ),
        rx.text_area(
            placeholder="내용",
            name="content",
            max_length=5000,
            value=State.form_content,
            on_change=State.set_form_content,
            width="100%",
            rows="10",
        ),
        rx.cond(
            State.form_error != "",
            rx.text(State.form_error, color="red", size="2"),
        ),
        rx.button(submit_label, on_click=on_submit),
        spacing="3",
        width="100%",
        max_width="480px",
    )

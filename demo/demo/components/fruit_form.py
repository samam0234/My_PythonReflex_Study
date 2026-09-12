import reflex as rx

from ..state import State


def fruit_form() -> rx.Component:
    """새 과일을 추가하는 폼. study3에서 fruit_list.py에 섞여 있던
    입력창+버튼+에러 메시지를 독립된 컴포넌트로 분리했다.
    """
    return rx.vstack(
        rx.hstack(
            rx.input(
                placeholder="새 과일 이름",
                value=State.new_fruit_name,
                on_change=State.set_new_fruit_name,
                width="100%",
            ),
            rx.button("추가", on_click=State.add_fruit),
            width="100%",
        ),
        rx.cond(
            State.form_error != "",
            rx.text(State.form_error, color="red", size="2"),
        ),
        align="start",
        width="100%",
        spacing="1",
    )

import reflex as rx

from ..state import State


def fruit_detail() -> rx.Component:
    """`/fruit/[fruit_id]` 페이지. 목록 페이지(index)와 분리된 두 번째 화면이다."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.cond(
                State.current_fruit["name"] != "",
                rx.vstack(
                    rx.heading(State.current_fruit["name"], size="8"),
                    rx.badge(
                        rx.cond(State.current_fruit["in_stock"], "재고 있음", "품절"),
                        color_scheme=rx.cond(
                            State.current_fruit["in_stock"], "green", "red"
                        ),
                        variant="solid",
                    ),
                    align="start",
                    spacing="3",
                ),
                rx.text("해당 id의 과일을 찾을 수 없습니다."),
            ),
            rx.button(
                "재미있는 사실 보기 (외부 API 호출)",
                on_click=State.load_fruit_fact,
                loading=State.fruit_fact_loading,
                variant="surface",
            ),
            rx.cond(State.fruit_fact != "", rx.text(State.fruit_fact)),
            rx.link(rx.button("← 목록으로"), href="/"),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )

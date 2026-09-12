import reflex as rx

from ..state import State
from .fruit_card import fruit_card


def fruit_list_practice() -> rx.Component:
    return rx.vstack(
        rx.heading("실습3: 과일 재고 CRUD", size="5"),
        rx.text("재고 있는 과일: ", State.in_stock_count, "개"),
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
        rx.list(
            # State가 된 리스트는 rx.foreach로 반복한다. study1의 파이썬
            # for-컴프리헨션은 "고정 데이터"에서만 통했다.
            rx.foreach(State.fruits, fruit_card),
            list_style_type="none",
            width="100%",
        ),
        align="start",
        width="100%",
        max_width="480px",
    )

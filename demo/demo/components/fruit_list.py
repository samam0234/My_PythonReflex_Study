import reflex as rx

from ..state import State
from .fruit_card import fruit_card


def fruit_list_practice() -> rx.Component:
    return rx.vstack(
        rx.heading("실습2: State로 관리하는 과일 재고 목록", size="5"),
        rx.text("재고 있는 과일: ", State.in_stock_count, "개"),
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

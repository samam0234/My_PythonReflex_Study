import reflex as rx

from ..state import State
from .fruit_badge import fruit_badge


def fruit_card(fruit: dict) -> rx.Component:
    """과일 하나를 보여주는 카드.

    study1과 함수 시그니처는 똑같이 `fruit: dict`이지만, study2부터는
    `rx.foreach`가 이 함수를 "리스트의 각 항목에 대해 반복 호출"하기
    때문에, 함수 안에서 받는 `fruit`은 실제 dict가 아니라 **아직 값이
    정해지지 않은 Var**다. 그래서 `fruit["in_stock"]`으로 값을 꺼내는
    문법은 똑같이 쓰지만, 그 값으로 Python `if`를 직접 쓸 수는 없고
    `rx.cond`를 거쳐야 한다.
    """
    return rx.list_item(
        rx.hstack(
            rx.text(
                fruit["name"],
                text_decoration=rx.cond(fruit["in_stock"], "none", "line-through"),
            ),
            fruit_badge(
                rx.cond(fruit["in_stock"], "재고 있음", "품절"),
                soldout=~fruit["in_stock"],
            ),
            rx.hstack(
                rx.button(
                    "토글",
                    size="1",
                    variant="outline",
                    on_click=State.toggle_stock(fruit["id"]),
                ),
                rx.button(
                    "삭제",
                    size="1",
                    variant="outline",
                    color_scheme="red",
                    on_click=State.remove_fruit(fruit["id"]),
                ),
                spacing="2",
            ),
            justify="between",
            width="100%",
        ),
        padding="0.5em 0",
    )

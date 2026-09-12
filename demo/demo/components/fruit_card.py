import reflex as rx

from .fruit_badge import fruit_badge


def fruit_card(fruit: dict) -> rx.Component:
    """과일 하나를 보여주는 카드. React의 `FruitCard({ fruit })`에 대응한다.

    `fruit` 파라미터가 props 역할이다. 지금 단계(study1)에서는 `fruit`이
    그냥 평범한 Python dict이므로, 내부에서 `fruit["name"]`처럼 일반
    Python 문법으로 값을 꺼내 써도 문제가 없다. study2에서 이 값이
    State(서버 상태)로 바뀌면 이 접근 방식이 왜 더 이상 통하지 않는지
    확인한다.
    """
    return rx.list_item(
        rx.hstack(
            rx.text(
                fruit["name"],
                text_decoration="line-through" if not fruit["in_stock"] else "none",
            ),
            fruit_badge(
                "재고 있음" if fruit["in_stock"] else "품절",
                soldout=not fruit["in_stock"],
            ),
            justify="between",
            width="100%",
        ),
        padding="0.5em 0",
    )

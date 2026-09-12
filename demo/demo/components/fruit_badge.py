import reflex as rx


def fruit_badge(*children: rx.Component | str, soldout: bool = False) -> rx.Component:
    """재고 여부를 보여주는 배지.

    React의 `FruitBadge({ soldout, children })`에 대응한다.
    `*children`으로 받은 위치 인자를 그대로 하위 컴포넌트에 넘기는 것이
    JSX의 "여는 태그와 닫는 태그 사이의 내용(children)"과 같은 역할을 한다.
    """
    return rx.badge(
        *children,
        color_scheme="red" if soldout else "green",
        variant="solid",
    )

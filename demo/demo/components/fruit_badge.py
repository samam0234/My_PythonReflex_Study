import reflex as rx


def fruit_badge(*children: rx.Component | str, soldout) -> rx.Component:
    """재고 여부를 보여주는 배지.

    study2부터 `soldout`은 더 이상 평범한 Python bool이 아니라 State에서
    나온 Var(아직 값이 정해지지 않은 심볼)일 수 있다. 그래서 Python의
    `if soldout: ...`처럼 직접 분기할 수 없고, 반드시 `rx.cond`로
    "브라우저에서 값이 정해지면 이 중 하나를 보여줘라"라고 표현해야 한다.
    """
    return rx.badge(
        *children,
        color_scheme=rx.cond(soldout, "red", "green"),
        variant="solid",
    )

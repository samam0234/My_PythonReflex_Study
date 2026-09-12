import reflex as rx

from .fruit_card import fruit_card

# study1 단계에서는 State가 아직 없으므로 평범한 Python 리스트(고정 데이터)다.
# study2에서 이 데이터를 State 클래스 안으로 옮기고 나서야 "진짜 상태"가 된다.
initial_fruits = [
    {"id": 1, "name": "사과", "in_stock": True},
    {"id": 2, "name": "바나나", "in_stock": False},
    {"id": 3, "name": "포도", "in_stock": True},
]


def fruit_list_practice() -> rx.Component:
    return rx.vstack(
        rx.heading("실습1: 과일 재고 목록 (컴포넌트 함수 / 인자 / 자식 요소)", size="5"),
        rx.list(
            # 지금은 initial_fruits가 고정된 Python list라서 그냥 파이썬
            # 리스트 컴프리헨션(for)으로 반복해도 된다. State 리스트가
            # 되는 순간부터는 이 방식 대신 rx.foreach를 써야 한다(study2/3).
            *[fruit_card(fruit) for fruit in initial_fruits],
            list_style_type="none",
            width="100%",
        ),
        align="start",
        width="100%",
        max_width="480px",
    )

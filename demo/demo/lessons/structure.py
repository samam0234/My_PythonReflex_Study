import reflex as rx

from ..components.notice import notice


def index() -> rx.Component:
    return rx.vstack(
        notice("안내", rx.text("읽기 전용 컴포넌트입니다.")),
        notice("다음 학습", rx.link("데이터", href="/data")),
        padding="2rem",
    )


def data_page() -> rx.Component:
    return rx.text("study3에서 상태를 연결합니다.")

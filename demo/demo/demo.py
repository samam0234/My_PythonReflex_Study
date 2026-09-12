"""Reflex 학습용 데모 프로젝트.

study1 ~ study5 실습 내용이 이 파일과 components/ 아래에 계속 누적되는 구조다.
(vue.js/react 학습 저장소의 demo/ 프로젝트와 같은 역할)
"""

import reflex as rx

from rxconfig import config

from .components.fruit_list import fruit_list_practice


class State(rx.State):
    """앱 전역 상태. study2부터 여기에 실습 내용이 추가된다."""


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Reflex 학습 데모", size="9"),
            rx.text(f"{config.app_name} 프로젝트 — study1 실습", size="5"),
            fruit_list_practice(),
            spacing="6",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)

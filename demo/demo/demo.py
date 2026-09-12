"""Reflex 학습용 데모 프로젝트.

study1 ~ study5 실습 내용이 이 파일과 components/, pages/ 아래에 계속 누적되는 구조다.
(vue.js/react 학습 저장소의 demo/ 프로젝트와 같은 역할)
"""

import reflex as rx

from rxconfig import config

from .components.fruit_list import fruit_list_practice
from .pages.admin import admin_page
from .pages.fruit_detail import fruit_detail
from .pages.login import login_page
from .state import State


def index() -> rx.Component:
    return rx.container(
        rx.hstack(
            rx.color_mode.button(),
            rx.link(rx.button("관리자 페이지", variant="soft"), href="/admin"),
            justify="end",
            width="100%",
        ),
        rx.vstack(
            rx.heading("Reflex 학습 데모", size="9"),
            rx.text(f"{config.app_name} 프로젝트 — study9 실습", size="5"),
            fruit_list_practice(),
            spacing="6",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index, route="/", on_load=State.load_fruits)
app.add_page(fruit_detail, route="/fruit/[fruit_id]", on_load=State.load_fruits)
app.add_page(login_page, route="/login")
app.add_page(admin_page, route="/admin", on_load=State.require_login)

"""study1~7·11·13을 독립 화면으로 실행하는 Reflex 실습실."""

import reflex as rx

from .lessons import (
    async_lab,
    auth,
    auth_page,
    charts,
    data,
    database,
    form,
    hello,
    routing,
    structure,
)
from .lessons.db_state import DbState
from .models import FruitRecord  # noqa: F401 - 기존 migration 모델을 보존한다.


def index() -> rx.Component:
    entries = [
        ("study1 Hello World", "/study1"),
        ("study2 컴포넌트·모듈", "/study2"),
        ("study3 State·Var", "/study3"),
        ("study4 라우팅", "/study4"),
        ("study5 폼 검증", "/study5"),
        ("study6 DB CRUD", "/study6"),
        ("study7 학습용 인증", "/study7"),
        ("study7 로그인", "/study7/login"),
        ("study11 비동기·TTL 캐시", "/study11"),
        ("study13 차트·필터", "/study13"),
    ]
    return rx.container(
        rx.vstack(
            rx.heading("Reflex 단원별 실습실", size="8"),
            rx.text(
                "study0 설정 · study8 구조 · study9 테스트 · study10 빌드는 저장소 파일과 연결됩니다."
            ),
            *[rx.link(label, href=route) for label, route in entries],
            rx.text("DB CRUD와 데모 계정 화면은 로컬 학습 전용입니다.", color="gray"),
            spacing="4",
            padding_y="3rem",
            align="start",
        )
    )


app = rx.App()
app.add_page(index, route="/")
app.add_page(hello.index, route="/study1")
app.add_page(structure.index, route="/study2")
app.add_page(structure.data_page, route="/data")
app.add_page(data.index, route="/study3")
app.add_page(routing.index, route="/study4")
app.add_page(
    routing.detail, route="/study4/post/[lesson_post_id]", on_load=routing.RouteState.load_post
)
app.add_page(form.index, route="/study5")
app.add_page(database.index, route="/study6", on_load=DbState.load_posts)
app.add_page(auth_page.index, route="/study7", on_load=auth.AuthState.load_posts)
app.add_page(auth.login_page, route="/study7/login")
app.add_page(async_lab.index, route="/study11")
app.add_page(charts.index, route="/study13")

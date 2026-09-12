import reflex as rx

from ..state import State


def admin_page() -> rx.Component:
    """`/admin` — 로그인한 사용자만 볼 수 있는 보호된 페이지.

    `demo.py`에서 `app.add_page(admin_page, route="/admin",
    on_load=State.require_login)`처럼 등록하면, 로그인 안 한 사용자가
    URL을 직접 입력해서 들어와도 `require_login`이 `/login`으로
    돌려보낸다.
    """
    return rx.container(
        rx.vstack(
            rx.heading("관리자 페이지", size="7"),
            rx.text("환영합니다, ", State.current_username, "님"),
            rx.text("이 페이지는 로그인한 사용자만 볼 수 있습니다.", color="gray"),
            rx.button("로그아웃", on_click=State.logout),
            rx.link(rx.button("← 목록으로", variant="soft"), href="/"),
            spacing="3",
            justify="center",
            min_height="85vh",
        ),
    )

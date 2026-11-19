import reflex as rx

from ..components.layout import error_message, layout
from ..components.post_card import post_card
from ..state import State


def index() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("게시글", size="7"),
            rx.text("글을 읽고 나누는 Reflex 학습 게시판", color="gray"),
            rx.form(
                rx.hstack(
                    rx.input(name="search", placeholder="제목 검색", max_length=64),
                    rx.button("검색", type="submit"),
                ),
                on_submit=State.search_posts,
            ),
            error_message(),
            rx.cond(
                State.total == 0,
                rx.text("아직 게시글이 없습니다."),
                rx.vstack(rx.foreach(State.posts, post_card), width="100%", spacing="3"),
            ),
            rx.hstack(
                rx.button("이전", on_click=State.previous_page, disabled=State.page == 0),
                rx.text(State.page_label),
                rx.button(
                    "다음", on_click=State.next_page, disabled=(State.page + 1) * 20 >= State.total
                ),
                align="center",
                wrap="wrap",
            ),
            rx.hstack(
                rx.button("새로 조회", on_click=State.on_home, variant="soft"),
                rx.text(State.load_note, size="1", color="gray"),
                wrap="wrap",
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )

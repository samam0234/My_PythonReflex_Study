import reflex as rx

from ..state import State


def post_detail() -> rx.Component:
    return rx.container(
        rx.cond(
            State.current_post["title"] != "",
            rx.vstack(
                rx.heading(State.current_post["title"], size="7"),
                rx.hstack(
                    rx.text(State.current_post["author"], color="gray"),
                    rx.text(State.current_post["created_at"], color="gray"),
                    spacing="3",
                ),
                rx.text(
                    State.current_post["content"],
                    white_space="pre-wrap",
                    margin_y="1em",
                ),
                rx.cond(
                    State.can_edit_current_post,
                    rx.hstack(
                        rx.link(
                            rx.button("수정"),
                            href="/post/" + State.current_post["id"].to_string() + "/edit",
                        ),
                        rx.button(
                            "삭제",
                            color_scheme="red",
                            on_click=State.delete_post(State.current_post["id"]),
                        ),
                        spacing="2",
                    ),
                ),
                rx.link(rx.button("← 목록으로", variant="soft"), href="/"),
                align="start",
                spacing="4",
                width="100%",
            ),
            rx.vstack(
                rx.text("게시글을 찾을 수 없습니다."),
                rx.link(rx.button("← 목록으로", variant="soft"), href="/"),
                spacing="3",
            ),
        ),
        padding_y="2em",
    )

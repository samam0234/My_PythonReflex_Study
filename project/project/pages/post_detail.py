import reflex as rx

from ..components.layout import error_message, layout
from ..state import State


def post_detail() -> rx.Component:
    return layout(
        error_message(),
        rx.cond(
            State.current_post.id > 0,
            rx.vstack(
                rx.heading(State.current_post.title, size="7"),
                rx.hstack(
                    rx.text(State.current_post.author),
                    rx.text(State.current_post.created_at),
                    color="gray",
                    wrap="wrap",
                ),
                rx.text(
                    State.current_post.content, white_space="pre-wrap", width="100%", id="post-body"
                ),
                rx.cond(
                    State.can_edit_current_post,
                    rx.vstack(
                        rx.hstack(
                            rx.link(
                                "수정", href="/post/" + State.current_post.id.to_string() + "/edit"
                            ),
                            rx.button(
                                "삭제",
                                on_click=State.delete_post(State.current_post.id),
                                color_scheme="red",
                            ),
                        ),
                        rx.button(
                            "AI 요약",
                            on_click=State.summarize_post(State.current_post.id),
                            loading=State.ai_busy,
                            disabled=~State.ai_configured,
                        ),
                        rx.cond(
                            ~State.ai_configured,
                            rx.text(
                                "AI 기능은 서버 모델 설정 후 사용할 수 있습니다.",
                                size="2",
                                color="gray",
                            ),
                        ),
                        rx.text(State.summary, white_space="pre-wrap", id="ai-summary"),
                        rx.text(State.ai_error, role="alert", color="red"),
                        align="start",
                        spacing="3",
                    ),
                ),
                align="start",
                spacing="5",
                width="100%",
            ),
            rx.text("게시글을 찾을 수 없습니다."),
        ),
        rx.box(rx.link("목록으로", href="/"), padding_top="2rem"),
    )

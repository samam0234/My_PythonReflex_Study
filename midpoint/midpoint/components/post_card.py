import reflex as rx


def post_card(post: dict) -> rx.Component:
    """게시글 목록의 카드 하나. 클릭하면 상세 페이지로 이동한다."""
    return rx.link(
        rx.box(
            rx.heading(post["title"], size="4"),
            rx.hstack(
                rx.text(post["author"], size="2", color="gray"),
                rx.text(post["created_at"], size="2", color="gray"),
                spacing="3",
            ),
            padding="1em",
            border="1px solid var(--gray-6)",
            border_radius="8px",
            width="100%",
            _hover={"border_color": "var(--accent-8)"},
        ),
        href="/post/" + post["id"].to_string(),
        text_decoration="none",
        width="100%",
    )

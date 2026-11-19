import reflex as rx

from ..schemas import PostSummary


def post_card(post: rx.Var[PostSummary]) -> rx.Component:
    return rx.link(
        rx.card(
            rx.heading(post.title, size="4"),
            rx.hstack(
                rx.text(post.author, size="2"),
                rx.text(post.created_at, size="1"),
                color="gray",
                wrap="wrap",
            ),
            width="100%",
        ),
        href="/post/" + post.id.to_string(),
        text_decoration="none",
        width="100%",
    )

import reflex as rx


def notice(title: str, *children: rx.Component) -> rx.Component:
    return rx.box(
        rx.heading(title, size="4"),
        *children,
        border="1px solid #ddd",
        padding="1rem",
        width="100%",
    )

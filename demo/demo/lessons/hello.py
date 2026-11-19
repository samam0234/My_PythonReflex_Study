import reflex as rx


class HelloState(rx.State):
    count: int = 0

    @rx.event
    def increment(self):
        self.count += 1


def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Hello, Reflex!", size="7"),
        rx.text("Python으로 만든 첫 화면"),
        rx.text("클릭 수: ", HelloState.count),
        rx.button("증가", on_click=HelloState.increment),
        spacing="4",
        padding="2rem",
    )

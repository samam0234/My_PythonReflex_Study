import reflex as rx


class DataState(rx.State):
    names: list[str] = []
    show_list: bool = True

    @rx.event
    def add_name(self):
        self.names.append(f"항목 {len(self.names) + 1}")

    @rx.event
    def toggle(self):
        self.show_list = not self.show_list

    @rx.var
    def total(self) -> int:
        return len(self.names)


def index() -> rx.Component:
    return rx.vstack(
        rx.text("개수: ", DataState.total),
        rx.button("추가", on_click=DataState.add_name),
        rx.button("표시 전환", on_click=DataState.toggle),
        rx.cond(
            DataState.show_list,
            rx.vstack(rx.foreach(DataState.names, lambda name: rx.text(name))),
            rx.text("목록 숨김"),
        ),
        rx.text(rx.cond(~DataState.show_list, "숨김 상태", "표시 상태")),
    )

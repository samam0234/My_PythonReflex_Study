from typing import Any, TypedDict

import reflex as rx


class TodoItem(TypedDict):
    id: int
    title: str
    done: bool


class TodoState(rx.State):
    items: list[TodoItem] = []
    error: str = ""
    _next_id: int = 1

    @rx.var
    def remaining(self) -> int:
        return sum(not item["done"] for item in self.items)

    @rx.event
    def add(self, data: dict[str, Any]):
        value = data.get("title")
        title = value.strip() if isinstance(value, str) else ""
        if not 1 <= len(title) <= 80:
            self.error = "할 일을 1~80자로 입력하세요."
            return
        self.items.append({"id": self._next_id, "title": title, "done": False})
        self._next_id += 1
        self.error = ""

    @rx.event
    def toggle(self, item_id: int):
        for item in self.items:
            if item["id"] == item_id:
                item["done"] = not item["done"]
                return

    @rx.event
    def remove(self, item_id: int):
        self.items = [item for item in self.items if item["id"] != item_id]


def todo_row(item: rx.Var[TodoItem]) -> rx.Component:
    return rx.hstack(
        rx.cond(item["done"], rx.text("완료"), rx.text("진행 중")),
        rx.text(item["title"]),
        rx.button("완료 전환", on_click=TodoState.toggle(item["id"])),
        rx.button("삭제", on_click=TodoState.remove(item["id"]), color_scheme="red"),
        align="center",
        wrap="wrap",
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Reflex Todo"),
            rx.form(
                rx.hstack(
                    rx.input(name="title", placeholder="할 일"), rx.button("추가", type="submit")
                ),
                on_submit=TodoState.add,
            ),
            rx.text(TodoState.error, role="alert"),
            rx.text("남은 할 일: ", TodoState.remaining, id="todo-remaining"),
            rx.cond(
                TodoState.items.length() == 0,
                rx.text("할 일이 없습니다."),
                rx.foreach(TodoState.items, todo_row),
            ),
            rx.link("실습 목록", href="/"),
            align="start",
            padding_y="3rem",
        )
    )

import reflex as rx


class RouteState(rx.State):
    title: str = ""
    error: str = ""

    @rx.event
    def load_post(self):
        self.title = ""
        self.error = ""
        try:
            selected = int(self.lesson_post_id)
        except ValueError:
            self.error = "올바른 글 번호가 아닙니다."
            return
        if selected != 1:
            self.error = "글을 찾을 수 없습니다."
            return
        self.title = "첫 번째 글"


def index() -> rx.Component:
    return rx.link("첫 글 보기", href="/study4/post/1")


def detail() -> rx.Component:
    return rx.vstack(
        rx.cond(RouteState.error != "", rx.text(RouteState.error), rx.heading(RouteState.title)),
        rx.link("목록", href="/study4"),
    )

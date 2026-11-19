import reflex as rx

DATA = [{"day": "월", "count": 3}, {"day": "화", "count": 5}, {"day": "수", "count": 2}]


class ChartState(rx.State):
    period: str = "최근 3일"

    @rx.event
    def set_period(self, value: str):
        if value in {"최근 3일", "오늘"}:
            self.period = value

    @rx.var
    def chart_data(self) -> list[dict[str, str | int]]:
        return DATA[-1:] if self.period == "오늘" else DATA


def index() -> rx.Component:
    return rx.vstack(
        rx.select(["최근 3일", "오늘"], value=ChartState.period, on_change=ChartState.set_period),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.x_axis(data_key="day"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            rx.recharts.bar(data_key="count", fill="#4f46e5"),
            data=ChartState.chart_data,
            width="100%",
            height=260,
        ),
        width="100%",
        max_width="640px",
    )

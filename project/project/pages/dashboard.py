import reflex as rx

from ..components.layout import error_message, layout
from ..state import State


def dashboard() -> rx.Component:
    return layout(
        rx.heading("최근 7일 게시글", size="7"),
        error_message(),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.x_axis(data_key="day"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            rx.recharts.bar(data_key="count", fill="#4f46e5"),
            data=State.chart_data,
            width="100%",
            height=280,
        ),
        rx.text("텍스트 요약", weight="bold"),
        rx.foreach(State.chart_data, lambda row: rx.text(row["day"], ": ", row["count"], "개")),
        rx.heading("읽기 전용 MCP", size="5", margin_top="2rem"),
        rx.button("MCP 연결 확인", on_click=State.check_mcp, loading=State.mcp_busy),
        rx.text(State.mcp_result, id="mcp-result"),
    )


def operations_page() -> rx.Component:
    return layout(
        rx.heading("운영 지표", size="7"),
        error_message(),
        rx.text("이 프로세스의 최근 이벤트 지표입니다. 재시작하면 초기화됩니다.", color="gray"),
        rx.code_block(State.operations, language="json"),
        rx.button("지표 갱신", on_click=State.load_operations),
    )

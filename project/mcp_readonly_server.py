"""study18: 비밀 값·DB 접근이 없는 고정 읽기 전용 stdio 도구."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("reflex-study-readonly")


@mcp.tool()
def course_status() -> str:
    return "Reflex 학습용 읽기 전용 도구가 연결되었습니다."


if __name__ == "__main__":
    mcp.run(transport="stdio")

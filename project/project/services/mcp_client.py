"""임의 명령을 받지 않고 저장소 안의 고정 MCP 서버만 실행한다."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def read_course_status() -> str:
    server = Path(__file__).resolve().parents[2] / "mcp_readonly_server.py"
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(server)],
        cwd=str(server.parent),
        env={"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    async with asyncio.timeout(10):
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                if "course_status" not in {tool.name for tool in listed.tools}:
                    raise ValueError("허용한 MCP 도구가 없습니다.")
                result = await session.call_tool("course_status", arguments={})
                if result.isError:
                    raise ValueError("MCP 조회가 실패했습니다.")
                return "\n".join(item.text for item in result.content if item.type == "text")[:2000]

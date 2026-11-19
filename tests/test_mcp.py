from project.services.mcp_client import read_course_status


async def test_real_readonly_mcp_round_trip():
    result = await read_course_status()
    assert result == "Reflex 학습용 읽기 전용 도구가 연결되었습니다."

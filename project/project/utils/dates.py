"""study13: UTC 저장 값에서 시간대가 명확한 표시 문자열을 생성한다."""

from datetime import datetime
from zoneinfo import ZoneInfo


def seoul_time(iso_utc: str) -> str:
    value = datetime.fromisoformat(iso_utc)
    if value.tzinfo is None:
        raise ValueError("UTC offset이 필요합니다.")
    return value.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")

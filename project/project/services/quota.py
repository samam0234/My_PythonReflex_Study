"""final: 동시에 요청해도 사용자별 하루 10회를 넘지 않는 예약."""

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import CursorResult
from sqlmodel import col

from ..models import AiDaily
from ..settings import get_settings
from .auth import require_user
from .database import open_session
from .errors import LimitExceeded


def reserve_ai_call(raw_token: str) -> None:
    day = datetime.now(timezone.utc).date().isoformat()
    with open_session() as session:
        user = require_user(session, raw_token)
        session.execute(
            insert(AiDaily).values(user_id=user.id, day=day, calls=0).on_conflict_do_nothing()
        )
        result = session.execute(
            update(AiDaily)
            .where(
                col(AiDaily.user_id) == user.id,
                col(AiDaily.day) == day,
                col(AiDaily.calls) < get_settings().ai_daily_limit,
            )
            .values(calls=col(AiDaily.calls) + 1)
        )
        assert isinstance(result, CursorResult)
        if result.rowcount != 1:
            raise LimitExceeded("오늘의 AI 요청 한도를 초과했습니다.")
        session.commit()

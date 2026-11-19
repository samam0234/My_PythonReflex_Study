from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from project.schemas import PostInput
from project.services import ai, auth, posts
from project.services.database import open_session
from project.services.errors import AccessDenied, Conflict, LimitExceeded
from project.services.quota import reserve_ai_call


def make_post(owner):
    with open_session() as session:
        return posts.create_post(session, owner, PostInput(title="제목", content="요약할 본문"))


def test_quota_concurrent(accounts):
    owner, _ = accounts

    def attempt(_):
        try:
            reserve_ai_call(owner)
            return True
        except LimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(18))) == 10


async def test_authorized_ai_and_denied_other(accounts, monkeypatch):
    owner, other = accounts
    post_id = make_post(owner)
    mock = AsyncMock(return_value="요약 결과")
    monkeypatch.setattr(ai, "summarize", mock)
    monkeypatch.setattr(ai, "ai_available", lambda: True)
    assert await ai.summarize_owned_post(owner, post_id) == ("요약 결과", 1)
    with pytest.raises(AccessDenied):
        await ai.summarize_owned_post(other, post_id)
    assert mock.await_count == 1


@pytest.mark.parametrize("changed", ["logout", "edit"])
async def test_old_ai_result_is_rejected(accounts, monkeypatch, changed):
    owner, _ = accounts
    post_id = make_post(owner)

    async def respond(text):
        if changed == "logout":
            auth.revoke(owner)
        else:
            with open_session() as session:
                posts.update_post(
                    session, owner, post_id, PostInput(title="변경", content="바뀐 본문"), 1
                )
        return "오래된 결과"

    monkeypatch.setattr(ai, "ai_available", lambda: True)
    monkeypatch.setattr(ai, "summarize", respond)
    with pytest.raises((AccessDenied, Conflict)):
        await ai.summarize_owned_post(owner, post_id)


async def test_timeout_is_propagated(accounts, monkeypatch):
    owner, _ = accounts
    post_id = make_post(owner)
    monkeypatch.setattr(ai, "ai_available", lambda: True)
    monkeypatch.setattr(ai, "summarize", AsyncMock(side_effect=TimeoutError))
    with pytest.raises(TimeoutError):
        await ai.summarize_owned_post(owner, post_id)


async def test_sdk_bounds_and_no_real_api(monkeypatch):
    captured = {}

    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text="요약")

    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setattr(ai, "AsyncOpenAI", Client)
    assert await ai.summarize("본문") == "요약"
    assert captured["max_retries"] == 0 and captured["max_output_tokens"] == 300
    assert captured["store"] is False and captured["timeout"] == 20


async def test_no_config_does_not_consume_quota(accounts, monkeypatch):
    owner, _ = accounts
    monkeypatch.setattr(ai, "ai_available", lambda: False)
    with pytest.raises(ValueError):
        await ai.summarize_owned_post(owner, make_post(owner))

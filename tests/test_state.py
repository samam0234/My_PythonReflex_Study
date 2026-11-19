import json

from project.state import State


def test_backend_credentials_are_not_serialized():
    state = State(_reflex_internal_init=True)
    state._session_token = "private-test-token"
    state._actor_id = 7
    state._username = "demo"
    serialized = json.dumps(state.dict(), default=str)
    assert "private-test-token" not in serialized
    assert "_session_token" not in serialized
    assert "password_hash" not in serialized
    assert state.is_logged_in


def test_writing_invalidates_page_cache():
    state = State(_reflex_internal_init=True)
    state._expires = 12345
    state._cached_key = "0:test"
    state._invalidate()
    assert state._expires == 0 and state._cached_key == ""

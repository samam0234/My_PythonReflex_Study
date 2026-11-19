import pytest
import reflex as rx
from project.settings import get_settings


def test_reflex_origin_uses_comma_list(monkeypatch):
    monkeypatch.setenv("REFLEX_CORS_ALLOWED_ORIGINS", "http://127.0.0.1:3100,http://localhost:3100")
    config = rx.Config(app_name="origin_test")
    assert list(config.cors_allowed_origins) == ["http://127.0.0.1:3100", "http://localhost:3100"]


def test_production_requires_https(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_API_URL", "http://localhost:8000")
    monkeypatch.setenv("APP_FRONTEND_ORIGIN", "http://localhost:3000")
    with pytest.raises(ValueError):
        get_settings()
    monkeypatch.setenv("APP_API_URL", "https://board.example.com")
    monkeypatch.setenv("APP_FRONTEND_ORIGIN", "https://board.example.com")
    assert get_settings().production

"""study8·16: 환경설정과 공개/비밀 값의 경계."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    db_url: str
    api_url: str
    origins: tuple[str, ...]
    production: bool
    session_seconds: int = 3600
    login_limit: int = 5
    ai_daily_limit: int = 10


def get_settings() -> Settings:
    production = os.getenv("APP_ENV", "development") == "production"
    api_url = os.getenv("APP_API_URL", os.getenv("REFLEX_API_URL", "http://localhost:8000"))
    raw = os.getenv("APP_FRONTEND_ORIGIN", "http://localhost:3000")
    origins = tuple(json.loads(raw)) if raw.startswith("[") else (raw,)
    if not origins or any(not isinstance(v, str) or v == "*" for v in origins):
        raise ValueError("APP_FRONTEND_ORIGIN에는 명시적인 origin이 필요합니다.")
    if production and (
        not api_url.startswith("https://") or any(not o.startswith("https://") for o in origins)
    ):
        raise ValueError("운영 API와 화면 origin에는 HTTPS가 필요합니다.")
    db_url = os.getenv("APP_DB_URL", os.getenv("REFLEX_DB_URL", "sqlite:///reflex.db"))
    if not db_url.startswith("sqlite:"):
        raise ValueError("이 학습 구현은 SQLite를 지원합니다.")
    return Settings(db_url=db_url, api_url=api_url, origins=origins, production=production)

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("app", ["demo", "midpoint", "project"])
def test_migration_fresh_and_legacy(tmp_path, app):
    db = tmp_path / f"{app}.db"
    env = dict(
        os.environ,
        APP_DB_URL=f"sqlite:///{db.as_posix()}",
        REFLEX_DB_URL=f"sqlite:///{db.as_posix()}",
        APP_ENV="development",
        PYTHONUTF8="1",
    )

    def migrate(revision):
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", revision],
            cwd=ROOT / app,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

    if app == "project":
        migrate("c730dbc292db")
        with sqlite3.connect(db) as connection:
            connection.execute(
                "INSERT INTO post (title,content,author,created_at) VALUES (?,?,?,?)",
                ("보존할 글", "본문", "demo", "2026-11-19 00:00:00"),
            )
    migrate("head")
    migrate("head")  # 이미 적용된 이력의 재실행은 멱등이어야 한다.
    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        if app == "project":
            assert connection.execute("SELECT title,owner_id,revision FROM post").fetchone() == (
                "보존할 글",
                None,
                1,
            )
            assert connection.execute('SELECT count(*) FROM "user"').fetchone()[0] == 0
        elif app == "midpoint":
            assert connection.execute("SELECT count(*) FROM midpoint_post").fetchone()[0] == 0
        else:
            for table in ("fruitrecord", "lessonpost", "authpost"):
                assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0

import json
import sqlite3

from project.health import readiness
from project.manage import backup_database
from project.models import Post
from project.observability import metrics_snapshot, record_event
from project.services.database import open_session


def test_backup_restore(database, tmp_path):
    with open_session() as session:
        session.add(Post(title="보존", content="본문", author="legacy"))
        session.commit()
    destination = tmp_path / "restore.db"
    assert backup_database(destination) == (1, 0)
    with sqlite3.connect(destination) as db:
        assert db.execute("SELECT title FROM post").fetchone()[0] == "보존"
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_readiness_and_metrics(database):
    assert readiness().status_code == 200
    record_event("test", "ok", 1, 12.5)
    metrics = json.loads(metrics_snapshot())
    assert metrics["events"]["test:ok"] >= 1
    assert metrics["timings_ms"]["test"]["p95_ms"] == 12.5

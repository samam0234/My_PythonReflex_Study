"""study12: 실제 DB를 건드리지 않고 전체 조회와 목록 DTO의 p95·크기를 비교."""

import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "project"))
from project.models import Post  # noqa: E402
from project.services.posts import list_posts  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine, select  # noqa: E402


def measure(function):
    for _ in range(3):
        function()
    samples = []
    value = None
    for _ in range(30):
        started = time.perf_counter()
        value = function()
        samples.append((time.perf_counter() - started) * 1000)
    ordered = sorted(samples)
    return {
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(ordered[28], 3),
        "json_bytes": len(json.dumps(value, ensure_ascii=False).encode()),
    }


def main():
    with tempfile.TemporaryDirectory(prefix="reflex-performance-") as tmp:
        engine = create_engine(f"sqlite:///{(Path(tmp) / 'bench.db').as_posix()}")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            session.add_all(
                [
                    Post(title=f"학습 글 {i}", content="가" * 1000, author="benchmark")
                    for i in range(1000)
                ]
            )
            session.commit()

        def full():
            with Session(engine) as session:
                return [
                    row.model_dump(mode="json")
                    for row in session.exec(
                        select(Post).order_by(Post.created_at.desc(), Post.id.desc())
                    ).all()
                ]

        def paged():
            with Session(engine) as session:
                return list_posts(session).model_dump(mode="json")

        result = {
            "python": sys.version.split()[0],
            "rows": 1000,
            "body_chars": 1000,
            "warmup": 3,
            "samples": 30,
            "full_query": measure(full),
            "page_20": measure(paged),
        }
        with engine.connect() as connection:
            result["query_plan"] = [
                list(row)
                for row in connection.exec_driver_sql(
                    "EXPLAIN QUERY PLAN SELECT id,title,author,created_at FROM post ORDER BY created_at DESC,id DESC LIMIT 20"
                ).all()
            ]
        engine.dispose()
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    path = ROOT / "artifacts" / "benchmark.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

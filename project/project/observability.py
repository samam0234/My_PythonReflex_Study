"""study16: 허용한 필드만 JSON 로그로 남기고 프로세스 지표를 집계."""

import json
import logging
import threading
from collections import Counter, deque
from datetime import datetime, timezone

_logger = logging.getLogger("reflex.board")
_lock = threading.Lock()
_counts: Counter[str] = Counter()
_durations: dict[str, deque[float]] = {}


def configure_logging() -> None:
    if not _logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
        _logger.propagate = False
    _logger.setLevel(logging.INFO)


def record_event(
    action: str, outcome: str, actor_id: int | None = None, duration_ms: float | None = None
) -> None:
    with _lock:
        _counts[f"{action}:{outcome}"] += 1
        if duration_ms is not None:
            _durations.setdefault(action, deque(maxlen=1000)).append(duration_ms)
    _logger.info(
        json.dumps(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "outcome": outcome,
                "actor_id": actor_id,
                "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            },
            ensure_ascii=False,
        )
    )


def metrics_snapshot() -> str:
    with _lock:
        timings = {}
        for action, samples in _durations.items():
            ordered = sorted(samples)
            if ordered:
                index = min(len(ordered) - 1, int(len(ordered) * 0.95))
                timings[action] = {"samples": len(ordered), "p95_ms": round(ordered[index], 2)}
        return json.dumps({"events": dict(_counts), "timings_ms": timings}, ensure_ascii=False)

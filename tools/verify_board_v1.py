"""격리된 FastAPI와 Reflex를 실행하고 실제 HTTP 연동을 브라우저에서 확인한다."""

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from verify_app import ROOT, free_port, run, stop_process_tree


def main():
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="reflex-board-v1-") as folder:
        os.environ.update(
            BOARD_V1_DB=str(Path(folder) / "board.sqlite3"),
            BOARD_V1_API_URL=url,
            BOARD_V1_VERIFY="1",
            PYTHONUTF8="1",
        )
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        server = subprocess.Popen(command, cwd=ROOT)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and server.poll() is None:
                try:
                    with urllib.request.urlopen(url + "/health", timeout=1):
                        break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("FastAPI /health 응답을 받지 못했습니다.")
            run("demo", "dev", False, backend_port=8001)
        finally:
            stop_process_tree(server.pid)
            server.wait(timeout=10)


if __name__ == "__main__":
    main()

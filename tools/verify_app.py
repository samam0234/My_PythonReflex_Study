"""임시 DB와 별도 포트에서 실제 Reflex 서버→브라우저→DB 흐름을 검증한다."""

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop_process_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        processes = parent.children(recursive=True) + [parent]
        for process in reversed(processes):
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(processes, timeout=8)
        for process in alive:
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
    except psutil.NoSuchProcess:
        pass


def run(app: str, mode: str, build_only: bool, backend_port: int | None = None):
    folder = ROOT / app
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    back = backend_port if backend_port is not None else free_port()
    front = free_port()
    while front == back:
        front = free_port()
    with tempfile.TemporaryDirectory(prefix=f"reflex-{app}-verify-") as tmp:
        db = Path(tmp) / "verify.db"
        url = f"http://127.0.0.1:{front}"
        api = url if mode == "prod" else f"http://127.0.0.1:{back}"
        env = dict(
            os.environ,
            PYTHONUTF8="1",
            PYTHONIOENCODING="utf-8",
            APP_ENV="development",
            APP_DB_URL=f"sqlite:///{db.as_posix()}",
            REFLEX_DB_URL=f"sqlite:///{db.as_posix()}",
            APP_API_URL=api,
            REFLEX_API_URL=api,
            APP_FRONTEND_ORIGIN=url,
            REFLEX_CORS_ALLOWED_ORIGINS=url,
            REFLEX_E2E_URL=url,
            REFLEX_E2E_APP=app,
            REFLEX_E2E_ARTIFACTS=str(artifacts),
            PYTHONPATH=str(folder),
        )
        # 테스트가 실제 유료 공급자를 호출하지 않도록 실행 환경에서 키를 제거한다.
        env.pop("OPENAI_API_KEY", None)
        env.pop("AI_MODEL", None)
        env.pop("REFLEX_REDIS_URL", None)
        env["GRANIAN_WORKERS"] = "1"
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=folder, env=env, check=True
        )
        if app == "project":
            subprocess.run(
                [sys.executable, "-m", "project.manage", "seed-demo"],
                cwd=folder,
                env=env,
                check=True,
            )
        if mode == "prod" or build_only:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "reflex",
                    "export",
                    "--frontend-only",
                    "--no-zip",
                    "--env",
                    "prod",
                ],
                cwd=folder,
                env=env,
                check=True,
            )
        if build_only:
            return
        log_path = artifacts / f"{app}-{mode}.log"
        command = [
            sys.executable,
            "-m",
            "reflex",
            "run",
            "--env",
            mode,
            "--frontend-port",
            str(front),
            "--backend-port",
            str(front if mode == "prod" else back),
            "--backend-host",
            "127.0.0.1",
        ]
        if mode == "prod":
            command.append("--single-port")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                command,
                cwd=folder,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            try:
                deadline = time.monotonic() + 240
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(
                            f"서버 종료: {log_path.read_text(encoding='utf-8')[-4000:]}"
                        )
                    try:
                        with urllib.request.urlopen(url, timeout=2) as response:
                            if response.status == 200:
                                break
                    except (OSError, urllib.error.URLError):
                        time.sleep(1)
                else:
                    raise TimeoutError(f"서버 준비 시간 초과: {log_path}")
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "tests/e2e",
                        "-q",
                        "-x",
                        "--browser",
                        "chromium",
                    ],
                    cwd=ROOT,
                    env=env,
                    check=True,
                )
            finally:
                stop_process_tree(process.pid)
                process.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", choices=["demo", "midpoint", "project"], default="project")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--backend-port", type=int)
    args = parser.parse_args()
    if args.backend_port is not None and (
        args.mode != "dev" or not 1 <= args.backend_port <= 65535
    ):
        parser.error("--backend-port requires dev mode and a port from 1 to 65535")
    run(args.app, args.mode, args.build_only, args.backend_port)

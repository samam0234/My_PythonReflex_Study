"""로컬 포트 443에서 임시 Docker 볼륨과 Caddy TLS로 배포 경로를 검증한다."""

import json
import ssl
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright
from verify_app import ROOT

URL = "https://localhost"


def docker(*args, check=True):
    return subprocess.run(["docker", *args], cwd=ROOT, check=check)


def readiness():
    # 이 검사에만 Caddy가 생성한 로컬 테스트 인증서를 허용한다.
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(URL + "/health/ready", context=context, timeout=2) as response:
        if json.load(response)["status"] != "ready":
            raise RuntimeError("DB 준비 상태를 확인하지 못했습니다.")


def wait_for_app():
    deadline = time.monotonic() + 80
    while time.monotonic() < deadline:
        try:
            readiness()
            return
        except (OSError, ValueError):
            time.sleep(1)
    raise TimeoutError("프록시를 통한 응답을 받지 못했습니다.")


def login(page):
    page.goto(URL + "/login", wait_until="networkidle")
    assert page.url.startswith(URL + "/login")
    page.locator('input[name="username"]').fill("demo")
    page.locator('input[name="password"]').fill("demo-password-123")
    page.get_by_role("button", name="로그인", exact=True).click()
    expect(page.get_by_role("button", name="로그아웃")).to_be_visible(timeout=20_000)


def main():
    prefix = "reflex-check-" + uuid4().hex[:10]
    app, proxy, network, volume = (f"{prefix}-{name}" for name in ("app", "tls", "net", "db"))
    image = "reflex-local:tls-check"
    env = [
        "-e",
        "APP_DB_URL=sqlite:////data/board.db",
        "-e",
        "REFLEX_DB_URL=sqlite:////data/board.db",
        "-v",
        volume + ":/data",
    ]

    def start_app():
        docker(
            "run",
            "-d",
            "--name",
            app,
            "--network",
            network,
            "--network-alias",
            "board",
            *env,
            image,
        )

    docker("build", "--build-arg", f"PUBLIC_API_URL={URL}", "-t", image, "project")
    try:
        docker("network", "create", network)
        docker("volume", "create", volume)
        docker("run", "--rm", *env, image, "reflex", "db", "migrate")
        docker(
            "run",
            "--rm",
            *env,
            "-e",
            "APP_ENV=development",
            image,
            "python",
            "-m",
            "project.manage",
            "seed-demo",
        )
        start_app()
        docker(
            "run",
            "-d",
            "--name",
            proxy,
            "--network",
            network,
            "-p",
            "127.0.0.1:443:443",
            "caddy:2.10.2",
            "caddy",
            "reverse-proxy",
            "--from",
            URL,
            "--to",
            "board:3000",
            "--internal-certs",
        )
        wait_for_app()
        docker("exec", app, "sh", "-c", 'test "$(id -u)" = 10001')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_context(ignore_https_errors=True).new_page()
            socket_urls = []
            page.on("websocket", lambda socket: socket_urls.append(socket.url))
            login(page)
            page.get_by_role("link", name="새 글 작성").click()
            page.locator('input[name="title"]').fill(prefix)
            page.locator('textarea[name="content"]').fill("영속 볼륨 확인")
            page.get_by_role("button", name="작성 완료").click()
            expect(page.get_by_role("heading", name=prefix, exact=True)).to_be_visible()
            detail = page.url
            assert any(url.startswith("wss://localhost/") for url in socket_urls)
            print("HTTPS redirect, WSS, login, write and non-root UID: PASS", flush=True)
            docker("exec", app, "python", "-m", "project.manage", "backup", "/data/check-backup.db")
            docker("rm", "-f", app)
            start_app()
            wait_for_app()
            page.goto(detail)
            expect(page.get_by_text("영속 볼륨 확인", exact=True)).to_be_visible()
            expect(page.get_by_role("link", name="로그인", exact=True)).to_be_visible()
            login(page)
            page.goto(detail)
            page.get_by_role("button", name="삭제", exact=True).click()
            expect(page.get_by_role("heading", name=prefix, exact=True)).to_have_count(0)
            print(
                "Container replacement, retained post, cleared session and relogin: PASS",
                flush=True,
            )

        def elapsed(_):
            started = time.perf_counter()
            readiness()
            return (time.perf_counter() - started) * 1000

        with ThreadPoolExecutor(max_workers=8) as workers:
            samples = sorted(workers.map(elapsed, range(64)))
        print(f"Local TLS readiness: 64/64 successful, 8 concurrent, p95 {samples[60]:.1f} ms")
    except BaseException:
        docker("logs", "--tail", "40", app, check=False)
        raise
    finally:
        docker("rm", "-f", proxy, app, check=False)
        docker("network", "rm", network, check=False)
        docker("volume", "rm", volume, check=False)


if __name__ == "__main__":
    main()

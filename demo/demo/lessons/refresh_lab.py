import asyncio

import httpx
import reflex as rx


async def request_with_refresh(client: httpx.AsyncClient) -> tuple[httpx.Response, list[int]]:
    first = await client.get("/result", headers={"Authorization": "Bearer simulated-expired"})
    statuses = [first.status_code]
    if first.status_code != 401:
        return first, statuses

    refreshed = await client.post("/refresh")
    statuses.append(refreshed.status_code)
    if not refreshed.is_success:
        return refreshed, statuses

    access = refreshed.json()["access"]
    retried = await client.get("/result", headers={"Authorization": f"Bearer {access}"})
    statuses.append(retried.status_code)
    return retried, statuses


def simulated_transport(failure: str) -> httpx.MockTransport:
    async def respond(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.15)
        if request.url.path == "/refresh":
            if failure == "refresh":
                return httpx.Response(401)
            return httpx.Response(200, json={"access": "simulated-renewed"})
        if request.headers.get("Authorization") != "Bearer simulated-renewed" or failure == "retry":
            return httpx.Response(401)
        return httpx.Response(200, json={"label": "갱신 후 조회 성공"})

    return httpx.MockTransport(respond)


class RefreshState(rx.State):
    busy: bool = False
    status: str = ""
    result: str = ""

    @rx.event
    async def run(self, failure: str):
        if self.busy or failure not in {"none", "refresh", "retry"}:
            return
        self.busy = True
        self.status = ""
        yield
        try:
            async with (
                asyncio.timeout(3),
                httpx.AsyncClient(
                    base_url="https://reflex-lab.invalid",
                    transport=simulated_transport(failure),
                ) as client,
            ):
                response, statuses = await request_with_refresh(client)
            self.status = " → ".join(str(code) for code in statuses)
            if response.is_success:
                self.result = response.json()["label"]
            else:
                self.result = "실습 세션 만료 · 다시 로그인하세요."
        except TimeoutError:
            self.status = "조회 시간 초과"
        finally:
            self.busy = False


def panel() -> rx.Component:
    return rx.vstack(
        rx.heading("HTTP 401 복구 실습", size="5"),
        rx.text("로컬 모의 응답으로 요청 순서를 확인합니다."),
        rx.hstack(
            rx.button("갱신 성공", on_click=RefreshState.run("none"), disabled=RefreshState.busy),
            rx.button(
                "갱신 거부", on_click=RefreshState.run("refresh"), disabled=RefreshState.busy
            ),
            rx.button(
                "재요청 거부", on_click=RefreshState.run("retry"), disabled=RefreshState.busy
            ),
            wrap="wrap",
        ),
        rx.cond(RefreshState.busy, rx.text("응답 대기 중")),
        rx.text(RefreshState.status, id="refresh-status"),
        rx.text(RefreshState.result, role="status"),
        align="start",
    )

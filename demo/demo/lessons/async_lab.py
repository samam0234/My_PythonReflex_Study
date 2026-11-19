import asyncio
import time

import reflex as rx


async def fetch_label() -> str:
    await asyncio.sleep(1)
    return "조회 완료"


class AsyncState(rx.State):
    result: str = ""
    busy: bool = False
    error: str = ""
    _cached: str = ""
    _expires: float = 0.0

    @rx.var(cache=True)
    def result_length(self) -> int:
        return len(self.result)

    @rx.event(background=True)
    async def reload(self):
        async with self:
            if self.busy:
                return
            if self._cached and time.monotonic() < self._expires:
                self.result = self._cached
                return
            self.busy = True
            self.error = ""
        try:
            value = await asyncio.wait_for(fetch_label(), timeout=5)
            async with self:
                self.result = value
                self._cached = value
                self._expires = time.monotonic() + 30
        except TimeoutError:
            async with self:
                self.error = "조회 시간이 초과되었습니다."
        finally:
            async with self:
                self.busy = False

    @rx.event
    def invalidate(self):
        self._cached = ""
        self._expires = 0.0

    @rx.event
    async def reload_with_yield(self):
        if self.busy:
            return
        self.busy = True
        yield
        try:
            self.result = await asyncio.wait_for(fetch_label(), timeout=5)
        finally:
            self.busy = False


def index() -> rx.Component:
    return rx.vstack(
        rx.button("조회", on_click=AsyncState.reload, loading=AsyncState.busy),
        rx.button("yield 조회", on_click=AsyncState.reload_with_yield),
        rx.button("캐시 비우기", on_click=AsyncState.invalidate),
        rx.text(AsyncState.result),
        rx.text(AsyncState.error, role="alert"),
        rx.text("결과 길이: ", AsyncState.result_length),
    )

"""Reflex api_transformer를 통해 readiness만 추가하는 ASGI 래퍼."""

import asyncio

from sqlalchemy import text
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .services.database import open_session


def readiness() -> JSONResponse:
    try:
        with open_session() as session:
            session.execute(text("SELECT id, owner_id, revision FROM post LIMIT 1"))
            session.execute(text("SELECT token_hash FROM loginsession LIMIT 1"))
        return JSONResponse({"status": "ready"})
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)


class HealthCheck:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["path"] == "/health/ready":
            response = await asyncio.to_thread(readiness)
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)

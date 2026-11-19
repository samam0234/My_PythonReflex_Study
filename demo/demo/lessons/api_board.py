"""Reflex 서버 이벤트에서 별도 프로세스의 공통 게시판 API를 호출한다."""

import os
from typing import Any

import httpx
import reflex as rx


class ApiBoard(rx.State):
    rows: list[dict[str, Any]] = []
    selected: dict[str, Any] = {}
    comments: list[dict[str, Any]] = []
    user_id: int = 0
    nickname: str = ""
    selected_id: int = 0
    title: str = ""
    body: str = ""
    query: str = ""
    page: int = 1
    total_pages: int = 0
    message: str = ""
    _access_token: str = ""

    async def _request(self, method, path, **kwargs):
        base = os.getenv("BOARD_V1_API_URL", "http://127.0.0.1:8011")
        headers = {"Authorization": f"Bearer {self._access_token}"} if self._access_token else {}
        try:
            async with httpx.AsyncClient(base_url=base, timeout=5, headers=headers) as client:
                response = await client.request(method, path, **kwargs)
        except httpx.RequestError:
            self.message = (
                "FastAPI 서버에 연결할 수 없습니다. backend/README.md의 실행 방법을 확인하세요."
            )
            return None
        self.message = f"HTTP {response.status_code}"
        if response.status_code == 204:
            return {}
        if not response.is_success:
            if response.status_code == 401 and path != "/api/auth/login":
                self._clear_session()
            try:
                self.message += " · " + response.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                pass
            return None
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except ValueError:
            self.message += " · JSON 응답을 읽을 수 없습니다."
            return None

    def _clear_session(self):
        self.user_id = 0
        self.nickname = ""
        self._access_token = ""

    @rx.event
    def set_title(self, value: str):
        self.title = value

    @rx.event
    def set_body(self, value: str):
        self.body = value

    @rx.event
    async def signup(self, data: dict[str, Any]):
        await self._request("POST", "/api/auth/signup", json=data)

    @rx.event
    async def login(self, data: dict[str, Any]):
        result = await self._request("POST", "/api/auth/login", json=data)
        if result is not None:
            credentials = result["data"]
            self._access_token = credentials["accessToken"]
            self.user_id = credentials["user"]["id"]
            self.nickname = credentials["user"]["nickname"]

    @rx.event
    async def logout(self):
        if await self._request("POST", "/api/auth/logout") is not None:
            self._clear_session()

    @rx.event
    async def load(self):
        result = await self._request(
            "GET", "/api/posts", params={"q": self.query, "page": self.page, "limit": 10}
        )
        if result is not None:
            self.rows = result["data"]
            self.total_pages = result["meta"]["totalPages"]

    @rx.event
    async def search(self, data: dict[str, Any]):
        self.query = str(data.get("q", ""))[:200]
        self.page = 1
        await self.load()

    @rx.event
    async def turn_page(self, direction: int):
        target = self.page + direction
        if direction in (-1, 1) and 1 <= target <= self.total_pages:
            self.page = target
            await self.load()

    async def _open(self, post_id: int):
        result = await self._request("GET", f"/api/posts/{post_id}")
        if result is None:
            return
        self.selected = result["data"]
        self.selected_id = post_id
        self.title = self.selected["title"]
        self.body = self.selected["body"]
        await self._load_comments()

    async def _load_comments(self):
        result = await self._request("GET", f"/api/posts/{self.selected_id}/comments")
        self.comments = result["data"] if result is not None else []

    @rx.event
    async def open_post(self, post_id: int):
        await self._open(post_id)

    @rx.event
    async def create(self, data: dict[str, Any]):
        result = await self._request("POST", "/api/posts", json=data)
        if result is not None:
            await self.load()
            await self._open(result["data"]["id"])
            self.message = "HTTP 201 · 작성 완료"

    @rx.event
    async def update(self, data: dict[str, Any]):
        result = await self._request("PATCH", f"/api/posts/{self.selected_id}", json=data)
        if result is not None:
            await self.load()
            await self._open(self.selected_id)
            self.message = "HTTP 200 · 수정 완료"

    @rx.event
    async def delete(self):
        if await self._request("DELETE", f"/api/posts/{self.selected_id}") is not None:
            self.selected = {}
            self.selected_id = 0
            self.comments = []
            await self.load()
            self.message = "HTTP 204 · 삭제 완료"

    @rx.event
    async def comment(self, data: dict[str, Any]):
        path = f"/api/posts/{self.selected_id}/comments"
        if await self._request("POST", path, json=data) is not None:
            await self._load_comments()
            await self.load()
            self.message = "HTTP 201 · 댓글 작성 완료"

    @rx.event
    async def remove_comment(self, comment_id: int):
        if await self._request("DELETE", f"/api/comments/{comment_id}") is not None:
            await self._load_comments()
            await self.load()
            self.message = "HTTP 204 · 댓글 삭제 완료"


def account_form(register: bool):
    label = "가입" if register else "로그인"
    fields = [rx.input(name="email", type="email", placeholder="이메일", required=True)]
    if register:
        fields.append(rx.input(name="nickname", placeholder="닉네임", required=True))
    return rx.form(
        rx.vstack(
            *fields,
            rx.input(name="password", type="password", placeholder="비밀번호", required=True),
            rx.button(label, type="submit"),
        ),
        on_submit=ApiBoard.signup if register else ApiBoard.login,
        aria_label=label,
    )


def post_form(edit: bool):
    label = "글 수정" if edit else "글 작성"
    title = (
        rx.input(name="title", value=ApiBoard.title, on_change=ApiBoard.set_title)
        if edit
        else rx.input(name="title", placeholder="제목")
    )
    body = (
        rx.text_area(name="body", value=ApiBoard.body, on_change=ApiBoard.set_body)
        if edit
        else rx.text_area(name="body", placeholder="본문")
    )
    return rx.form(
        rx.vstack(title, body, rx.button(label, type="submit")),
        on_submit=ApiBoard.update if edit else ApiBoard.create,
        aria_label=label,
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Reflex × FastAPI 게시판"),
            rx.link("실습 목록", href="/"),
            rx.text(ApiBoard.message, role="status", id="api-board-status"),
            rx.cond(
                ApiBoard.user_id > 0,
                rx.hstack(
                    rx.text(ApiBoard.nickname), rx.button("로그아웃", on_click=ApiBoard.logout)
                ),
                rx.hstack(account_form(True), account_form(False), wrap="wrap"),
            ),
            rx.form(
                rx.hstack(
                    rx.input(name="q", placeholder="제목·본문 검색"),
                    rx.button("검색", type="submit"),
                ),
                on_submit=ApiBoard.search,
            ),
            rx.foreach(
                ApiBoard.rows,
                lambda row: rx.button(row["title"], on_click=ApiBoard.open_post(row["id"].to(int))),
            ),
            rx.hstack(
                rx.button("이전", on_click=ApiBoard.turn_page(-1), disabled=ApiBoard.page <= 1),
                rx.text(ApiBoard.page, " / ", ApiBoard.total_pages),
                rx.button(
                    "다음",
                    on_click=ApiBoard.turn_page(1),
                    disabled=ApiBoard.page >= ApiBoard.total_pages,
                ),
            ),
            rx.cond(ApiBoard.user_id > 0, post_form(False)),
            rx.cond(
                ApiBoard.selected_id > 0,
                rx.vstack(
                    rx.heading(ApiBoard.selected["title"], size="4"),
                    rx.text(ApiBoard.selected["body"]),
                    rx.cond(
                        ApiBoard.selected["author"].to(dict[str, int])["id"] == ApiBoard.user_id,
                        rx.vstack(post_form(True), rx.button("글 삭제", on_click=ApiBoard.delete)),
                    ),
                    rx.foreach(
                        ApiBoard.comments,
                        lambda item: rx.hstack(
                            rx.text(item["body"]),
                            rx.cond(
                                item["author"].to(dict[str, int])["id"] == ApiBoard.user_id,
                                rx.button(
                                    "댓글 삭제",
                                    on_click=ApiBoard.remove_comment(item["id"].to(int)),
                                ),
                            ),
                        ),
                    ),
                    rx.cond(
                        ApiBoard.user_id > 0,
                        rx.form(
                            rx.hstack(
                                rx.input(name="body", placeholder="댓글"),
                                rx.button("댓글 등록", type="submit"),
                            ),
                            on_submit=ApiBoard.comment,
                        ),
                    ),
                    align="start",
                ),
            ),
            align="start",
            padding_y="3rem",
        )
    )

"""midpoint → final: 표시 상태는 공개, 인증 근거·작업 세대·캐시는 backend 전용."""

import asyncio
import time
from typing import Any

import reflex as rx
from pydantic import ValidationError

from .observability import metrics_snapshot, record_event
from .schemas import LoginInput, PostDetail, PostInput, PostSummary, parse_post_id
from .services import ai, auth, posts
from .services.database import open_session
from .services.errors import AccessDenied, Conflict, LimitExceeded
from .services.mcp_client import read_course_status


def empty_post() -> PostDetail:
    return PostDetail(id=0, title="", content="", author="", created_at="")


class State(rx.State):
    posts: list[PostSummary] = []
    current_post: PostDetail = empty_post()
    page: int = 0
    total: int = 0
    search: str = ""
    load_note: str = ""
    form_title: str = ""
    form_content: str = ""
    form_error: str = ""
    login_error: str = ""
    login_busy: bool = False
    ai_busy: bool = False
    ai_error: str = ""
    summary: str = ""
    ai_configured: bool = False
    chart_data: list[dict[str, str | int]] = []
    mcp_busy: bool = False
    mcp_result: str = ""
    operations: str = ""
    _session_token: str = ""
    _actor_id: int = 0
    _username: str = ""
    _admin: bool = False
    _generation: int = 0
    _cached_items: list[PostSummary] = []
    _cached_total: int = 0
    _cached_key: str = ""
    _expires: float = 0

    @rx.var
    def is_logged_in(self) -> bool:
        return self._actor_id > 0

    @rx.var
    def is_admin(self) -> bool:
        return self._admin

    @rx.var
    def current_username(self) -> str:
        return self._username

    @rx.var
    def can_edit_current_post(self) -> bool:
        return self._actor_id > 0 and self.current_post.owner_id == self._actor_id

    @rx.var
    def page_label(self) -> str:
        return f"{self.page + 1} / {max(1, (self.total + 19) // 20)} 페이지 · {self.total}개"

    def _clear_auth(self):
        self._session_token = ""
        self._actor_id = 0
        self._username = ""
        self._admin = False
        self._generation += 1
        self.summary = ""
        self.operations = ""

    def _sync_identity(self):
        if self._session_token:
            try:
                self._actor_id, self._username, self._admin = auth.check_identity(
                    self._session_token
                )
            except AccessDenied:
                self._clear_auth()

    def _fail(self, error: Exception):
        if isinstance(error, ValidationError):
            self.form_error = "제목은 1~50자, 본문은 1~5000자로 입력하세요."
        elif isinstance(error, AccessDenied):
            self._sync_identity()
            self.form_error = str(error)
        elif isinstance(error, (ValueError, Conflict, LimitExceeded)):
            self.form_error = str(error)
        else:
            self.form_error = "처리하지 못했습니다. 잠시 후 다시 시도하세요."
        record_event(
            "request",
            "denied" if isinstance(error, AccessDenied) else "error",
            self._actor_id or None,
        )

    def _invalidate(self):
        self._expires = 0
        self._cached_key = ""

    @rx.event
    def on_home(self):
        self._generation += 1
        self.current_post = empty_post()
        self.summary = ""
        self._invalidate()
        try:
            self._sync_identity()
            self.load_posts()
        except Exception as error:
            self._fail(error)

    @rx.event
    def load_posts(self):
        started = time.perf_counter()
        key = f"{self.page}:{self.search}"
        try:
            if key == self._cached_key and time.monotonic() < self._expires:
                self.posts = self._cached_items
                self.total = self._cached_total
                self.load_note = "캐시에서 조회"
                return
            with open_session() as session:
                result = posts.list_posts(session, self.page, self.search)
            self.posts = result.items
            self.total = result.total
            self.page = result.page
            self._cached_items = result.items
            self._cached_total = result.total
            self._cached_key = f"{result.page}:{self.search}"
            self._expires = time.monotonic() + 10
            elapsed = (time.perf_counter() - started) * 1000
            self.load_note = f"DB 조회 {elapsed:.1f}ms · 목록에는 본문을 전송하지 않습니다."
            record_event("list", "ok", self._actor_id or None, elapsed)
        except Exception as error:
            self._fail(error)

    @rx.event
    def search_posts(self, data: dict[str, Any]):
        value = data.get("search", "")
        self.search = value.strip()[:64] if isinstance(value, str) else ""
        self.page = 0
        self._invalidate()
        self.load_posts()

    @rx.event
    def next_page(self):
        if (self.page + 1) * 20 < self.total:
            self.page += 1
            self.load_posts()

    @rx.event
    def previous_page(self):
        self.page = max(0, self.page - 1)
        self.load_posts()

    @rx.event
    def load_post(self):
        self._generation += 1
        self.current_post = empty_post()
        self.summary = ""
        self.ai_error = ""
        self.form_error = ""
        self.ai_configured = ai.ai_available()
        try:
            self._sync_identity()
            with open_session() as session:
                self.current_post = posts.read_post(session, self.post_id)
        except Exception as error:
            self._fail(error)

    @rx.event
    async def login(self, data: dict[str, Any]):
        if self.login_busy:
            return
        self.login_error = ""
        try:
            payload = LoginInput.model_validate(data)
        except ValidationError:
            self.login_error = "아이디 또는 비밀번호가 올바르지 않습니다."
            return
        self.login_busy = True
        yield
        try:
            raw, actor_id, username, admin = await asyncio.to_thread(auth.authenticate, payload)
            if self._session_token:
                await asyncio.to_thread(auth.revoke, self._session_token)
            self._session_token = raw
            self._actor_id = actor_id
            self._username = username
            self._admin = admin
            self._generation += 1
            record_event("login", "ok", actor_id)
            yield rx.redirect("/")
        except (AccessDenied, LimitExceeded) as error:
            self.login_error = str(error)
            record_event("login", "denied")
        except Exception:
            self.login_error = "로그인을 처리하지 못했습니다."
            record_event("login", "error")
        finally:
            self.login_busy = False

    @rx.event
    def logout(self):
        try:
            if self._session_token:
                auth.revoke(self._session_token)
        except Exception:
            record_event("logout", "error")
        self._clear_auth()
        return rx.redirect("/login")

    @rx.event
    def set_form_title(self, value: str):
        self.form_title = value[:51]
        self.form_error = ""

    @rx.event
    def set_form_content(self, value: str):
        self.form_content = value[:5001]
        self.form_error = ""

    @rx.event
    def prepare_new_post(self):
        self._generation += 1
        self.summary = ""
        self.form_error = ""
        self.form_title = ""
        self.form_content = ""
        try:
            self._sync_identity()
            if not self._actor_id:
                return rx.redirect("/login")
        except Exception as error:
            self._fail(error)

    @rx.event
    def create_post(self):
        try:
            payload = PostInput(title=self.form_title, content=self.form_content)
            with open_session() as session:
                post_id = posts.create_post(session, self._session_token, payload)
            self._invalidate()
            record_event("create", "ok", self._actor_id)
            return rx.redirect(f"/post/{post_id}")
        except Exception as error:
            self._fail(error)

    @rx.event
    def prepare_edit_post(self):
        self.load_post()
        if not self._actor_id:
            return rx.redirect("/login")
        if not self.can_edit_current_post:
            self.form_error = "이 글을 수정할 수 없습니다."
            return
        self.form_title = self.current_post.title
        self.form_content = self.current_post.content

    @rx.event
    def update_post(self):
        try:
            payload = PostInput(title=self.form_title, content=self.form_content)
            with open_session() as session:
                posts.update_post(
                    session, self._session_token, self.post_id, payload, self.current_post.revision
                )
            self._invalidate()
            record_event("update", "ok", self._actor_id)
            return rx.redirect(f"/post/{self.current_post.id}")
        except Exception as error:
            self._fail(error)

    @rx.event
    def delete_post(self, post_id: int):
        try:
            with open_session() as session:
                posts.delete_post(session, self._session_token, parse_post_id(post_id))
            self._invalidate()
            record_event("delete", "ok", self._actor_id)
            return rx.redirect("/")
        except Exception as error:
            self._fail(error)

    @rx.event(background=True)
    async def summarize_post(self, post_id: int):
        async with self:
            if self.ai_busy:
                return
            self.ai_busy = True
            self.ai_error = ""
            self.summary = ""
            raw, generation = self._session_token, self._generation
        try:
            answer, revision = await ai.summarize_owned_post(raw, parse_post_id(post_id))
            async with self:
                if (
                    self._session_token == raw
                    and self._generation == generation
                    and self.current_post.id == post_id
                    and self.current_post.revision == revision
                ):
                    self.summary = answer
            record_event("ai", "ok")
        except (AccessDenied, ValueError, Conflict, LimitExceeded) as error:
            async with self:
                if self._generation == generation:
                    self.ai_error = str(error)
            record_event("ai", "denied")
        except Exception:
            async with self:
                if self._generation == generation:
                    self.ai_error = "요약에 실패했습니다. 잠시 후 다시 시도하세요."
            record_event("ai", "error")
        finally:
            async with self:
                self.ai_busy = False

    @rx.event
    def load_dashboard(self):
        try:
            self._sync_identity()
            with open_session() as session:
                self.chart_data = posts.weekly_counts(session)
        except Exception as error:
            self._fail(error)

    @rx.event(background=True)
    async def check_mcp(self):
        async with self:
            if self.mcp_busy:
                return
            self.mcp_busy = True
        try:
            value = await read_course_status()
            async with self:
                self.mcp_result = value
        except Exception:
            async with self:
                self.mcp_result = "MCP 조회에 실패했습니다."
        finally:
            async with self:
                self.mcp_busy = False

    @rx.event
    def load_operations(self):
        try:
            with open_session() as session:
                user = auth.require_user(session, self._session_token)
                if not user.is_admin:
                    raise AccessDenied("관리자 권한이 필요합니다.")
            self.operations = metrics_snapshot()
        except Exception as error:
            self.operations = ""
            self._fail(error)

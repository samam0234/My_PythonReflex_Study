"""studyFinal: Reflex 단독 게시판의 페이지·내장 health API."""

import reflex as rx

from .components import layout  # noqa: F401
from .health import HealthCheck
from .observability import configure_logging
from .pages.dashboard import dashboard, operations_page
from .pages.index import index
from .pages.login import login_page
from .pages.post_detail import post_detail
from .pages.post_edit import post_edit_page
from .pages.post_new import post_new_page
from .state import State

configure_logging()
app = rx.App(api_transformer=HealthCheck)
app.add_page(index, route="/", on_load=State.on_home, title="Reflex 게시판")
app.add_page(login_page, route="/login", title="로그인")
app.add_page(post_detail, route="/post/[post_id]", on_load=State.load_post, title="게시글")
app.add_page(post_new_page, route="/post/new", on_load=State.prepare_new_post)
app.add_page(post_edit_page, route="/post/[post_id]/edit", on_load=State.prepare_edit_post)
app.add_page(dashboard, route="/dashboard", on_load=State.load_dashboard)
app.add_page(operations_page, route="/ops", on_load=State.load_operations)

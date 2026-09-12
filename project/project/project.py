"""studyFinal — study1~10에서 배운 것을 모두 합친 미니 게시판 웹사이트.

- State 클래스로 상태 관리 (study2)
- 이벤트 핸들러로 CRUD (study3, study4)
- 라우팅으로 목록/상세/작성/수정/로그인 페이지 분리 (study5)
- SQLModel + Alembic으로 DB 연동 (study7)
- 로그인 상태 관리와 보호된 페이지 (study8)
- 환경변수 기반 설정 (study9), Docker 배포 (study10)
"""

import reflex as rx

from .pages.index import index
from .pages.login import login_page
from .pages.post_detail import post_detail
from .pages.post_edit import post_edit_page
from .pages.post_new import post_new_page
from .state import State

app = rx.App()
app.add_page(index, route="/", on_load=State.load_posts)
app.add_page(login_page, route="/login")
app.add_page(post_detail, route="/post/[post_id]", on_load=State.load_posts)
app.add_page(post_new_page, route="/post/new", on_load=State.prepare_new_post)
app.add_page(
    post_edit_page, route="/post/[post_id]/edit", on_load=State.prepare_edit_post
)

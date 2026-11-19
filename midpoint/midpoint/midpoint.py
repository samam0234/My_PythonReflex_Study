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
app.add_page(post_edit_page, route="/post/[post_id]/edit", on_load=State.prepare_edit_post)

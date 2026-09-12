import reflex as rx
import sqlmodel

from .models import Post

# 데모용 계정. 실제 서비스는 반드시 DB + 비밀번호 해시(passlib 등)를 써야 한다.
# (study8 참고)
DEMO_USERS = {
    "demo": "reflex123",
    "guest": "guest123",
}


def _post_to_dict(post: Post) -> dict:
    """DB의 SQLModel 객체를 State에 담을 수 있는 평범한 dict로 변환한다.

    study7에서 배운 대로, datetime은 미리 문자열로 포맷해서 넣는다 —
    화면 쪽 컴포넌트가 date 포맷팅을 신경 쓸 필요가 없어진다.
    """
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
    }


class State(rx.State):
    """게시판 전역 상태. study1~10에서 배운 패턴을 그대로 모아 놓았다."""

    posts: list[dict] = []

    # --- 로그인 상태 (study8) ---
    username_input: str = ""
    password_input: str = ""
    login_error: str = ""
    is_logged_in: bool = False
    current_username: str = ""

    @rx.event
    def set_username_input(self, value: str):
        self.username_input = value
        self.login_error = ""

    @rx.event
    def set_password_input(self, value: str):
        self.password_input = value
        self.login_error = ""

    @rx.event
    def login(self):
        username = self.username_input.strip()
        if DEMO_USERS.get(username) != self.password_input:
            self.login_error = "아이디 또는 비밀번호가 올바르지 않습니다."
            return
        self.is_logged_in = True
        self.current_username = username
        self.password_input = ""
        return rx.redirect("/")

    @rx.event
    def logout(self):
        self.is_logged_in = False
        self.current_username = ""
        return rx.redirect("/")

    # --- 게시글 목록 (study2, study7) ---
    @rx.event
    def load_posts(self):
        with rx.session() as session:
            records = session.exec(
                sqlmodel.select(Post).order_by(Post.created_at.desc())
            ).all()
            self.posts = [_post_to_dict(post) for post in records]

    # --- 글쓰기/수정 폼 (study3, study4) ---
    form_title: str = ""
    form_content: str = ""
    form_error: str = ""

    @rx.event
    def set_form_title(self, value: str):
        self.form_title = value
        self.form_error = ""

    @rx.event
    def set_form_content(self, value: str):
        self.form_content = value
        self.form_error = ""

    def _validate_form(self) -> bool:
        title = self.form_title.strip()
        content = self.form_content.strip()
        if not title:
            self.form_error = "제목을 입력하세요."
            return False
        if len(title) > 50:
            self.form_error = "제목은 50자 이내로 입력하세요."
            return False
        if not content:
            self.form_error = "내용을 입력하세요."
            return False
        return True

    @rx.event
    def prepare_new_post(self):
        """`/post/new` 페이지의 on_load. 로그인 안 했으면 돌려보내고,
        폼을 빈 값으로 초기화한다."""
        if not self.is_logged_in:
            return rx.redirect("/login")
        self.form_title = ""
        self.form_content = ""
        self.form_error = ""

    @rx.event
    def create_post(self):
        """Create — 로그인한 사용자 이름을 작성자로 저장한다."""
        if not self.is_logged_in:
            return rx.redirect("/login")
        if not self._validate_form():
            return
        with rx.session() as session:
            post = Post(
                title=self.form_title.strip(),
                content=self.form_content.strip(),
                author=self.current_username,
            )
            session.add(post)
            session.commit()
            session.refresh(post)
        self.load_posts()
        return rx.redirect(f"/post/{post.id}")

    @rx.event
    def prepare_edit_post(self):
        """`/post/[post_id]/edit` 페이지의 on_load.

        로그인 여부, 그리고 "본인 글인지"까지 서버에서 다시 확인한다 —
        화면에서 수정 버튼을 숨기는 것만으로는 부족하다. URL을 직접
        입력해서 들어오는 경우까지 막아야 진짜 보호가 된다.
        """
        if not self.is_logged_in:
            return rx.redirect("/login")
        self.load_posts()
        post = self.current_post
        if post["id"] == 0 or post["author"] != self.current_username:
            return rx.redirect("/")
        self.form_title = post["title"]
        self.form_content = post["content"]
        self.form_error = ""

    @rx.event
    def update_post(self):
        """Update — DB에서 다시 한번 작성자 본인인지 확인한 뒤 수정한다."""
        if not self._validate_form():
            return
        post_id = int(self.post_id)
        with rx.session() as session:
            record = session.get(Post, post_id)
            if record is None or record.author != self.current_username:
                return rx.redirect("/")
            record.title = self.form_title.strip()
            record.content = self.form_content.strip()
            session.add(record)
            session.commit()
        self.load_posts()
        return rx.redirect(f"/post/{post_id}")

    @rx.event
    def delete_post(self, post_id: int):
        """Delete — 작성자 본인 글만 삭제할 수 있다."""
        with rx.session() as session:
            record = session.get(Post, post_id)
            if record is not None and record.author == self.current_username:
                session.delete(record)
                session.commit()
        self.load_posts()
        return rx.redirect("/")

    # --- 상세 페이지 (study5) ---
    @rx.var
    def current_post(self) -> dict:
        """동적 라우트 `/post/[post_id]`(및 `/post/[post_id]/edit`)의
        `post_id`로 현재 보고 있는 게시글을 찾는다."""
        for post in self.posts:
            if str(post["id"]) == self.post_id:
                return post
        return {"id": 0, "title": "", "content": "", "author": "", "created_at": ""}

    @rx.var
    def can_edit_current_post(self) -> bool:
        return (
            self.is_logged_in
            and self.current_post["author"] == self.current_username
        )

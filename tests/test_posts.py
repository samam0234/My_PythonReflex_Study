import pytest
from project.models import Post
from project.schemas import PostInput
from project.services import auth, posts
from project.services.database import open_session
from project.services.errors import AccessDenied, Conflict
from sqlmodel import select

PAYLOAD = PostInput(title="원래 제목", content="본문")


def make_post(raw):
    with open_session() as session:
        return posts.create_post(session, raw, PAYLOAD)


@pytest.mark.parametrize("anonymous", [True, False])
def test_denied_changes_keep_database(accounts, anonymous):
    owner, other = accounts
    post_id = make_post(owner)
    token = "" if anonymous else other
    with open_session() as session:
        with pytest.raises(AccessDenied):
            posts.update_post(session, token, post_id, PostInput(title="침해", content="침해"), 1)
    with open_session() as session:
        with pytest.raises(AccessDenied):
            posts.delete_post(session, token, post_id)
    with open_session() as session:
        assert posts.read_post(session, post_id).title == "원래 제목"


def test_owner_crud_and_conflict(accounts):
    owner, _ = accounts
    post_id = make_post(owner)
    with open_session() as session:
        row = posts.read_post(session, post_id)
        assert row.owner_id is not None and row.author == "demo"
        posts.update_post(
            session, owner, post_id, PostInput(title="새 제목", content="새 본문"), row.revision
        )
    with open_session() as session:
        assert posts.read_post(session, post_id).revision == 2
        with pytest.raises(Conflict):
            posts.update_post(session, owner, post_id, PAYLOAD, 1)
    with open_session() as session:
        posts.delete_post(session, owner, post_id)
    with open_session() as session:
        assert session.get(Post, post_id) is None


def test_revoked_cannot_create(accounts):
    owner, _ = accounts
    auth.revoke(owner)
    with open_session() as session, pytest.raises(AccessDenied):
        posts.create_post(session, owner, PAYLOAD)


def test_pagination_search_and_dto(database):
    with open_session() as session:
        session.add_all(
            [Post(title=f"글 {i:02}", content="본문" * 100, author="legacy") for i in range(25)]
        )
        session.add(Post(title="100% 진짜", content="비밀 본문", author="legacy"))
        session.commit()
    with open_session() as session:
        first = posts.list_posts(session)
        second = posts.list_posts(session, page=1)
        assert first.total == 26 and len(first.items) == 20 and len(second.items) == 6
        assert not set(row.id for row in first.items) & set(row.id for row in second.items)
        assert all("content" not in row.model_dump() for row in first.items)
        assert len(posts.list_posts(session, search="%").items) == 1
        assert posts.list_posts(session, page=1000, search="없는 제목").page == 0
        assert len(session.exec(select(Post)).all()) == 26


def test_legacy_owner_is_not_claimed(accounts):
    owner, _ = accounts
    with open_session() as session:
        row = Post(title="기존 글", content="본문", author="demo")
        session.add(row)
        session.commit()
        session.refresh(row)
        post_id = row.id
    with open_session() as session, pytest.raises(AccessDenied):
        posts.update_post(session, owner, post_id, PAYLOAD, 1)

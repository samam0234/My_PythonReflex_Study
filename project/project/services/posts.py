"""study6·12·16: 목록 컬럼 제한, 서버 세션/소유권, 낙관적 동시성."""

from datetime import datetime, timezone

from sqlalchemy import func, update
from sqlalchemy.engine import CursorResult
from sqlmodel import Session, col, select

from ..models import Post
from ..schemas import PostDetail, PostInput, PostPage, PostSummary, parse_post_id
from .auth import require_user
from .errors import AccessDenied, Conflict

PAGE_SIZE = 20


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def list_posts(session: Session, page: int = 0, search: str = "") -> PostPage:
    page = max(0, min(page, 1000))
    search = search.strip()[:64]
    query = select(col(Post.id), col(Post.title), col(Post.author), col(Post.created_at))
    count = select(func.count(col(Post.id)))
    if search:
        query = query.where(col(Post.title).contains(search, autoescape=True))
        count = count.where(col(Post.title).contains(search, autoescape=True))
    total = session.exec(count).one()
    # 검색 결과가 줄어 마지막 페이지를 벗어나면 실제 범위로 되돌린다.
    page = min(page, max(0, (total - 1) // PAGE_SIZE))
    rows = session.exec(
        query.order_by(col(Post.created_at).desc(), col(Post.id).desc())
        .offset(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).all()
    items = [
        PostSummary(id=pid, title=title, author=author, created_at=utc_text(created))
        for pid, title, author, created in rows
        if pid is not None
    ]
    return PostPage(items=items, total=total, page=page)


def read_post(session: Session, raw_id: str | int) -> PostDetail:
    post = session.get(Post, parse_post_id(raw_id))
    if post is None or post.id is None:
        raise ValueError("게시글을 찾을 수 없습니다.")
    return PostDetail(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        owner_id=post.owner_id,
        revision=post.revision,
        created_at=utc_text(post.created_at),
    )


def create_post(session: Session, raw_token: str, payload: PostInput) -> int:
    user = require_user(session, raw_token)
    row = Post(title=payload.title, content=payload.content, author=user.username, owner_id=user.id)
    session.add(row)
    session.commit()
    session.refresh(row)
    assert row.id is not None
    return row.id


def update_post(
    session: Session, raw_token: str, raw_id: str | int, payload: PostInput, revision: int
) -> None:
    user = require_user(session, raw_token)
    post = session.get(Post, parse_post_id(raw_id))
    if post is None or post.owner_id != user.id:
        raise AccessDenied("이 글을 수정할 수 없습니다.")
    result = session.execute(
        update(Post)
        .where(
            col(Post.id) == post.id, col(Post.owner_id) == user.id, col(Post.revision) == revision
        )
        .values(title=payload.title, content=payload.content, revision=revision + 1)
    )
    assert isinstance(result, CursorResult)
    if result.rowcount != 1:
        raise Conflict("다른 작업에서 수정되었습니다. 다시 불러오세요.")
    session.commit()


def delete_post(session: Session, raw_token: str, raw_id: str | int) -> None:
    user = require_user(session, raw_token)
    row = session.get(Post, parse_post_id(raw_id))
    if row is None or row.owner_id != user.id:
        raise AccessDenied("삭제할 수 없습니다.")
    session.delete(row)
    session.commit()


def weekly_counts(session: Session) -> list[dict[str, str | int]]:
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(days=6)
    day = func.date(col(Post.created_at))
    rows = session.exec(
        select(day, func.count(col(Post.id)))
        .where(col(Post.created_at) >= since)
        .group_by(day)
        .order_by(day)
    ).all()
    return [{"day": str(label), "count": count} for label, count in rows]

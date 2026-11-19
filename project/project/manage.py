"""관리 명령. 계정은 명시적으로 생성하며 import 때 DB를 변경하지 않는다."""

import argparse
import getpass
import sqlite3
import time
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlmodel import select

from .models import AiDaily, LoginSession, Post, RateWindow, User
from .services.auth import create_user
from .services.database import open_session
from .settings import get_settings


def backup_database(destination: Path) -> tuple[int, int]:
    database = make_url(get_settings().db_url).database
    if not database or database == ":memory:":
        raise ValueError("파일 SQLite DB가 필요합니다.")
    source = Path(database).resolve()
    target = destination.resolve()
    if source == target or target.exists():
        raise ValueError("백업은 존재하지 않는 다른 경로를 지정하세요.")
    if not source.is_file():
        raise ValueError("원본 DB가 없습니다.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as original, sqlite3.connect(target) as backup:
        original.backup(backup)
        integrity = backup.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise ValueError("백업 무결성 검사 실패")
        return (
            backup.execute("SELECT count(*) FROM post").fetchone()[0],
            backup.execute('SELECT count(*) FROM "user"').fetchone()[0],
        )


def main():
    parser = argparse.ArgumentParser(description="Reflex 게시판 관리")
    sub = parser.add_subparsers(dest="command", required=True)
    account = sub.add_parser("create-user")
    account.add_argument("username")
    account.add_argument("--admin", action="store_true")
    sub.add_parser("seed-demo")
    backup = sub.add_parser("backup")
    backup.add_argument("destination", type=Path)
    assign = sub.add_parser("assign-owner")
    assign.add_argument("post_id", type=int)
    assign.add_argument("username")
    sub.add_parser("cleanup")
    args = parser.parse_args()
    if args.command == "create-user":
        password = getpass.getpass("비밀번호 (12~128자): ")
        if password != getpass.getpass("비밀번호 확인: "):
            raise ValueError("비밀번호가 일치하지 않습니다.")
        user_id = create_user(args.username, password, admin=args.admin)
        print(f"사용자 생성 완료: {args.username} (id={user_id})")
    elif args.command == "seed-demo":
        if get_settings().production:
            raise ValueError("운영 환경에서는 데모 계정을 만들 수 없습니다.")
        for name, password in (("demo", "demo-password-123"), ("guest", "guest-password-123")):
            with open_session() as session:
                exists = session.exec(select(User).where(User.username == name)).first()
            if exists is None:
                create_user(name, password, admin=name == "demo")
        print("로컬 학습용 계정 demo, guest 준비 완료")
    elif args.command == "backup":
        posts, users = backup_database(args.destination)
        print(f"백업·무결성 확인 완료: posts={posts}, users={users}")
    elif args.command == "assign-owner":
        with open_session() as session:
            user = session.exec(select(User).where(User.username == args.username)).first()
            post = session.get(Post, args.post_id)
            if user is None or post is None or post.owner_id is not None:
                raise ValueError("사용자·글 존재 여부와 미지정 소유권을 확인하세요.")
            post.owner_id, post.author = user.id, user.username
            session.add(post)
            session.commit()
        print("명시한 게시글의 소유권 지정 완료")
    elif args.command == "cleanup":
        with open_session() as session:
            now = int(time.time())
            session.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
            session.execute(delete(RateWindow).where(RateWindow.window < now // 60 - 1440))
            session.execute(
                delete(AiDaily).where(
                    AiDaily.day < time.strftime("%Y-%m-%d", time.gmtime(now - 90 * 86400))
                )
            )
            session.commit()
        print("만료 세션과 오래된 요청 기록 정리 완료")


if __name__ == "__main__":
    main()

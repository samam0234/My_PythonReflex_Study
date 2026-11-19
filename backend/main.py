"""공통 게시판 API v1을 별도 SQLite 파일로 실행하는 FastAPI 학습 서버."""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints
from starlette.exceptions import HTTPException as StarletteHTTPException

TITLE = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
BODY = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
TOKEN = Annotated[str, Header(alias="Authorization")]
DEFAULT_DB = Path(__file__).with_name("board-v1.sqlite3")


def connect():
    db = sqlite3.connect(os.environ.get("BOARD_V1_DB") or DEFAULT_DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


@asynccontextmanager
async def lifespan(_app):
    with closing(connect()) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, email TEXT UNIQUE, nickname TEXT, digest TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires INTEGER
            );
            CREATE TABLE IF NOT EXISTS login_attempts (
                key TEXT PRIMARY KEY, minute INTEGER NOT NULL, attempts INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT, tags TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id), created TEXT, updated TEXT
            );
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT, created TEXT,
                user_id INTEGER REFERENCES users(id), post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE
            );
        """)
    yield


app = FastAPI(lifespan=lifespan, docs_url="/api-docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGIN", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    expose_headers=["X-Request-Id", "Location"],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id") or uuid4().hex
    length = request.headers.get("Content-Length", "")
    if length.isdecimal() and int(length) > 128_000:
        return error_response(
            request,
            413,
            {
                "code": "PAYLOAD_TOO_LARGE",
                "message": "요청 본문이 너무 큽니다.",
            },
        )
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    if response.headers.get("Content-Type") == "application/json":
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


def error(status, code, message):
    return HTTPException(status, {"code": code, "message": message})


def error_response(request, status, detail):
    rid = request.state.request_id
    return JSONResponse(
        {"error": {**detail, "requestId": rid}},
        status_code=status,
        headers={"X-Request-Id": rid},
        media_type="application/json; charset=utf-8",
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    detail = (
        exc.detail
        if isinstance(exc.detail, dict)
        else {
            "code": "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST",
            "message": str(exc.detail),
        }
    )
    return error_response(request, exc.status_code, detail)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    errors = exc.errors()
    if any(item["type"] == "json_invalid" or item["loc"][0] == "path" for item in errors):
        return error_response(
            request, 400, {"code": "BAD_REQUEST", "message": "요청 형식을 확인하세요."}
        )
    fields = {}
    for item in errors:
        fields.setdefault(str(item["loc"][-1]), []).append(item["msg"])
    return error_response(
        request,
        400,
        {
            "code": "VALIDATION_ERROR",
            "message": "입력값을 확인하세요.",
            "fields": fields,
        },
    )


@app.exception_handler(Exception)
async def internal_error(request, _exc):
    return error_response(
        request, 500, {"code": "INTERNAL", "message": "서버 오류가 발생했습니다."}
    )


class Credentials(BaseModel):
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        ),
    ]
    password: str = Field(min_length=12, max_length=128)


class Signup(Credentials):
    nickname: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


class PostInput(BaseModel):
    title: TITLE
    body: BODY
    tags: list[Tag] = Field(default_factory=list, max_length=10)


class PostPatch(BaseModel):
    title: TITLE | None = None
    body: BODY | None = None
    tags: list[Tag] | None = Field(default=None, max_length=10)


class CommentInput(BaseModel):
    body: BODY


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def token_hash(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def reserve_login(email: str):
    minute = int(time.time()) // 60
    with closing(connect()) as db, db:
        db.execute("DELETE FROM login_attempts WHERE minute < ?", (minute,))
        cursor = db.execute(
            "INSERT INTO login_attempts VALUES (?, ?, 1) ON CONFLICT(key) "
            "DO UPDATE SET attempts=attempts+1 WHERE attempts < 5",
            (token_hash(email.lower()), minute),
        )
        if cursor.rowcount != 1:
            raise error(429, "RATE_LIMITED", "잠시 후 다시 로그인하세요.")


def authorize(db, authorization):
    scheme, _, token = authorization.partition(" ")
    user = (
        db.execute(
            "SELECT users.* FROM users JOIN sessions ON users.id=sessions.user_id "
            "WHERE sessions.token_hash=? AND sessions.expires>?",
            (token_hash(token), int(time.time())),
        ).fetchone()
        if scheme.lower() == "bearer" and token
        else None
    )
    if user is None:
        raise error(401, "UNAUTHORIZED", "로그인이 필요합니다.")
    return user


def user_data(row):
    return {key: row[key] for key in ("id", "email", "nickname")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/signup", status_code=201)
def signup(data: Signup):
    salt = secrets.token_bytes(16)
    with closing(connect()) as db, db:
        try:
            cursor = db.execute(
                "INSERT INTO users(email,nickname,digest) VALUES (?,?,?)",
                (data.email.lower(), data.nickname, f"{salt.hex()}:{digest(data.password, salt)}"),
            )
        except sqlite3.IntegrityError:
            raise error(409, "EMAIL_TAKEN", "이미 등록된 이메일입니다.") from None
        return {
            "data": {"id": cursor.lastrowid, "email": data.email.lower(), "nickname": data.nickname}
        }


@app.post("/api/auth/login")
def login(data: Credentials):
    reserve_login(data.email)
    with closing(connect()) as db, db:
        user = db.execute("SELECT * FROM users WHERE email=?", (data.email.lower(),)).fetchone()
        salt, expected = user["digest"].split(":") if user else ("00" * 16, "0" * 128)
        valid = hmac.compare_digest(digest(data.password, bytes.fromhex(salt)), expected)
        if not user or not valid:
            raise error(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호를 확인하세요.")
        token = secrets.token_urlsafe(32)
        db.execute(
            "INSERT INTO sessions VALUES(?,?,?)",
            (token_hash(token), user["id"], int(time.time()) + 3600),
        )
        return {"data": {"user": user_data(user), "accessToken": token}}


@app.post("/api/auth/logout", status_code=204)
def logout(authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        authorize(db, authorization)
        db.execute(
            "DELETE FROM sessions WHERE token_hash=?",
            (token_hash(authorization.partition(" ")[2]),),
        )
    return Response(status_code=204)


@app.get("/api/auth/me")
def me(authorization: TOKEN = ""):
    with closing(connect()) as db:
        return {"data": user_data(authorize(db, authorization))}


POSTS = """SELECT posts.*, users.nickname,
    (SELECT count(*) FROM comments WHERE comments.post_id=posts.id) AS comment_count
    FROM posts JOIN users ON users.id=posts.user_id"""


def get_row(db, post_id):
    row = db.execute(POSTS + " WHERE posts.id=?", (post_id,)).fetchone()
    if row is None:
        raise error(404, "NOT_FOUND", "게시글을 찾지 못했습니다.")
    return row


def post_data(row, detail=True):
    result = {
        "id": row["id"],
        "title": row["title"],
        "createdAt": row["created"],
        "author": {"id": row["user_id"], "nickname": row["nickname"]},
        "commentCount": row["comment_count"],
    }
    if detail:
        result.update(body=row["body"], tags=json.loads(row["tags"]), updatedAt=row["updated"])
    return result


@app.get("/api/posts")
def list_posts(
    q: Annotated[str, Query(max_length=200)] = "",
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
    sort: Literal["createdAt", "-createdAt", "-commentCount"] = "-createdAt",
):
    limit = min(limit, 50)
    value = q.strip().casefold()
    where = " WHERE instr(fold(posts.title), ?) OR instr(fold(posts.body), ?)"
    order = {
        "createdAt": "posts.created ASC, posts.id ASC",
        "-createdAt": "posts.created DESC, posts.id DESC",
        "-commentCount": "comment_count DESC, posts.id DESC",
    }[sort]
    with closing(connect()) as db:
        db.create_function("fold", 1, str.casefold, deterministic=True)
        total = db.execute("SELECT count(*) FROM posts" + where, (value, value)).fetchone()[0]
        rows = db.execute(
            POSTS + where + f" ORDER BY {order} LIMIT ? OFFSET ?",
            (value, value, limit, (page - 1) * limit),
        ).fetchall()
    return {
        "data": [post_data(row, False) for row in rows],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit,
            "q": q,
        },
    }


@app.get("/api/posts/{post_id}")
def detail(post_id: int):
    with closing(connect()) as db:
        return {"data": post_data(get_row(db, post_id))}


@app.post("/api/posts", status_code=201)
def create(data: PostInput, response: Response, authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        user = authorize(db, authorization)
        timestamp = now()
        cursor = db.execute(
            "INSERT INTO posts(title,body,tags,user_id,created,updated) VALUES(?,?,?,?,?,?)",
            (data.title, data.body, json.dumps(data.tags), user["id"], timestamp, timestamp),
        )
        response.headers["Location"] = f"/api/posts/{cursor.lastrowid}"
        return {"data": post_data(get_row(db, cursor.lastrowid))}


def require_owner(user, row):
    if row["user_id"] != user["id"]:
        raise error(403, "FORBIDDEN", "작성자만 변경할 수 있습니다.")


@app.patch("/api/posts/{post_id}")
def update(post_id: int, data: PostPatch, authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        user = authorize(db, authorization)
        row = get_row(db, post_id)
        require_owner(user, row)
        if data.model_dump(exclude_unset=True, exclude_none=True):
            db.execute(
                "UPDATE posts SET title=?,body=?,tags=?,updated=? WHERE id=?",
                (
                    data.title or row["title"],
                    data.body or row["body"],
                    json.dumps(data.tags) if data.tags is not None else row["tags"],
                    now(),
                    post_id,
                ),
            )
        return {"data": post_data(get_row(db, post_id))}


@app.delete("/api/posts/{post_id}", status_code=204)
def delete(post_id: int, authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        require_owner(authorize(db, authorization), get_row(db, post_id))
        db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    return Response(status_code=204)


def comment_data(row):
    return {
        "id": row["id"],
        "body": row["body"],
        "createdAt": row["created"],
        "author": {"id": row["user_id"], "nickname": row["nickname"]},
    }


@app.get("/api/posts/{post_id}/comments")
def comments(post_id: int):
    with closing(connect()) as db:
        get_row(db, post_id)
        rows = db.execute(
            "SELECT comments.*, users.nickname FROM comments JOIN users "
            "ON users.id=comments.user_id WHERE post_id=? ORDER BY comments.id",
            (post_id,),
        ).fetchall()
        return {"data": [comment_data(row) for row in rows]}


@app.post("/api/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: int, data: CommentInput, authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        user = authorize(db, authorization)
        get_row(db, post_id)
        created = now()
        cursor = db.execute(
            "INSERT INTO comments(body,created,user_id,post_id) VALUES(?,?,?,?)",
            (data.body, created, user["id"], post_id),
        )
        return {
            "data": {
                "id": cursor.lastrowid,
                "body": data.body,
                "createdAt": created,
                "author": {"id": user["id"], "nickname": user["nickname"]},
            }
        }


@app.delete("/api/comments/{comment_id}", status_code=204)
def remove_comment(comment_id: int, authorization: TOKEN = ""):
    with closing(connect()) as db, db:
        user = authorize(db, authorization)
        row = db.execute("SELECT user_id FROM comments WHERE id=?", (comment_id,)).fetchone()
        if row is None:
            raise error(404, "NOT_FOUND", "댓글을 찾지 못했습니다.")
        require_owner(user, row)
        db.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    return Response(status_code=204)

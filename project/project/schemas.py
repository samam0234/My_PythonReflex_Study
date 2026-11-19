"""study5·14: 외부 입력을 엄격히 검사하고 화면 DTO를 별도로 정의."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Body = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
Username = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z][a-z0-9_]{2,31}$")
]


class PostInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    title: Title
    content: Body


class LoginInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    username: Username
    password: str = Field(min_length=12, max_length=128)


class PostSummary(BaseModel):
    id: int
    title: str
    author: str
    created_at: str


class PostDetail(PostSummary):
    content: str
    owner_id: int | None = None
    revision: int = 1


class PostPage(BaseModel):
    items: list[PostSummary]
    total: int
    page: int


def parse_post_id(raw: str | int) -> int:
    text = str(raw)
    if not text.isascii() or not text.isdecimal() or len(text) > 10:
        raise ValueError("올바른 글 번호가 아닙니다.")
    value = int(text)
    if not 1 <= value <= 2_147_483_647:
        raise ValueError("올바른 글 번호가 아닙니다.")
    return value

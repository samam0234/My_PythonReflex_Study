import pytest
from project.schemas import LoginInput, PostInput, parse_post_id
from pydantic import ValidationError


@pytest.mark.parametrize(
    "title,content,valid",
    [
        ("제목", "본문", True),
        (" ", "본문", False),
        ("가" * 50, "본문", True),
        ("가" * 51, "본문", False),
        ("제목", " ", False),
        ("제목", "가" * 5000, True),
        ("제목", "가" * 5001, False),
    ],
)
def test_post_boundaries(title, content, valid):
    if valid:
        assert PostInput(title=title, content=content).title == title.strip()
    else:
        with pytest.raises(ValidationError):
            PostInput(title=title, content=content)


@pytest.mark.parametrize(
    "data",
    [
        {"title": 42, "content": "본문"},
        {"title": "제목", "content": "본문", "owner_id": 1},
        {"title": "제목", "content": None},
    ],
)
def test_untrusted_input(data):
    with pytest.raises(ValidationError):
        PostInput.model_validate(data)


@pytest.mark.parametrize("raw", ["abc", "0", "-1", "1.5", "１", "9" * 200, "2147483648"])
def test_invalid_id(raw):
    with pytest.raises(ValueError):
        parse_post_id(raw)


def test_valid_id_and_trim():
    assert parse_post_id("123") == 123
    assert PostInput(title=" a ", content=" b ").model_dump() == {"title": "a", "content": "b"}


def test_password_constraints():
    with pytest.raises(ValidationError):
        LoginInput(username="demo", password="short")

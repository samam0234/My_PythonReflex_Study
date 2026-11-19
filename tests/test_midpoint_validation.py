import pytest
from midpoint.validation import validate_post


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
def test_validate_post(title: str, content: str, valid: bool):
    assert (validate_post(title, content) == "") is valid

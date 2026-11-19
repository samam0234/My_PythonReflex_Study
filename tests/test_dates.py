import pytest
from project.utils.dates import seoul_time


def test_utc_to_seoul():
    assert seoul_time("2026-11-19T00:00:00+00:00") == "2026-11-19 09:00"


@pytest.mark.parametrize("raw", ["2026-11-19T00:00:00", "invalid"])
def test_ambiguous_or_invalid_date(raw):
    with pytest.raises(ValueError):
        seoul_time(raw)

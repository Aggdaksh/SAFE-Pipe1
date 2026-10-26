import pytest

from safe_pipe.memory import parse_bytes, parse_gb


def test_parse_gb() -> None:
    assert parse_gb("1GB") == 1.0
    assert parse_gb("512MB") == 0.5


def test_bad_limit() -> None:
    with pytest.raises(ValueError):
        parse_bytes("lots")

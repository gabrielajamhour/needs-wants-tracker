import pytest

from app import normalize_category_name, safe_next


@pytest.mark.parametrize(
    "target, expected",
    [
        (None, "/"),
        ("", "/"),
        ("/", "/"),
        ("/?month=2026-11&q=mercado", "/?month=2026-11&q=mercado"),
        ("https://example.com", "/"),
        ("//example.com", "/"),
        ("/categories", "/"),
        ("/\\example.com", "/"),
        ("javascript:alert(1)", "/"),
    ],
)
def test_safe_next(app, target, expected):
    with app.test_request_context():
        assert safe_next(target) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  Dining   OUT ", "dining out"),
        ("Groceries", "groceries"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_category_name(raw, expected):
    assert normalize_category_name(raw) == expected

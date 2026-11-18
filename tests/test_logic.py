import pytest

from app import normalize_category_name, safe_next


@pytest.mark.parametrize(
    "target, expected",
    [
        (None, "/expenses"),
        ("", "/expenses"),
        ("/expenses", "/expenses"),
        ("/expenses?month=2026-11&q=mercado", "/expenses?month=2026-11&q=mercado"),
        ("/", "/expenses"),
        ("https://example.com", "/expenses"),
        ("//example.com", "/expenses"),
        ("/categories", "/expenses"),
        ("/\\example.com", "/expenses"),
        ("javascript:alert(1)", "/expenses"),
    ],
)
def test_safe_next(app, target, expected):
    """Verify that only safe local redirect destinations are accepted."""

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
    """Verify that category names are trimmed, lowercased and normalized."""
    assert normalize_category_name(raw) == expected

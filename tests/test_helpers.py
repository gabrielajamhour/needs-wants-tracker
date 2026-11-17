import pytest

from helpers import cents_to_eur, eur_to_cents, format_date, month_label, shift_month


@pytest.mark.parametrize(
    "cents, expected",
    [
        (0, "0,00 €"),
        (5, "0,05 €"),
        (1234, "12,34 €"),
        (123456, "1.234,56 €"),
        (-1234, "-12,34 €"),
    ],
)
def test_cents_to_eur(cents, expected):
    """Verify that integer cents are formatted as European euro amounts."""
    assert cents_to_eur(cents) == expected


@pytest.mark.parametrize("bad", ["12", 1.5, True, None])
def test_cents_to_eur_rejects_non_integers(bad):
    """Verify that non-integer inputs raise a TypeError."""
    with pytest.raises(TypeError):
        cents_to_eur(bad)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("12,34", 1234),
        ("1.234,56", 123456),
        ("12", 1200),
        ("0,5", 50),
        (" 12,34 € ", 1234),
        ("1.234", 123400),  # valid European thousands separator
        ("1,005", 101),  # half-up rounding: 100.5 cents -> 101
    ],
)
def test_eur_to_cents_valid(text, expected):
    """Verify that valid European euro amounts are converted to integer cents."""
    assert eur_to_cents(text) == expected


@pytest.mark.parametrize(
    "bad",
    ["1,234.56", "12.5", "abc", "", ",50", "12,", "1.23", "1..234,56", None, 12],
)
def test_eur_to_cents_invalid(bad):
    """Verify that invalid euro amount strings return None."""
    assert eur_to_cents(bad) is None


@pytest.mark.parametrize("cents", [0, 1, 99, 100, 123456])
def test_round_trip(cents):
    """Verify that converting cents to euros and back preserves the original amount."""
    assert eur_to_cents(cents_to_eur(cents)) == cents


@pytest.mark.parametrize(
    "month, delta, expected",
    [
        ("2026-11", 1, "2026-12"),
        ("2026-12", 1, "2027-01"),
        ("2026-01", -1, "2025-12"),
        ("2026-11", 0, "2026-11"),
        ("2026-11", 14, "2028-01"),
        ("2026-03", -15, "2024-12"),
    ],
)
def test_shift_month(month, delta, expected):
    """Verify that months are shifted forward and backward across year boundaries."""
    assert shift_month(month, delta) == expected


@pytest.mark.parametrize(
    "month, label",
    [("2026-11", "November 2026"), ("2027-01", "January 2027"), ("2026-03", "March 2026")],
)
def test_month_label(month, label):
    """Verify that YYYY-MM months are formatted as month labels."""
    assert month_label(month) == label


@pytest.mark.parametrize(
    "iso, label",
    [("2026-11-27", "27/11/2026"), ("2026-01-05", "05/01/2026"), ("2027-12-31", "31/12/2027")],
)
def test_format_date(iso, label):
    assert format_date(iso) == label

import pytest

from helpers import cents_to_eur, eur_to_cents


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
    assert cents_to_eur(cents) == expected


@pytest.mark.parametrize("bad", ["12", 1.5, True, None])
def test_cents_to_eur_rejects_non_integers(bad):
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
    assert eur_to_cents(text) == expected


@pytest.mark.parametrize(
    "bad",
    ["1,234.56", "12.5", "abc", "", ",50", "12,", "1.23", "1..234,56", None, 12],
)
def test_eur_to_cents_invalid(bad):
    assert eur_to_cents(bad) is None


@pytest.mark.parametrize("cents", [0, 1, 99, 100, 123456])
def test_round_trip(cents):
    assert eur_to_cents(cents_to_eur(cents)) == cents

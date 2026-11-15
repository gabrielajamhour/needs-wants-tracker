import pytest

from budget import build_cards


def card(cards, label):
    return next(c for c in cards if c["label"] == label)


def test_limits_follow_50_30_20():
    assert [c["limit"] for c in build_cards(100000, {})] == [50000, 30000, 20000]


def test_no_income_means_no_limits():
    cards = build_cards(None, {"needs": 1000})
    assert all(c["limit"] is None and c["used"] is None and not c["over"] for c in cards)


def test_zero_income_has_no_bars():
    cards = build_cards(0, {"needs": 100})
    assert all(c["used"] is None and not c["over"] for c in cards)


def test_cap_exactly_reached_is_not_over():
    needs = card(build_cards(100000, {"needs": 50000}), "Needs")
    assert needs["used"] == 100 and not needs["over"]


def test_cap_exceeded_is_flagged():
    assert card(build_cards(100000, {"needs": 50001}), "Needs")["over"]


def test_savings_above_goal_is_never_over():
    savings = card(build_cards(100000, {"savings": 99999}), "Savings")
    assert not savings["over"]


@pytest.mark.parametrize("income", [0, 1, 99, 100, 12345])
def test_limits_never_exceed_income(income):
    assert sum(c["limit"] for c in build_cards(income, {})) <= income
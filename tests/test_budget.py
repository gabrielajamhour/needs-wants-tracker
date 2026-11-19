import pytest

from budget import build_cards, build_income_bar


def card(cards, label):
    """Return the budget card matching the given label."""
    return next(c for c in cards if c["label"] == label)


def test_limits_follow_50_30_20():
    """Verify that income is split according to the 50/30/20 rule."""
    assert [c["limit"] for c in build_cards(100000, {})] == [50000, 30000, 20000]


def test_no_income_means_no_limits():
    """Verify that missing income results in undefined budget limits."""
    cards = build_cards(None, {"needs": 1000})
    assert all(c["limit"] is None and c["used"] is None and not c["over"] for c in cards)


def test_zero_income_has_no_bars():
    """Verify that zero income produces no usage bars or over-cap flags."""
    cards = build_cards(0, {"needs": 100})
    assert all(c["used"] is None and not c["over"] for c in cards)


def test_cap_exactly_reached_is_not_over():
    """Verify that reaching a spending cap does not count as exceeding it."""
    needs = card(build_cards(100000, {"needs": 50000}), "Needs")
    assert needs["used"] == 100 and not needs["over"]


def test_cap_exceeded_is_flagged():
    """Verify that exceeding a spending cap sets the over-cap flag."""
    assert card(build_cards(100000, {"needs": 50001}), "Needs")["over"]


def test_savings_above_goal_is_never_over():
    """Verify that exceeding the savings goal does not trigger an over-cap flag."""
    savings = card(build_cards(100000, {"savings": 99999}), "Savings")
    assert not savings["over"]


@pytest.mark.parametrize("income", [0, 1, 99, 100, 12345])
def test_limits_never_exceed_income(income):
    """Verify that the total budget limits never exceed the available income."""
    assert sum(c["limit"] for c in build_cards(income, {})) <= income


def bar_part(bar, kind):
    """Return the income bar part of the given kind."""
    return next(p for p in bar if p["kind"] == kind)


def test_income_bar_needs_an_income():
    """Verify that there is no income bar without income or with zero income."""
    assert build_income_bar(None, {"needs": 100}) is None
    assert build_income_bar(0, {"needs": 100}) is None


def test_income_bar_widths_fill_the_whole_bar():
    """Verify that the parts of the income bar add up to the whole bar."""
    bar = build_income_bar(100000, {"needs": 50000, "wants": 20000, "savings": 10000})
    assert sum(p["width"] for p in bar) == pytest.approx(100)
    assert bar_part(bar, "left")["pct"] == 20


def test_income_bar_percentages_are_of_the_income():
    """Verify that each percentage is calculated over the income."""
    assert bar_part(build_income_bar(100000, {"needs": 49000}), "needs")["pct"] == 49


def test_income_bar_without_spending_is_all_left():
    """Verify that without spending the whole bar is what is left."""
    assert bar_part(build_income_bar(100000, {}), "left")["width"] == 100


def test_income_bar_over_the_income_has_nothing_left():
    """Verify that spending above the income leaves nothing and keeps the bar full."""
    bar = build_income_bar(100000, {"needs": 80000, "wants": 40000})
    assert bar_part(bar, "left")["width"] == 0
    assert sum(p["width"] for p in bar) == pytest.approx(100)
    assert bar_part(bar, "needs")["pct"] == 80

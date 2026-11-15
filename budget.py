"""Budget rules: split income into needs, wants and savings and compare with spending."""

# (type, label, percent, is_cap): needs and wants are caps, savings is a goal
SPLIT = (
    ("needs", "Needs", 50, True),
    ("wants", "Wants", 30, True),
    ("savings", "Savings", 20, False),
)


def build_cards(income_cents, spent_by_type):
    """Return one dict per budget part with limit, spent, percent used and over-cap flag."""
    cards = []
    for kind, label, pct, is_cap in SPLIT:
        limit = income_cents * pct // 100 if income_cents is not None else None
        spent = spent_by_type.get(kind, 0)
        cards.append(
            {
                "label": label,
                "pct": pct,
                "limit": limit,
                "spent": spent,
                "is_cap": is_cap,
                "used": round(spent * 100 / limit) if limit else None,
                "over": is_cap and bool(limit) and spent > limit,
            }
        )
    return cards
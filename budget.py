"""Budget rules: split income into needs, wants and savings and compare with spending."""

# (type, label, percent, is_cap): needs and wants are caps, savings is a goal
SPLIT = (
    ("needs", "Needs", 50, True),
    ("wants", "Wants", 30, True),
    ("savings", "Savings", 20, False),
)


def build_cards(income_cents, spent_by_type):
    """Build budget cards with spending limits, usage and over-cap status."""
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


def build_income_bar(income_cents, spent_by_type):
    """Split the income bar into what each type spent and what is left."""
    if not income_cents:
        return None

    total = sum(spent_by_type.get(kind, 0) for kind, *_ in SPLIT)
    left = max(income_cents - total, 0)
    # Over the income, the bar is as wide as the spending, so it stays full
    scale = max(income_cents, total)

    parts = [(kind, label, spent_by_type.get(kind, 0)) for kind, label, *_ in SPLIT]
    parts.append(("left", "Left", left))

    return [
        {
            "kind": kind,
            "label": label,
            "width": amount * 100 / scale,
            "pct": round(amount * 100 / income_cents),
        }
        for kind, label, amount in parts
    ]

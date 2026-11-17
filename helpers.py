# Convert monetary values ​​between euros and cents to ensure an user-friendly environment

import re
from decimal import (  # Class used for working with decimal numbers with precision
    ROUND_HALF_UP,
    Decimal,
    InvalidOperation,
)

import emoji

DEFAULT_EMOJI = "🏷️"

MONTH_NAMES = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def emoji_error(text):
    """Return an error message if text is not exactly one emoji, otherwise None."""
    found = emoji.emoji_list(text)
    if not found:
        return "That is not an emoji."
    if len(found) > 1:
        return "Choose only one emoji."
    if found[0]["match_start"] != 0 or found[0]["match_end"] != len(text):
        return "Use only the emoji, without other characters."
    return None


def shift_month(month, delta):
    """Move a 'YYYY-MM' month by delta months: shift_month('2026-12', 1) -> '2027-01'."""
    year, number = map(int, month.split("-"))
    index = year * 12 + (number - 1) + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_label(month):
    """'2026-11' -> 'November 2026'."""
    year, number = month.split("-")
    return f"{MONTH_NAMES[int(number) - 1].capitalize()} {year}"


def cents_to_eur(cents: int) -> str:  # Receives an integer and returns a string
    """Convert an integer amount in cents to a formatted euro string."""
    # 1234 -> '12,34 €'; 123456 -> '1.234,56 €'

    if not isinstance(cents, int) or isinstance(cents, bool):
        raise TypeError(f"cents must be int, got {type(cents).__name__}")

    euros, rest = divmod(abs(cents), 100)  # Returns (quotient, remainder)
    # e.g. divmod(1234, 100) returns (12, 34)
    sign = "-" if cents < 0 else ""

    return f"{sign}{euros:,}".replace(",", ".") + f",{rest:02d} €"  # European format 1.234,56 €


def eur_to_cents(text: str) -> int | None:
    """Convert a European-formatted euro amount to integer cents."""
    # '12,34' -> 1234; '1.234,56' -> 123456

    if not isinstance(text, str):
        return None

    text = text.replace("€", "").replace(" ", "")

    # Validate European format to Decimal-compatible format
    pattern = r"-?(\d+|\d{1,3}(\.\d{3})+)(,\d+)?"

    if not re.fullmatch(pattern, text):
        return None

    # Convert European format to Decimal-compatible format
    text = text.replace(".", "").replace(",", ".")  # Converts to the format expected by Decimal

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None

    if not value.is_finite():
        return None

    return int(
        (value * 100).quantize(  # To ensure that values ​​are stored with exactly
            Decimal("1"),
            rounding=ROUND_HALF_UP,  # 2 decimal places for cents
        )
    )


def format_date(iso_date):
    """'2026-11-27' -> '27/11/2026'."""
    year, month, day = iso_date.split("-")
    return f"{day}/{month}/{year}"

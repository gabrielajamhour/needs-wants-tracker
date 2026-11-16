# Convert monetary values ​​between euros and cents to ensure an user-friendly environment

import re
import unicodedata
from decimal import (  # Class used for working with decimal numbers with precision
    ROUND_HALF_UP,
    Decimal,
    InvalidOperation,
)

DEFAULT_EMOJI = "🏷️"
MAX_EMOJI_LENGTH = 12
_ZERO_WIDTH_JOINER = "\u200d"
_EMOJI_CATEGORIES = {"So", "Sk", "Mn", "Me"}


def is_valid_emoji(text):
    """Check for emoji-like characters, including joined sequences, flags, and skin tones."""
    if not text or len(text) > MAX_EMOJI_LENGTH:
        return False
    if not all(ord(ch) > 127 for ch in text):
        return False
    categories = {unicodedata.category(ch) for ch in text if ch != _ZERO_WIDTH_JOINER}
    return categories <= _EMOJI_CATEGORIES and "So" in categories


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

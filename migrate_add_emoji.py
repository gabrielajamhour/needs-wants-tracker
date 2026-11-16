"""One-off migration: add the emoji column and fill in the default emojis."""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "instance" / "tracker.db"
DEFAULT_EMOJI = "🏷️"
EMOJIS = {
    "housing": "🏠",
    "groceries": "🛒",
    "utilities": "💡",
    "transport": "🚌",
    "health": "💊",
    "insurance": "🛡️",
    "education": "🎓",
    "other needs": "📦",
    "dining out": "🍽️",
    "entertainment": "🎬",
    "shopping": "🛍️",
    "travel": "✈️",
    "subscriptions": "🔁",
    "gifts": "🎁",
    "personal care": "🧴",
    "other wants": "✨",
    "emergency fund": "🛟",
    "investments": "📈",
    "other savings": "🐷",
}


def migrate(path=DEFAULT_DB):
    """Add the emoji column and update default category emojis."""
    conn = sqlite3.connect(path)
    try:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(categories)")]
        if "emoji" not in columns:
            conn.execute(
                f"ALTER TABLE categories ADD COLUMN emoji TEXT NOT NULL DEFAULT '{DEFAULT_EMOJI}'"
            )
        for name, emoji in EMOJIS.items():
            # only replace the default, so emojis chosen by hand are kept
            conn.execute(
                "UPDATE categories SET emoji = ? WHERE name = ? AND emoji = ?",
                (emoji, name, DEFAULT_EMOJI),
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate(*sys.argv[1:2])

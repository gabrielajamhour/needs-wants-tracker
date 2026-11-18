import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_PATH = ROOT / "instance" / "demo.db"

MONTHS = ["2026-08", "2026-09", "2026-10"]
INCOME_CENTS = 180000

# (day, name, category, amount in cents)
BASE = [
    (1, "Rent", "housing", 52000),
    (2, "Electricity", "utilities", 4800),
    (3, "Internet", "utilities", 3000),
    (4, "Metro pass", "transport", 3500),
    (5, "Supermarket", "groceries", 6200),
    (12, "Supermarket", "groceries", 5400),
    (19, "Supermarket", "groceries", 7100),
    (26, "Supermarket", "groceries", 4900),
    (8, "Pharmacy", "health", 1850),
    (6, "Pizza night", "dining out", 2800),
    (14, "Cinema", "entertainment", 1100),
    (15, "Streaming", "subscriptions", 1299),
    (21, "Dinner with friends", "dining out", 4200),
    (22, "New shoes", "shopping", 5900),
    (27, "Monthly transfer", "emergency fund", 20000),
]

EXTRA = {
    "2026-09": [
        (11, "Weekend trip", "travel", 18000),
        (24, "Birthday gift", "gifts", 3500),
    ],
    "2026-10": [
        (9, "Concert tickets", "entertainment", 9500),
        (10, "Winter jacket", "shopping", 12000),
        (16, "Weekend trip", "travel", 24000),
    ],
}


def create_demo_db(path=DEFAULT_PATH):
    """Create a fresh demo database with three months of sample data."""
    path = Path(path)
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    try:
        conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        conn.executescript((ROOT / "seed.sql").read_text(encoding="utf-8"))
        ids = {
            name.casefold(): cid for cid, name in conn.execute("SELECT id, name FROM categories")
        }

        for month in MONTHS:
            conn.execute(
                "INSERT INTO budgets (month, income_cents) VALUES (?, ?)",
                (month, INCOME_CENTS),
            )
            for day, name, category, cents in BASE + EXTRA.get(month, []):
                conn.execute(
                    "INSERT INTO expenses (name, amount_cents, date, category_id) "
                    "VALUES (?, ?, ?, ?)",
                    (name, cents, f"{month}-{day:02d}", ids[category]),
                )
        conn.commit()
    finally:
        conn.close()
    return path


if __name__ == "__main__":
    print("Demo database created at", create_demo_db(*sys.argv[1:2]))

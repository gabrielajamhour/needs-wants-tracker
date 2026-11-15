import sqlite3

from seed_demo import MONTHS, create_demo_db


def test_demo_db_is_consistent(tmp_path):
    path = create_demo_db(tmp_path / "demo.db")
    conn = sqlite3.connect(path)
    try:
        months = {r[0] for r in conn.execute("SELECT DISTINCT substr(date, 1, 7) FROM expenses")}
        assert months == set(MONTHS)
        assert conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == len(MONTHS)
        assert conn.execute("SELECT MIN(amount_cents) FROM expenses").fetchone()[0] > 0
    finally:
        conn.close()


def test_demo_summary_flags_only_november(app, client, tmp_path):
    app.config["DATABASE"] = create_demo_db(tmp_path / "demo.db")
    assert "Above the limit" in client.get("/summary?month=2026-11").data.decode()
    assert "Above the limit" not in client.get("/summary?month=2026-09").data.decode()
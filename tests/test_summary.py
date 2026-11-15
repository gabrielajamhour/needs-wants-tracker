def set_income(client, month, income):
    return client.post("/summary", data={"month": month, "income": income})


def test_summary_without_income_prompts_for_it(client):
    response = client.get("/summary?month=2026-11")
    assert response.status_code == 200
    assert b"Set this month's income" in response.data


def test_invalid_month_returns_400(client):
    assert client.get("/summary?month=abc").status_code == 400


def test_income_is_saved_and_updated_not_duplicated(client, db_rows):
    set_income(client, "2026-11", "1.000,00")
    set_income(client, "2026-11", "2.000,00")
    rows = db_rows("SELECT income_cents FROM budgets WHERE month = '2026-11'")
    assert [r["income_cents"] for r in rows] == [200000]


def test_invalid_income_is_rejected(client, db_rows):
    response = set_income(client, "2026-11", "1,234.56")
    assert response.status_code == 302
    assert db_rows("SELECT COUNT(*) AS n FROM budgets")[0]["n"] == 0
    followed = client.post(
        "/summary", data={"month": "2026-11", "income": "abc"}, follow_redirects=True
    )
    assert b"Enter a valid income" in followed.data


def test_limits_remaining_and_over_cap(client, add_expense):
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Rent", amount="100,00", date="2026-11-02", category="groceries")
    add_expense(name="Dinner", amount="350,00", date="2026-11-03", category="dining out")
    # other month: must not count
    add_expense(name="Old", amount="77,00", date="2026-10-20", category="groceries")

    page = client.get("/summary?month=2026-11").data.decode()
    assert "500,00 €" in page  # needs cap (50%)
    assert "300,00 €" in page  # wants cap (30%)
    assert "200,00 €" in page  # savings goal (20%)
    assert "Above the limit in 50,00 €" in page
    assert "550,00 €" in page  # remaining: 1000 - 100 - 350


def test_savings_above_goal_is_not_flagged(client, add_expense):
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Transfer", amount="300,00", date="2026-11-05", category="emergency fund")
    page = client.get("/summary?month=2026-11").data.decode()
    assert "Above the limit" not in page

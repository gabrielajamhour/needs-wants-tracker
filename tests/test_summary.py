def set_income(client, month, income):
    """Submit the income form for the specified month."""
    return client.post("/", data={"month": month, "income": income})


def test_summary_without_income_prompts_for_it(client):
    """Verify that the summary prompts users to enter missing monthly income."""
    response = client.get("/?month=2026-11")
    assert response.status_code == 200
    assert b"Set this month's income" in response.data


def test_invalid_month_returns_400(client):
    """Verify that invalid month values return a 400 response."""
    assert client.get("/?month=abc").status_code == 400


def test_income_is_saved_and_updated_not_duplicated(client, db_rows):
    """Verify that monthly income is updated instead of duplicated."""
    set_income(client, "2026-11", "1.000,00")
    set_income(client, "2026-11", "2.000,00")
    rows = db_rows("SELECT income_cents FROM budgets WHERE month = '2026-11'")
    assert [r["income_cents"] for r in rows] == [200000]


def test_invalid_income_is_rejected(client, db_rows):
    """Verify that invalid income values are not saved."""
    response = set_income(client, "2026-11", "1,234.56")
    assert response.status_code == 302
    assert db_rows("SELECT COUNT(*) AS n FROM budgets")[0]["n"] == 0
    followed = client.post("/", data={"month": "2026-11", "income": "abc"}, follow_redirects=True)
    assert b"Enter a valid income" in followed.data


def test_limits_remaining_and_over_cap(client, add_expense):
    """Verify that budget limits, remaining income and overspending are calculated correctly."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Rent", amount="100,00", date="2026-11-02", category="groceries")
    add_expense(name="Dinner", amount="350,00", date="2026-11-03", category="dining out")
    # other month: must not count
    add_expense(name="Old", amount="77,00", date="2026-10-20", category="groceries")

    page = client.get("/?month=2026-11").data.decode()
    assert "500,00 €" in page  # needs cap (50%)
    assert "300,00 €" in page  # wants cap (30%)
    assert "200,00 €" in page  # savings goal (20%)
    assert "Above the limit in 50,00 €" in page
    assert "550,00 €" in page  # remaining: 1000 - 100 - 350


def test_savings_above_goal_is_not_flagged(client, add_expense):
    """Verify that exceeding the savings goal does not trigger an overspending warning."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Transfer", amount="300,00", date="2026-11-05", category="emergency fund")
    page = client.get("/?month=2026-11").data.decode()
    assert "Above the limit" not in page


def test_income_is_shown_as_text_with_an_edit_button(client):
    """Check that a saved income shows as text and the form stays hidden."""
    set_income(client, "2026-11", "1.800,00")
    page = client.get("/?month=2026-11").data.decode()
    assert "1.800,00 €" in page
    assert "Edit income" in page and "edit=income" in page
    assert 'name="income"' not in page


def test_edit_income_opens_the_form_with_the_saved_value(client):
    """Check that the edit link opens the form filled with the saved income."""
    set_income(client, "2026-11", "1.800,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'name="income"' in page and 'value="1.800,00"' in page
    assert "Save income" in page and "Cancel" in page
    assert "Edit income" not in page


def test_without_income_the_summary_offers_to_add_it(client):
    """Check that a month without income shows the invitation and the Add income button."""
    page = client.get("/?month=2026-11").data.decode()
    assert "Set this month's income to see your limits." in page
    assert "Add income" in page
    assert 'name="income"' not in page


def test_invalid_income_reopens_the_form(client):
    """Check that an invalid income redirects back to the open form."""
    response = client.post("/", data={"month": "2026-11", "income": "abc"})
    assert response.status_code == 302
    assert "edit=income" in response.headers["Location"]


def test_valid_income_returns_to_the_closed_form(client):
    """Check that saving a valid income redirects back without the open form."""
    response = set_income(client, "2026-11", "1.800,00")
    assert response.status_code == 302
    assert "edit" not in response.headers["Location"]


def test_add_income_button_sits_in_the_toolbar(client):
    """Check that without income the Add income button sits in the toolbar next to the month."""
    page = client.get("/?month=2026-11").data.decode()
    toolbar = page.split('class="summary-toolbar"')[1].split('<div class="cards">')[0]
    assert "Add income" in toolbar
    assert "Set this month's income to see your limits." not in toolbar.split("Add income")[0]
    assert "0,00 €" in toolbar

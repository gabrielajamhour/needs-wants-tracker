def set_income(client, month, income):
    """Submit the income form for the specified month."""
    return client.post("/", data={"month": month, "income": income})


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
    assert response.status_code == 400
    assert db_rows("SELECT COUNT(*) AS n FROM budgets")[0]["n"] == 0
    assert b"Enter a valid income" in response.data


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
    assert "50,00 € over the limit" in page
    assert "550,00 €" in page  # remaining: 1000 - 100 - 350


def test_savings_above_goal_is_not_flagged(client, add_expense):
    """Verify that exceeding the savings goal does not trigger an overspending warning."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Transfer", amount="300,00", date="2026-11-05", category="emergency fund")
    page = client.get("/?month=2026-11").data.decode()
    assert "over the limit" not in page
    assert "Goal reached" in page


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


def test_invalid_income_reopens_the_form_with_the_typed_value(client):
    """Check that an invalid income shows the open form, the typed value and the error."""
    response = client.post("/", data={"month": "2026-11", "income": "abc"})
    page = response.data.decode()
    assert response.status_code == 400
    assert 'name="income"' in page and 'value="abc"' in page
    assert 'id="income-error"' in page and "Enter a valid income" in page


def test_valid_income_returns_to_the_closed_form(client):
    """Check that saving a valid income redirects back without the open form."""
    response = set_income(client, "2026-11", "1.800,00")
    assert response.status_code == 302
    assert "edit" not in response.headers["Location"]


def test_add_income_button_sits_in_the_toolbar(client):
    """Check that without income the Add income button sits in the toolbar next to the month."""
    page = client.get("/?month=2026-11").data.decode()
    toolbar = page.split('class="summary-toolbar"')[1].split('<div class="buckets">')[0]
    assert "Add income" in toolbar
    assert toolbar.index("Add income") < toolbar.index(
        "Set this month's income to see your limits."
    )
    assert "0,00 €" in toolbar


def test_income_form_starts_from_the_previous_month(client):
    """Verify that the income form of a new month starts from the previous income."""
    set_income(client, "2026-10", "1.800,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'value="1.800,00"' in page
    assert "Filled in from October 2026" in page


def test_income_form_skips_months_without_income(client):
    """Verify that the suggestion comes from the latest earlier month that has income."""
    set_income(client, "2026-08", "1.500,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'value="1.500,00"' in page
    assert "Filled in from August 2026" in page


def test_income_form_ignores_later_months(client):
    """Verify that the suggestion never comes from a later month."""
    set_income(client, "2026-12", "2.000,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'name="income"' in page
    assert 'value="2.000,00"' not in page and "Filled in from" not in page


def test_saved_income_wins_over_the_suggestion(client):
    """Verify that a month with its own income does not use the suggestion."""
    set_income(client, "2026-10", "1.800,00")
    set_income(client, "2026-11", "1.900,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'value="1.900,00"' in page and "Filled in from" not in page


def test_suggestion_is_not_saved_until_the_user_saves(client, db_rows):
    """Verify that opening the form does not save the suggested income."""
    set_income(client, "2026-10", "1.800,00")
    client.get("/?month=2026-11&edit=income")
    assert db_rows("SELECT * FROM budgets WHERE month = '2026-11'") == []


def test_closed_income_line_ignores_the_suggestion(client):
    """Verify that the income line still shows 0,00 € until the income is saved."""
    set_income(client, "2026-10", "1.800,00")
    page = client.get("/?month=2026-11").data.decode()
    assert "Add income" in page and "1.800,00" not in page


def test_income_suggestion_hint_comes_right_after_the_form(client):
    """Verify that the suggestion hint sits in the toolbar, after the income form."""
    set_income(client, "2026-10", "1.800,00")
    page = client.get("/?month=2026-11&edit=income").data.decode()
    form_end = page.index("</form>", page.index('class="control-form income-form"'))
    hint = page.index("Filled in from October 2026")
    assert form_end < hint < page.index("<section")


def test_hero_shows_what_is_left_to_spend(client, add_expense):
    """Check that the hero shows the amount left and how much of the income was used."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(amount="100,00", date="2026-11-02")
    page = client.get("/?month=2026-11").data.decode()
    assert "Left to spend" in page and "900,00 €" in page
    assert "100,00 € of 1.000,00 € used this month" in page


def test_hero_is_hidden_without_income(client):
    """Check that without income there is no hero and no income bar."""
    page = client.get("/?month=2026-11").data.decode()
    assert "Left to spend" not in page and "income-bar" not in page


def test_hero_warns_when_spending_passes_the_income(client, add_expense):
    """Check that spending above the income shows a negative number and the warning line."""
    set_income(client, "2026-11", "100,00")
    add_expense(amount="130,00", date="2026-11-02")
    page = client.get("/?month=2026-11").data.decode()
    assert "-30,00 €" in page
    assert "30,00 € over this month's income" in page


def test_zero_income_has_a_hero_but_no_income_bar(client, add_expense):
    """Check that zero income shows the hero without the income bar."""
    set_income(client, "2026-11", "0")
    add_expense(amount="3,58", date="2026-11-11")
    page = client.get("/?month=2026-11").data.decode()
    assert "Left to spend" in page and "income-bar" not in page


def test_income_bar_describes_the_split_for_screen_readers(client, add_expense):
    """Check that the income bar has the percentages as its accessible label."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(amount="100,00", date="2026-11-02", category="groceries")
    page = client.get("/?month=2026-11").data.decode()
    assert 'role="img" aria-label="Needs, Wants, Savings, Left"' in page


def test_income_bar_segments_get_their_width_from_a_css_variable(client, add_expense):
    """Check that each segment of the income bar carries its width as a CSS variable."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(amount="100,00", date="2026-11-02", category="groceries")
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="segment segment-needs" style="--w: 10.00"' in page
    assert 'class="segment segment-left" style="--w: 90.00"' in page


def test_buckets_show_the_share_the_limit_and_what_is_left(client, add_expense):
    """Check that each bucket column shows its share, limit and status line."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(name="Rent", amount="100,00", date="2026-11-02", category="groceries")
    page = client.get("/?month=2026-11").data.decode()
    assert "50% of income" in page and "30% of income" in page and "20% of income" in page
    assert "Limit 500,00 €" in page and "Goal 200,00 €" in page
    assert "400,00 € left" in page
    assert "200,00 € to reach the goal" in page


def test_buckets_without_income_have_no_limit_bar_or_status(client, add_expense):
    """Check that without income the buckets only show what was spent."""
    add_expense(amount="3,58", date="2026-11-11")
    page = client.get("/?month=2026-11").data.decode()
    assert "3,58 €" in page
    assert "bucket-bar" not in page and "Limit" not in page and "% of income" not in page


def test_over_limit_bucket_has_a_full_striped_bar(client, add_expense):
    """Check that a bucket over its limit shows a full striped bar and the warning line."""
    set_income(client, "2026-11", "1.000,00")
    add_expense(amount="350,00", date="2026-11-03", category="dining out")
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="bucket-fill is-over" style="--bar-width: 100%"' in page
    assert "50,00 € over the limit" in page

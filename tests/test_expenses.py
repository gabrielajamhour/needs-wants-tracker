import pytest


def count_expenses(db_rows):
    """Return the total number of expenses in the database."""
    return db_rows("SELECT COUNT(*) AS n FROM expenses")[0]["n"]


def first_expense_id(db_rows):
    """Return the ID of the first expense in the database."""
    return db_rows("SELECT id FROM expenses")[0]["id"]


def test_add_expense_stores_cents(add_expense, db_rows):
    """Verify that expense amounts are stored as integer cents."""
    response = add_expense(amount="3,58")
    assert response.status_code == 302
    rows = db_rows("SELECT name, amount_cents, date FROM expenses")
    assert [tuple(r) for r in rows] == [("Mercado", 358, "2026-11-11")]


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "   "},
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "abc"},
        {"amount": "1,234.56"},
        {"date": "2026-13-45"},
        {"date": ""},
    ],
)
def test_add_expense_rejects_invalid_input(add_expense, db_rows, overrides):
    """Verify that invalid expense form data is rejected."""
    response = add_expense(**overrides)
    assert response.status_code == 400
    assert count_expenses(db_rows) == 0


def test_add_expense_rejects_unknown_category(client, db_rows):
    """Verify that expenses cannot be created with an unknown category."""
    response = client.post(
        "/expenses/new",
        data={"name": "x", "amount": "1,00", "date": "2026-11-11", "category_id": "9999"},
    )
    assert response.status_code == 400
    assert count_expenses(db_rows) == 0


def test_invalid_form_shows_error_message(add_expense):
    """Verify that invalid expense forms display an error message."""
    response = add_expense(name="")
    assert b"Enter a name." in response.data


def test_edit_form_is_prefilled(client, add_expense, db_rows):
    """Verify that the edit form is prefilled with the expense data."""
    add_expense(amount="3,58")
    response = client.get(f"/expenses/{first_expense_id(db_rows)}/edit")
    assert b'value="3,58"' in response.data


def test_edit_expense(client, add_expense, category_id, db_rows):
    """Verify that an existing expense can be updated."""
    add_expense()
    expense_id = first_expense_id(db_rows)
    new_category = category_id("dining out")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"name": "Lidl", "amount": "10,00", "date": "2026-11-12", "category_id": new_category},
    )
    assert response.status_code == 302
    row = db_rows("SELECT name, amount_cents, date, category_id FROM expenses")[0]
    assert tuple(row) == ("Lidl", 1000, "2026-11-12", new_category)


def test_edit_and_delete_follow_safe_next(client, add_expense, category_id, db_rows):
    """Verify that edit and delete redirects use only safe destinations."""
    add_expense()
    expense_id = first_expense_id(db_rows)
    data = {
        "name": "Lidl",
        "amount": "10,00",
        "date": "2026-11-12",
        "category_id": category_id("groceries"),
    }

    good = client.post(
        f"/expenses/{expense_id}/edit", data=data, query_string={"next": "/?month=2026-11"}
    )
    assert good.headers["Location"] == "/?month=2026-11"

    bad = client.post(
        f"/expenses/{expense_id}/edit", data=data, query_string={"next": "https://example.com"}
    )
    assert bad.headers["Location"] == "/"

    deleted = client.post(f"/expenses/{expense_id}/delete", query_string={"next": "/?q=lidl"})
    assert deleted.headers["Location"] == "/?q=lidl"


def test_delete_expense(client, add_expense, db_rows):
    """Verify that an expense can be deleted."""
    add_expense()
    response = client.post(f"/expenses/{first_expense_id(db_rows)}/delete")
    assert response.status_code == 302
    assert count_expenses(db_rows) == 0


def test_delete_requires_post(client, add_expense, db_rows):
    """Verify that deleting an expense requires a POST request."""
    add_expense()
    response = client.get(f"/expenses/{first_expense_id(db_rows)}/delete")
    assert response.status_code == 405
    assert count_expenses(db_rows) == 1


def test_delete_unknown_expense_returns_404(client):
    """Verify that deleting a nonexistent expense returns a 404 response."""
    assert client.post("/expenses/999/delete").status_code == 404


def test_empty_result_keeps_filter_form(client, add_expense):
    """Verify that the filter form remains visible when no expenses match."""
    add_expense()
    response = client.get("/?q=zzzz")
    assert response.status_code == 200
    assert b'name="q"' in response.data
    assert b"Mercado" not in response.data


def test_list_filters(client, add_expense):
    """Verify that the expense list is filtered by month, type and search query."""
    add_expense(name="Mercado", date="2026-11-11", category="groceries")
    add_expense(name="Cinema", amount="9,00", date="2026-10-05", category="entertainment")

    def page(query):
        """Return the decoded HTML of the expense list for the given query string."""
        return client.get(f"/{query}").data.decode()

    assert "Mercado" in page("?month=all") and "Cinema" in page("?month=all")
    assert "Cinema" not in page("?month=2026-11")
    assert "Mercado" not in page("?month=all&type=wants")
    assert "Mercado" in page("?month=all&q=merc") and "Cinema" not in page("?month=all&q=merc")
    # an invalid month falls back to the current month, an invalid type is ignored
    fallback = page("?month=abc&type=xyz")
    assert "Mercado" in fallback and "Cinema" not in fallback


def test_list_defaults_to_the_current_month(client, add_expense):
    """Verify that the expense list shows only the current month by default."""
    add_expense(name="Current", date="2026-11-11")
    add_expense(name="Older", date="2026-10-05")
    page = client.get("/").data.decode()
    assert "Current" in page and "Older" not in page


def test_month_menu_always_offers_the_current_month(client):
    """Verify that the month menu includes the current month and the 'all' option."""
    page = client.get("/").data.decode()
    assert 'value="2026-11"' in page and 'value="all"' in page


def test_new_expense_form_defaults_to_today(client):
    """Verify that the new expense form defaults the date to today."""
    assert 'value="2026-11-15"' in client.get("/expenses/new").data.decode()

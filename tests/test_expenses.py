import pytest


def count_expenses(db_rows):
    return db_rows("SELECT COUNT(*) AS n FROM expenses")[0]["n"]


def first_expense_id(db_rows):
    return db_rows("SELECT id FROM expenses")[0]["id"]


def test_add_expense_stores_cents(add_expense, db_rows):
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
    response = add_expense(**overrides)
    assert response.status_code == 400
    assert count_expenses(db_rows) == 0


def test_add_expense_rejects_unknown_category(client, db_rows):
    response = client.post(
        "/expenses/new",
        data={"name": "x", "amount": "1,00", "date": "2026-11-11", "category_id": "9999"},
    )
    assert response.status_code == 400
    assert count_expenses(db_rows) == 0


def test_invalid_form_shows_error_message(add_expense):
    response = add_expense(name="")
    assert b"Enter a name." in response.data


def test_edit_form_is_prefilled(client, add_expense, db_rows):
    add_expense(amount="3,58")
    response = client.get(f"/expenses/{first_expense_id(db_rows)}/edit")
    assert b'value="3,58"' in response.data


def test_edit_expense(client, add_expense, category_id, db_rows):
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
    add_expense()
    response = client.post(f"/expenses/{first_expense_id(db_rows)}/delete")
    assert response.status_code == 302
    assert count_expenses(db_rows) == 0


def test_delete_requires_post(client, add_expense, db_rows):
    add_expense()
    response = client.get(f"/expenses/{first_expense_id(db_rows)}/delete")
    assert response.status_code == 405
    assert count_expenses(db_rows) == 1


def test_delete_unknown_expense_returns_404(client):
    assert client.post("/expenses/999/delete").status_code == 404


def test_list_filters(client, add_expense):
    add_expense(name="Mercado", date="2026-11-11", category="groceries")
    add_expense(name="Cinema", amount="9,00", date="2026-10-05", category="entertainment")

    def page(query):
        return client.get(f"/{query}").data.decode()

    assert "Mercado" in page("") and "Cinema" in page("")
    assert "Cinema" not in page("?month=2026-11")
    assert "Mercado" not in page("?type=wants")
    assert "Mercado" in page("?q=merc") and "Cinema" not in page("?q=merc")
    # invalid month and type are ignored, so everything is listed
    everything = page("?month=abc&type=xyz")
    assert "Mercado" in everything and "Cinema" in everything


def test_empty_result_keeps_filter_form(client, add_expense):
    add_expense()
    response = client.get("/?q=zzzz")
    assert response.status_code == 200
    assert b'name="q"' in response.data
    assert b"Mercado" not in response.data

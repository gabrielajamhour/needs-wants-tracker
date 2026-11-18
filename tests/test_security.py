import pytest


def count_rows(db_rows, table):
    """Return the total number of rows in the specified database table."""
    return db_rows(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]


INJECTIONS = ["' OR 1=1 --", "'; DROP TABLE expenses; --", "%' OR '%'='", '" OR ""="']


@pytest.mark.parametrize("payload", INJECTIONS)
@pytest.mark.parametrize("param", ["q", "month", "type", "category_id"])
def test_list_filters_are_not_injectable(client, add_expense, db_rows, param, payload):
    """Verify that malicious input cannot alter expense list filter queries."""
    add_expense()
    response = client.get("/expenses", query_string={param: payload})
    assert response.status_code == 200
    assert count_rows(db_rows, "expenses") == 1  # the table is still there


@pytest.mark.parametrize("payload", INJECTIONS)
def test_search_payloads_match_nothing(client, add_expense, payload):
    """Verify that SQL injection payloads do not return unintended search results."""
    add_expense(name="Mercado")
    page = client.get("/expenses", query_string={"q": payload}).data.decode()
    assert "Mercado" not in page


@pytest.mark.parametrize("payload", INJECTIONS)
def test_categories_filter_is_not_injectable(client, payload):
    """Verify that malicious input cannot alter category filter queries."""
    assert client.get("/categories", query_string={"show": payload}).status_code == 200


def test_malicious_text_is_stored_literally(add_expense, db_rows):
    """Verify that SQL injection attempts are stored as literal expense names."""
    payload = "'); DROP TABLE expenses; --"
    assert add_expense(name=payload).status_code == 302
    assert db_rows("SELECT name FROM expenses")[0]["name"] == payload


def test_quotes_in_names_cannot_break_out_of_attributes(client, add_expense, db_rows):
    """Verify that quotes in expense names are escaped in HTML attributes."""
    add_expense(name='" onfocus="alert(1)')
    expense_id = db_rows("SELECT id FROM expenses")[0]["id"]
    page = client.get(f"/expenses/{expense_id}/edit").data.decode()
    assert '" onfocus="alert(1)' not in page
    assert "&#34; onfocus=&#34;alert(1)" in page


def test_category_names_are_escaped(client):
    """Verify that category names are escaped when rendered in HTML."""
    client.post("/categories", data={"name": "<b>bold</b>", "type": "wants"})
    page = client.get("/categories").data.decode()
    assert "<b>bold</b>" not in page
    assert "&lt;b&gt;" in page


@pytest.mark.parametrize("url", ["/", "/", "/categories", "/expenses/new"])
def test_security_headers(client, url):
    """Verify that application pages include the required security headers."""
    response = client.get(url)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"


def test_secret_key_is_not_hard_coded(app):
    """Verify that the application does not use the default development secret key."""
    assert app.secret_key
    assert app.secret_key != "dev-only-change-me"

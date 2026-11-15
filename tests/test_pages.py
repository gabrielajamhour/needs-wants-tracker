import pytest


@pytest.mark.parametrize("url", ["/", "/expenses/new", "/summary", "/categories"])
def test_pages_load(client, url):
    assert client.get(url).status_code == 200


def test_missing_expense_returns_404(client):
    assert client.get("/expenses/999/edit").status_code == 404


@pytest.mark.parametrize("url", ["/", "/summary", "/categories", "/expenses/new"])
def test_pages_declare_viewport(client, url):
    assert b'name="viewport"' in client.get(url).data


@pytest.mark.parametrize("url", ["/", "/summary?month=2026-11", "/categories"])
def test_tables_are_scrollable_on_small_screens(client, add_expense, url):
    add_expense(date="2026-11-11")
    assert b'class="table-wrap"' in client.get(url).data


def test_stylesheet_uses_border_box(client):
    assert b"box-sizing: border-box" in client.get("/static/styles.css").data

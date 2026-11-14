import pytest


@pytest.mark.parametrize("url", ["/", "/expenses/new", "/summary", "/categories"])
def test_pages_load(client, url):
    assert client.get(url).status_code == 200


def test_missing_expense_returns_404(client):
    assert client.get("/expenses/999/edit").status_code == 404
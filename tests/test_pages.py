import pytest


@pytest.mark.parametrize("url", ["/", "/expenses/new", "/summary", "/categories"])
def test_pages_load(client, url):
    """Verify that the main application pages load successfully."""
    assert client.get(url).status_code == 200


def test_missing_expense_returns_404(client):
    """Verify that editing a nonexistent expense returns a 404 response."""
    assert client.get("/expenses/999/edit").status_code == 404


@pytest.mark.parametrize("url", ["/", "/summary", "/categories", "/expenses/new"])
def test_pages_declare_viewport(client, url):
    """Verify that application pages declare a responsive viewport."""
    assert b'name="viewport"' in client.get(url).data


@pytest.mark.parametrize("url", ["/", "/summary?month=2026-11", "/categories"])
def test_tables_are_scrollable_on_small_screens(client, add_expense, url):
    """Verify that tables are wrapped for horizontal scrolling on small screens."""
    add_expense(date="2026-11-11")
    assert b'class="table-wrap"' in client.get(url).data


def test_stylesheet_uses_border_box(client):
    """Verify that the stylesheet applies border-box sizing."""
    assert b"box-sizing: border-box" in client.get("/static/styles.css").data


@pytest.mark.parametrize(
    "url, labels",
    [
        ("/", ["Date", "Name", "Category", "Type", "Amount"]),
        ("/categories", ["Name", "Type", "Uses", "Status"]),
    ],
)
def test_wide_tables_have_card_labels(client, add_expense, url, labels):
    """Check that wide tables include labels for mobile card layouts."""
    add_expense(date="2026-11-11")
    page = client.get(url).data.decode()
    assert 'class="table-cards"' in page
    for label in labels:
        assert f'data-label="{label}"' in page


def test_categories_page_has_the_emoji_picker(client):
    """Check that the categories page includes the emoji picker."""
    page = client.get("/categories").data.decode()
    assert 'id="emoji-dialog"' in page
    assert 'class="emoji-open"' in page
    assert "emoji-picker.js" in page


def test_emoji_picker_script_is_served(client):
    """Check that the emoji picker script is served successfully."""
    assert client.get("/static/emoji-picker.js").status_code == 200

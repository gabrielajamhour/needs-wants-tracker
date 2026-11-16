import pytest

from helpers import DEFAULT_EMOJI, is_valid_emoji


@pytest.mark.parametrize("text", ["🏠", "🏷️", "☕", "🇵🇹", "👍🏽", "👨‍👩‍👧"])
def test_valid_emojis(text):
    """Accept valid emoji characters and sequences."""
    assert is_valid_emoji(text)


@pytest.mark.parametrize("text", ["", " ", "a", "ab", "1", "<b>", "😀 ", "😀a", "é", "😀" * 13])
def test_invalid_emojis(text):
    """Reject invalid emoji values."""
    assert not is_valid_emoji(text)


def emoji_of(db_rows, name):
    """Return the emoji assigned to a category."""
    return db_rows("SELECT emoji FROM categories WHERE name = ?", (name,))[0]["emoji"]


def test_seeded_categories_have_emojis(db_rows):
    """Check that all seeded categories have emojis."""
    assert emoji_of(db_rows, "housing") == "🏠"
    assert all(r["emoji"] for r in db_rows("SELECT emoji FROM categories"))


def test_create_category_with_and_without_emoji(client, db_rows):
    """Check category creation with a custom or default emoji."""
    client.post("/categories", data={"name": "streaming", "type": "wants", "emoji": "📺"})
    client.post("/categories", data={"name": "pets", "type": "wants"})
    assert emoji_of(db_rows, "streaming") == "📺"
    assert emoji_of(db_rows, "pets") == DEFAULT_EMOJI


def test_invalid_emoji_is_rejected_on_create(client, db_rows):
    """Reject category creation with an invalid emoji."""
    client.post("/categories", data={"name": "streaming", "type": "wants", "emoji": "abc"})
    assert db_rows("SELECT COUNT(*) AS n FROM categories WHERE name = 'streaming'")[0]["n"] == 0


def test_edit_only_the_emoji(client, category_id, db_rows):
    """Allow changing a category emoji without renaming it."""
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/rename", data={"name": "groceries", "emoji": "🥦"})
    assert emoji_of(db_rows, "groceries") == "🥦"


def test_edit_with_nothing_changed_reports_no_changes(client, category_id):
    """Report when a category is submitted without changes."""
    cid = category_id("groceries")
    response = client.post(
        f"/categories/{cid}/rename", data={"name": "Groceries"}, follow_redirects=True
    )
    assert b"No changes to save." in response.data


def test_pages_show_the_category_emoji(client, add_expense):
    """Display category emojis across the main application pages."""
    add_expense(category="groceries", date="2026-11-11")
    for url in ["/", "/categories", "/expenses/new", "/summary?month=2026-11"]:
        assert "🛒" in client.get(url).data.decode()

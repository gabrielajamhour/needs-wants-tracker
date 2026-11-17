import pytest

from app import get_db
from helpers import DEFAULT_EMOJI, emoji_error


@pytest.mark.parametrize("text", ["🏠", "🏷️", "☕", "🇵🇹", "👍🏽", "👨‍👩‍👧"])
def test_a_single_emoji_is_accepted(text):
    """Accept valid single emojis and joined sequences."""
    assert emoji_error(text) is None


@pytest.mark.parametrize(
    "text, message",
    [
        ("abc", "That is not an emoji."),
        ("1", "That is not an emoji."),
        ("<b>", "That is not an emoji."),
        ("😀😀", "Choose only one emoji."),
        ("🏠🛒", "Choose only one emoji."),
        ("abc😀", "Use only the emoji, without other characters."),
        ("😀 x", "Use only the emoji, without other characters."),
    ],
)
def test_emoji_error_messages(text, message):
    """Return the appropriate error message for invalid emoji input."""
    assert emoji_error(text) == message


def emoji_of(db_rows, name):
    """Return the emoji assigned to a category."""
    return db_rows("SELECT emoji FROM categories WHERE name = ?", (name,))[0]["emoji"]


def test_seeded_emojis_are_valid(db_rows):
    """Check that all seeded category emojis are valid."""
    assert all(emoji_error(r["emoji"]) is None for r in db_rows("SELECT emoji FROM categories"))


def test_create_category_with_and_without_emoji(client, db_rows):
    """Check category creation with custom and default emojis."""
    client.post("/categories", data={"name": "streaming", "type": "wants", "emoji": "🎬"})
    client.post("/categories", data={"name": "pets", "type": "wants"})
    assert emoji_of(db_rows, "streaming") == "🎬"
    assert emoji_of(db_rows, "pets") == DEFAULT_EMOJI


@pytest.mark.parametrize(
    "bad, message",
    [
        ("abc", b"That is not an emoji."),
        ("\U0001f600\U0001f600", b"Choose only one emoji."),
        ("abc\U0001f600", b"Use only the emoji, without other characters."),
    ],
)
def test_bad_emoji_is_rejected_on_create_with_its_own_message(client, db_rows, bad, message):
    """Reject invalid emojis with specific error messages when creating categories."""
    response = client.post(
        "/categories",
        data={"name": "streaming", "type": "wants", "emoji": bad},
        follow_redirects=True,
    )
    assert message in response.data
    assert db_rows("SELECT COUNT(*) AS n FROM categories WHERE name = 'streaming'")[0]["n"] == 0


def test_edit_only_the_emoji(client, category_id, db_rows):
    """Allow changing a category emoji without renaming it."""
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/edit", data={"name": "groceries", "emoji": "🥦"})
    assert emoji_of(db_rows, "groceries") == "🥦"


def test_edit_rejects_two_emojis(client, category_id, db_rows):
    """Reject multiple emojis when editing a category."""
    cid = category_id("groceries")
    response = client.post(
        f"/categories/{cid}/edit",
        data={"name": "groceries", "emoji": "😀😀"},
        follow_redirects=True,
    )
    assert b"Choose only one emoji." in response.data
    assert emoji_of(db_rows, "groceries") == "🛒"


def test_edit_keeps_an_old_custom_emoji(app, client, category_id, db_rows):
    """Preserve existing custom emojis when no new emoji is submitted."""
    cid = category_id("groceries")
    with app.app_context():
        db = get_db()
        db.execute("UPDATE categories SET emoji = ? WHERE id = ?", ("😀😀", cid))
        db.commit()
    client.post(f"/categories/{cid}/edit", data={"name": "supermarket"})
    assert emoji_of(db_rows, "supermarket") == "😀😀"


def test_edit_with_nothing_changed_reports_no_changes(client, category_id):
    """Report when a category is submitted without any changes."""
    cid = category_id("groceries")
    response = client.post(
        f"/categories/{cid}/edit", data={"name": "Groceries"}, follow_redirects=True
    )
    assert b"No changes to save." in response.data

import pytest


def count_categories(db_rows):
    """Return the total number of categories in the database."""
    return db_rows("SELECT COUNT(*) AS n FROM categories")[0]["n"]


def test_create_category_is_normalized(client, db_rows):
    """Verify that new category names are normalized before being stored."""
    response = client.post("/categories", data={"name": "  Streaming  ", "type": "wants"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/categories?show=wants"
    row = db_rows("SELECT name, type, is_active FROM categories WHERE name = 'streaming'")[0]
    assert tuple(row) == ("streaming", "wants", 1)


def test_duplicate_category_is_rejected_ignoring_case(client, db_rows):
    """Verify that duplicate category names are rejected regardless of case."""
    before = count_categories(db_rows)
    response = client.post(
        "/categories", data={"name": "GROCERIES", "type": "needs"}, follow_redirects=True
    )
    assert b"That category already exists." in response.data
    assert count_categories(db_rows) == before


@pytest.mark.parametrize(
    "data",
    [
        {"name": "", "type": "wants"},
        {"name": "ok", "type": "invalid"},
        {"name": "x" * 41, "type": "wants"},
    ],
)
def test_invalid_category_is_rejected(client, db_rows, data):
    """Verify that categories with invalid names or types cannot be created."""
    before = count_categories(db_rows)
    client.post("/categories", data=data)
    assert count_categories(db_rows) == before


def test_rename_keeps_expenses(client, add_expense, category_id, db_rows):
    """Verify that renaming a category preserves its associated expenses."""
    add_expense(category="groceries")
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/edit", data={"name": "Supermarket"})
    assert db_rows("SELECT name FROM categories WHERE id = ?", (cid,))[0]["name"] == "supermarket"
    assert db_rows("SELECT category_id FROM expenses")[0]["category_id"] == cid


def test_rename_to_existing_name_is_rejected(client, category_id, db_rows):
    """Verify that a category cannot be renamed to another category's name."""
    cid = category_id("groceries")

    original_name = db_rows("SELECT name FROM categories WHERE id = ?", (cid,))[0]["name"]

    response = client.post(
        f"/categories/{cid}/edit", data={"name": "housing"}, follow_redirects=True
    )

    assert b"That category already exists." in response.data

    assert db_rows("SELECT name FROM categories WHERE id = ?", (cid,))[0]["name"] == original_name


def test_toggle_archives_and_restores(client, category_id, db_rows):
    """Verify that a category can be archived and restored."""
    cid = category_id("groceries")

    def is_active():
        """Return the current activation status of the category."""
        return db_rows("SELECT is_active FROM categories WHERE id = ?", (cid,))[0]["is_active"]

    client.post(f"/categories/{cid}/toggle")
    assert is_active() == 0
    client.post(f"/categories/{cid}/toggle")
    assert is_active() == 1


def test_archived_category_hidden_for_new_but_kept_for_existing(
    client, add_expense, category_id, db_rows
):
    """Check archived category visibility for new and existing expenses."""
    add_expense(category="groceries")
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/toggle")

    new_page = client.get("/expenses/new").data.decode()
    assert f'value="{cid}"' not in new_page

    expense_id = db_rows("SELECT id FROM expenses")[0]["id"]
    edit_page = client.get(f"/expenses/{expense_id}/edit").data.decode()
    assert f'value="{cid}"' in edit_page


def test_type_filter_on_categories_page(client):
    """Verify that the category page displays only the selected type."""
    page = client.get("/categories?show=savings").data.decode()
    assert "Emergency fund" in page
    assert "Housing" not in page


def test_archived_categories_are_listed_last_in_their_group(client, category_id):
    """Verify that archived categories appear after active categories within their type."""
    cid = category_id("education")  # first alphabetically among needs
    client.post(f"/categories/{cid}/toggle")
    page = client.get("/categories?show=needs").data.decode()
    assert page.index("Education") > page.index("Utilities")


def test_category_filter_shows_a_count_for_each_type(client, db_rows):
    """Check that the type filter shows how many categories there are in total and per type."""
    total = db_rows("SELECT COUNT(*) AS n FROM categories")[0]["n"]
    needs = db_rows("SELECT COUNT(*) AS n FROM categories WHERE type = 'needs'")[0]["n"]
    page = client.get("/categories").data.decode()
    assert f'<span class="segmented-count">{total}</span>' in page
    assert f'<span class="segmented-count">{needs}</span>' in page


def test_category_filter_marks_the_chosen_type(client):
    """Check that only the chosen type is marked as active."""
    page = client.get("/categories?show=wants").data.decode()
    assert page.count("segmented-option is-active") == 1


def test_categories_are_grouped_by_type_in_order(client):
    """Check that the list has one group per type: needs, then wants, then savings."""
    page = client.get("/categories").data.decode()
    needs = page.index("category-group-needs")
    wants = page.index("category-group-wants")
    savings = page.index("category-group-savings")
    assert needs < wants < savings


def test_rename_link_turns_one_row_into_a_form(client, category_id):
    """Check that ?edit=<id> shows the rename form only for that category."""
    cid = category_id("groceries")
    assert "Save name" not in client.get("/categories").data.decode()
    page = client.get(f"/categories?edit={cid}").data.decode()
    assert page.count("Save name") == 1
    assert f'action="/categories/{cid}/edit"' in page
    assert 'value="Groceries"' in page


def test_archived_category_is_marked_and_can_be_restored(client, category_id):
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/toggle")
    page = client.get("/categories").data.decode()
    assert "category-state" in page
    assert "Restore" in page


def test_add_form_picks_the_bucket_with_a_segmented_control(client):
    """Check that the bucket is a radio group with Needs chosen by default."""
    page = client.get("/categories").data.decode()
    assert page.count('type="radio" name="type"') == 3
    assert 'value="needs" checked' in page

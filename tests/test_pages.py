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


def test_list_has_month_arrows_that_keep_other_filters(client):
    """Check that the expense list month arrows link to adjacent months and keep other filters."""
    page = client.get("/?month=2026-12&type=wants").data.decode()
    assert "month=2026-11" in page and "month=2027-01" in page
    assert "type=wants" in page


def test_default_list_has_arrows_around_the_current_month(client):
    """Check that the default expense list shows arrows around the current month."""
    page = client.get("/").data.decode()
    assert "month=2026-10" in page and "month=2026-12" in page
    assert "November 2026" in page


def test_no_month_arrows_when_all_months_are_shown(client):
    """Check that month arrows are hidden when all months are shown."""
    assert 'class="month-nav"' not in client.get("/?month=all").data.decode()


def test_summary_has_month_arrows_across_the_year(client):
    """Check that the summary page month arrows cross year boundaries."""
    page = client.get("/summary?month=2026-12").data.decode()
    assert "month=2026-11" in page and "month=2027-01" in page
    assert "December 2026" in page


def test_summary_breakdown_is_ordered_needs_wants_savings(client, add_expense):
    """Check that the summary breakdown lists needs, then wants, then savings."""
    add_expense(category="groceries", date="2026-11-11")
    add_expense(name="Dinner", category="dining out", date="2026-11-12")
    add_expense(name="Transfer", category="emergency fund", date="2026-11-13")
    page = client.get("/summary?month=2026-11").data.decode()
    assert (
        page.index('class="type-needs"')
        < page.index('class="type-wants"')
        < page.index('class="type-savings"')
    )


def test_summary_remaining_card_is_full_width(client):
    """Check that the summary remaining card spans the full width of the grid."""
    assert 'class="card card-wide"' in client.get("/summary?month=2026-11").data.decode()


def test_expense_form_links_to_the_categories_page(client):
    """Check that the expense form links to the categories page."""
    assert 'id="manage-categories-link"' in client.get("/expenses/new").data.decode()


def main_nav(page):
    """Return the HTML inside the main navigation bar."""
    return page.split('class="main-nav"')[1].split("</nav>")[0]


@pytest.mark.parametrize("url", ["/", "/summary", "/expenses/new", "/categories"])
def test_every_page_has_the_menu_with_categories(client, url):
    """Check that every page has the menu with a link to the categories page."""
    page = client.get(url).data.decode()
    menu = page.split('class="menu"')[1].split("</details>")[0]
    assert 'href="/categories"' in menu


def test_categories_is_not_in_the_visible_navigation(client):
    """Check that the categories link is not shown in the visible navigation."""
    assert "/categories" not in main_nav(client.get("/").data.decode())


@pytest.mark.parametrize("url, label", [("/", "Expenses"), ("/summary", "Summary")])
def test_current_page_is_marked_in_the_navigation(client, url, label):
    """Check that the navigation marks the current page."""
    nav = main_nav(client.get(url).data.decode())
    current = nav.split('aria-current="page"')[1].split("</a>")[0]
    assert label in current


def test_header_has_the_add_button_and_a_brand_link(client):
    """Check that the header has the add expense button and a brand link to the home page."""
    page = client.get("/").data.decode()
    assert 'class="button primary add-button" href="/expenses/new"' in page
    assert 'class="brand" href="/"' in page


def test_menu_script_is_served(client):
    """Check that the menu script is served successfully."""
    assert client.get("/static/menu.js").status_code == 200


def test_logo_is_served_and_used_as_brand_and_icon(client):
    """Check that the logo is served and used as the brand link and page icon."""
    response = client.get("/static/logo.svg")
    assert response.status_code == 200
    assert "svg" in response.content_type
    page = client.get("/").data.decode()
    assert 'aria-label="Needs/Wants Tracker, home"' in page
    assert 'rel="icon"' in page


def test_header_stays_on_one_row_on_small_screens(client):
    """Check that the header stays on a single row on small screens."""
    css = client.get("/static/styles.css").data.decode()
    assert "flex-wrap: nowrap" in css

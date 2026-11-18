import pytest


@pytest.mark.parametrize("url", ["/expenses", "/expenses/new", "/", "/categories"])
def test_pages_load(client, url):
    """Verify that the main application pages load successfully."""
    assert client.get(url).status_code == 200


def test_missing_expense_returns_404(client):
    """Verify that editing a nonexistent expense returns a 404 response."""
    assert client.get("/expenses/999/edit").status_code == 404


@pytest.mark.parametrize("url", ["/expenses", "/", "/categories", "/expenses/new"])
def test_pages_declare_viewport(client, url):
    """Verify that application pages declare a responsive viewport."""
    assert b'name="viewport"' in client.get(url).data


@pytest.mark.parametrize("url", ["/expenses", "/?month=2026-11", "/categories"])
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
        ("/expenses", ["Date", "Name", "Category", "Type", "Amount"]),
        ("/categories", ["Name", "Type", "Expenses", "Status"]),
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
    assert 'class="emoji-open emoji-choice"' in page
    assert "emoji-picker.js" in page


def test_emoji_picker_script_is_served(client):
    """Check that the emoji picker script is served successfully."""
    assert client.get("/static/emoji-picker.js").status_code == 200


def test_list_has_month_arrows_that_keep_other_filters(client):
    """Check that the expense list month arrows link to adjacent months and keep other filters."""
    page = client.get("/expenses?month=2026-12&type=wants").data.decode()
    assert "month=2026-11" in page and "month=2027-01" in page
    assert "type=wants" in page


def test_default_list_has_arrows_around_the_current_month(client):
    """Check that the default expense list shows arrows around the current month."""
    page = client.get("/expenses").data.decode()
    assert "month=2026-10" in page and "month=2026-12" in page
    assert "November 2026" in page


def test_no_month_arrows_when_all_months_are_shown(client):
    """Check that month arrows are hidden when all months are shown."""
    assert 'class="month-nav"' not in client.get("/expenses?month=all").data.decode()


def test_summary_has_month_arrows_across_the_year(client):
    """Check that the summary page month arrows cross year boundaries."""
    page = client.get("/?month=2026-12").data.decode()
    assert "month=2026-11" in page and "month=2027-01" in page
    assert "December 2026" in page


def test_summary_breakdown_is_ordered_needs_wants_savings(client, add_expense):
    """Check that the summary breakdown lists needs, then wants, then savings."""
    add_expense(category="groceries", date="2026-11-11")
    add_expense(name="Dinner", category="dining out", date="2026-11-12")
    add_expense(name="Transfer", category="emergency fund", date="2026-11-13")
    page = client.get("/?month=2026-11").data.decode()
    assert (
        page.index('class="type-needs"')
        < page.index('class="type-wants"')
        < page.index('class="type-savings"')
    )


def test_summary_remaining_card_is_full_width(client):
    """Check that the summary remaining card spans the full width of the grid."""
    assert 'class="card card-wide"' in client.get("/?month=2026-11").data.decode()


def test_expense_form_links_to_the_categories_page(client):
    """Check that the expense form links to the categories page."""
    assert 'id="manage-categories-link"' in client.get("/expenses/new").data.decode()


def main_nav(page):
    """Return the HTML inside the main navigation bar."""
    return page.split('class="main-nav"')[1].split("</nav>")[0]


@pytest.mark.parametrize("url", ["/expenses", "/", "/expenses/new", "/categories"])
def test_every_page_has_the_menu_with_categories(client, url):
    """Check that every page has the menu with a link to the categories page."""
    page = client.get(url).data.decode()
    menu = page.split('class="menu"')[1].split("</details>")[0]
    assert 'href="/categories"' in menu


def test_categories_is_not_in_the_visible_navigation(client):
    """Check that the categories link is not shown in the visible navigation."""
    assert "/categories" not in main_nav(client.get("/expenses").data.decode())


@pytest.mark.parametrize("url, label", [("/expenses", "Expenses"), ("/", "Summary")])
def test_current_page_is_marked_in_the_navigation(client, url, label):
    """Check that the navigation marks the current page."""
    nav = main_nav(client.get(url).data.decode())
    current = nav.split('aria-current="page"')[1].split("</a>")[0]
    assert label in current


def test_header_has_the_add_button_and_a_brand_link(client):
    """Check that the header has the add expense button and a brand link to the home page."""
    page = client.get("/expenses").data.decode()
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
    page = client.get("/expenses").data.decode()
    assert 'aria-label="Needs/Wants Tracker, home"' in page
    assert 'rel="icon"' in page


def test_header_stays_on_one_row_on_small_screens(client):
    """Check that the header stays on a single row on small screens."""
    css = client.get("/static/styles.css").data.decode()
    assert "flex-wrap: nowrap" in css


def test_row_actions_are_buttons_not_links(client, add_expense):
    """Check that row actions are shown as buttons instead of links."""
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert "button secondary small" in page  # Edit
    assert "danger small" in page  # Delete
    assert "Clear" in page and 'class="button secondary"' in page


@pytest.mark.parametrize("url", ["/expenses", "/categories", "/expenses/new", "/"])
def test_no_pages_use_the_old_link_button_style(client, add_expense, url):
    """Check that no page uses the old link button style."""
    add_expense(date="2026-11-11")
    assert "link-button" not in client.get(url).data.decode()


def test_expense_form_actions_are_buttons(client):
    """Check that the expense form actions are shown as buttons."""
    page = client.get("/expenses/new").data.decode()
    assert 'class="form-actions"' in page
    assert 'class="button secondary"' in page


def test_stylesheet_defines_the_design_tokens(client):
    """Check that the stylesheet defines the design tokens and drops the old link button style."""
    css = client.get("/static/styles.css").data.decode()
    assert "--color-primary" in css and "--space-3" in css
    assert ":where(a:visited)" in css
    assert ".link-button" not in css


def test_add_button_uses_an_icon_not_a_text_plus(client):
    page = client.get("/expenses").data.decode()
    assert '<svg class="plus"' in page
    assert ">+</span>" not in page


@pytest.mark.parametrize("url, header", [("/expenses", "Actions"), ("/categories", "Edit")])
def test_actions_column_header_can_shrink_to_fit(client, add_expense, url, header):
    add_expense(date="2026-11-11")
    page = client.get(url).data.decode()
    assert f'<th role="columnheader" class="actions">{header}</th>' in page


def test_stylesheet_shrinks_the_actions_column(client):
    css = client.get("/static/styles.css").data.decode()
    assert "td.actions" in css and "width: 1%" in css


def test_stylesheet_keeps_row_actions_on_one_line_on_wide_screens(client):
    css = client.get("/static/styles.css").data.decode()
    assert "td.actions .actions-group" in css


def test_list_shows_dates_as_day_month_year(client, add_expense):
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert "11/11/2026" in page


def test_stylesheet_centers_titles_and_draws_the_table_grid(client):
    css = client.get("/static/styles.css").data.decode()
    assert "text-align: center" in css
    assert ".table-cards th," in css


def test_month_picker_lives_in_the_month_navigation(client):
    page = client.get("/?month=2026-11").data.decode()
    nav = page.split('class="month-nav"')[1].split("</nav>")[0]
    assert 'type="month"' in nav and 'name="month"' in nav
    assert 'aria-label="Choose month"' in nav


def test_summary_has_no_view_button_and_a_separate_income_form(client):
    page = client.get("/?month=2026-11").data.decode()
    assert ">View<" not in page
    income = page.split('class="control-form income-form"')[1]
    assert 'name="income"' in income


def test_expense_list_navigation_has_no_month_picker(client):
    page = client.get("/expenses").data.decode()  # "/expenses" after the home page change
    assert 'class="month-picker"' not in page


def test_month_picker_script_is_served(client):
    assert client.get("/static/month-picker.js").status_code == 200


def test_main_pages_keep_a_hidden_title(client):
    for url, title in [("/expenses", "Expenses"), ("/?month=2026-11", "Monthly summary")]:
        page = client.get(url).data.decode()
        assert f'<h1 class="sr-only">{title}</h1>' in page


def test_summary_toolbar_has_month_navigation_before_income(client):
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="summary-toolbar"' in page
    assert page.index('class="month-nav"') < page.index('class="control-form income-form"')


def test_filter_form_uses_the_full_width_bar(client):
    page = client.get("/expenses").data.decode()  # "/expenses" after the home page change
    assert 'class="row filter-bar"' in page
    assert 'class="grow"' in page


def test_stylesheet_lets_the_summary_month_navigation_grow(client):
    css = client.get("/static/styles.css").data.decode()
    assert ".summary-toolbar .month-nav strong" in css


def test_summary_is_the_home_page(client):
    page = client.get("/").data.decode()
    assert "Monthly summary" in page


def test_expense_list_lives_at_expenses(client):
    assert client.get("/expenses").status_code == 200


def test_navigation_lists_summary_first(client):
    nav = main_nav(client.get("/").data.decode())
    assert nav.index("Summary") < nav.index("Expenses")


def test_brand_links_to_the_home_page_and_not_to_the_list(client):
    page = client.get("/expenses").data.decode()
    assert 'class="brand" href="/"' in page


def test_old_summary_url_redirects_to_the_home_page(client):
    response = client.get("/summary?month=2026-10")
    assert response.status_code == 301
    assert response.headers["Location"] == "/?month=2026-10"


def test_categories_headers_are_clear(client):
    page = client.get("/categories").data.decode()
    assert ">Expenses</th>" in page
    assert ">Uses<" not in page
    assert '<th role="columnheader" class="actions">Edit</th>' in page


def test_emoji_is_one_button_with_a_text_fallback(client):
    page = client.get("/categories").data.decode()
    assert 'class="emoji-field"' in page
    assert 'class="emoji-open emoji-choice"' in page
    assert 'id="emoji-new"' in page


def test_invalid_category_keeps_what_the_user_typed(client):
    response = client.post(
        "/categories", data={"name": "My new thing", "type": "wants", "emoji": "abc"}
    )
    assert response.status_code == 400
    page = response.data.decode()
    assert "That is not an emoji." in page
    assert 'value="My new thing"' in page
    assert 'value="wants" selected' in page


def test_failed_edit_keeps_what_the_user_typed(client, category_id):
    cid = category_id("groceries")
    response = client.post(f"/categories/{cid}/edit", data={"name": "housing", "emoji": "🛒"})
    assert response.status_code == 400
    page = response.data.decode()
    assert "That category already exists." in page
    assert 'value="housing"' in page


def test_stylesheet_makes_the_hidden_attribute_win(client):
    css = client.get("/static/styles.css").data.decode()
    assert "[hidden]" in css


def test_category_status_is_a_badge(client):
    assert 'class="status-badge active"' in client.get("/categories").data.decode()


def test_archived_category_shows_an_archived_badge(client, category_id):
    cid = category_id("groceries")
    client.post(f"/categories/{cid}/toggle")
    assert 'class="status-badge archived"' in client.get("/categories").data.decode()


def test_stylesheet_aligns_the_emoji_label_with_the_other_fields(client):
    css = client.get("/static/styles.css").data.decode()
    assert ".row .emoji-field" in css

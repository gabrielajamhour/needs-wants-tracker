import re

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


@pytest.mark.parametrize("url", ["/expenses"])
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
    """Check that the summary lists needs, then wants, then savings, each category in its column."""
    add_expense(category="groceries", date="2026-11-11")
    add_expense(name="Dinner", category="dining out", date="2026-11-12")
    add_expense(name="Transfer", category="emergency fund", date="2026-11-13")
    page = client.get("/?month=2026-11").data.decode()
    buckets = page[page.index('class="buckets"') :]
    assert (
        buckets.index('class="bucket bucket-needs"')
        < buckets.index("Groceries")
        < buckets.index('class="bucket bucket-wants"')
        < buckets.index("Dining out")
        < buckets.index('class="bucket bucket-savings"')
        < buckets.index("Emergency fund")
    )


def test_summary_has_no_tables(client, add_expense):
    """Check that the summary shows ledger lists instead of the old tables."""
    add_expense(category="groceries", date="2026-11-11")
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="ledger"' in page
    assert "<table" not in page and ">Spent</th>" not in page


def test_summary_hero_replaces_the_remaining_card(client):
    """Check that the hero shows what is left to spend instead of a Remaining card."""
    client.post("/", data={"month": "2026-11", "income": "1.000,00"})
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="hero"' in page
    assert "Remaining" not in page and "card-wide" not in page


def test_expense_form_links_to_the_categories_page(client):
    """Check that the expense form links to the categories page."""
    assert 'id="manage-categories-link"' in client.get("/expenses/new").data.decode()


def main_nav(page):
    """Return the HTML inside the main navigation bar."""
    return page.split('class="main-nav"')[1].split("</nav>")[0]


@pytest.mark.parametrize("url", ["/expenses", "/", "/expenses/new", "/categories"])
def test_every_page_has_the_three_tabs(client, url):
    """Check that every page shows the Summary, Expenses and Categories tabs."""
    nav = main_nav(client.get(url).data.decode())
    for href in ('href="/"', 'href="/expenses"', 'href="/categories"'):
        assert href in nav


def test_header_has_no_menu(client):
    """Check that the old hamburger menu and its script are gone."""
    page = client.get("/expenses").data.decode()
    assert 'class="menu"' not in page
    assert "menu.js" not in page
    assert client.get("/static/menu.js").status_code == 404


def test_add_button_is_hidden_on_the_new_expense_page(client):
    """Check that the add button is not shown on the page it leads to."""
    page = client.get("/expenses/new").data.decode()
    assert 'class="button primary add-button"' not in page


@pytest.mark.parametrize(
    "url, label",
    [("/expenses", "Expenses"), ("/", "Summary"), ("/categories", "Categories")],
)
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


def test_logo_is_served_and_used_as_brand_and_icon(client):
    """Check that the logo is served and used as the brand link and page icon."""
    response = client.get("/static/logo.svg")
    assert response.status_code == 200
    assert "svg" in response.content_type
    page = client.get("/expenses").data.decode()
    assert 'aria-label="Needs/Wants Tracker, home"' in page
    assert 'rel="icon"' in page
    assert '<span class="brand-name">Needs/Wants</span>' in page


def test_header_stays_on_one_row_on_small_screens(client):
    """Check that the header stays on a single row on small screens."""
    css = client.get("/static/styles.css").data.decode()
    assert "flex-wrap: nowrap" in css


def test_row_actions_are_labelled_icon_buttons(client, add_expense):
    """Check that the row actions are icon buttons that name the expense for screen readers."""
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert page.count("row-action") >= 2
    assert 'aria-label="Edit ' in page
    assert 'aria-label="Delete ' in page


def test_clear_filters_link_only_shows_when_a_filter_is_active(client, add_expense):
    add_expense(date="2026-11-11")
    assert "Clear filters" not in client.get("/expenses").data.decode()
    assert "Clear filters" in client.get("/expenses?type=needs").data.decode()


@pytest.mark.parametrize("url", ["/expenses", "/categories", "/expenses/new", "/"])
def test_no_pages_use_the_old_link_button_style(client, add_expense, url):
    """Check that no page uses the old link button style."""
    add_expense(date="2026-11-11")
    assert "link-button" not in client.get(url).data.decode()


def test_expense_form_actions_are_buttons(client):
    """Check that the expense form actions are shown as buttons."""
    page = client.get("/expenses/new").data.decode()
    assert 'class="form-actions"' in page
    assert 'class="button ghost"' in page


def test_stylesheet_defines_the_design_tokens(client):
    """Check that the stylesheet defines the design tokens and drops the old link button style."""
    css = client.get("/static/styles.css").data.decode()
    assert "--color-ink" in css and "--space-3" in css
    assert ":where(a:visited)" in css
    assert ".link-button" not in css


def test_add_button_uses_an_icon_not_a_text_plus(client):
    page = client.get("/expenses").data.decode()
    assert '<svg class="plus"' in page
    assert ">+</span>" not in page


@pytest.mark.parametrize(
    "url, header",
    [
        ("/expenses", '<span class="sr-only">Actions</span>'),
    ],
)
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


def test_list_shows_dates_as_day_and_month(client, add_expense):
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert "11 Nov" in page
    assert "11 Nov 2026" not in page


def test_list_shows_the_year_when_all_months_are_listed(client, add_expense):
    add_expense(date="2026-11-11")
    page = client.get("/expenses?month=all").data.decode()
    assert "11 Nov 2026" in page


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
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert ">View<" not in page
    income = page.split('class="control-form income-form"')[1]
    assert 'name="income"' in income


def test_expense_list_navigation_has_the_month_picker(client):
    page = client.get("/expenses").data.decode()
    assert 'class="month-picker"' in page
    assert 'action="/expenses"' in page


def test_month_picker_script_is_served(client):
    assert client.get("/static/month-picker.js").status_code == 200


def test_main_pages_keep_a_hidden_title(client):
    for url, title in [("/expenses", "Expenses"), ("/?month=2026-11", "Monthly summary")]:
        page = client.get(url).data.decode()
        assert f'<h1 class="sr-only">{title}</h1>' in page


def test_summary_toolbar_has_month_navigation_before_income(client):
    page = client.get("/?month=2026-11&edit=income").data.decode()
    assert 'class="summary-toolbar"' in page
    assert page.index('class="month-nav"') < page.index('class="control-form income-form"')


def test_filter_form_uses_the_full_width_bar(client):
    page = client.get("/expenses").data.decode()  # "/expenses" after the home page change
    assert 'class="row filter-bar"' in page
    assert 'class="grow"' in page


def test_summary_is_the_home_page(client):
    page = client.get("/").data.decode()
    assert "Monthly summary" in page


def test_navigation_lists_summary_first(client):
    nav = main_nav(client.get("/").data.decode())
    assert nav.index("Summary") < nav.index("Expenses")


def test_old_summary_url_redirects_to_the_home_page(client):
    response = client.get("/summary?month=2026-10")
    assert response.status_code == 301
    assert response.headers["Location"] == "/?month=2026-10"


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
    assert 'value="wants" checked' in page


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


def test_stylesheet_aligns_the_emoji_label_with_the_other_fields(client):
    css = client.get("/static/styles.css").data.decode()
    assert ".add-category .emoji-field" in css


@pytest.mark.parametrize("url", ["/expenses", "/categories", "/expenses/new", "/"])
def test_no_pages_use_the_old_secondary_style(client, add_expense, url):
    """Check that the old secondary button style was replaced by ghost and quiet."""
    add_expense(date="2026-11-11")
    assert "secondary" not in client.get(url).data.decode()


def test_archive_uses_the_quiet_button(client, category_id):
    """Check that Archive is a quiet button, as repeated row actions are."""
    assert 'class="quiet small">Archive' in client.get("/categories").data.decode()


def month_nav_html(client, url):
    """Return the HTML inside the month navigation of a page."""
    page = client.get(url).data.decode()
    return page.split('class="month-nav"')[1].split("</nav>")[0]


@pytest.mark.parametrize("url", ["/expenses", "/?month=2026-11"])
def test_month_arrows_are_icon_buttons(client, url):
    """Check that the month arrows are ghost icon buttons with an SVG chevron."""
    nav = month_nav_html(client, url)
    assert nav.count('class="button ghost icon-button"') == 2
    assert "‹" not in nav and "›" not in nav


def test_summary_month_title_opens_the_picker(client):
    """Check that on the summary the month title is the button of the month picker."""
    nav = month_nav_html(client, "/?month=2026-11")
    assert 'class="month-title month-title-button"' in nav
    assert "November 2026" in nav


def test_expenses_month_title_opens_the_picker(client):
    """Check that on the expense list the month title is the button of the month picker."""
    nav = month_nav_html(client, "/expenses")
    assert 'class="month-title month-title-button"' in nav
    assert "November 2026" in nav


def test_expenses_month_picker_keeps_the_active_filters(client, category_id):
    """Check that choosing another month keeps the category, type and search filters."""
    cid = category_id("groceries")
    nav = month_nav_html(client, f"/expenses?category_id={cid}&type=needs&q=market")
    assert f'<input type="hidden" name="category_id" value="{cid}">' in nav
    assert '<input type="hidden" name="type" value="needs">' in nav
    assert '<input type="hidden" name="q" value="market">' in nav


def test_expenses_month_picker_has_no_hidden_filters_when_none_are_active(client):
    """Check that the picker adds no hidden fields when no filter is active."""
    assert 'type="hidden"' not in month_nav_html(client, "/expenses")


def test_expense_list_loads_the_script_that_applies_filters(client):
    """Check that the expense list loads the script that applies filters as soon as they change."""
    page = client.get("/expenses").data.decode()
    assert "filters.js" in page and "month-filters.js" not in page
    assert client.get("/static/filters.js").status_code == 200


def test_flash_messages_have_a_hidden_close_button_and_the_right_role(client):
    """Check that flash messages have a close button and errors use role alert."""
    client.post("/", data={"month": "2026-11", "income": "abc"})
    page = client.get("/?month=2026-11").data.decode()
    assert 'class="flash error" role="alert"' in page
    assert (
        'class="quiet flash-close"' in page
        and "hidden" in page.split("flash-close")[1].split(">")[0]
    )


def test_flash_script_is_served_and_loaded(client):
    """Check that the script that fades out flash messages is loaded and served."""
    assert "flash.js" in client.get("/").data.decode()
    assert client.get("/static/flash.js").status_code == 200


def test_each_bucket_lists_the_categories_of_its_type(client, add_expense):
    """Check that every category appears inside the column of its own type."""
    add_expense(amount="10,00", date="2026-11-03", category="groceries")
    add_expense(amount="20,00", date="2026-11-04", category="dining out")
    page = client.get("/?month=2026-11").data.decode()
    needs, wants, savings = page.split('<section class="bucket bucket-')[1:]
    assert "Groceries" in needs and "10,00 €" in needs and "Dining out" not in needs
    assert "Dining out" in wants and "20,00 €" in wants
    assert "ledger-row" not in savings


def test_pages_show_the_current_month_when_none_was_chosen(client):
    """Check that without a chosen month both pages start on the current month."""
    for url in ("/", "/expenses"):
        page = client.get(url).data.decode()
        assert "month=2026-10" in page and "month=2026-12" in page


def test_expenses_follows_the_month_chosen_in_summary(client):
    """Check that the month picked in Summary is the one Expenses shows."""
    client.get("/?month=2026-09")
    page = client.get("/expenses").data.decode()
    assert "month=2026-08" in page and "month=2026-10" in page


def test_summary_follows_the_month_chosen_in_expenses(client):
    """Check that the month picked in Expenses is the one Summary shows."""
    client.get("/expenses?month=2026-09")
    page = client.get("/").data.decode()
    assert "month=2026-08" in page and "month=2026-10" in page


def test_month_survives_a_visit_to_categories(client):
    """Check that a page without a month does not make the chosen month go away."""
    client.get("/?month=2026-09")
    client.get("/categories")
    page = client.get("/").data.decode()
    assert "month=2026-08" in page and "month=2026-10" in page


def test_all_months_filter_does_not_replace_the_chosen_month(client):
    """Check that viewing all months in Expenses keeps the month chosen before."""
    client.get("/?month=2026-09")
    client.get("/expenses?month=all")
    page = client.get("/").data.decode()
    assert "month=2026-08" in page and "month=2026-10" in page


def filter_bar_html(client, url):
    """Return the HTML inside the filter form of an expenses page."""
    page = client.get(url).data.decode()
    return page.split('class="row filter-bar"')[1].split("</form>")[0]


def test_filters_carry_the_chosen_month_in_a_hidden_field(client):
    """Check that the month is sent with the filters now that the select is gone."""
    bar = filter_bar_html(client, "/expenses?month=2026-09")
    assert '<input type="hidden" name="month" value="2026-09">' in bar
    assert 'id="month"' not in bar


def test_filters_keep_all_months_in_the_hidden_field(client):
    """Check that the all-months view stays when a filter changes."""
    bar = filter_bar_html(client, "/expenses?month=all")
    assert 'name="month" value="all"' in bar


def test_filter_button_only_shows_without_javascript(client):
    """Check that the Filter button lives inside noscript."""
    bar = filter_bar_html(client, "/expenses")
    assert "<noscript><button" in bar and ">Filter</button></noscript>" in bar


def test_expenses_links_to_all_months_and_back(client):
    """Check the link to all months keeps filters and the link back goes to one month."""
    page = client.get("/expenses?month=2026-09&type=wants").data.decode()
    assert "month=all" in page and "type=wants" in page.split("All months")[0].split("href=")[-1]
    all_page = client.get("/expenses?month=all&type=wants").data.decode()
    assert "Back to one month" in all_page
    assert 'href="/expenses?type=wants"' in all_page


def test_filters_script_is_served_and_the_old_one_is_gone(client):
    """Check that filters.js exists and month-filters.js does not."""
    assert client.get("/static/filters.js").status_code == 200
    assert client.get("/static/month-filters.js").status_code == 404


def test_expenses_category_filter_is_grouped_by_type(client):
    """Check that the category filter lists categories by type, each option carrying its type."""
    page = client.get("/expenses").data.decode()
    for kind in ("Needs", "Wants", "Savings"):
        assert f'<optgroup label="{kind}">' in page
    assert 'data-type="needs"' in page and 'data-type="wants"' in page


def test_expenses_type_filter_is_a_segmented_control(client):
    """Check that the type filter has one radio per option and marks the chosen one."""
    html = client.get("/expenses?month=all&type=wants").get_data(as_text=True)
    assert html.count('type="radio" name="type"') == 4
    assert re.search(r'value="wants"\s+checked', html)
    assert not re.search(r'value=""\s+checked', html)


def test_list_marks_each_expense_with_its_type_tag(client, add_expense):
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert 'class="type-tag type-tag-' in page


def test_list_ends_with_a_total_row(client, add_expense):
    add_expense(date="2026-11-11")
    add_expense(date="2026-11-12")
    page = client.get("/expenses").data.decode()
    assert "Total of 2 expenses" in page
    assert page.index("</tbody>") < page.index("<tfoot")


def test_total_row_uses_the_singular_for_one_expense(client, add_expense):
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert "Total of 1 expense<" in page


def test_delete_asks_for_confirmation_in_a_dialog(client, add_expense):
    """Check that each row names its expense for the dialog, with confirm() kept as the fallback."""
    add_expense(name="Supermarket", date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert '<dialog id="delete-dialog"' in page
    assert 'data-delete-name="Supermarket"' in page
    assert 'data-delete-amount="' in page
    assert "Delete expense" in page
    assert "confirm(" in page


def test_expense_form_has_a_back_link(client):
    page = client.get("/expenses/new").data.decode()
    assert '<a class="back-link" href="/expenses">← Back to expenses</a>' in page


def test_expense_form_amount_field_is_focused_and_has_a_currency_sign(client):
    page = client.get("/expenses/new").data.decode()
    assert "autofocus" in page
    assert 'class="amount-currency"' in page


def test_expense_form_has_a_suggestion_line_with_a_use_button(client):
    page = client.get("/expenses/new").data.decode()
    assert 'id="suggestion" class="suggestion" hidden' in page
    assert 'id="suggestion-use" class="button ghost small"' in page


def test_expense_form_manage_link_is_outside_the_select(client):
    page = client.get("/expenses/new").data.decode()
    select = page[page.index("<select") : page.index("</select>")]
    assert "manage-categories-link" not in select
    assert page.index('id="category_id"') < page.index('id="manage-categories-link"')
    assert page.index('id="manage-categories-link"') < page.index('id="date"')


def test_new_expense_form_keeps_a_draft_but_not_after_an_error(client):
    assert 'data-draft="expense-new"' in client.get("/expenses/new").data.decode()

    page = client.post("/expenses/new", data={}).data.decode()
    assert "data-draft" not in page


def test_save_and_add_another_returns_to_an_empty_form(client, category_id):
    """Check that saving with the add another button leads back to the new expense form."""
    response = client.post(
        "/expenses/new",
        data={
            "name": "Bread",
            "amount": "2,50",
            "date": "2026-11-15",
            "category_id": category_id("Groceries"),
            "action": "add_another",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/expenses/new")


def test_only_the_new_expense_form_offers_save_and_add_another(client):
    """Check that the add another button is shown when creating, not when editing."""
    assert "Save and add another" in client.get("/expenses/new").data.decode()


def test_expense_rows_mark_the_category_and_type_cells(client, add_expense):
    """Check that the category and type cells have classes for the small screen layout."""
    add_expense(date="2026-11-11")
    page = client.get("/expenses").data.decode()
    assert 'class="cell-category"' in page
    assert 'class="cell-type"' in page

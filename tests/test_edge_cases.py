import pytest

from app import MAX_AMOUNT_CENTS, MAX_NAME_LENGTH


def count_rows(db_rows, table):
    """Return the total number of rows in the specified database table."""
    return db_rows(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]


@pytest.mark.parametrize(
    "amount, cents",
    [
        ("0,01", 1),
        ("0,99", 99),
        ("1.000.000,00", 100000000),
        ("10.000.000,00", MAX_AMOUNT_CENTS),
    ],
)
def test_boundary_amounts_are_stored_exactly(add_expense, db_rows, amount, cents):
    """Verify that boundary monetary amounts are stored exactly in cents."""
    assert add_expense(amount=amount).status_code == 302
    assert db_rows("SELECT amount_cents FROM expenses")[0]["amount_cents"] == cents


@pytest.mark.parametrize("amount", ["0,004", "99999999999999999999", "10.000.001,00"])
def test_amount_out_of_range_is_rejected_not_a_server_error(add_expense, db_rows, amount):
    """Verify that invalid or excessive amounts are rejected without a server error."""
    assert add_expense(amount=amount).status_code == 400
    assert count_rows(db_rows, "expenses") == 0


def test_name_length_limit(add_expense, db_rows):
    """Verify that expense names cannot exceed the maximum allowed length."""
    assert add_expense(name="x" * MAX_NAME_LENGTH).status_code == 302
    assert add_expense(name="x" * (MAX_NAME_LENGTH + 1)).status_code == 400
    assert count_rows(db_rows, "expenses") == 1


@pytest.mark.parametrize(
    "date, expected_status",
    [
        ("2026-02-28", 302),
        ("2028-02-29", 302),  # leap year
        ("2026-02-29", 400),  # not a leap year
        ("2026-04-31", 400),
        ("2026-2-5", 302),  # accepted and normalized
    ],
)
def test_dates_at_month_ends(add_expense, date, expected_status):
    """Verify that valid and invalid dates near month boundaries are handled correctly."""
    assert add_expense(date=date).status_code == expected_status


def test_short_date_is_normalized(add_expense, db_rows):
    """Verify that dates with single-digit months or days are normalized."""
    add_expense(date="2026-2-5")
    assert db_rows("SELECT date FROM expenses")[0]["date"] == "2026-02-05"


def test_month_boundaries_in_summary(client, add_expense):
    """Verify that expenses are included in the correct monthly summary."""
    client.post("/", data={"month": "2026-11", "income": "1.000,00"})
    client.post("/", data={"month": "2026-12", "income": "1.000,00"})
    add_expense(name="Last", amount="10,00", date="2026-11-30")
    add_expense(name="First", amount="20,00", date="2026-12-01")
    november = client.get("/?month=2026-11").data.decode()
    december = client.get("/?month=2026-12").data.decode()
    assert "10,00 € of 1.000,00 € used this month" in november
    assert "20,00 € of 1.000,00 € used this month" in december


def test_empty_month_summary(client):
    """Verify that the summary handles months without recorded expenses."""
    page = client.get("/?month=2030-01").data.decode()
    assert "No expenses this month." in page


def test_zero_income_shows_negative_remaining(client, add_expense):
    """Verify that spending with zero income produces a negative remaining balance."""
    client.post("/", data={"month": "2026-11", "income": "0"})
    add_expense(amount="3,58", date="2026-11-11")
    page = client.get("/?month=2026-11").data.decode()
    assert "-3,58 €" in page


def test_huge_income_is_rejected(client, db_rows):
    """Verify that excessively large income values are not saved."""
    response = client.post("/", data={"month": "2026-11", "income": "99999999999999999999"})
    assert response.status_code == 400
    assert count_rows(db_rows, "budgets") == 0


@pytest.mark.parametrize(
    "query", ["?month=2026-13", "?category_id=abc", "?type=xyz", "?q=" + "a" * 5000]
)
def test_list_survives_bad_filters(client, add_expense, query):
    """Verify that invalid or excessive filters do not cause server errors."""
    add_expense()
    assert client.get("/expenses" + query).status_code == 200


def test_names_are_html_escaped(client, add_expense):
    """Verify that expense names are HTML-escaped to prevent script injection."""
    add_expense(name="<script>alert(1)</script>")
    page = client.get("/expenses").data.decode()
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_unicode_names_round_trip(client, add_expense):
    """Verify that Unicode expense names are stored, displayed and searchable."""
    add_expense(name="Coffee ☕")
    assert "Coffee ☕" in client.get("/expenses").data.decode()
    assert "Coffee" in client.get("/expenses?q=Coffee").data.decode()


@pytest.mark.xfail(
    reason="LIKE ignores case only for ASCII; "
    "                           accent-insensitive search is in the backlog"
)
def test_search_ignores_case_of_accented_letters(client, add_expense):
    """Verify that searches ignore case differences in accented letters."""
    add_expense(name="Café")
    assert "Café" in client.get("/expenses?q=CAFÉ").data.decode()

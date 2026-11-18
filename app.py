import os
from datetime import date, datetime
from urllib.parse import urlsplit

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

# Imports from other files in the project
from budget import build_cards
from db import DEFAULT_DB_PATH, close_db, get_db
from helpers import (
    DEFAULT_EMOJI,
    cents_to_eur,
    emoji_error,
    eur_to_cents,
    format_date,
    month_label,
    shift_month,
)

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("TRACKER_DB", DEFAULT_DB_PATH)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
app.teardown_appcontext(close_db)  # Close connection when context finishes
app.add_template_filter(cents_to_eur, "eur")  # Simplify function usage
app.add_template_filter(month_label, "month_label")
app.add_template_filter(format_date, "date_label")

# Types of expenses
VALID_TYPES = {"needs", "wants", "savings"}

# Custom order for category types
TYPE_ORDER_SQL = "CASE c.type WHEN 'needs' THEN 1 WHEN 'wants' THEN 2 ELSE 3 END"

MAX_AMOUNT_CENTS = 1_000_000_000  # 10,000,000.00 €
MAX_CATEGORY_NAME_LENGTH = 40
MAX_NAME_LENGTH = 100

# Helpers


def today():
    """Today's date; a function so tests can freeze it."""
    return date.today()


def get_categories(include_archived=False, keep_id=None):
    """Retrieve active categories, optionally including archived categories."""

    sql = "SELECT id, name, type, emoji, is_active FROM categories"

    params = []

    if not include_archived:
        # Since it is False by default, the 'not' makes it True, and the block executes
        sql += " WHERE is_active = 1 OR id = ?"
        params.append(keep_id if keep_id is not None else -1)
    # In practice, it returns only the active categories (id = -1, which acts as an impossible ID)

    sql += f""" ORDER BY is_active DESC, 
                {TYPE_ORDER_SQL.replace("c.type", "type")}, 
                name COLLATE NOCASE"""

    return get_db().execute(sql, params).fetchall()


def parse_expense_form(form, valid_category_ids):
    """Validate expense form data and return the parsed values and errors."""
    name = form.get("name", "").strip()
    amount_cents = eur_to_cents(form.get("amount", ""))
    category_id = form.get("category_id", type=int)
    date_text = form.get("date", "")

    # Created an empty list to store ALL the errors encountered during validation
    errors = []

    if not name:  # In Python, an empty string "" is considered false
        errors.append("Enter a name.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Name must be at most {MAX_NAME_LENGTH} characters.")

    if amount_cents is None or amount_cents <= 0:
        errors.append("Enter an amount greater than zero, using a comma for cents (e.g. 12,50).")
    elif amount_cents > MAX_AMOUNT_CENTS:
        errors.append("Amount is too large.")

    if category_id not in valid_category_ids:
        errors.append("Choose a category.")

    date_iso = None
    try:
        date_iso = datetime.strptime(date_text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        errors.append("Enter a valid date.")

    return (name, amount_cents, date_iso, category_id), errors


def like_pattern(text):
    """Escape SQL LIKE wildcards and build a partial-match pattern."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def normalize_category_name(raw):
    """Normalize a category name by trimming and collapsing whitespace."""
    return " ".join(raw.lower().split())


def back_to_categories():
    """Redirect to the categories page while preserving a valid type filter."""
    show = request.form.get("show", "")

    return redirect(url_for("manage_categories", show=show if show in VALID_TYPES else None))


def safe_next(target):
    """Validate a redirect target and prevent external redirects."""

    default = url_for("list_expenses")

    if not target:  # url
        return default

    # Split the URL into components
    parts = urlsplit(target)

    if parts.scheme or parts.netloc or parts.path != default:
        # scheme: HTTP protocol (https or http);
        # netloc: domain (e.g.: google.com);
        # path: site path (e.g.: /expenses)
        # parts.netloc rejects URLs that specify a domain, and parts.scheme that specify a protocol
        return default

    return target


def category_name_exists(db, name, exclude_id=None):
    """Check whether another category uses this name (case-insensitive)."""
    row = db.execute(
        "SELECT 1 FROM categories WHERE name = ? COLLATE NOCASE AND id != ?",
        (name, exclude_id or -1),
    ).fetchone()
    return row is not None


@app.context_processor
def inject_constants():
    """Make application constants available to all templates."""
    return {"MAX_CATEGORY_NAME_LENGTH": MAX_CATEGORY_NAME_LENGTH}


@app.route("/expenses")
def list_expenses():
    """Display expenses with the selected filters and totals."""
    db = get_db()

    current_month = today().strftime("%Y-%m")
    month = request.args.get("month")
    category_id = request.args.get("category_id", type=int)
    category_type = request.args.get("type", "")
    search_query = request.args.get("q", "").strip()

    conditions, params = [], []

    if month is None:
        month = current_month
    elif month in ("", "all"):
        month = ""
    else:
        try:
            month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        except ValueError:
            month = current_month

    if month:
        conditions.append("strftime('%Y-%m', e.date) = ?")
        params.append(month)

    if category_id:
        conditions.append("e.category_id = ?")
        params.append(category_id)

    if category_type in VALID_TYPES:
        conditions.append("c.type = ?")
        params.append(category_type)
    else:
        category_type = ""

    if search_query:
        conditions.append("e.name LIKE ? ESCAPE '\\'")
        params.append(like_pattern(search_query))

    month_links = None

    if month:
        keep = {
            key: value
            for key, value in (
                ("category_id", category_id),
                ("type", category_type),
                ("q", search_query),
            )
            if value
        }
        month_links = {
            "month": month,
            "prev_url": url_for("list_expenses", month=shift_month(month, -1), **keep),
            "next_url": url_for("list_expenses", month=shift_month(month, 1), **keep),
        }

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    expenses = db.execute(
        f""" 
        SELECT e.id, e.date, e.name, e.amount_cents,
               c.name AS category, c.emoji AS emoji, c.type
        FROM expenses e
            JOIN categories c ON c.id = e.category_id
        {where}
        ORDER BY e.date DESC, e.id DESC
        """,
        params,
    ).fetchall()
    # 'f' allows you to insert the 'where' variable into the query

    # Store months for which there are recorded expenses
    months = [
        row["month"]
        for row in db.execute(
            "SELECT DISTINCT strftime('%Y-%m', date) AS month FROM expenses ORDER BY month DESC"
        )
    ]

    if current_month not in months:
        months.insert(0, current_month)
        months.sort(reverse=True)

    return render_template(
        "index.html",
        expenses=expenses,
        total=sum(e["amount_cents"] for e in expenses),
        categories=get_categories(include_archived=True),
        months=months,
        filters={
            "month": month,
            "category_id": category_id,
            "type": category_type,
            "q": search_query,
        },
        month_links=month_links,
    )


@app.route("/expenses/new", methods=["GET", "POST"])
def new_expense():
    """Display the expense form or create a new expense."""

    categories = get_categories()

    if request.method == "POST":
        values, errors = parse_expense_form(request.form, {c["id"] for c in categories})

        if not errors:  # In Python, an empty list is considered false
            db = get_db()
            db.execute(
                "INSERT INTO expenses (name, amount_cents, date, category_id) VALUES (?, ?, ?, ?)",
                values,
            )  # No need for .fetchall() since INSERT does not return records
            db.commit()

            flash("Expense added.", "success")  # Flask's temporary messaging system

            return redirect(url_for("list_expenses"))

        for message in errors:
            flash(message, "error")

        return render_template(
            "expense_form.html",
            heading="New expense",
            categories=categories,
            form=request.form,
            back_url=url_for("list_expenses"),
        ), 400

    return render_template(
        "expense_form.html",
        heading="New expense",
        categories=categories,
        form={"date": today().isoformat()},
        back_url=url_for("list_expenses"),
    )


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    """Display the expense form or update an existing expense."""

    db = get_db()
    expense = db.execute(
        "SELECT id, name, amount_cents, date, category_id FROM expenses WHERE id = ?",
        (expense_id,),
    ).fetchone()

    if expense is None:
        abort(404)
        # Helper function used in web frameworks to halt the execution
        # and return an HTTP 404 (Not Found) error

    back_url = safe_next(request.args.get("next"))

    categories = get_categories(keep_id=expense["category_id"])

    if request.method == "POST":
        values, errors = parse_expense_form(request.form, {c["id"] for c in categories})

        if not errors:
            db.execute(
                "UPDATE expenses SET name = ?, amount_cents = ?, date = ?, "
                "category_id = ? WHERE id = ?",
                (*values, expense_id),
            )
            db.commit()

            flash("Expense updated.", "success")

            return redirect(back_url)

        for message in errors:
            flash(message, "error")

        return render_template(
            "expense_form.html",
            heading="Edit expense",
            categories=categories,
            form=request.form,
            back_url=back_url,
        ), 400

    form = {
        "name": expense["name"],
        "amount": cents_to_eur(expense["amount_cents"]).removesuffix(" €"),
        "date": expense["date"],
        "category_id": expense["category_id"],
    }

    return render_template(
        "expense_form.html",
        heading="Edit expense",
        categories=categories,
        form=form,
        back_url=back_url,
    )


@app.post("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):
    """Delete an expense and redirect to the previous page."""

    db = get_db()
    cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()

    if cursor.rowcount == 0:
        abort(404)

    flash("Expense deleted.", "success")

    return redirect(safe_next(request.args.get("next")))


@app.route("/", methods=["GET", "POST"])
def summary():
    """Display the monthly spending summary and manage income."""

    db = get_db()

    # The user can choose which month they wish to view
    # If none is selected, the system automatically displays the current month
    month = request.values.get("month") or today().strftime("%Y-%m")

    try:
        month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        # ensuring that the received month has a valid format
    except ValueError:
        abort(400)

    if request.method == "POST":
        income_cents = eur_to_cents(request.form.get("income", ""))

        if income_cents is None or not 0 <= income_cents <= MAX_AMOUNT_CENTS:
            flash("Enter a valid income (e.g. 1.000,00).", "error")

        else:
            db.execute(
                "INSERT INTO budgets (month, income_cents) VALUES (?, ?) "
                "ON CONFLICT(month) DO UPDATE "
                "SET income_cents = excluded.income_cents",
                (month, income_cents),
            )
            # 'excluded' is a special SQLite reference to the value that
            # was attempted to be inserted but could not be, due to a conflict

            db.commit()

            flash("Income saved.", "success")

        return redirect(url_for("summary", month=month))

    budget = db.execute(
        "SELECT income_cents FROM budgets WHERE month = ?",
        (month,),  # single-value tuple
    ).fetchone()

    income = budget["income_cents"] if budget else None

    category_totals = db.execute(
        """
        SELECT c.name, c.emoji, c.type, COALESCE(SUM(e.amount_cents), 0) AS total
        FROM categories c
        LEFT JOIN expenses e 
               ON e.category_id = c.id AND strftime('%Y-%m', e.date) = ?
        GROUP BY c.id
        ORDER BY c.type, total DESC, c.name COLLATE NOCASE
        """,
        (month,),
    ).fetchall()
    # Use LEFT JOIN to also get categories without expenses
    # Use COALESCE to substitute NULL values to 0,
    # as a category with no expenses returns NULL when attempting to do the SUM

    # Store the total spent by category type (needs/wants)
    spent = {}

    for row in category_totals:
        spent[row["type"]] = spent.get(row["type"], 0) + row["total"]

    total_spent = sum(spent.values())

    # Budget cards
    cards = build_cards(income, spent)

    month_links = {
        "month": month,
        "prev_url": url_for("summary", month=shift_month(month, -1)),
        "next_url": url_for("summary", month=shift_month(month, 1)),
    }

    return render_template(
        "summary.html",
        month=month,
        income=income,
        income_value=(cents_to_eur(income).removesuffix(" €") if income is not None else ""),
        cards=cards,
        total_spent=total_spent,
        breakdown=[r for r in category_totals if r["total"] > 0],
        # So as to not display categories with zero spending
        month_links=month_links,
    )


@app.get("/summary")
def summary_legacy():
    """Old URL of the summary; it moved to the home page."""
    return redirect(url_for("summary", **request.args.to_dict()), code=301)


@app.get("/suggest-category")
def suggest_category():
    """Return the category most often used with this expense name, as JSON."""

    name = request.args.get("name", "").strip()

    if not name:
        return jsonify(suggestion=None)

    category_row = (
        get_db()
        .execute(
            """
        SELECT c.id, c.name, c.emoji, c.type
        FROM expenses e
            JOIN categories c ON c.id = e.category_id
        WHERE lower(e.name) = lower(?)
        GROUP BY c.id
        ORDER BY COUNT(*) DESC, MAX(e.date) DESC
        LIMIT 1
        """,
            (name,),
        )
        .fetchone()
    )
    # ORDER BY COUNT(*) causes the most frequently used category to appear as a suggestion
    # If two categories have the exact same number of occurrences,
    # they are sorted by the most recent date (MAX(e.date))
    # LIMIT 1 ensures that only one suggestion is returned

    if category_row is None:
        return jsonify(suggestion=None)

    return jsonify(
        suggestion={
            "id": category_row["id"],
            "name": category_row["name"].capitalize(),
            "emoji": category_row["emoji"],
            "type": category_row["type"],
        }
    )


@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    """Display categories or create a new category."""
    db = get_db()
    if request.method == "POST":
        name = normalize_category_name(request.form.get("name", ""))
        category_type = request.form.get("type", "")
        emoji = request.form.get("emoji", "").strip() or DEFAULT_EMOJI
        emoji_problem = emoji_error(emoji)

        error = None
        if not name:
            error = "Enter a category name."
        elif len(name) > MAX_CATEGORY_NAME_LENGTH:
            error = "Category name must be at most 40 characters."
        elif category_type not in VALID_TYPES:
            error = "Choose a type."
        elif emoji_problem:
            error = emoji_problem
        elif category_name_exists(db, name):
            error = "That category already exists."

        if error:
            flash(error, "error")
            return back_to_categories()

        db.execute(
            "INSERT INTO categories (name, type, emoji) VALUES (?, ?, ?)",
            (name, category_type, emoji),
        )
        db.commit()
        flash("Category added.", "success")
        return redirect(url_for("manage_categories", show=category_type))  # show where it landed

    show = request.args.get("show", "")
    if show not in VALID_TYPES:
        show = ""
    where, params = ("WHERE c.type = ?", (show,)) if show else ("", ())

    categories = db.execute(
        f"""
        SELECT c.id, c.name, c.emoji, c.type, c.is_active, COUNT(e.id) AS uses
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id
        {where}
        GROUP BY c.id
        ORDER BY c.is_active DESC, {TYPE_ORDER_SQL}, c.name COLLATE NOCASE
        """,
        params,
    ).fetchall()
    return render_template("categories.html", categories=categories, selected=show)


@app.post("/categories/<int:category_id>/edit")
def edit_category(category_id):
    """Change a category's name and/or emoji."""

    db = get_db()

    category = db.execute(
        "SELECT name, emoji FROM categories WHERE id = ?", (category_id,)
    ).fetchone()

    if category is None:
        abort(404)

    name = normalize_category_name(request.form.get("name", ""))
    emoji = request.form.get("emoji", "").strip() or category["emoji"]
    emoji_problem = None if emoji == category["emoji"] else emoji_error(emoji)

    if not name or len(name) > MAX_CATEGORY_NAME_LENGTH:
        flash(f"Enter a name of up to {MAX_CATEGORY_NAME_LENGTH} characters.", "error")

    elif name.casefold() == category["name"].casefold() and emoji == category["emoji"]:
        flash("No changes to save.", "info")

    elif name.casefold() != category["name"].casefold() and category_name_exists(
        db, name, category_id
    ):
        flash("That category already exists.", "error")

    elif emoji_problem:
        flash(emoji_error(emoji), "error")

    else:
        db.execute(
            "UPDATE categories SET name = ?, emoji = ? WHERE id = ?", (name, emoji, category_id)
        )
        db.commit()

        flash("Category updated.", "success")

    return back_to_categories()


@app.post("/categories/<int:category_id>/toggle")
def toggle_category(category_id):
    """Activate or archive a category."""

    db = get_db()

    cursor = db.execute(
        "UPDATE categories SET is_active = 1 - is_active WHERE id = ?", (category_id,)
    )
    db.commit()

    if cursor.rowcount == 0:
        abort(404)

    flash("Category updated.", "success")

    return back_to_categories()


@app.after_request
def set_security_headers(response):
    """Add security-related HTTP headers to every response."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    # prevents the browser from “guessing” a content type different from the one declared
    response.headers.setdefault("X-Frame-Options", "DENY")
    # prevents another site from placing your app and trick the user into clicking
    response.headers.setdefault("Referrer-Policy", "same-origin")
    # only sends the source address when navigating within the site itself
    return response

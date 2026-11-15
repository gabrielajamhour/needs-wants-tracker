import os

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

from datetime import date, datetime
from urllib.parse import urlsplit

# Imports from other files in the project
from db import DEFAULT_DB_PATH, close_db, get_db
from helpers import cents_to_eur, eur_to_cents

app = Flask(__name__)
app.config["DATABASE"] = DEFAULT_DB_PATH

app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me") # Temporary key
app.teardown_appcontext(close_db) # Close connection when context finishes
app.add_template_filter(cents_to_eur, "eur") # Simplify function usage

# Types of expenses
VALID_TYPES = {"needs", "wants", "savings"}

# 50/30/20 Rule
SPLIT = (
    ("needs", "Needs", 50, True),
    ("wants", "Wants", 30, True),
    ("savings", "Savings", 20, False),
)

# Custom order for category types
TYPE_ORDER_SQL = "CASE c.type WHEN 'needs' THEN 1 WHEN 'wants' THEN 2 ELSE 3 END"

# Helpers

def get_categories(include_archived=False, keep_id=None):
    """Active categories; optionally all, or active plus one specific id."""

    sql = "SELECT id, name, type, is_active FROM categories"

    params = []

    if not include_archived: # Since it is False by default, the 'not' makes it True, and the block executes
        sql += " WHERE is_active = 1 OR id = ?"
        params.append(keep_id if keep_id is not None else -1)
    # In practice, it returns only the active categories (id = -1, which acts as an impossible ID)

    sql += f" ORDER BY is_active DESC, {TYPE_ORDER_SQL.replace('c.type', 'type')}, name COLLATE NOCASE"

    return get_db().execute(sql, params).fetchall()


def parse_expense_form(form, valid_category_ids):
    """Validate the expense form; return ((name, cents, date, category_id), errors)."""
    name = request.form.get("name", "").strip()
    amount_cents = eur_to_cents(request.form.get("amount", ""))
    category_id = request.form.get("category_id", type=int)
    date_text = request.form.get("date", "")

    # Created an empty list to store ALL the errors encountered during validation
    errors = []

    if not name: # In Python, an empty string "" is considered false
        errors.append("Enter a name.")

    if amount_cents is None or amount_cents <= 0:
        errors.append("Enter an amount greater than zero, using a comma for cents (e.g. 12,50).")

    if category_id not in valid_category_ids:
        errors.append("Choose a category.")

    date_iso = None
    try:
        date_iso = datetime.strptime(date_text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        errors.append("Enter a valid date.")

    return (name, amount_cents, date_iso, category_id), errors

def like_pattern(text):
    """Escape LIKE wildcards so user input is matched literally."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"

def normalize_category_name(raw):
    """Trim, collapse inner spaces and lowercase: '  Dining   OUT ' -> 'dining out'."""
    return " ".join(raw.lower().split())

def back_to_categories():
    """Redirect to the categories page, keeping the type filter if it is valid."""
    show = request.form.get("show", "")

    return redirect(url_for("manage_categories", show=show if show in VALID_TYPES else None))

def safe_next(target):
    """Return target only if it is a local link to the expense list; otherwise the plain list URL."""

    default = url_for("index")

    if not target: # url
        return default

    # Split the URL into components
    parts = urlsplit(target)

    if parts.scheme or parts.netloc or parts.path != default:
    # scheme: HTTP protocol (https or http); netloc: domain (e.g., google.com); path: site path (e.g., /expenses)
    # parts.netloc rejects URLs that specify a domain, and parts.scheme rejects URLs that specify a protocol
        return default
    
    return target


@app.route("/")
def index():
    db = get_db()

    month = request.args.get("month", "")
    category_id = request.args.get("category_id", type=int)
    kind = request.args.get("type", "")
    query = request.args.get("q", "").strip()

    # Store the conditions in WHERE and the values ​​corresponding to each condition
    conditions, params = [], []

    if month:
        try:
            month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        except ValueError:
            month = ""
        else:
            conditions.append("strftime('%Y-%m', e.date) = ?")
            params.append(month)

    if category_id:
        conditions.append("e.category_id = ?")
        params.append(category_id)

    if kind in VALID_TYPES:
        conditions.append("c.type = ?")
        params.append(kind)
    else:
        kind = ""

    if query:
        conditions.append("e.name LIKE ? ESCAPE '\\'")
        params.append(like_pattern(query))

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    expenses = db.execute(
        f""" 
        SELECT e.id, e.date, e.name, e.amount_cents,
               c.name AS category, c.type
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
            "SELECT DISTINCT strftime('%Y-%m', date) AS month "
            "FROM expenses ORDER BY month DESC"
        )
    ]

    return render_template(
        "index.html",
        expenses=expenses,
        total=sum(e["amount_cents"] for e in expenses),
        categories=get_categories(include_archived=True),
        months=months,
        filters={"month": month, "category_id": category_id, "type": kind, "q": query},
    )

@app.route("/expenses/new", methods=["GET", "POST"])
def new_expense():

    categories = get_categories()

    if request.method == "POST":

        values, errors = parse_expense_form(request.form, {c["id"] for c in categories})

        if not errors: # In Python, an empty list is considered false
            db = get_db()
            db.execute(
                "INSERT INTO expenses (name, amount_cents, date, category_id) "
                "VALUES (?, ?, ?, ?)",
                values,
            ) # No need for .fetchall() since INSERT does not return records
            db.commit()

            flash("Expense added.", "success") # Flask's temporary messaging system

            return redirect(url_for("index"))
        
        for message in errors:
            flash(message, "error")

        return render_template(
            "expense_form.html", heading="New expense",
            categories=categories, form=request.form,
            back_url=url_for("index"),
        ), 400

    # request.method == "GET"
    return render_template(
        "expense_form.html", heading="New expense",
        categories=categories, form={"date": date.today().isoformat()},
        back_url=url_for("index"),
    )


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):

    db = get_db()
    expense = db.execute(
        "SELECT id, name, amount_cents, date, category_id FROM expenses WHERE id = ?",
        (expense_id,),
    ).fetchone()

    if expense is None:
        abort(404) # Helper function used in web frameworks to halt the execution and return an HTTP 404 (Not Found) error

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
            "expense_form.html", heading="Edit expense",
            categories=categories, form=request.form,
            back_url=back_url,
        ), 400

    # request.method == "GET"
    form = {
        "name": expense["name"],
        "amount": cents_to_eur(expense["amount_cents"]).removesuffix(" €"), # Saving without changing anyting doesn't change the amount
        "date": expense["date"],
        "category_id": expense["category_id"],
    }

    return render_template(
        "expense_form.html", heading="Edit expense",
        categories=categories, form=form,
        back_url=back_url,
    )

@app.post("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):

    db = get_db()
    cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()

    if cursor.rowcount == 0:
        abort(404)

    flash("Expense deleted.", "success")

    return redirect(safe_next(request.args.get("next")))

@app.route("/summary", methods=["GET", "POST"])
def summary():

    db = get_db()

    # The user can choose which month they wish to view
    # If none is selected, the system automatically displays the current month
    month = request.values.get("month") or date.today().strftime("%Y-%m")

    try:
        month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m") # ensuring that the received month has a valid format
    except ValueError:
        abort(400)

    if request.method == "POST":

        income_cents = eur_to_cents(request.form.get("income", ""))

        if income_cents is None or income_cents < 0:
            flash("Enter a valid income (e.g. 1.000,00).", "error")

        else:
            db.execute(
                "INSERT INTO budgets (month, income_cents) VALUES (?, ?) "
                "ON CONFLICT(month) DO UPDATE " 
                    "SET income_cents = excluded.income_cents",
                (month, income_cents),
            )
            # 'excluded' is a special SQLite reference to the value that was attempted to be inserted but could not be, due to a conflict

            db.commit()

            flash("Income saved.", "success")

        return redirect(url_for("summary", month=month))

    # request.method == "GET"
    budget = db.execute(
        "SELECT income_cents FROM budgets WHERE month = ?", (month,) # single-value tuple
    ).fetchone()

    income = budget["income_cents"] if budget else None

    rows = db.execute(
        """
        SELECT c.name, c.type, COALESCE(SUM(e.amount_cents), 0) AS total
        FROM categories c
        LEFT JOIN expenses e 
               ON e.category_id = c.id AND strftime('%Y-%m', e.date) = ?
        GROUP BY c.id
        ORDER BY c.type, total DESC, c.name COLLATE NOCASE
        """,
        (month,),
    ).fetchall()
    # Use LEFT JOIN to also get categories without expenses
    # Use COALESCE to substitute NULL values to 0, as a category with no expenses returns NULL when attempting to do the SUM

    # Store the total spent by category type (needs/wants)
    spent = {}

    for row in rows:
        spent[row["type"]] = spent.get(row["type"], 0) + row["total"]

    total_spent = sum(spent.values())

    # Budget cards
    cards = []

    for kind, label, pct, is_cap in SPLIT: # type identifier, name to be displayed on the card, percentage allocated to that type

        limit = income * pct // 100 if income is not None else None

        total = spent.get(kind, 0)

        cards.append({
            "label": label,
            "pct": pct,
            "limit": limit,
            "spent": total,
            "is_cap": is_cap,
            "used": round(total * 100 / limit) if limit else None,
            "over": is_cap and bool(limit) and total > limit,
    })

    return render_template(
        "summary.html",
        month=month,
        income=income,
        income_value=(cents_to_eur(income).removesuffix(" €") if income is not None else ""),
        cards=cards,
        total_spent=total_spent,
        breakdown=[r for r in rows if r["total"] > 0], # So as to not display categories with zero spending
    )

@app.get("/suggest-category")
def suggest_category():
    """Return the category most often used with this expense name, as JSON."""

    name = request.args.get("name", "").strip()

    if not name:
        return jsonify(suggestion=None)

    row = get_db().execute(
        """
        SELECT c.id, c.name, c.type
        FROM expenses e
            JOIN categories c ON c.id = e.category_id
        WHERE lower(e.name) = lower(?)
        GROUP BY c.id
        ORDER BY COUNT(*) DESC, MAX(e.date) DESC
        LIMIT 1
        """,
        (name,),
    ).fetchone()
    # ORDER BY COUNT(*) causes the most frequently used category to appear as a suggestion
    # If two categories have the exact same number of occurrences, they are sorted by the most recent date (MAX(e.date))
    # LIMIT 1 ensures that only one suggestion is returned

    if row is None:
        return jsonify(suggestion=None)
    
    return jsonify(
        suggestion={"id": row["id"], "name": row["name"].capitalize(), "type": row["type"]}
    )

@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    db = get_db()
    if request.method == "POST":
        name = normalize_category_name(request.form.get("name", ""))
        kind = request.form.get("type", "")

        error = None
        if not name:
            error = "Enter a category name."
        elif len(name) > 40:
            error = "Category name must be at most 40 characters."
        elif kind not in VALID_TYPES:
            error = "Choose a type."
        elif db.execute("SELECT 1 FROM categories WHERE name = ? COLLATE NOCASE", (name,)).fetchone():
            error = "That category already exists."

        if error:
            flash(error, "error")
            return back_to_categories()

        db.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, kind))
        db.commit()
        flash("Category added.", "success")
        return redirect(url_for("manage_categories", show=kind))  # show where it landed

    show = request.args.get("show", "")
    if show not in VALID_TYPES:
        show = ""
    where, params = ("WHERE c.type = ?", (show,)) if show else ("", ())

    rows = db.execute(
        f"""
        SELECT c.id, c.name, c.type, c.is_active, COUNT(e.id) AS uses
        FROM categories c
        LEFT JOIN expenses e ON e.category_id = c.id
        {where}
        GROUP BY c.id
        ORDER BY c.is_active DESC, {TYPE_ORDER_SQL}, c.name COLLATE NOCASE
        """,
        params,
    ).fetchall()
    return render_template("categories.html", categories=rows, selected=show)

@app.post("/categories/<int:category_id>/rename")
def rename_category(category_id):

    db = get_db()

    # Checks whether the category exists in the database
    category = db.execute(
        "SELECT name FROM categories WHERE id = ?", (category_id,)
    ).fetchone()

    if category is None:
        abort(404)

    name = normalize_category_name(request.form.get("name", ""))

    if not name or len(name) > 40:
        flash("Enter a name of up to 40 characters.", "error")

    elif name.casefold() == category["name"].casefold():
        flash("The name was not changed.", "info")

    elif db.execute(
        "SELECT 1 FROM categories WHERE name = ? COLLATE NOCASE AND id != ?", (name, category_id)
    ).fetchone():
        flash("That category already exists.", "error")

    else:
        db.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
        db.commit()

        flash("Category renamed.", "success")

    return back_to_categories()

@app.post("/categories/<int:category_id>/toggle")
def toggle_category(category_id):

    db = get_db()

    cursor = db.execute(
        "UPDATE categories SET is_active = 1 - is_active WHERE id = ?", (category_id,)
    )
    db.commit()

    if cursor.rowcount == 0:
        abort(404)

    flash("Category updated.", "success")

    return back_to_categories()
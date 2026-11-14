import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from datetime import date, datetime

# Imports from other files in the project
from db import close_db, get_db
from helpers import cents_to_eur, eur_to_cents

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me") # Temporary key
app.teardown_appcontext(close_db) # Close connection when context finishes
app.add_template_filter(cents_to_eur, "eur") # Simplify function usage

# 50/30/20 Rule
SPLIT = (("needs", "Needs", 50), ("wants", "Wants", 30))

# Helpers

def get_categories():
    return get_db().execute(
        "SELECT id, name, type FROM categories ORDER BY type, name"
    ).fetchall()


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


@app.route("/")
def index():

    expenses = get_db().execute(
        """
        SELECT e.id, e.date, e.name, e.amount_cents,
               c.name AS category, c.type
        FROM expenses e
            JOIN categories c ON c.id = e.category_id
        ORDER BY e.date DESC, e.id DESC
        """
    ).fetchall()

    return render_template("index.html", expenses=expenses)

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
        ), 400

    # request.method == "GET"
    return render_template(
        "expense_form.html", heading="New expense",
        categories=categories, form={"date": date.today().isoformat()},
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

    categories = get_categories()

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

            return redirect(url_for("index"))
        
        for message in errors:
            flash(message, "error")

        return render_template(
            "expense_form.html", heading="Edit expense",
            categories=categories, form=request.form,
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
    )


@app.post("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):

    db = get_db()
    cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()

    if cursor.rowcount == 0:
        abort(404)

    flash("Expense deleted.", "success")

    return redirect(url_for("index"))

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
        ORDER BY c.type, total DESC, c.name
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

    for kind, label, pct in SPLIT: # type identifier, name to be displayed on the card, percentage allocated to that type

        limit = income * pct // 100 if income is not None else None

        total = spent.get(kind, 0)

        cards.append({
            "label": label,
            "pct": pct,
            "limit": limit,
            "spent": total,
            "used": round(total * 100 / limit) if limit else None,
            "over": bool(limit) and total > limit,
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
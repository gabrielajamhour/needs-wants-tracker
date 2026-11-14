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
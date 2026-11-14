import os

from flask import Flask, flash, redirect, render_template, request, url_for

from datetime import date, datetime

# Imports from other files in the project
from db import close_db, get_db
from helpers import cents_to_eur, eur_to_cents

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me") # Temporary key
app.teardown_appcontext(close_db) # Close connection when context finishes
app.add_template_filter(cents_to_eur, "eur") # Simplify function usage


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

    db = get_db()

    categories = db.execute(
        """SELECT id, name, type 
        FROM categories 
        ORDER BY type, name"""
    ).fetchall() # Retrieve all the rows found

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        amount_cents = eur_to_cents(request.form.get("amount", ""))
        category_id = request.form.get("category_id", type=int)
        date_text = request.form.get("date", "")

        # Created an empty list to store ALL the errors encountered during validation
        errors = []

        if not name: # In Python, an empty string "" is considered false
            errors.append("Enter a name.")

        if amount_cents is None or amount_cents <= 0:
            errors.append("Enter an amount greater than zero, using a comma for the cents (e.g., 12,50).")

        if category_id not in {c["id"] for c in categories}:
                    errors.append("Choose a category.")

        try:
            date_iso = datetime.strptime(date_text, "%Y-%m-%d").date().isoformat()
        except ValueError:
            errors.append("Enter a valid date.")

        if errors: # In Python, an empty list is considered false
            for message in errors:
                flash(message, "error") # Flask's temporary messaging system
            return render_template("expense_form.html", categories=categories, form=request.form), 400

        db.execute(
            "INSERT INTO expenses (name, amount_cents, date, category_id) "
            "VALUES (?, ?, ?, ?)",
            (name, amount_cents, date_iso, category_id),
        ) # No need for .fetchall() since INSERT does not return records
        db.commit()

        flash("Expense added.", "success")
        return redirect(url_for("index"))

    # request.method == "GET"
    return render_template(
        "expense_form.html",
        categories=categories,
        form={"date": date.today().isoformat()},
    )
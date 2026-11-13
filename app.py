import os

from flask import Flask, render_template

# Imports from other files in the project
from db import close_db, get_db
from helpers import cents_to_eur

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
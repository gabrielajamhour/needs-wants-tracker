import sqlite3
from pathlib import Path

import pytest

from app import app as flask_app
from db import get_db

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def app(tmp_path):
    """Configure the Flask app with a fresh temporary database for each test."""

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)

    conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed.sql").read_text(encoding="utf-8"))

    conn.close()

    flask_app.config.update(DATABASE=db_path, TESTING=True)

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def db_rows(app):
    """Run a query against the test database and return the rows."""

    def run(sql, params=()):
        """Execute a SQL query and return all matching rows."""
        with app.app_context():
            return get_db().execute(sql, params).fetchall()

    return run


@pytest.fixture
def category_id(db_rows):
    """Provide a helper to retrieve category IDs by name."""

    def find(name):
        """Return the ID of a category matching the given name."""
        return db_rows("SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,))[0]["id"]

    return find


@pytest.fixture
def add_expense(client, category_id):
    """Create an expense through the real form route."""

    def add(name="Mercado", amount="3,58", date="2026-11-11", category="groceries"):
        """Submit an expense using the provided form data."""
        return client.post(
            "/expenses/new",
            data={
                "name": name,
                "amount": amount,
                "date": date,
                "category_id": category_id(category),
            },
        )

    return add

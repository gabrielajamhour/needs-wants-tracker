import sqlite3
from pathlib import Path

import pytest

from app import app as flask_app

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def app(tmp_path):
    """The Flask app pointed at a fresh temporary database for each test."""

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)

    conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed.sql").read_text(encoding="utf-8"))

    conn.close()

    flask_app.config.update(DATABASE=db_path, TESTING=True)
    
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
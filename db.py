# Connection between Flask application and the SQLite database

import sqlite3
from pathlib import Path

from flask import current_app, g # 'g' is a special object provided by Flask for storing temporary information 
                                 # during the processing of a request or an application context.

BASE = Path(__file__).parent
DEFAULT_DB_PATH = BASE / "instance" / "tracker.db"

# Open connection
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"]) # Establish the connection to the database
        g.db.row_factory = sqlite3.Row # Access the values ​​either by index or by column name 
                                       # (e.g. {"id": 1, "name": "Rent", "type": "needs"} instead of [(1, "Rent", "needs")])
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

# Close connection
def close_db(error=None):
    db = g.pop("db", None) # Look for a property called db within g; if it doesn't exist, return None
    if db is not None: # If it exists, close connection
        db.close()
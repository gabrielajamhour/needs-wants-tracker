import sqlite3
from pathlib import Path # Makes working with file paths and directories easier 

BASE = Path(__file__).parent # Returns the directory that contains the file 
DB = BASE / "instance" / "tracker.db"
    # instance: directory where the database will be stored 
    # tracker.db: name of the database file 

DB.parent.mkdir(parents=True, exist_ok=True) # Creates directory instance 
with sqlite3.connect(DB) as conn: # Connects to SQLite and runs the SQL files
    conn.executescript((BASE / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((BASE / "seed.sql").read_text(encoding="utf-8"))

print("Database created in ", DB)
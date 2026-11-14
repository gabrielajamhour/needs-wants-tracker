PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE,
    type  TEXT NOT NULL CHECK (type IN ('needs', 'wants', 'savings')),
    is_active  INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS expenses (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents > 0), /* Store values ​​in cents to avoid precision issues */ 
    date          TEXT NOT NULL
                  CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'), /* Check if it matches the standard */ 
    category_id   INTEGER NOT NULL
                  REFERENCES categories (id) ON DELETE RESTRICT /* Prevent a category from being deleted */ 
);

CREATE TABLE IF NOT EXISTS budgets (
    id            INTEGER PRIMARY KEY,
    month         TEXT NOT NULL UNIQUE
                  CHECK (month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'),
    income_cents  INTEGER NOT NULL CHECK (income_cents >= 0)
);

/* An index is a data structure that allows a database to locate records more quickly, without needing to scan the entire table. */
CREATE INDEX IF NOT EXISTS idx_expenses_date     ON expenses (date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_name     ON expenses (name);
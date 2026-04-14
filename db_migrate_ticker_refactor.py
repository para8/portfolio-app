"""
One-time migration: remove ticker text field, rename display_name → short_name,
switch Transaction and Price to use ticker_id (int FK) instead of ticker (text).

Usage:
    python db_migrate_ticker_refactor.py          # dry-run (prints SQL, no changes)
    python db_migrate_ticker_refactor.py --apply  # execute against live DB

Run this BEFORE deploying the updated application code.
Safe to inspect first: without --apply nothing is written.
"""

import sys
import os

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DRY_RUN = "--apply" not in sys.argv

DATABASE_URL = os.environ["DATABASE_URL"]

STEPS = [
    # ── 1. Rename display_name → short_name on tickers ────────────────────────
    ("Rename tickers.display_name → short_name",
     "ALTER TABLE tickers RENAME COLUMN display_name TO short_name"),

    # ── 2. transactions: add ticker_id, populate, NOT NULL, drop ticker ────────
    ("Add transactions.ticker_id column",
     "ALTER TABLE transactions ADD COLUMN ticker_id INTEGER"),

    ("Populate transactions.ticker_id from tickers join",
     """
     UPDATE transactions t
       SET ticker_id = tk.id
       FROM tickers tk
       WHERE tk.user_id = t.user_id AND tk.ticker = t.ticker
     """),

    ("Verify no NULL ticker_id in transactions — will raise if any orphans",
     """
     DO $$
     BEGIN
       IF EXISTS (SELECT 1 FROM transactions WHERE ticker_id IS NULL) THEN
         RAISE EXCEPTION 'transactions has rows with NULL ticker_id — orphaned ticker references exist';
       END IF;
     END $$
     """),

    ("Set transactions.ticker_id NOT NULL",
     "ALTER TABLE transactions ALTER COLUMN ticker_id SET NOT NULL"),

    ("Drop transactions.ticker column",
     "ALTER TABLE transactions DROP COLUMN ticker"),

    # ── 3. prices: add ticker_id, populate, drop ticker, fix constraint ────────
    ("Add prices.ticker_id column",
     "ALTER TABLE prices ADD COLUMN ticker_id INTEGER"),

    ("Populate prices.ticker_id from tickers join",
     """
     UPDATE prices p
       SET ticker_id = tk.id
       FROM tickers tk
       WHERE tk.user_id = p.user_id AND tk.ticker = p.ticker
     """),

    ("Drop prices.ticker column",
     "ALTER TABLE prices DROP COLUMN ticker"),

    ("Drop old prices unique constraint (user_id, ticker)",
     "ALTER TABLE prices DROP CONSTRAINT IF EXISTS prices_user_ticker_key"),

    ("Add new prices unique constraint (user_id, ticker_id)",
     "ALTER TABLE prices ADD CONSTRAINT prices_user_ticker_id_key UNIQUE (user_id, ticker_id)"),

    # ── 4. tickers: drop ticker column, swap unique constraint ─────────────────
    ("Drop old tickers unique constraint (user_id, ticker)",
     "ALTER TABLE tickers DROP CONSTRAINT IF EXISTS tickers_user_ticker_key"),

    ("Drop tickers.ticker column",
     "ALTER TABLE tickers DROP COLUMN ticker"),

    ("Add new tickers unique constraint (user_id, name)",
     "ALTER TABLE tickers ADD CONSTRAINT tickers_user_name_key UNIQUE (user_id, name)"),
]


def run():
    engine = create_engine(DATABASE_URL)

    if DRY_RUN:
        print("=== DRY RUN — no changes will be made ===")
        print("Run with --apply to execute.\n")
        for label, sql in STEPS:
            print(f"  [{label}]")
            print(f"  {sql.strip()}\n")
        return

    print("=== APPLYING MIGRATION ===\n")
    with engine.begin() as conn:
        for label, sql in STEPS:
            print(f"  → {label} ...", end=" ", flush=True)
            conn.execute(text(sql.strip()))
            print("OK")

    print("\nMigration complete.")

    # Print post-migration row counts for sanity check
    with engine.connect() as conn:
        for table in ("tickers", "transactions", "prices"):
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table}: {count} rows")


if __name__ == "__main__":
    run()

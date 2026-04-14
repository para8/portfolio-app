"""
Migration v2: add price_history table, symbol column on tickers, drop user_id from fx_history.

Usage:
    python db_migrate_v2_price_history.py          # dry-run (prints SQL, no changes)
    python db_migrate_v2_price_history.py --apply  # execute against live DB

Run BEFORE deploying the updated application code.
"""

import sys
import os

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DRY_RUN = "--apply" not in sys.argv

DATABASE_URL = os.environ["DATABASE_URL"]

STEPS = [
    # ── 1. Add symbol column to tickers (nullable) ────────────────────────────
    ("Add tickers.symbol column",
     "ALTER TABLE tickers ADD COLUMN IF NOT EXISTS symbol TEXT"),

    # ── 2. Create price_history table ─────────────────────────────────────────
    ("Create price_history table",
     """
     CREATE TABLE IF NOT EXISTS price_history (
         id          SERIAL PRIMARY KEY,
         symbol      TEXT NOT NULL,
         granularity TEXT NOT NULL,
         date        TEXT NOT NULL,
         close       FLOAT,
         high        FLOAT,
         low         FLOAT,
         open        FLOAT,
         source      TEXT,
         fetched_at  TEXT,
         CONSTRAINT price_history_symbol_gran_date_key UNIQUE (symbol, granularity, date)
     )
     """),

    # ── 3. Drop user_id from fx_history ───────────────────────────────────────
    ("Drop fx_history.user_id column",
     "ALTER TABLE fx_history DROP COLUMN IF EXISTS user_id"),
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

    # Post-migration sanity check
    with engine.connect() as conn:
        for table in ("tickers", "price_history", "fx_history"):
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table}: {count} rows")


if __name__ == "__main__":
    run()

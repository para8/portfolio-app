"""
One-time migration: SQLite (portfolio.db) → Supabase (Postgres).

Usage:
    python migrate.py

Requires DATABASE_URL set in environment (or .env file).
Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING.
"""

import os
import sqlite3

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import models

SQLITE_PATH = os.environ.get("SQLITE_PATH", "portfolio.db")


def migrate():
    # ── Source: SQLite ────────────────────────────────────────────────────────
    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f"SQLite file not found: {SQLITE_PATH}")
    src = sqlite3.connect(SQLITE_PATH)
    src.row_factory = sqlite3.Row

    # ── Target: Supabase (Postgres) ───────────────────────────────────────────
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)
    models.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    dst = Session()

    totals = {}

    # Helper: fetch all rows from SQLite table
    def fetch(table):
        return [dict(r) for r in src.execute(f"SELECT * FROM {table}").fetchall()]

    # ── categories ────────────────────────────────────────────────────────────
    rows = fetch("categories")
    if rows:
        dst.execute(
            text("""
                INSERT INTO categories (id, name, color)
                VALUES (:id, :name, :color)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["categories"] = len(rows)

    # ── sectors ───────────────────────────────────────────────────────────────
    rows = fetch("sectors")
    if rows:
        dst.execute(
            text("""
                INSERT INTO sectors (id, name, color)
                VALUES (:id, :name, :color)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["sectors"] = len(rows)

    # ── brokers ───────────────────────────────────────────────────────────────
    rows = fetch("brokers")
    if rows:
        dst.execute(
            text("""
                INSERT INTO brokers (id, name)
                VALUES (:id, :name)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["brokers"] = len(rows)

    # ── tickers ───────────────────────────────────────────────────────────────
    rows = fetch("tickers")
    if rows:
        dst.execute(
            text("""
                INSERT INTO tickers (ticker, name, currency, category_id, sector_id, created_at)
                VALUES (:ticker, :name, :currency, :category_id, :sector_id, :created_at)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["tickers"] = len(rows)

    # ── transactions ──────────────────────────────────────────────────────────
    rows = fetch("transactions")
    if rows:
        dst.execute(
            text("""
                INSERT INTO transactions (id, date, ticker, type, units, price, amount, broker_id, created_at)
                VALUES (:id, :date, :ticker, :type, :units, :price, :amount, :broker_id, :created_at)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["transactions"] = len(rows)

    # ── prices ────────────────────────────────────────────────────────────────
    rows = fetch("prices")
    if rows:
        dst.execute(
            text("""
                INSERT INTO prices (ticker, price, updated_at)
                VALUES (:ticker, :price, :updated_at)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["prices"] = len(rows)

    # ── fx_history ────────────────────────────────────────────────────────────
    rows = fetch("fx_history")
    if rows:
        dst.execute(
            text("""
                INSERT INTO fx_history (id, from_ym, rate)
                VALUES (:id, :from_ym, :rate)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["fx_history"] = len(rows)

    # ── config ────────────────────────────────────────────────────────────────
    rows = fetch("config")
    if rows:
        dst.execute(
            text("""
                INSERT INTO config (key, value, updated_at)
                VALUES (:key, :value, :updated_at)
                ON CONFLICT DO NOTHING
            """),
            rows,
        )
    totals["config"] = len(rows)

    dst.commit()
    dst.close()
    src.close()

    print("Migration complete. Rows processed (ON CONFLICT DO NOTHING):")
    for table, count in totals.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    migrate()

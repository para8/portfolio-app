"""
Migration v3: Normalize all monthly price_history dates to first-of-month (YYYY-MM-01).

Previously, Alpha Vantage records used the last trading day of the month as the date
(e.g. 2024-01-31). This migration aligns them to 2024-01-01 so that manual CSV uploads
and AV data share the same date key and can upsert correctly via the unique constraint
(symbol, granularity, date).

Safe to run multiple times (idempotent).
Run with:  python db_migrate_v3_normalize_dates.py
"""

import sys
import os

# Allow running from the portfolio-app directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
import models
from database import engine

SOURCE_PRIORITY = {"manual_upload": 3, "alpha_vantage": 2, "mfapi": 1}


def run():
    with Session(engine) as db:
        monthly_rows = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.granularity == "monthly")
            .all()
        )

        already_normalised = 0
        updated = 0
        conflicts_resolved = 0

        for row in monthly_rows:
            new_date = row.date[:7] + "-01"
            if row.date == new_date:
                already_normalised += 1
                continue

            # Check whether a row already exists at the normalised date
            existing = (
                db.query(models.PriceHistory)
                .filter_by(symbol=row.symbol, granularity="monthly", date=new_date)
                .first()
            )

            if existing and existing.id != row.id:
                # Conflict: keep whichever row has higher source priority;
                # on a tie keep existing (already at the normalised date).
                row_prio      = SOURCE_PRIORITY.get(row.source or "", 0)
                existing_prio = SOURCE_PRIORITY.get(existing.source or "", 0)

                if row_prio > existing_prio:
                    # Incoming row wins — copy its values onto the existing normalised row
                    existing.close      = row.close
                    existing.high       = row.high
                    existing.low        = row.low
                    existing.open       = row.open
                    existing.source     = row.source
                    existing.fetched_at = row.fetched_at
                    db.delete(row)
                else:
                    # Existing row wins — just remove the unnormalised duplicate
                    db.delete(row)

                conflicts_resolved += 1
            else:
                row.date = new_date
                updated += 1

        db.commit()

        print(
            f"Migration v3 complete: "
            f"{updated} rows updated, "
            f"{conflicts_resolved} conflicts resolved, "
            f"{already_normalised} already normalised."
        )


if __name__ == "__main__":
    run()

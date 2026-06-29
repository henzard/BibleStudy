#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database ingestion: fetch every source and persist it to SQLite.

Previously this script only ingested earthquakes (and had a broken economic
call). It now drives the unified hybrid collection layer: it runs every
refactored ``fetch_*.py`` collector over the network and persists the results
into their tables via ``earlywarning.persist``. Offline pipeline runs
(``run_pipeline.py``) then replay this stored data.

Usage:
    python ingest_data.py [--days 7]
"""

from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Allow "python scripts/ingest_data.py" without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from earlywarning.collectors import collect_live  # noqa: E402
from earlywarning.config import DEFAULT_DB_PATH  # noqa: E402
from earlywarning.persist import persist_signals  # noqa: E402
from earlywarning.schema import ensure_schema  # noqa: E402

DB_PATH = Path(DEFAULT_DB_PATH)


def summarize(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        tables = [
            "earthquakes", "disasters", "conflicts", "economic_indicators",
            "worldbank_news", "space_weather", "digital_rights",
            "temple_mount_news", "fred_news",
        ]
        print("\n" + "=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"   {table}: {count} rows")
            except sqlite3.Error:
                print(f"   {table}: (missing)")
    finally:
        conn.close()


def main() -> int:
    days = 7
    if "--days" in sys.argv:
        try:
            idx = sys.argv.index("--days")
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python ingest_data.py [--days 7]")
            return 1

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Make sure all tables exist (creates any missing ones on existing DBs).
    conn = sqlite3.connect(str(DB_PATH))
    try:
        ensure_schema(conn)
    finally:
        conn.close()

    print(f"🗄️  Ingesting data for past {days} days into {DB_PATH}")
    print("   Fetching all sources over the network...\n")

    signals = collect_live(lookback_days=days)
    print(f"   Collected {len(signals)} signal(s) from "
          f"{len({s.source for s in signals})} source(s)")

    inserted = persist_signals(DB_PATH, signals)
    total_new = sum(inserted.values())
    print(f"   Persisted {total_new} new row(s):")
    for source, count in sorted(inserted.items()):
        print(f"      {source}: +{count}")

    summarize(DB_PATH)
    print("\n✅ Data ingestion complete!")
    print("   Next: python scripts/run_pipeline.py --days", days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data freshness / source-health monitoring.

A warning system that silently stops receiving data is dangerous. This stage
checks how recently each source table was updated and flags any that have gone
stale beyond their expected cadence — a stale Tier-1 source (earthquakes,
economic) is itself an alert condition.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .models import FreshnessReport

# (table, date_column, expected_max_age_days, tier)
_SOURCES = [
    ("earthquakes", "date_utc", 3, 1),
    ("disasters", "date_utc", 7, 1),
    ("conflicts", "date", 7, 2),
    ("economic_indicators", "date", 45, 1),
    ("worldbank_news", "date", 14, 2),
    ("space_weather", "date", 7, 1),
    ("digital_rights", "date", 21, 2),
    ("temple_mount_news", "date", 7, 2),
    ("fred_news", "date", 14, 2),
]


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _age_days(latest: str) -> float:
    # Compare on the leading YYYY-MM-DD, tolerant of trailing time text.
    try:
        d = datetime.strptime(latest[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return float("inf")
    return (datetime.utcnow() - d).total_seconds() / 86400.0


def analyze_freshness(db_path: Path) -> FreshnessReport:
    db_path = Path(db_path)
    items: List[Dict] = []
    stale: List[str] = []

    if not db_path.exists():
        return FreshnessReport(items=[], stale_sources=[], any_stale=False)

    conn = sqlite3.connect(str(db_path))
    try:
        for table, col, max_age, tier in _SOURCES:
            if not _table_exists(conn, table):
                continue
            row = conn.execute(f"SELECT MAX({col}) FROM {table}").fetchone()
            latest = row[0] if row else None
            if not latest:
                items.append({"source": table, "latest": None,
                              "age_days": None, "stale": True, "tier": tier,
                              "reason": "no data"})
                stale.append(table)
                continue
            age = _age_days(str(latest))
            is_stale = age > max_age
            items.append({
                "source": table, "latest": str(latest)[:16],
                "age_days": round(age, 1) if age != float("inf") else None,
                "stale": is_stale, "tier": tier, "max_age_days": max_age,
            })
            if is_stale:
                stale.append(table)
    finally:
        conn.close()

    return FreshnessReport(items=items, stale_sources=stale,
                           any_stale=bool(stale))

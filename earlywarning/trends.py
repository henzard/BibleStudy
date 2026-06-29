#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Historical trend & acceleration analysis.

Where the research agents look at the current window, this stage looks *back*
to answer "is this escalating?" It compares recent activity to a trailing
baseline so the system reports trend/acceleration rather than isolated events
(the "research memory" idea from the architecture analysis).

Reads the SQLite store directly; degrades to empty results when a table or the
database is absent.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


def _weekly_counts(conn: sqlite3.Connection, table: str, date_col: str,
                   weeks: int) -> List[int]:
    """Counts per trailing week (oldest..newest) for a table."""
    counts = []
    for w in range(weeks, 0, -1):
        start = (datetime.utcnow() - timedelta(weeks=w)).strftime("%Y-%m-%d")
        end = (datetime.utcnow() - timedelta(weeks=w - 1)).strftime("%Y-%m-%d")
        row = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {date_col} >= ? AND {date_col} < ?",
            (start, end),
        ).fetchone()
        counts.append(int(row[0]) if row else 0)
    return counts


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _direction(recent: float, baseline: float) -> str:
    if baseline <= 0:
        return "escalating" if recent > 0 else "flat"
    change = (recent - baseline) / baseline
    if change >= 0.15:
        return "escalating"
    if change <= -0.15:
        return "easing"
    return "steady"


def _metric(conn: sqlite3.Connection, table: str, date_col: str,
            weeks: int) -> Dict[str, Any]:
    if not _table_exists(conn, table):
        return {"available": False}
    series = _weekly_counts(conn, table, date_col, weeks)
    if not series:
        return {"available": False}
    recent = series[-1]
    prior = series[:-1] or [0]
    baseline = sum(prior) / len(prior)
    return {
        "available": True,
        "weekly_series": series,
        "recent_week": recent,
        "baseline_avg": round(baseline, 2),
        "acceleration_pct": round(
            ((recent - baseline) / baseline * 100) if baseline else 0.0, 1
        ),
        "direction": _direction(recent, baseline),
    }


def analyze_trends(db_path: Path, weeks: int = 8) -> Dict[str, Any]:
    db_path = Path(db_path)
    if not db_path.exists():
        return {"available": False, "reason": "database not found"}

    conn = sqlite3.connect(str(db_path))
    try:
        metrics = {
            "earthquakes": _metric(conn, "earthquakes", "date_utc", weeks),
            "conflicts": _metric(conn, "conflicts", "date", weeks),
            "disasters": _metric(conn, "disasters", "date_utc", weeks),
            "worldbank_news": _metric(conn, "worldbank_news", "date", weeks),
        }
    finally:
        conn.close()

    escalating = [
        name for name, m in metrics.items()
        if m.get("available") and m.get("direction") == "escalating"
    ]
    return {
        "available": True,
        "weeks": weeks,
        "metrics": metrics,
        "escalating_metrics": escalating,
        "summary": (
            f"{len(escalating)} metric(s) accelerating vs {weeks}-week baseline"
            if escalating else "No metrics accelerating vs baseline"
        ),
    }

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collector registry and the top-level sweep."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from ..models import RawSignal
from .base import Collector, CollectorContext
from .db_collectors import ALL_DB_COLLECTORS


def build_default_collectors() -> List[Collector]:
    """Instantiate the default collector set (the DB-backed readers)."""
    return [cls() for cls in ALL_DB_COLLECTORS]


def collect_all(db_path: Path, lookback_days: int = 7,
                collectors: List[Collector] | None = None) -> List[RawSignal]:
    """Run every collector against the store and return all raw signals.

    Missing database or missing tables yield an empty list rather than an
    error — the pipeline degrades gracefully when a source has no data yet.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    collectors = collectors or build_default_collectors()
    conn = sqlite3.connect(str(db_path))
    try:
        ctx = CollectorContext(conn=conn, lookback_days=lookback_days)
        signals: List[RawSignal] = []
        for collector in collectors:
            signals.extend(collector.safe_collect(ctx))
        return signals
    finally:
        conn.close()


def collect_live(lookback_days: int = 7) -> List[RawSignal]:
    """Run the live (network) collectors and return their raw signals.

    Imported lazily so the network-facing fetch modules are only loaded when
    live mode is actually requested.
    """
    from .live import build_live_collectors

    ctx = CollectorContext(conn=None, lookback_days=lookback_days)
    signals: List[RawSignal] = []
    for collector in build_live_collectors():
        signals.extend(collector.safe_collect(ctx))
    return signals

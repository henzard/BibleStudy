#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collector base classes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from ..models import RawSignal


@dataclass
class CollectorContext:
    """Shared inputs passed to every collector run.

    ``conn`` is required by DB-backed collectors but unused by live
    (network) collectors, so it is optional.
    """

    conn: Optional[sqlite3.Connection] = None
    lookback_days: int = 7

    @property
    def cutoff_date(self) -> str:
        return (datetime.utcnow() - timedelta(days=self.lookback_days)).strftime(
            "%Y-%m-%d"
        )


class Collector:
    """Base collector. Subclasses implement :meth:`collect`."""

    #: stable collector name (matches taxonomy collector keys)
    name: str = "base"
    #: default prophecy node hint for items from this collector
    node_id: str = ""
    scripture: str = ""

    def table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return cur.fetchone() is not None

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        raise NotImplementedError

    def safe_collect(self, ctx: CollectorContext) -> List[RawSignal]:
        """Run :meth:`collect`, swallowing per-collector errors so one bad
        source never aborts the whole sweep."""
        try:
            return self.collect(ctx)
        except sqlite3.Error:
            return []
        except Exception:
            return []

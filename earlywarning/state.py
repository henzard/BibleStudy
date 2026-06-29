#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pipeline run-state persistence.

Each run is recorded in the ``pipeline_runs`` table so the next run can diff
against it (change detection) and so alert routing can debounce on the previous
level/time. Without this, the pipeline has no memory and can only snapshot —
not *warn on change*.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import ensure_schema


def save_run(db_path: Path, payload: Dict[str, Any], alert_level: str,
             generated_at: str, overall_intensity: float,
             phase: str) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        ensure_schema(conn)
        conn.execute(
            "INSERT INTO pipeline_runs "
            "(generated_at, alert_level, overall_intensity, phase, payload) "
            "VALUES (?,?,?,?,?)",
            (generated_at, alert_level, float(overall_intensity), phase,
             json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()


def load_previous(db_path: Path) -> Optional[Dict[str, Any]]:
    """Return the most recent stored run payload, or None if there is none."""
    db_path = Path(db_path)
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        if conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='pipeline_runs'"
        ).fetchone() is None:
            return None
        row = conn.execute(
            "SELECT payload, alert_level, generated_at FROM pipeline_runs "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        payload = json.loads(row[0])
    except json.JSONDecodeError:
        return None
    # Ensure the level/time are present even if an older payload lacked them.
    payload.setdefault("alert_level", row[1])
    payload.setdefault("generated_at", row[2])
    return payload

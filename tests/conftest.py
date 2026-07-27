#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared pytest fixtures.

Builds a seeded SQLite store using the real schema so the early-warning
pipeline can be exercised deterministically and offline.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import init_database  # noqa: E402


@pytest.fixture
def seeded_db(tmp_path) -> Path:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.executescript(init_database.SCHEMA)
    conn.executemany(
        "INSERT INTO earthquakes (event_id,date_utc,magnitude,location,source_url) "
        "VALUES (?,?,?,?,?)",
        [
            ("eq1", "2026-07-27 10:00 UTC", 6.5,
             "10 km S of Antofagasta, Chile", "http://u/eq1"),
            ("eq2", "2026-07-26 10:00 UTC", 5.1,
             "Off coast of Honshu, Japan", "http://u/eq2"),
            ("eq3", "2026-07-25 10:00 UTC", 4.4,
             "Antofagasta, Chile", "http://u/eq3"),
        ],
    )
    conn.executemany(
        "INSERT INTO conflicts (date,location,conflict_type,casualties,"
        "description,source_url,confidence) VALUES (?,?,?,?,?,?,?)",
        [
            ("2026-07-27", "Sudan", "Active Conflict", 140,
             "Heavy fighting in Sudan offensive", "http://u/c1", "High"),
            ("2026-07-26", "Sudan", "Casualties", 5,
             "Casualties reported in Sudan offensive", "http://u/c2", "Med"),
        ],
    )
    conn.executemany(
        "INSERT INTO economic_indicators (date,indicator_name,"
        "indicator_category,value,yoy_change,status,confidence) "
        "VALUES (?,?,?,?,?,?,?)",
        [
            ("2026-07-20", "Consumer Price Index", "Inflation", 312.5, 7.2,
             "Crisis", "High"),
        ],
    )
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def empty_db(tmp_path) -> Path:
    db = tmp_path / "empty.db"
    conn = sqlite3.connect(db)
    conn.executescript(init_database.SCHEMA)
    conn.commit()
    conn.close()
    return db

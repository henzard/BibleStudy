#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for the SQLite schema.

Both ``scripts/init_database.py`` (fresh installs) and
``earlywarning.persist`` (live-mode migration) use this. Every statement is
``CREATE ... IF NOT EXISTS`` so :func:`ensure_schema` is safe to run against an
existing database — it adds any missing tables without touching existing data.
"""

from __future__ import annotations

import sqlite3

SCHEMA = """
-- Earthquakes from USGS
CREATE TABLE IF NOT EXISTS earthquakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date_utc TEXT NOT NULL,
    magnitude REAL NOT NULL,
    location TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    depth_km REAL,
    source_url TEXT,
    node_id TEXT DEFAULT 'J0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_earthquakes_date ON earthquakes(date_utc);
CREATE INDEX IF NOT EXISTS idx_earthquakes_magnitude ON earthquakes(magnitude);

-- Disasters from GDACS
CREATE TABLE IF NOT EXISTS disasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date_utc TEXT NOT NULL,
    disaster_type TEXT NOT NULL,
    location TEXT NOT NULL,
    alert_level TEXT,
    severity_description TEXT,
    population_affected INTEGER,
    source_url TEXT,
    node_id TEXT DEFAULT 'J0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_disasters_date ON disasters(date_utc);
CREATE INDEX IF NOT EXISTS idx_disasters_type ON disasters(disaster_type);
CREATE INDEX IF NOT EXISTS idx_disasters_alert ON disasters(alert_level);

-- Conflicts from UN Peacekeeping
CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    location TEXT NOT NULL,
    conflict_type TEXT NOT NULL,
    casualties INTEGER,
    description TEXT,
    source_url TEXT,
    confidence TEXT NOT NULL,
    node_id TEXT DEFAULT 'J0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conflicts_date ON conflicts(date);
CREATE INDEX IF NOT EXISTS idx_conflicts_location ON conflicts(location);
CREATE INDEX IF NOT EXISTS idx_conflicts_confidence ON conflicts(confidence);

-- Economic Indicators from FRED
CREATE TABLE IF NOT EXISTS economic_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    indicator_name TEXT NOT NULL,
    indicator_category TEXT NOT NULL,
    value REAL NOT NULL,
    yoy_change REAL,
    status TEXT NOT NULL,
    confidence TEXT NOT NULL,
    source TEXT DEFAULT 'FRED',
    node_id TEXT DEFAULT 'H0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_economic_date ON economic_indicators(date);
CREATE INDEX IF NOT EXISTS idx_economic_indicator ON economic_indicators(indicator_name);
CREATE INDEX IF NOT EXISTS idx_economic_status ON economic_indicators(status);

-- World Bank News
CREATE TABLE IF NOT EXISTS worldbank_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    headline TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    keywords TEXT,
    confidence TEXT NOT NULL,
    source_url TEXT,
    node_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_worldbank_date ON worldbank_news(date);
CREATE INDEX IF NOT EXISTS idx_worldbank_category ON worldbank_news(category);

-- Weekly Assessments
CREATE TABLE IF NOT EXISTS weekly_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    j0_status TEXT DEFAULT 'Observed',
    j0_confidence TEXT DEFAULT 'Med',
    j1_status TEXT DEFAULT 'Observed',
    j1_confidence TEXT DEFAULT 'Low',
    j2_status TEXT DEFAULT 'Observed',
    j2_confidence TEXT DEFAULT 'Med',
    j3_status TEXT DEFAULT 'Not Observed',
    j4_status TEXT DEFAULT 'Not Observed',
    j6_status TEXT DEFAULT 'Not Observed',
    j7_status TEXT DEFAULT 'Not Observed',
    h0_status TEXT DEFAULT 'Not Observed',
    h0_confidence TEXT DEFAULT 'Low',
    notes TEXT,
    scripture_focus TEXT,
    newsletter_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weekly_start ON weekly_assessments(week_start);

-- Trends for analysis
CREATE TABLE IF NOT EXISTS trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    time_period TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    value REAL NOT NULL,
    comparison_to_previous REAL,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trends_metric ON trends(metric_name);
CREATE INDEX IF NOT EXISTS idx_trends_period ON trends(period_start);

-- Space Weather from NOAA SWPC (node J6)
CREATE TABLE IF NOT EXISTS space_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    confidence TEXT NOT NULL,
    source_url TEXT,
    node_id TEXT DEFAULT 'J6',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spaceweather_date ON space_weather(date);

-- Digital rights / surveillance from EFF (node B2)
CREATE TABLE IF NOT EXISTS digital_rights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    keywords TEXT,
    confidence TEXT NOT NULL,
    source_url TEXT,
    node_id TEXT DEFAULT 'B2',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_digital_rights_date ON digital_rights(date);

-- Temple Mount & Middle East (nodes J3 / MS0)
CREATE TABLE IF NOT EXISTS temple_mount_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    category TEXT,
    keywords TEXT,
    confidence TEXT NOT NULL,
    scripture TEXT,
    source_url TEXT,
    node_id TEXT DEFAULT 'J3',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_temple_mount_date ON temple_mount_news(date);

-- FRED economic news announcements (node H0)
CREATE TABLE IF NOT EXISTS fred_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    confidence TEXT DEFAULT 'Low',
    source_url TEXT,
    node_id TEXT DEFAULT 'H0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fred_news_date ON fred_news(date);

-- Pipeline run history (early-warning state for change detection)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    alert_level TEXT NOT NULL,
    overall_intensity REAL NOT NULL,
    phase TEXT,
    payload TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_at ON pipeline_runs(generated_at);

-- Schema Version Tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""

# Bump when SCHEMA changes in a way fresh installs should record.
SCHEMA_VERSION = 3
SCHEMA_VERSION_DESCRIPTION = (
    "Add space_weather, digital_rights, temple_mount_news, fred_news, "
    "pipeline_runs tables"
)


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create any missing tables/indexes. Safe on existing databases."""
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)",
        (SCHEMA_VERSION, SCHEMA_VERSION_DESCRIPTION),
    )
    conn.commit()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initialization Script
Creates the SQLite database schema for prophecy tracking.

Usage:
    python init_database.py [--reset]
"""

import sys
import io
import sqlite3
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path("data/prophecy_tracking.db")

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

-- Schema Version Tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""

def init_database(reset=False):
    """Initialize the database with schema."""
    # Create data directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if database exists
    exists = DB_PATH.exists()
    
    if exists and reset:
        print(f"⚠️  Resetting database: {DB_PATH}")
        DB_PATH.unlink()
        exists = False
    
    if exists and not reset:
        print(f"✅ Database already exists: {DB_PATH}")
        print("   Use --reset to recreate")
        return
    
    # Create database
    print(f"📊 Creating database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Execute schema
    cursor.executescript(SCHEMA)
    
    # Insert schema version
    cursor.execute(
        "INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)",
        (1, "Initial schema with 7 core tables")
    )
    
    conn.commit()
    
    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n✅ Database created successfully!")
    print(f"   Tables created: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} rows")
    
    conn.close()


def main():
    """Main execution."""
    reset = '--reset' in sys.argv
    
    if reset:
        response = input("⚠️  This will DELETE all existing data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    init_database(reset)
    
    print(f"\n📁 Database location: {DB_PATH.absolute()}")
    print("🚀 Ready to collect prophecy tracking data!")


if __name__ == '__main__':
    main()


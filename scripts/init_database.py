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

# Schema lives in one place (shared with the early-warning pipeline).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from earlywarning.schema import (  # noqa: E402
    SCHEMA, SCHEMA_VERSION, SCHEMA_VERSION_DESCRIPTION,
)


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
        (SCHEMA_VERSION, SCHEMA_VERSION_DESCRIPTION)
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


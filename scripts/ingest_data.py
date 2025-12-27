#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Ingestion Script
Runs all automation scripts and ingests data into SQLite database.

Usage:
    python ingest_data.py [--days 7]
"""

import sys
import io
import sqlite3
import subprocess
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path("data/prophecy_tracking.db")


def run_fetch_script(script_name: str, days: int = 7) -> str:
    """Run a fetch script and return output."""
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), '--days', str(days)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        print(f"⚠️  Error running {script_name}: {e}", file=sys.stderr)
        return ""


def parse_earthquake_output(output: str) -> list:
    """Parse earthquake data from script output."""
    earthquakes = []
    
    # Look for table rows with earthquake data
    for line in output.split('\n'):
        # Match: | **6.5** | Location | Date | Lat, Lon | [USGS](url) |
        match = re.search(r'\|\s*\*\*(\d+\.?\d*)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\s*\|\s*([^|]+)\|\s*\[USGS\]\(([^)]+)\)', line)
        if match:
            mag, location, date_str, coords, url = match.groups()
            earthquakes.append({
                'magnitude': float(mag),
                'location': location.strip(),
                'date_utc': date_str.strip(),
                'source_url': url.strip(),
                'event_id': url.split('/')[-1]  # Extract event ID from URL
            })
    
    return earthquakes


def ingest_earthquakes(conn: sqlite3.Connection, days: int):
    """Fetch and ingest earthquake data."""
    print("📊 Fetching earthquake data...")
    output = run_fetch_script('fetch_earthquakes.py', days)
    earthquakes = parse_earthquake_output(output)
    
    cursor = conn.cursor()
    inserted = 0
    
    for eq in earthquakes:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO earthquakes 
                (event_id, date_utc, magnitude, location, source_url, node_id)
                VALUES (?, ?, ?, ?, ?, 'J0')
            """, (
                eq['event_id'],
                eq['date_utc'],
                eq['magnitude'],
                eq['location'],
                eq['source_url']
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"⚠️  Error inserting earthquake: {e}", file=sys.stderr)
    
    conn.commit()
    print(f"   ✅ Inserted {inserted} new earthquakes (skipped {len(earthquakes) - inserted} duplicates)")


def ingest_economic_data(conn: sqlite3.Connection, days: int):
    """Fetch and ingest economic data."""
    print("📉 Fetching economic data...")
    output = run_fetch_script('fetch_economic.py', months=12)
    
    cursor = conn.cursor()
    inserted = 0
    
    # Parse economic data (simplified for now - would need more robust parsing)
    # This is a placeholder - actual implementation would parse the formatted output
    
    # For now, just log that we attempted
    print(f"   ℹ️  Economic data ingestion: Placeholder (needs parser implementation)")


def calculate_trends(conn: sqlite3.Connection):
    """Calculate and store trend data."""
    print("📈 Calculating trends...")
    cursor = conn.cursor()
    
    # Earthquake trend: average per week over last 8 weeks
    cursor.execute("""
        INSERT INTO trends (metric_name, time_period, period_start, period_end, value)
        SELECT 
            'avg_earthquakes_per_week' as metric_name,
            'week' as time_period,
            date('now', '-56 days') as period_start,
            date('now') as period_end,
            CAST(COUNT(*) AS REAL) / 8.0 as value
        FROM earthquakes
        WHERE date_utc >= date('now', '-56 days')
    """)
    
    # Major earthquake trend (6.0+)
    cursor.execute("""
        INSERT INTO trends (metric_name, time_period, period_start, period_end, value)
        SELECT 
            'major_earthquakes_per_week' as metric_name,
            'week' as time_period,
            date('now', '-56 days') as period_start,
            date('now') as period_end,
            CAST(COUNT(*) AS REAL) / 8.0 as value
        FROM earthquakes
        WHERE date_utc >= date('now', '-56 days')
        AND magnitude >= 6.0
    """)
    
    conn.commit()
    print("   ✅ Trends calculated")


def generate_summary_report(conn: sqlite3.Connection):
    """Generate summary report from database."""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE SUMMARY REPORT")
    print("="*60)
    
    # Total records
    cursor.execute("SELECT COUNT(*) FROM earthquakes")
    eq_count = cursor.fetchone()[0]
    print(f"\n📊 Total Records:")
    print(f"   Earthquakes: {eq_count}")
    
    # Recent earthquakes (last 7 days)
    cursor.execute("""
        SELECT COUNT(*), AVG(magnitude), MAX(magnitude)
        FROM earthquakes
        WHERE date_utc >= date('now', '-7 days')
    """)
    recent = cursor.fetchone()
    if recent[0] > 0:
        print(f"\n🌍 Last 7 Days:")
        print(f"   Earthquakes: {recent[0]}")
        print(f"   Average magnitude: {recent[1]:.2f}")
        print(f"   Largest: {recent[2]}")
    
    # Trends
    cursor.execute("""
        SELECT metric_name, value 
        FROM trends 
        WHERE calculated_at >= date('now', '-1 day')
        ORDER BY calculated_at DESC
        LIMIT 5
    """)
    trends = cursor.fetchall()
    if trends:
        print(f"\n📈 Recent Trends:")
        for metric, value in trends:
            print(f"   {metric}: {value:.2f}")
    
    print("\n" + "="*60)


def main():
    """Main execution."""
    days = 7
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python ingest_data.py [--days 7]")
            sys.exit(1)
    
    # Check if database exists
    if not DB_PATH.exists():
        print("❌ Database not found. Run: python scripts/init_database.py")
        sys.exit(1)
    
    print(f"🗄️  Ingesting data for past {days} days...")
    print(f"   Database: {DB_PATH}")
    print()
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Ingest data from each source
        ingest_earthquakes(conn, days)
        # ingest_economic_data(conn, days)  # Placeholder
        
        # Calculate trends
        calculate_trends(conn)
        
        # Generate report
        generate_summary_report(conn)
        
        print("\n✅ Data ingestion complete!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()


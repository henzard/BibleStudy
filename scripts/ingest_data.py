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

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path("data/prophecy_tracking.db")


def run_fetch_script(script_name: str, days: int = 7, extra_args: list = None) -> str:
    """Run a fetch script and return output."""
    script_path = Path(__file__).parent / script_name

    cmd = [sys.executable, str(script_path), '--days', str(days)]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        print(f"  Error running {script_name}: {e}", file=sys.stderr)
        return ""


def parse_earthquake_output(output: str) -> list:
    """Parse earthquake data from fetch_earthquakes.py output."""
    earthquakes = []
    for line in output.split('\n'):
        match = re.search(
            r'\|\s*\*\*(\d+\.?\d*)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\s*\|\s*([^|]+)\|\s*\[USGS\]\(([^)]+)\)',
            line
        )
        if match:
            mag, location, date_str, coords, url = match.groups()
            earthquakes.append({
                'magnitude': float(mag),
                'location': location.strip(),
                'date_utc': date_str.strip(),
                'source_url': url.strip(),
                'event_id': url.split('/')[-1]
            })
    return earthquakes


def parse_conflicts_output(output: str) -> list:
    """Parse conflict data from fetch_un_peacekeeping.py output."""
    conflicts = []
    for line in output.split('\n'):
        # Format: | Date | **Headline** | Key Data | Confidence | [UN PKO](url) |
        match = re.search(
            r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]*)\|\s*(High|Med|Low)\s*\|\s*\[UN PKO\]\(([^)]+)\)',
            line
        )
        if match:
            date, headline, key_data, confidence, url = match.groups()
            conflicts.append({
                'date': date.strip(),
                'description': headline.strip(),
                'location': 'Conflict Zone',
                'conflict_type': 'Active Conflict',
                'casualties': _extract_casualties(key_data),
                'confidence': confidence.strip(),
                'source_url': url.strip()
            })
    return conflicts


def parse_temple_mount_output(output: str) -> list:
    """Parse conflict data from fetch_temple_mount_news.py output."""
    conflicts = []
    for line in output.split('\n'):
        # Format: | Date | **Headline...** | Category | Confidence | Source | [Link](url) |
        match = re.search(
            r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|\s*(High|Med|Low)\s*\|\s*([^|]+)\|\s*\[Link\]\(([^)]+)\)',
            line
        )
        if match:
            date, headline, category, confidence, source, url = match.groups()
            conflict_type = category.strip()
            if 'conflict' in conflict_type.lower():
                conflict_type = 'Active Conflict'
            conflicts.append({
                'date': date.strip(),
                'description': headline.strip(),
                'location': 'Middle East',
                'conflict_type': conflict_type,
                'casualties': 0,
                'confidence': confidence.strip(),
                'source_url': url.strip()
            })
    return conflicts


def parse_worldbank_output(output: str) -> list:
    """Parse news data from fetch_worldbank_news.py output."""
    articles = []
    for line in output.split('\n'):
        # Format: | Date | **Headline...** | Keywords | Confidence | [Source](url) |
        match = re.search(
            r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|\s*(High|Med|Low)\s*\|\s*\[Source\]\(([^)]+)\)',
            line
        )
        if match:
            date, headline, keywords, confidence, url = match.groups()
            kw = keywords.strip()
            category = 'Disaster/Famine' if any(w in kw for w in ['famine', 'disaster', 'flood', 'earthquake', 'hurricane', 'drought']) else 'Economic/Aid'
            node_id = 'J0' if category == 'Disaster/Famine' else 'H0'
            articles.append({
                'date': date.strip(),
                'headline': headline.strip(),
                'category': category,
                'keywords': kw,
                'confidence': confidence.strip(),
                'source_url': url.strip(),
                'node_id': node_id
            })
    return articles


def parse_economic_output(output: str) -> list:
    """Parse economic data from fetch_economic.py output."""
    indicators = []
    current_category = 'Unknown'

    for line in output.split('\n'):
        cat_match = re.match(r'###\s+(Inflation|Unemployment|Gdp|Trade)', line, re.IGNORECASE)
        if cat_match:
            current_category = cat_match.group(1).capitalize()
            continue

        # Format: | **Indicator Name** | value | date | YoY | status_emoji STATUS | Assessment |
        match = re.search(
            r'\|\s*\*\*([^*]+)\*\*\s*\|\s*([-\d.,]+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]*)\|\s*[^\s]*\s*(NORMAL|CONCERN|CRISIS|UNKNOWN)\s*\|\s*([^|]+)\|',
            line
        )
        if match:
            name, value_str, date, yoy_str, status, assessment = match.groups()
            try:
                value = float(value_str.replace(',', ''))
            except ValueError:
                continue

            yoy = None
            yoy_clean = yoy_str.strip()
            if yoy_clean and yoy_clean != 'N/A':
                try:
                    yoy = float(re.sub(r'[^-\d.]', '', yoy_clean))
                except ValueError:
                    pass

            indicators.append({
                'date': date.strip(),
                'indicator_name': name.strip(),
                'indicator_category': current_category,
                'value': value,
                'yoy_change': yoy,
                'status': status.strip(),
                'confidence': 'Med' if status in ('NORMAL', 'CONCERN') else 'Low'
            })
    return indicators


def parse_gdacs_output(output: str) -> list:
    """Parse disaster data from fetch_gdacs.py output."""
    disasters = []
    current_type = 'Unknown'

    for line in output.split('\n'):
        type_match = re.match(r'###\s+(Droughts|Earthquakes|Floods|Tropical Cyclones|Volcanoes|Unknowns)', line, re.IGNORECASE)
        if type_match:
            raw = type_match.group(1)
            type_map = {
                'droughts': 'Drought', 'earthquakes': 'Earthquake', 'floods': 'Flood',
                'tropical cyclones': 'Cyclone', 'volcanoes': 'Volcano', 'unknowns': 'Wildfire/Other'
            }
            current_type = type_map.get(raw.lower(), raw)
            continue

        # Format: | alert_emoji **Level** | Location | Date | Severity | Population | [GDACS](url) |
        match = re.search(
            r'\|\s*[^\s]*\s*\*\*(Green|Orange|Red)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*\[GDACS\]\(([^)]+)\)',
            line
        )
        if match:
            alert, location, date_str, severity, population, url = match.groups()
            pop_count = _extract_number(population)
            event_id = re.search(r'eventid=(\d+)', url)
            disasters.append({
                'event_id': f"GDACS-{event_id.group(1)}" if event_id else f"GDACS-{hash(url) % 100000}",
                'date_utc': date_str.strip(),
                'disaster_type': current_type,
                'location': location.strip(),
                'alert_level': alert.strip(),
                'severity_description': severity.strip(),
                'population_affected': pop_count,
                'source_url': url.strip()
            })
    return disasters


def _extract_casualties(text: str) -> int:
    """Extract casualty numbers from text."""
    nums = re.findall(r'(\d[\d,]*)\s*(?:killed|dead|casualties|deaths)', text.lower())
    if nums:
        return int(nums[0].replace(',', ''))
    return 0


def _extract_number(text: str) -> int:
    """Extract the first large number from population text."""
    text = text.replace(',', '')
    # Look for "X million" or "X thousand"
    m = re.search(r'([\d.]+)\s*million', text.lower())
    if m:
        return int(float(m.group(1)) * 1_000_000)
    m = re.search(r'([\d.]+)\s*thousand', text.lower())
    if m:
        return int(float(m.group(1)) * 1_000)
    # Look for number in parentheses like (1701983 people)
    m = re.search(r'\((\d+)\s*people\)', text)
    if m:
        return int(m.group(1))
    # Any number
    m = re.search(r'(\d+)', text)
    if m and int(m.group(1)) > 0:
        return int(m.group(1))
    return 0


# === INGESTION FUNCTIONS ===

def ingest_earthquakes(conn: sqlite3.Connection, days: int):
    """Fetch and ingest earthquake data."""
    print("  Fetching earthquake data...")
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
            """, (eq['event_id'], eq['date_utc'], eq['magnitude'],
                  eq['location'], eq['source_url']))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"    DB error (earthquake): {e}", file=sys.stderr)

    conn.commit()
    print(f"    Earthquakes: {inserted} new / {len(earthquakes)} total parsed")


def ingest_conflicts(conn: sqlite3.Connection, days: int):
    """Fetch and ingest conflict data from UN Peacekeeping + Temple Mount."""
    print("  Fetching conflict data...")

    un_output = run_fetch_script('fetch_un_peacekeeping.py', days)
    un_conflicts = parse_conflicts_output(un_output)

    temple_output = run_fetch_script('fetch_temple_mount_news.py', days)
    temple_conflicts = parse_temple_mount_output(temple_output)

    all_conflicts = un_conflicts + temple_conflicts

    cursor = conn.cursor()
    inserted = 0
    for c in all_conflicts:
        try:
            cursor.execute("""
                INSERT INTO conflicts
                (date, location, conflict_type, casualties, description, source_url, confidence, node_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'J0')
            """, (c['date'], c['location'], c['conflict_type'],
                  c['casualties'], c['description'], c['source_url'], c['confidence']))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"    DB error (conflict): {e}", file=sys.stderr)

    conn.commit()
    print(f"    Conflicts: {inserted} new / {len(all_conflicts)} total parsed")


def ingest_worldbank(conn: sqlite3.Connection, days: int):
    """Fetch and ingest World Bank news."""
    print("  Fetching World Bank data...")
    output = run_fetch_script('fetch_worldbank_news.py', days)
    articles = parse_worldbank_output(output)

    cursor = conn.cursor()
    inserted = 0
    for a in articles:
        try:
            cursor.execute("""
                INSERT INTO worldbank_news
                (date, headline, category, keywords, confidence, source_url, node_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (a['date'], a['headline'], a['category'],
                  a['keywords'], a['confidence'], a['source_url'], a['node_id']))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"    DB error (worldbank): {e}", file=sys.stderr)

    conn.commit()
    print(f"    World Bank: {inserted} new / {len(articles)} total parsed")


def ingest_economic(conn: sqlite3.Connection):
    """Fetch and ingest FRED economic data."""
    print("  Fetching economic data...")
    output = run_fetch_script('fetch_economic.py', days=7, extra_args=['--months', '12'])
    indicators = parse_economic_output(output)

    cursor = conn.cursor()
    inserted = 0
    for ind in indicators:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO economic_indicators
                (date, indicator_name, indicator_category, value, yoy_change, status, confidence, node_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'H0')
            """, (ind['date'], ind['indicator_name'], ind['indicator_category'],
                  ind['value'], ind['yoy_change'], ind['status'], ind['confidence']))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"    DB error (economic): {e}", file=sys.stderr)

    conn.commit()
    print(f"    Economic: {inserted} new / {len(indicators)} total parsed")


def ingest_disasters(conn: sqlite3.Connection, days: int):
    """Fetch and ingest GDACS disaster data."""
    print("  Fetching GDACS disaster data...")
    output = run_fetch_script('fetch_gdacs.py', days)
    disasters = parse_gdacs_output(output)

    cursor = conn.cursor()
    inserted = 0
    for d in disasters:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO disasters
                (event_id, date_utc, disaster_type, location, alert_level,
                 severity_description, population_affected, source_url, node_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'J0')
            """, (d['event_id'], d['date_utc'], d['disaster_type'],
                  d['location'], d['alert_level'], d['severity_description'],
                  d['population_affected'], d['source_url']))
            if cursor.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"    DB error (disaster): {e}", file=sys.stderr)

    conn.commit()
    print(f"    Disasters: {inserted} new / {len(disasters)} total parsed")


def calculate_trends(conn: sqlite3.Connection):
    """Calculate and store trend data."""
    print("  Calculating trends...")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trends (metric_name, time_period, period_start, period_end, value)
        SELECT 'avg_earthquakes_per_week', 'week',
               date('now', '-56 days'), date('now'),
               CAST(COUNT(*) AS REAL) / 8.0
        FROM earthquakes WHERE date_utc >= date('now', '-56 days')
    """)

    cursor.execute("""
        INSERT INTO trends (metric_name, time_period, period_start, period_end, value)
        SELECT 'major_earthquakes_per_week', 'week',
               date('now', '-56 days'), date('now'),
               CAST(COUNT(*) AS REAL) / 8.0
        FROM earthquakes WHERE date_utc >= date('now', '-56 days') AND magnitude >= 6.0
    """)

    cursor.execute("""
        INSERT INTO trends (metric_name, time_period, period_start, period_end, value)
        SELECT 'conflicts_per_week', 'week',
               date('now', '-56 days'), date('now'),
               CAST(COUNT(*) AS REAL) / 8.0
        FROM conflicts WHERE date >= date('now', '-56 days')
    """)

    conn.commit()
    print("    Trends calculated")


def generate_summary_report(conn: sqlite3.Connection):
    """Print database summary."""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("DATABASE SUMMARY REPORT")
    print("=" * 60)

    tables = ['earthquakes', 'conflicts', 'disasters', 'worldbank_news', 'economic_indicators']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")

    cursor.execute("""
        SELECT COUNT(*), AVG(magnitude), MAX(magnitude)
        FROM earthquakes WHERE date_utc >= date('now', '-7 days')
    """)
    recent = cursor.fetchone()
    if recent and recent[0] > 0:
        print(f"\n  Last 7 days: {recent[0]} earthquakes, avg {recent[1]:.1f}, max {recent[2]:.1f}")

    cursor.execute("SELECT COUNT(*) FROM conflicts WHERE date >= date('now', '-7 days')")
    c = cursor.fetchone()[0]
    print(f"  Last 7 days: {c} conflict reports")

    print("=" * 60)


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

    if not DB_PATH.exists():
        print("Database not found. Run: python scripts/init_database.py")
        sys.exit(1)

    print(f"Ingesting data for past {days} days...")
    print(f"  Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)

    try:
        ingest_earthquakes(conn, days)
        ingest_conflicts(conn, days)
        ingest_worldbank(conn, days)
        ingest_economic(conn)
        ingest_disasters(conn, days)
        calculate_trends(conn)
        generate_summary_report(conn)
        print("\nData ingestion complete!")
    except Exception as e:
        print(f"\nError during ingestion: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()

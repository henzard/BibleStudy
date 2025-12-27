#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USGS Earthquake Feed Parser
Fetches and parses earthquake data from USGS ATOM feed.
Filters for magnitude 4.0+ earthquakes for prophecy tracking (node J0).

Usage:
    python fetch_earthquakes.py [--min-mag 4.0] [--days 7]
"""

import sys
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import urllib.request
import urllib.error

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# USGS feed URLs
FEEDS = {
    "hour": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom",
    "day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.atom",
    "week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.atom",
    "month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.atom",
}

# XML namespaces
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'georss': 'http://www.georss.org/georss'
}


def fetch_feed(feed_url: str) -> str:
    """Fetch USGS earthquake feed."""
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)


def parse_magnitude(title: str) -> float:
    """Extract magnitude from title like 'M 4.4 - 15 km SSE of Fern Forest, Hawaii'"""
    try:
        return float(title.split('M ')[1].split(' - ')[0])
    except (IndexError, ValueError):
        return 0.0


def parse_earthquakes(xml_content: str, min_magnitude: float = 4.0, days_back: int = 7) -> List[Dict]:
    """Parse earthquake feed and filter by magnitude and date."""
    root = ET.fromstring(xml_content)
    earthquakes = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    for entry in root.findall('atom:entry', NS):
        # Extract data
        title_elem = entry.find('atom:title', NS)
        updated_elem = entry.find('atom:updated', NS)
        link_elem = entry.find('atom:link[@rel="alternate"]', NS)
        point_elem = entry.find('georss:point', NS)
        
        if title_elem is None or updated_elem is None:
            continue
            
        title = title_elem.text
        magnitude = parse_magnitude(title)
        
        # Filter by magnitude
        if magnitude < min_magnitude:
            continue
        
        # Parse date
        try:
            event_date = datetime.strptime(updated_elem.text[:19], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            continue
        
        # Filter by date
        if event_date < cutoff_date:
            continue
        
        # Extract location from title
        location = title.split(' - ', 1)[1] if ' - ' in title else 'Unknown'
        
        # Extract coordinates
        coords = point_elem.text.split() if point_elem is not None else ['?', '?']
        
        # Build earthquake dict
        earthquake = {
            'magnitude': magnitude,
            'location': location,
            'date': event_date.strftime('%Y-%m-%d %H:%M UTC'),
            'latitude': coords[0],
            'longitude': coords[1],
            'url': link_elem.get('href') if link_elem is not None else ''
        }
        
        earthquakes.append(earthquake)
    
    # Sort by magnitude (highest first)
    earthquakes.sort(key=lambda x: x['magnitude'], reverse=True)
    return earthquakes


def format_for_daily_review(earthquakes: List[Dict]) -> str:
    """Format earthquakes for daily review markdown table."""
    if not earthquakes:
        return "No earthquakes >= magnitude 4.0 in the specified period.\n"
    
    output = ["## Earthquakes (magnitude 4.0+) — Node J0\n"]
    output.append("| Magnitude | Location | Date (UTC) | Coordinates | Link |")
    output.append("|-----------|----------|------------|-------------|------|")
    
    for eq in earthquakes:
        output.append(
            f"| **{eq['magnitude']}** | {eq['location']} | {eq['date']} | "
            f"{eq['latitude']}, {eq['longitude']} | [USGS]({eq['url']}) |"
        )
    
    output.append(f"\n**Total:** {len(earthquakes)} earthquakes magnitude 4.0+")
    output.append("\n**Scripture anchor:** Matthew 24:7-8 — 'earthquakes in divers places… beginning of sorrows'")
    output.append("**Node ID:** J0 (Beginning of sorrows)")
    output.append("**Source:** USGS Earthquake Hazards Program (Tier 1)")
    
    return "\n".join(output)


def format_for_classification_table(earthquakes: List[Dict]) -> str:
    """Format top earthquakes for daily review classification table."""
    if not earthquakes:
        return ""
    
    # Take top 5 largest earthquakes
    top_quakes = earthquakes[:5]
    
    output = ["## For classification table (copy to daily review):\n"]
    
    for eq in top_quakes:
        headline = f"Magnitude {eq['magnitude']} earthquake: {eq['location']}"
        region = eq['location'].split(',')[-1].strip() if ',' in eq['location'] else eq['location']
        
        output.append(f"| {headline} | {region} | J0 | Matt 24:7-8 | Earthquakes | High | USGS verified; Tier 1 source |")
    
    return "\n".join(output)


def main():
    """Main execution."""
    # Parse command line arguments (simple)
    min_mag = 4.0
    days = 7
    
    if '--min-mag' in sys.argv:
        try:
            idx = sys.argv.index('--min-mag')
            min_mag = float(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_earthquakes.py [--min-mag 4.0] [--days 7]")
            sys.exit(1)
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_earthquakes.py [--min-mag 4.0] [--days 7]")
            sys.exit(1)
    
    # Determine which feed to use
    if days <= 1:
        feed_url = FEEDS['day']
    elif days <= 7:
        feed_url = FEEDS['week']
    else:
        feed_url = FEEDS['month']
    
    print(f"Fetching earthquakes (magnitude {min_mag}+, past {days} days)...\n")
    
    # Fetch and parse
    xml_content = fetch_feed(feed_url)
    earthquakes = parse_earthquakes(xml_content, min_mag, days)
    
    # Output results
    print(format_for_daily_review(earthquakes))
    print("\n" + "="*80 + "\n")
    print(format_for_classification_table(earthquakes))
    
    # Summary for confidence assessment
    if earthquakes:
        max_mag = earthquakes[0]['magnitude']
        print(f"\n{'='*80}")
        print(f"Highest magnitude: {max_mag}")
        if max_mag >= 6.0:
            print("⚠️  Magnitude 6.0+ detected — HIGH confidence for marking J0 as 'Observed'")
        elif max_mag >= 5.0:
            print("⚠️  Magnitude 5.0+ detected — MEDIUM confidence")
        else:
            print("ℹ️  Magnitude 4.0-4.9 — Standard seismic activity")
        
        print(f"\n✅ Cross-verify with: BBC, Reuters, or EMSC for international coverage")
        print(f"✅ Mark J0 as 'Observed' if magnitude 5.0+ and cross-verified")


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDACS Multi-Hazard Alert Parser
Fetches and parses disaster alerts from GDACS (Global Disaster Alert and Coordination System).
Covers earthquakes, floods, tropical cyclones, droughts, volcanoes for prophecy tracking (node J0).

Usage:
    python fetch_gdacs.py [--alert-level Orange] [--days 30]
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

# GDACS RSS feed
GDACS_FEED = "https://www.gdacs.org/xml/rss.xml"

# XML namespaces
NS = {
    'gdacs': 'http://www.gdacs.org',
    'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'georss': 'http://www.georss.org/georss',
    'glide': 'http://glidenumber.net'
}

# Disaster type mapping
DISASTER_TYPES = {
    'EQ': 'Earthquake',
    'TC': 'Tropical Cyclone',
    'FL': 'Flood',
    'DR': 'Drought',
    'VO': 'Volcano'
}

# Alert level colors
ALERT_LEVELS = {
    'Red': 3,      # Severe
    'Orange': 2,   # Medium
    'Green': 1     # Minor
}


def fetch_feed(feed_url: str) -> str:
    """Fetch GDACS RSS feed."""
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)


def parse_disasters(xml_content: str, min_alert_level: str = 'Green', days_back: int = 30) -> List[Dict]:
    """Parse GDACS RSS feed and filter by alert level and date."""
    root = ET.fromstring(xml_content)
    disasters = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    min_level_value = ALERT_LEVELS.get(min_alert_level, 1)
    
    for item in root.findall('.//item'):
        # Extract basic data
        title_elem = item.find('title')
        desc_elem = item.find('description')
        link_elem = item.find('link')
        pubdate_elem = item.find('pubDate')
        
        if title_elem is None or link_elem is None:
            continue
        
        # Parse date
        try:
            if pubdate_elem is not None:
                pub_date = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S %Z')
            else:
                continue
        except ValueError:
            continue
        
        # Filter by date
        if pub_date < cutoff_date:
            continue
        
        # Extract GDACS-specific data
        event_type = item.find('gdacs:eventtype', NS)
        alert_level = item.find('gdacs:alertlevel', NS)
        severity = item.find('gdacs:severity', NS)
        country = item.find('gdacs:country', NS)
        population = item.find('gdacs:population', NS)
        fromdate = item.find('gdacs:fromdate', NS)
        
        # Get disaster type
        disaster_type = DISASTER_TYPES.get(event_type.text if event_type is not None else 'Unknown', 'Unknown')
        
        # Get alert level
        alert = alert_level.text if alert_level is not None else 'Green'
        alert_value = ALERT_LEVELS.get(alert, 1)
        
        # Filter by alert level
        if alert_value < min_level_value:
            continue
        
        # Get country
        country_text = country.text if country is not None else 'Unknown'
        
        # Get severity description
        severity_text = severity.text if severity is not None else 'Unknown severity'
        
        # Get population affected
        pop_text = population.text if population is not None else '0'
        pop_value = population.get('value', '0') if population is not None else '0'
        
        # Get event date
        try:
            if fromdate is not None:
                event_date = datetime.strptime(fromdate.text, '%a, %d %b %Y %H:%M:%S %Z')
                event_date_str = event_date.strftime('%Y-%m-%d %H:%M UTC')
            else:
                event_date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
        except ValueError:
            event_date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
        
        # Build disaster dict
        disaster = {
            'type': disaster_type,
            'alert_level': alert,
            'title': title_elem.text,
            'description': desc_elem.text if desc_elem is not None else '',
            'severity': severity_text,
            'country': country_text,
            'population_affected': f"{pop_text} ({pop_value} people)" if pop_value != '0' else 'Unknown',
            'date': event_date_str,
            'url': link_elem.text
        }
        
        disasters.append(disaster)
    
    # Sort by alert level (Red > Orange > Green) then by date
    disasters.sort(key=lambda x: (ALERT_LEVELS.get(x['alert_level'], 0), x['date']), reverse=True)
    return disasters


def format_for_daily_review(disasters: List[Dict]) -> str:
    """Format disasters for daily review markdown table."""
    if not disasters:
        return "No disasters >= specified alert level in the specified period.\n"
    
    # Group by type
    by_type = {}
    for d in disasters:
        dtype = d['type']
        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(d)
    
    output = ["## GDACS Multi-Hazard Alerts — Node J0\n"]
    
    for dtype, items in sorted(by_type.items()):
        output.append(f"### {dtype}s ({len(items)})\n")
        output.append("| Alert | Location | Date | Severity | Population | Link |")
        output.append("|-------|----------|------|----------|------------|------|")
        
        for d in items:
            alert_emoji = "🔴" if d['alert_level'] == 'Red' else "🟠" if d['alert_level'] == 'Orange' else "🟢"
            output.append(
                f"| {alert_emoji} **{d['alert_level']}** | {d['country']} | {d['date']} | "
                f"{d['severity']} | {d['population_affected']} | [GDACS]({d['url']}) |"
            )
        output.append("")
    
    # Summary
    red_count = sum(1 for d in disasters if d['alert_level'] == 'Red')
    orange_count = sum(1 for d in disasters if d['alert_level'] == 'Orange')
    green_count = sum(1 for d in disasters if d['alert_level'] == 'Green')
    
    output.append(f"**Total:** {len(disasters)} disasters ({red_count} Red, {orange_count} Orange, {green_count} Green)")
    output.append("\n**Scripture anchor:** Matthew 24:7-8 — 'famines, pestilences, earthquakes… beginning of sorrows'")
    output.append("**Node ID:** J0 (Beginning of sorrows)")
    output.append("**Source:** GDACS (Global Disaster Alert and Coordination System, EC-JRC) — Tier 1")
    
    return "\n".join(output)


def format_for_classification_table(disasters: List[Dict]) -> str:
    """Format top disasters for daily review classification table."""
    if not disasters:
        return ""
    
    # Take top 10 most severe (Red/Orange priority)
    top_disasters = disasters[:10]
    
    output = ["## For classification table (copy to daily review):\n"]
    
    for d in top_disasters:
        headline = f"{d['alert_level']} alert: {d['type']} in {d['country']} - {d['severity']}"
        region = d['country']
        confidence = "High" if d['alert_level'] in ['Red', 'Orange'] else "Med"
        
        output.append(
            f"| {headline} | {region} | J0 | Matt 24:7-8 | "
            f"{d['type']} | {confidence} | GDACS {d['alert_level']} alert; Tier 1 source |"
        )
    
    return "\n".join(output)


def main():
    """Main execution."""
    # Parse command line arguments
    min_alert = 'Green'
    days = 30
    
    if '--alert-level' in sys.argv:
        try:
            idx = sys.argv.index('--alert-level')
            min_alert = sys.argv[idx + 1]
            if min_alert not in ALERT_LEVELS:
                print(f"Invalid alert level. Use: Red, Orange, or Green")
                sys.exit(1)
        except IndexError:
            print("Usage: python fetch_gdacs.py [--alert-level Red|Orange|Green] [--days 30]")
            sys.exit(1)
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_gdacs.py [--alert-level Red|Orange|Green] [--days 30]")
            sys.exit(1)
    
    print(f"Fetching GDACS alerts ({min_alert}+ level, past {days} days)...\n")
    
    # Fetch and parse
    xml_content = fetch_feed(GDACS_FEED)
    disasters = parse_disasters(xml_content, min_alert, days)
    
    # Output results
    print(format_for_daily_review(disasters))
    print("\n" + "="*80 + "\n")
    print(format_for_classification_table(disasters))
    
    # Summary for confidence assessment
    if disasters:
        red_count = sum(1 for d in disasters if d['alert_level'] == 'Red')
        orange_count = sum(1 for d in disasters if d['alert_level'] == 'Orange')
        
        print(f"\n{'='*80}")
        if red_count > 0:
            print(f"⚠️  {red_count} RED alert(s) detected — SEVERE humanitarian impact")
            print("    HIGH confidence for marking J0 as 'Observed'")
        elif orange_count > 0:
            print(f"⚠️  {orange_count} ORANGE alert(s) detected — MEDIUM humanitarian impact")
            print("    MEDIUM confidence for marking J0 as 'Observed'")
        else:
            print("ℹ️  Only GREEN alerts — Minor impact")
        
        print(f"\n✅ Cross-verify with:")
        print("   - Reuters disaster coverage")
        print("   - BBC World News")
        print("   - ReliefWeb (UN OCHA) for humanitarian impact")
        print(f"✅ Mark J0 as 'Observed' if Orange/Red alert and cross-verified")


if __name__ == '__main__':
    main()


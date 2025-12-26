#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRED News Monitor
Monitors St. Louis Fed FRED announcements for new economic data series.
Helps track when relevant economic indicators become available for prophecy tracking (node H0).

Usage:
    python fetch_fred_news.py [--days 30]
"""

import sys
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import urllib.request
import urllib.error
import re

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# FRED News RSS feed
FRED_NEWS_FEED = "https://news.research.stlouisfed.org/feed/"

# Economic indicators keywords to watch for (H0 mapping)
RELEVANT_KEYWORDS = [
    'inflation', 'cpi', 'consumer price',
    'unemployment', 'employment', 'jobs',
    'gdp', 'gross domestic product', 'economic growth',
    'trade', 'import', 'export', 'tariff',
    'recession', 'crisis', 'financial',
    'supply chain', 'shortage',
    'debt', 'deficit',
    'wage', 'income', 'earnings'
]


def fetch_feed(feed_url: str) -> str:
    """Fetch FRED news RSS feed."""
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub('<.*?>', '', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def is_relevant(title: str, description: str) -> bool:
    """Check if announcement is relevant to economic tracking."""
    combined = (title + ' ' + description).lower()
    return any(keyword in combined for keyword in RELEVANT_KEYWORDS)


def parse_announcements(xml_content: str, days_back: int = 30) -> List[Dict]:
    """Parse FRED news feed."""
    root = ET.fromstring(xml_content)
    announcements = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    for item in root.findall('.//item'):
        title_elem = item.find('title')
        link_elem = item.find('link')
        desc_elem = item.find('description')
        pubdate_elem = item.find('pubDate')
        category_elem = item.find('category')
        
        if title_elem is None or link_elem is None:
            continue
        
        # Parse date
        try:
            if pubdate_elem is not None:
                pub_date = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S %z')
                pub_date = pub_date.replace(tzinfo=None)  # Remove timezone for comparison
            else:
                continue
        except ValueError:
            continue
        
        # Filter by date
        if pub_date < cutoff_date:
            continue
        
        title = title_elem.text if title_elem is not None else 'No title'
        description = clean_html(desc_elem.text) if desc_elem is not None else ''
        category = category_elem.text if category_elem is not None else 'General'
        
        # Check relevance
        relevant = is_relevant(title, description)
        
        announcement = {
            'title': title,
            'description': description[:200] + '...' if len(description) > 200 else description,
            'category': category,
            'date': pub_date.strftime('%Y-%m-%d'),
            'url': link_elem.text,
            'relevant': relevant
        }
        
        announcements.append(announcement)
    
    # Sort by date (newest first)
    announcements.sort(key=lambda x: x['date'], reverse=True)
    return announcements


def format_for_daily_review(announcements: List[Dict]) -> str:
    """Format FRED announcements for review."""
    if not announcements:
        return "No FRED announcements in the specified period.\n"
    
    relevant = [a for a in announcements if a['relevant']]
    other = [a for a in announcements if not a['relevant']]
    
    output = ["## FRED Economic Data Updates — Node H0 (Economic Indicators)\n"]
    
    if relevant:
        output.append(f"### ⭐ Relevant to Economic Tracking ({len(relevant)})\n")
        output.append("| Date | Title | Category | Link |")
        output.append("|------|-------|----------|------|")
        
        for a in relevant:
            output.append(f"| {a['date']} | **{a['title']}** | {a['category']} | [FRED]({a['url']}) |")
        
        output.append("")
    
    if other:
        output.append(f"### Other Announcements ({len(other)})\n")
        output.append("| Date | Title | Category |")
        output.append("|------|-------|----------|")
        
        for a in other[:5]:  # Show only first 5
            output.append(f"| {a['date']} | {a['title']} | {a['category']} |")
        
        if len(other) > 5:
            output.append(f"| ... | ({len(other) - 5} more) | ... |")
        
        output.append("")
    
    output.append(f"**Total:** {len(announcements)} announcements ({len(relevant)} relevant)")
    output.append("\n**Note:** This tracks FRED announcements about new data series.")
    output.append("**For actual economic data:** Use FRED API (see scripts/README.md)")
    output.append("\n**Scripture anchor:** Revelation 17-18 — 'merchants/trade' patterns")
    output.append("**Node ID:** H0 (Babylon-like trade/economic patterns)")
    output.append("**Source:** Federal Reserve Economic Data (FRED) — Tier 1")
    
    return "\n".join(output)


def main():
    """Main execution."""
    days = 30
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_fred_news.py [--days 30]")
            sys.exit(1)
    
    print(f"Fetching FRED announcements (past {days} days)...\n")
    
    # Fetch and parse
    xml_content = fetch_feed(FRED_NEWS_FEED)
    announcements = parse_announcements(xml_content, days)
    
    # Output results
    print(format_for_daily_review(announcements))
    
    # Summary
    relevant_count = sum(1 for a in announcements if a['relevant'])
    if relevant_count > 0:
        print(f"\n{'='*80}")
        print(f"✅ {relevant_count} relevant economic data announcement(s) found")
        print("\n💡 To access actual economic data:")
        print("   1. Sign up for FRED API key: https://fredaccount.stlouisfed.org/")
        print("   2. Use FRED API to query indicators (inflation, unemployment, GDP, trade)")
        print("   3. See scripts/README.md for planned fetch_economic.py script")
        print("\n📊 Relevant indicators for H0 (Babylon/merchants):")
        print("   - Inflation (CPI, PCE)")
        print("   - Unemployment rate")
        print("   - Trade deficit/surplus")
        print("   - GDP growth")
        print("   - Supply chain disruptions")


if __name__ == '__main__':
    main()


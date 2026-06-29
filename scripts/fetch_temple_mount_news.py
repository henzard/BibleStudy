#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temple Mount & Middle East News Monitor
Monitors news about Temple Mount, Jerusalem, and Middle East developments.
Maps to J3 (Abomination of desolation) and MS0 (Man of sin) prophecy nodes.

BIBLE-ONLY APPROACH:
- Tracks observable events (Temple Mount access, conflicts, political developments)
- Does NOT claim fulfillment - only maps to biblical categories
- Scripture anchor: Dan 9:27; Matt 24:15; 2 Thess 2:3-4

Usage:
    python fetch_temple_mount_news.py [--days 7]
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

# News sources for Temple Mount / Middle East monitoring
SOURCES = {
    'times_of_israel': {
        'url': 'https://www.timesofisrael.com/feed/',
        'name': 'Times of Israel',
        'credibility': 'Tier 2 (specialty outlet, known bias acknowledged)'
    },
    'jerusalem_post': {
        'url': 'https://www.jpost.com/rss',
        'name': 'Jerusalem Post',
        'credibility': 'Tier 2 (specialty outlet, known bias acknowledged)'
    },
    'al_jazeera': {
        'url': 'https://www.aljazeera.com/xml/rss/all.xml',
        'name': 'Al Jazeera',
        'credibility': 'Tier 2 (mainstream, cross-spectrum verification required)'
    },
    'middle_east_monitor': {
        'url': 'https://www.middleeastmonitor.com/feed/',
        'name': 'Middle East Monitor',
        'credibility': 'Tier 2 (specialty outlet, cross-spectrum verification required)'
    }
}

# Keywords for Temple Mount / Jerusalem / Middle East relevance
TEMPLE_MOUNT_KEYWORDS = [
    'temple mount', 'al-aqsa', 'al aqsa', 'haram al-sharif', 'haram al sharif',
    'dome of the rock', 'jerusalem', 'old city', 'western wall', 'wailing wall',
    'third temple', 'temple', 'mount moriah', 'holy site'
]

MIDDLE_EAST_KEYWORDS = [
    'israel', 'palestine', 'gaza', 'west bank', 'judea', 'samaria',
    'hezbollah', 'hamas', 'iran', 'syria', 'lebanon', 'jordan',
    'middle east', 'mideast', 'israeli', 'palestinian'
]

PROPHECY_RELEVANT_KEYWORDS = [
    # J3 - Abomination of desolation markers
    'temple', 'sanctuary', 'abomination', 'desolation', 'sacrifice', 'worship',
    # MS0 - Man of sin markers (observable characteristics)
    'claims god', 'exalts himself', 'opposes god', 'sits in temple',
    'messianic', 'mahdi', 'false prophet', 'deception', 'signs and wonders',
    # General end-times relevance
    'covenant', 'peace treaty', 'jerusalem', 'israel', 'middle east conflict'
]


def fetch_feed(feed_url: str) -> str:
    """Fetch a single RSS feed (network I/O only)."""
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching feed {feed_url}: {e}", file=sys.stderr)
        return ""


def fetch_raw(sources: Dict = None) -> Dict[str, str]:
    """Fetch raw RSS text for all configured sources (network I/O only).

    Returns a mapping of source display name -> raw feed text.
    """
    if sources is None:
        sources = SOURCES
    raw = {}
    for source_info in sources.values():
        raw[source_info['name']] = fetch_feed(source_info['url'])
    return raw


def clean_html(text: str) -> str:
    """Remove HTML tags and entities from text."""
    if text is None:
        return ""
    clean = re.sub('<.*?>', '', text)
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'")
    clean = clean.replace('&nbsp;', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def parse_pubdate(pubdate_text: str) -> datetime:
    """Parse publication date from RSS feed."""
    clean = clean_html(pubdate_text)
    
    # Common RSS date formats
    formats = [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    
    return datetime.utcnow()


def classify_article(title: str, description: str, source: str) -> Dict[str, any]:
    """Classify article by relevance to prophecy nodes."""
    combined = (title + ' ' + description).lower()
    
    # Check for Temple Mount keywords
    temple_matches = [kw for kw in TEMPLE_MOUNT_KEYWORDS if kw in combined]
    
    # Check for Middle East keywords
    me_matches = [kw for kw in MIDDLE_EAST_KEYWORDS if kw in combined]
    
    # Check for prophecy-relevant keywords
    prophecy_matches = [kw for kw in PROPHECY_RELEVANT_KEYWORDS if kw in combined]
    
    # Determine primary node mapping
    node = None
    scripture = None
    category = None
    
    if 'temple mount' in combined or 'al-aqsa' in combined or 'al aqsa' in combined:
        node = 'J3'  # Abomination of desolation (Matt 24:15; Dan 9:27)
        scripture = 'Matt 24:15; Dan 9:27'
        category = 'Temple Mount'
    elif any(kw in combined for kw in ['temple', 'sanctuary', 'abomination', 'desolation']):
        node = 'J3'
        scripture = 'Matt 24:15; Dan 9:27'
        category = 'Temple/Sanctuary'
    elif any(kw in combined for kw in ['claims god', 'exalts himself', 'opposes god', 'sits in temple', 'messianic', 'mahdi']):
        node = 'MS0'  # Man of sin characteristics (2 Thess 2:3-4)
        scripture = '2 Thess 2:3-4'
        category = 'Man of Sin Characteristics'
    elif any(kw in combined for kw in ['false prophet', 'deception', 'signs and wonders']):
        node = 'MS1'  # Lying signs and wonders (2 Thess 2:9-12)
        scripture = '2 Thess 2:9-12'
        category = 'Deception/Signs'
    elif me_matches:
        node = 'J0'  # Wars and rumors (Matt 24:6-7)
        scripture = 'Matt 24:6-7'
        category = 'Middle East Conflict'
    else:
        node = 'General'
        scripture = 'Various'
        category = 'Middle East News'
    
    # Determine confidence
    if len(temple_matches) >= 2 and node == 'J3':
        confidence = 'High'  # Multiple Temple Mount keywords
    elif len(prophecy_matches) >= 2:
        confidence = 'Med'  # Multiple prophecy-relevant keywords
    elif temple_matches or (me_matches and prophecy_matches):
        confidence = 'Med'
    else:
        confidence = 'Low'
    
    relevant = len(temple_matches) > 0 or len(prophecy_matches) > 0 or (len(me_matches) > 0 and node in ['J3', 'MS0', 'MS1'])
    
    return {
        'node': node,
        'scripture': scripture,
        'category': category,
        'confidence': confidence,
        'relevant': relevant,
        'keywords': (temple_matches + prophecy_matches[:2])[:3]
    }


def parse_news(xml_content: str, source_name: str, days_back: int = 7) -> List[Dict]:
    """Parse RSS feed for Temple Mount / Middle East news."""
    if not xml_content:
        return []
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return []
    
    articles = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    for item in root.findall('.//item'):
        title_elem = item.find('title')
        link_elem = item.find('link')
        desc_elem = item.find('description')
        pubdate_elem = item.find('pubDate')
        
        if title_elem is None or link_elem is None:
            continue
        
        # Parse date
        try:
            if pubdate_elem is not None:
                pub_date = parse_pubdate(pubdate_elem.text)
            else:
                continue
        except Exception:
            continue
        
        # Filter by date
        if pub_date < cutoff_date:
            continue
        
        title = clean_html(title_elem.text) if title_elem is not None else 'No title'
        description = clean_html(desc_elem.text) if desc_elem is not None else ''
        
        # Classify
        classification = classify_article(title, description, source_name)
        
        if not classification['relevant']:
            continue
        
        article = {
            'title': title,
            'description': description[:200] + '...' if len(description) > 200 else description,
            'date': pub_date.strftime('%Y-%m-%d'),
            'url': link_elem.text,
            'source': source_name,
            'node': classification['node'],
            'scripture': classification['scripture'],
            'category': classification['category'],
            'confidence': classification['confidence'],
            'keywords': classification['keywords']
        }
        
        articles.append(article)
    
    # Sort by date (newest first)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


def parse(raw: str, source: str = "Unknown", days: int = 7) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into relevant article dicts.

    Fields per article: title, description, date, url, source, node,
    scripture, category, confidence, keywords.
    """
    return parse_news(raw, source, days)


def collect(days: int = 7) -> List[Dict]:
    """Fetch + parse + dedupe across all configured sources."""
    all_articles = []
    for source_info in SOURCES.values():
        xml_content = fetch_feed(source_info['url'])
        all_articles.extend(parse_news(xml_content, source_info['name'], days))

    # Remove duplicates (same title/URL)
    seen = set()
    unique_articles = []
    for a in all_articles:
        key = (a['title'].lower(), a['url'])
        if key not in seen:
            seen.add(key)
            unique_articles.append(a)

    unique_articles.sort(key=lambda x: x['date'], reverse=True)
    return unique_articles


def format_for_daily_review(articles: List[Dict]) -> str:
    """Format Temple Mount / Middle East news for daily review."""
    if not articles:
        return "No relevant Temple Mount / Middle East news in the specified period.\n"
    
    # Group by node
    by_node = {}
    for a in articles:
        node = a['node']
        if node not in by_node:
            by_node[node] = []
        by_node[node].append(a)
    
    output = ["## Temple Mount & Middle East News\n"]
    output.append("**BIBLE-ONLY APPROACH:** Observing events that *resemble* biblical categories. NOT claiming fulfillment.\n")
    
    for node in sorted(by_node.keys()):
        node_articles = by_node[node]
        output.append(f"### {node} — {node_articles[0]['scripture']} ({len(node_articles)})\n")
        output.append("| Date | Headline | Category | Confidence | Source | Link |")
        output.append("|------|----------|----------|------------|--------|------|")
        
        for a in node_articles:
            headline = a['title'][:50] + '...' if len(a['title']) > 50 else a['title']
            output.append(f"| {a['date']} | **{headline}** | {a['category']} | {a['confidence']} | {a['source']} | [Link]({a['url']}) |")
        
        output.append("")
    
    output.append(f"**Total:** {len(articles)} relevant articles")
    output.append("\n**Scripture anchors:**")
    output.append("- **J3:** Dan 9:27; Matt 24:15 — Abomination of desolation")
    output.append("- **MS0:** 2 Thess 2:3-4 — Man of sin characteristics")
    output.append("- **MS1:** 2 Thess 2:9-12 — Lying signs and wonders")
    output.append("\n**Note:** Cross-spectrum verification required (Tier 2 sources). Verify with Reuters, AP, BBC.")
    
    return "\n".join(output)


def main():
    """Main execution."""
    days = 7
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_temple_mount_news.py [--days 7]")
            sys.exit(1)
    
    print(f"Fetching Temple Mount & Middle East news (past {days} days)...\n")
    
    all_articles = []
    
    # Fetch from all sources
    for source_id, source_info in SOURCES.items():
        print(f"Fetching from {source_info['name']}...")
        xml_content = fetch_feed(source_info['url'])
        articles = parse_news(xml_content, source_info['name'], days)
        all_articles.extend(articles)
        print(f"  Found {len(articles)} relevant articles")
    
    # Remove duplicates (same title/URL)
    seen = set()
    unique_articles = []
    for a in all_articles:
        key = (a['title'].lower(), a['url'])
        if key not in seen:
            seen.add(key)
            unique_articles.append(a)
    
    # Sort by date
    unique_articles.sort(key=lambda x: x['date'], reverse=True)
    
    # Output results
    print("\n" + "="*80)
    print(format_for_daily_review(unique_articles))
    
    # Summary
    if unique_articles:
        print(f"\n{'='*80}")
        print(f"✅ {len(unique_articles)} relevant Temple Mount / Middle East article(s) found")
        print("\n💡 Why this matters (Bible-only perspective):")
        print("   - J3 (Abomination): Dan 9:27 mentions 'abomination' in context of temple/sacrifice")
        print("   - MS0 (Man of sin): 2 Thess 2:3-4 describes one who 'sits in temple of God'")
        print("   - Observing patterns, NOT claiming fulfillment")
        print("   - Cross-spectrum verification required (Tier 2 sources)")
        print("\n📊 Cross-verify with:")
        print("   - Reuters Middle East coverage")
        print("   - AP News Middle East")
        print("   - BBC Middle East")
        print("   - UN Peacekeeping (conflict monitoring)")


if __name__ == '__main__':
    main()

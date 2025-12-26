#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UN Peacekeeping News Monitor
Monitors UN peacekeeping operations for conflicts, casualties, and humanitarian crises.
Maps to J0 (wars and rumors of wars) prophecy node.

Usage:
    python fetch_un_peacekeeping.py [--days 30]
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

# UN Peacekeeping RSS feed
UN_PKO_FEED = "https://peacekeeping.un.org/en/rss.xml"

# Keywords for conflict/war indicators
WAR_KEYWORDS = [
    'conflict', 'fighting', 'offensive', 'attack', 'rebel', 'armed group',
    'violence', 'clashes', 'battle', 'warfare', 'military operation',
    'peacekeeping', 'ceasefire', 'armed conflict', 'insurgency'
]

CASUALTY_KEYWORDS = [
    'casualties', 'deaths', 'killed', 'wounded', 'injured', 'victims',
    'civilian casualties', 'fatalities', 'dead', 'died'
]

HUMANITARIAN_KEYWORDS = [
    'displaced', 'refugees', 'humanitarian crisis', 'emergency',
    'aid', 'relief', 'famine', 'starvation', 'persecution'
]


def fetch_feed(feed_url: str) -> str:
    """Fetch UN Peacekeeping RSS feed."""
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)


def clean_html(text: str) -> str:
    """Remove HTML tags and entities from text."""
    if text is None:
        return ""
    # Remove HTML tags
    clean = re.sub('<.*?>', '', text)
    # Decode HTML entities
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'")
    clean = clean.replace('&nbsp;', ' ')
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def extract_numbers(text: str) -> List[str]:
    """Extract significant numbers from text (casualties, displaced, etc.)."""
    # Match patterns like "2.39 million", "90%", "1,140", "77 per cent"
    patterns = [
        r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|thousand|billion)',
        r'\d+(?:,\d{3})*',
        r'\d+(?:\.\d+)?\s*(?:per cent|percent|%)'
    ]
    
    numbers = []
    combined = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, combined)
        numbers.extend(matches[:3])  # Max 3 per pattern
    
    return list(set(numbers))[:5]  # Return up to 5 unique numbers


def classify_article(title: str, description: str) -> Dict[str, any]:
    """Classify article by relevance to prophecy nodes."""
    combined = (title + ' ' + description).lower()
    
    # Check for conflict/war
    war_matches = [kw for kw in WAR_KEYWORDS if kw in combined]
    casualty_matches = [kw for kw in CASUALTY_KEYWORDS if kw in combined]
    humanitarian_matches = [kw for kw in HUMANITARIAN_KEYWORDS if kw in combined]
    
    # Extract numbers (casualties, displaced, etc.)
    numbers = extract_numbers(title + ' ' + description)
    
    # Determine confidence
    if casualty_matches and numbers:
        confidence = 'High'  # Verifiable casualty numbers
    elif war_matches and ('offensive' in combined or 'fighting' in combined or 'attack' in combined):
        confidence = 'High'  # Active conflict
    elif humanitarian_matches and numbers:
        confidence = 'Med'  # Humanitarian crisis with numbers
    elif war_matches or casualty_matches:
        confidence = 'Med'  # General conflict reporting
    else:
        confidence = 'Low'
    
    # Determine category
    if casualty_matches:
        category = 'Casualties'
    elif 'offensive' in combined or 'fighting' in combined or 'attack' in combined:
        category = 'Active Conflict'
    elif humanitarian_matches:
        category = 'Humanitarian Crisis'
    elif war_matches:
        category = 'Conflict/War'
    else:
        category = 'Peacekeeping'
    
    relevant = len(war_matches) > 0 or len(casualty_matches) > 0 or len(humanitarian_matches) > 0
    
    return {
        'keywords': (war_matches + casualty_matches + humanitarian_matches)[:3],
        'numbers': numbers,
        'confidence': confidence,
        'category': category,
        'relevant': relevant
    }


def parse_pubdate(pubdate_text: str) -> datetime:
    """Parse publication date from UN Peacekeeping feed."""
    # The feed has HTML in pubDate, extract the date string
    clean = clean_html(pubdate_text)
    
    try:
        # Format: "Wed, 24 Dec 2025 12:21:47 EST"
        return datetime.strptime(clean, '%a, %d %b %Y %H:%M:%S %Z')
    except ValueError:
        try:
            # Try without timezone
            return datetime.strptime(clean.rsplit(' ', 1)[0], '%a, %d %b %Y %H:%M:%S')
        except ValueError:
            return datetime.utcnow()


def parse_news(xml_content: str, days_back: int = 30) -> List[Dict]:
    """Parse UN Peacekeeping news feed."""
    root = ET.fromstring(xml_content)
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
        classification = classify_article(title, description)
        
        if not classification['relevant']:
            continue  # Skip irrelevant articles
        
        article = {
            'title': title,
            'description': description[:200] + '...' if len(description) > 200 else description,
            'date': pub_date.strftime('%Y-%m-%d'),
            'url': link_elem.text,
            'keywords': classification['keywords'],
            'numbers': classification['numbers'],
            'confidence': classification['confidence'],
            'category': classification['category']
        }
        
        articles.append(article)
    
    # Sort by date (newest first)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


def format_for_daily_review(articles: List[Dict]) -> str:
    """Format UN Peacekeeping news for daily review."""
    if not articles:
        return "No relevant UN Peacekeeping news in the specified period.\n"
    
    # Group by category
    by_category = {}
    for a in articles:
        cat = a['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(a)
    
    output = ["## UN Peacekeeping News — Node J0 (Wars and Rumors of Wars)\n"]
    
    for category, cat_articles in sorted(by_category.items()):
        output.append(f"### {category} ({len(cat_articles)})\n")
        output.append("| Date | Headline | Key Data | Confidence | Link |")
        output.append("|------|----------|----------|------------|------|")
        
        for a in cat_articles:
            headline = a['title'][:55] + '...' if len(a['title']) > 55 else a['title']
            key_data = ', '.join(a['numbers'][:2]) if a['numbers'] else ', '.join(a['keywords'][:2])
            output.append(f"| {a['date']} | **{headline}** | {key_data} | {a['confidence']} | [UN PKO]({a['url']}) |")
        
        output.append("")
    
    output.append(f"**Total:** {len(articles)} relevant articles")
    output.append("\n**Scripture anchor:** Matthew 24:6-7 — 'wars and rumours of wars… nation against nation'")
    output.append("**Node ID:** J0 (Beginning of sorrows)")
    output.append("**Source:** UN Peacekeeping Operations — Tier 1 (official UN operations)")
    output.append("**Note:** Tracks active conflicts, peacekeeping missions, civilian casualties")
    
    return "\n".join(output)


def format_for_classification_table(articles: List[Dict]) -> str:
    """Format articles for copy-paste into daily review classification table."""
    if not articles:
        return ""
    
    output = ["\n" + "="*80]
    output.append("\n## For classification table (copy to daily review):\n")
    
    for a in articles[:10]:  # Top 10 most relevant
        key_data = ', '.join(a['numbers'][:2]) if a['numbers'] else ', '.join(a['keywords'][:2])
        
        output.append(f"| UN Peacekeeping: {a['title'][:45]} | Conflict Zone | J0 | Matt 24:6-7 | {a['category']} | {a['confidence']} | UN PKO Tier 1; {key_data} |")
    
    return "\n".join(output)


def main():
    """Main execution."""
    days = 30
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_un_peacekeeping.py [--days 30]")
            sys.exit(1)
    
    print(f"Fetching UN Peacekeeping news (past {days} days)...\n")
    
    # Fetch and parse
    xml_content = fetch_feed(UN_PKO_FEED)
    articles = parse_news(xml_content, days)
    
    # Output results
    print(format_for_daily_review(articles))
    print(format_for_classification_table(articles))
    
    # Summary
    if articles:
        print(f"\n{'='*80}")
        print(f"✅ {len(articles)} relevant UN Peacekeeping article(s) found")
        print("\n💡 Why UN Peacekeeping matters:")
        print("   - Official conflict zone monitoring")
        print("   - Verifiable casualty data")
        print("   - Active war/peacekeeping operations")
        print("   - 'Wars and rumors of wars' indicator (Matt 24:6-7)")
        print("   - Tier 1 source (UN operations)")
        print("\n📊 Cross-verify with:")
        print("   - GDACS (disaster impacts in conflict zones)")
        print("   - ReliefWeb (humanitarian impact)")
        print("   - UNHCR (refugee/displacement data)")


if __name__ == '__main__':
    main()


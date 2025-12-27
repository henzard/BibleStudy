#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Bank News Monitor
Monitors World Bank news for poverty, economic crisis, and disaster reports.
Maps to H0 (economic/poverty) and J0 (disasters/famines) prophecy nodes.

Usage:
    python fetch_worldbank_news.py [--days 7]
"""

import sys
import io
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import urllib.request
import urllib.error
import re

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, will use system env vars

# World Bank news RSS feed (EIN News aggregator)
# Load key from environment variable (secure)
EINNEWS_RSS_KEY = os.getenv('EINNEWS_RSS_KEY')
if not EINNEWS_RSS_KEY:
    print("⚠️  EINNEWS_RSS_KEY not found in environment variables")
    print("   Set in .env file or use default (may be rate-limited)")
    EINNEWS_RSS_KEY = "YOUR_EINNEWS_KEY_HERE"  # Fallback for backward compatibility

WB_NEWS_FEED = f"https://worldbank.einnews.com/rss/{EINNEWS_RSS_KEY}"

# Keywords for different prophecy nodes
POVERTY_KEYWORDS = [
    'poverty', 'poor', 'famine', 'hunger', 'food security', 'malnutrition',
    'food crisis', 'humanitarian', 'aid', 'relief', 'vulnerable',
    'food assistance', 'drought', 'crop failure'
]

DISASTER_KEYWORDS = [
    'cyclone', 'hurricane', 'typhoon', 'flood', 'earthquake', 'tsunami',
    'disaster', 'damage', 'destroyed', 'devastated', 'emergency',
    'volcano', 'wildfire', 'landslide'
]

ECONOMIC_KEYWORDS = [
    'economic crisis', 'recession', 'collapse', 'inflation', 'debt crisis',
    'financial crisis', 'bankruptcy', 'economic instability',
    'currency crisis', 'trade collapse', 'market crash'
]


def fetch_feed(feed_url: str) -> str:
    """Fetch World Bank news RSS feed."""
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
    clean = clean.replace('&#8230;', '...').replace('&nbsp;', ' ')
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def classify_article(title: str, description: str) -> Dict[str, any]:
    """Classify article by relevance to prophecy nodes."""
    combined = (title + ' ' + description).lower()
    
    nodes = []
    keywords_found = []
    
    # Check for poverty/famine (J0)
    poverty_matches = [kw for kw in POVERTY_KEYWORDS if kw in combined]
    if poverty_matches:
        nodes.append('J0')
        keywords_found.extend(poverty_matches[:2])  # Top 2
    
    # Check for disasters (J0)
    disaster_matches = [kw for kw in DISASTER_KEYWORDS if kw in combined]
    if disaster_matches:
        if 'J0' not in nodes:
            nodes.append('J0')
        keywords_found.extend(disaster_matches[:2])
    
    # Check for economic crisis (H0)
    economic_matches = [kw for kw in ECONOMIC_KEYWORDS if kw in combined]
    if economic_matches:
        nodes.append('H0')
        keywords_found.extend(economic_matches[:2])
    
    # Determine confidence
    if disaster_matches and any(x in combined for x in ['billion', 'million', 'deaths', 'destroyed']):
        confidence = 'High'
    elif poverty_matches and any(x in combined for x in ['increase', 'crisis', 'forecast']):
        confidence = 'Med'
    elif economic_matches:
        confidence = 'Med'
    else:
        confidence = 'Low'
    
    return {
        'nodes': nodes,
        'keywords': list(set(keywords_found))[:3],  # Max 3 unique keywords
        'confidence': confidence,
        'relevant': len(nodes) > 0
    }


def parse_news(xml_content: str, days_back: int = 7) -> List[Dict]:
    """Parse World Bank news feed."""
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
                # Format: "Fri, 26 Dec 2025 05:46:24 GMT"
                pub_date = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S %Z')
            else:
                continue
        except ValueError:
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
            'description': description[:150] + '...' if len(description) > 150 else description,
            'date': pub_date.strftime('%Y-%m-%d'),
            'url': link_elem.text,
            'nodes': classification['nodes'],
            'keywords': classification['keywords'],
            'confidence': classification['confidence']
        }
        
        articles.append(article)
    
    # Sort by date (newest first)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


def format_for_daily_review(articles: List[Dict]) -> str:
    """Format World Bank news for daily review."""
    if not articles:
        return "No relevant World Bank news in the specified period.\n"
    
    # Group by node
    j0_articles = [a for a in articles if 'J0' in a['nodes']]
    h0_articles = [a for a in articles if 'H0' in a['nodes']]
    
    output = ["## World Bank News — Poverty, Disasters, Economic Indicators\n"]
    
    if j0_articles:
        output.append(f"### Node J0: Beginning of Sorrows (Disasters/Famines) — {len(j0_articles)} articles\n")
        output.append("| Date | Headline | Keywords | Confidence | Link |")
        output.append("|------|----------|----------|------------|------|")
        
        for a in j0_articles:
            keywords = ', '.join(a['keywords'][:2])
            output.append(f"| {a['date']} | **{a['title'][:60]}{'...' if len(a['title']) > 60 else ''}** | {keywords} | {a['confidence']} | [Source]({a['url']}) |")
        
        output.append("\n**Scripture anchor:** Matthew 24:7-8 — 'famines, pestilences, earthquakes… beginning of sorrows'\n")
    
    if h0_articles:
        output.append(f"### Node H0: Babylon/Merchants Pattern (Economic Crisis) — {len(h0_articles)} articles\n")
        output.append("| Date | Headline | Keywords | Confidence | Link |")
        output.append("|------|----------|----------|------------|------|")
        
        for a in h0_articles:
            keywords = ', '.join(a['keywords'][:2])
            output.append(f"| {a['date']} | **{a['title'][:60]}{'...' if len(a['title']) > 60 else ''}** | {keywords} | {a['confidence']} | [Source]({a['url']}) |")
        
        output.append("\n**Scripture anchor:** Revelation 17-18 — 'merchants weep… for no man buyeth their merchandise'\n")
    
    output.append(f"**Total:** {len(articles)} relevant articles")
    output.append("\n**Source:** World Bank (via EIN News) — Tier 1 (official WB projects/reports)")
    output.append("**Note:** World Bank data = authoritative poverty, disaster damage, economic indicators")
    
    return "\n".join(output)


def format_for_classification_table(articles: List[Dict]) -> str:
    """Format articles for copy-paste into daily review classification table."""
    if not articles:
        return ""
    
    output = ["\n" + "="*80]
    output.append("\n## For classification table (copy to daily review):\n")
    
    for a in articles[:10]:  # Top 10 most relevant
        nodes = ', '.join(a['nodes'])
        scripture = 'Matt 24:7-8' if 'J0' in a['nodes'] else 'Rev 17-18'
        category = 'Disaster/Famine' if 'J0' in a['nodes'] else 'Economic'
        
        output.append(f"| World Bank: {a['title'][:50]} | Global | {nodes} | {scripture} | {category} | {a['confidence']} | World Bank Tier 1; {', '.join(a['keywords'][:2])} |")
    
    return "\n".join(output)


def main():
    """Main execution."""
    days = 7
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_worldbank_news.py [--days 7]")
            sys.exit(1)
    
    print(f"Fetching World Bank news (past {days} days)...\n")
    
    # Fetch and parse
    xml_content = fetch_feed(WB_NEWS_FEED)
    articles = parse_news(xml_content, days)
    
    # Output results
    print(format_for_daily_review(articles))
    print(format_for_classification_table(articles))
    
    # Summary
    if articles:
        print(f"\n{'='*80}")
        print(f"✅ {len(articles)} relevant World Bank article(s) found")
        print("\n💡 Why World Bank matters:")
        print("   - Authoritative poverty data (tracks 'famines' proxy)")
        print("   - Official disaster damage assessments")
        print("   - Economic crisis indicators")
        print("   - Tier 1 source (international organization)")
        print("\n📊 Cross-verify with:")
        print("   - UN ReliefWeb (humanitarian impact)")
        print("   - World Food Programme (famine/food security)")
        print("   - GDACS (disaster alerts)")


if __name__ == '__main__':
    main()


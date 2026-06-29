#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFF (Electronic Frontier Foundation) Blog RSS Fetcher
Fetches digital rights, surveillance, and privacy news from EFF's Deeplinks blog.

Node: B2 (Digital ID / Commerce Control Patterns)
Scripture: Revelation 13:16-17 — "mark in their right hand, or in their foreheads... no man might buy or sell"

Usage:
    python fetch_eff_news.py [--days 7]
"""

import sys
import io
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
import argparse

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EFF_RSS_URL = "https://www.eff.org/rss/updates.xml"

# Keywords for B2 relevance (digital ID, surveillance, biometrics, commerce control)
B2_KEYWORDS = [
    'biometric', 'facial recognition', 'digital id', 'digital identity',
    'surveillance', 'tracking', 'age verification', 'vpn',
    'fingerprint', 'iris scan', 'palm scan', 'voice recognition',
    'cbdc', 'digital currency', 'crypto', 'blockchain payment',
    'social credit', 'compliance', 'mandate', 'verification',
    'authentication', 'authorization', 'access control',
    'payment system', 'cashless', 'digital wallet'
]


def fetch_raw():
    """Fetch raw EFF blog RSS feed text (network I/O only)."""
    response = requests.get(EFF_RSS_URL, timeout=10)
    response.raise_for_status()
    return response.text


def parse(raw, days=7):
    """Pure parse: extract B2-relevant articles from EFF RSS XML text.

    Returns a list of dicts with fields: title, link, pub_date, keywords,
    description, plus classification fields category, confidence, relevance.
    """
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"Error parsing RSS XML: {e}")
        return []

    channel = root.find('channel')
    items = channel.findall('item')

    cutoff_date = datetime.now() - timedelta(days=days)
    articles = []

    for item in items:
        title = item.find('title').text if item.find('title') is not None else 'N/A'
        link = item.find('link').text if item.find('link') is not None else 'N/A'
        pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else None
        description_elem = item.find('description')
        description = description_elem.text if description_elem is not None else ''

        # Parse date (format: "Thu, 13 Nov 2025 17:38:50 +0000")
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                pub_date = pub_date.replace(tzinfo=None)  # Remove timezone for comparison
            except ValueError:
                continue

            if pub_date < cutoff_date:
                continue

        # Check for B2 relevance
        content_lower = (title + ' ' + description).lower()
        matched_keywords = [kw for kw in B2_KEYWORDS if kw in content_lower]

        if matched_keywords:
            truncated_desc = (description[:200] + '...'
                              if len(description) > 200 else description)
            category, confidence, relevance = classify_article(
                title, matched_keywords, truncated_desc)
            articles.append({
                'title': title,
                'link': link,
                'pub_date': pub_date_str,
                'keywords': matched_keywords,
                'description': truncated_desc,
                'category': category,
                'confidence': confidence,
                'relevance': relevance,
            })

    return articles


def collect(days=7):
    """Fetch + parse: return B2-relevant EFF articles for the past `days`."""
    return parse(fetch_raw(), days)


def fetch_eff_rss(days_ago=7):
    """Fetch EFF blog RSS feed (backward-compatible wrapper)."""
    try:
        return fetch_raw()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching EFF RSS: {e}")
        return None


def parse_rss(xml_content, days_ago=7):
    """Parse RSS XML and extract relevant articles (backward-compatible)."""
    return parse(xml_content, days_ago)


def classify_article(title, keywords, description):
    """Classify article and assign confidence level."""
    content = (title + ' ' + description).lower()
    
    # High confidence: Multiple B2 keywords + explicit government/mandatory language
    high_conf_indicators = ['mandate', 'requirement', 'law', 'regulation', 'government', 'federal', 'state']
    biometric_indicators = ['biometric', 'facial recognition', 'fingerprint', 'iris scan', 'palm scan']
    id_indicators = ['digital id', 'digital identity', 'age verification', 'authentication']
    payment_indicators = ['cbdc', 'digital currency', 'cashless', 'payment system']
    
    has_high_conf = any(ind in content for ind in high_conf_indicators)
    has_biometric = any(ind in content for ind in biometric_indicators)
    has_id = any(ind in content for ind in id_indicators)
    has_payment = any(ind in content for ind in payment_indicators)
    
    category = []
    if has_biometric:
        category.append("Biometric Systems")
    if has_id:
        category.append("Digital ID")
    if has_payment:
        category.append("Payment Systems")
    if not category:
        category.append("Surveillance/Privacy")
    
    if (has_biometric or has_id or has_payment) and has_high_conf:
        confidence = "Med"
        relevance = "Potentially relevant to B2 patterns (commerce control)"
    elif has_biometric or has_id or has_payment:
        confidence = "Low"
        relevance = "Related to B2 category (monitoring)"
    else:
        confidence = "Low"
        relevance = "General digital rights (context only)"
    
    return ', '.join(category), confidence, relevance


def main():
    parser = argparse.ArgumentParser(description="Fetch EFF blog RSS for digital rights news.")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of past days to fetch news for (default: 7).")
    args = parser.parse_args()
    
    print(f"Fetching EFF Deeplinks blog (past {args.days} days)...")
    print("\n")
    
    xml_content = fetch_eff_rss(args.days)
    if not xml_content:
        print("❌ Failed to fetch EFF RSS feed.")
        return
    
    articles = parse_rss(xml_content, args.days)
    
    if not articles:
        print(f"⚠️  No B2-relevant articles in the past {args.days} days.")
        print("   (EFF publishes frequently, but not all posts are B2-relevant)")
        return
    
    print(f"## EFF Digital Rights News — Node B2 (Commerce Control Patterns)\n")
    print(f"**Period:** Past {args.days} days")
    print(f"**B2-relevant articles:** {len(articles)}\n")
    
    print("| Date | Category | Title | Confidence | B2 Relevance |")
    print("|------|----------|-------|------------|--------------|")
    
    for article in articles:
        date = article['pub_date'].split(' ')[0:4]  # "Thu, 13 Nov 2025"
        date_str = ' '.join(date)
        
        category, confidence, relevance = classify_article(
            article['title'],
            article['keywords'],
            article['description']
        )
        
        # Truncate title for table
        title_short = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
        
        print(f"| {date_str} | {category} | [{title_short}]({article['link']}) | {confidence} | {relevance} |")
    
    print("\n## Important Disclaimers\n")
    print("1. **Not Claiming Fulfillment:**")
    print("   We track PATTERNS consistent with Rev 13:16-17, NOT definitive fulfillment.")
    print()
    print("2. **Technology ≠ Mark of the Beast:**")
    print("   Digital ID, biometrics, CBDCs are TECHNOLOGIES.")
    print("   The mark requires worship of the beast (Rev 13:15-16) — not observed yet.")
    print()
    print("3. **Monitoring Context Only:**")
    print("   We track infrastructure that COULD enable commerce control.")
    print("   Current systems are not 'the mark' but may be precursors.")
    print()
    print("4. **EFF's Perspective:**")
    print("   EFF opposes surveillance/digital ID from a CIVIL LIBERTIES stance.")
    print("   Their concerns align with our monitoring, but they're not a prophetic source.")
    
    print("\n**Scripture anchor:** Revelation 13:16-17 — 'mark in their right hand... no man might buy or sell'")
    print("**Node ID:** B2 (Commerce control systems / Mark pattern)")
    print("**Source:** Electronic Frontier Foundation — Tier 1 (leading digital rights org)")
    
    print("\n" + "="*80 + "\n")
    
    # Output for classification table
    print("## For classification table (copy to daily review):\n")
    
    for article in articles:
        category, confidence, relevance = classify_article(
            article['title'],
            article['keywords'],
            article['description']
        )
        
        if confidence in ['Med', 'High']:
            date = article['pub_date'].split(' ')[1:4]  # "13 Nov 2025"
            date_str = ' '.join(date)
            print(f"| EFF: {category} — {article['title'][:50]}... | Global | B2 | Rev 13:16-17 | Digital ID/Surveillance | {confidence} | [EFF Blog]({article['link']}) Tier 1 |")
    
    print("\n" + "="*80)
    print("\n💡 EFF Blog RSS tracking operational!")
    print("🔒 Monitoring: Digital ID, biometrics, surveillance, payment systems")
    print("📊 Node B2 (Commerce Control Patterns) now tracked automatically")
    print("\n⚠️  Remember: Technology itself is not 'the mark' — context is infrastructure monitoring.")


if __name__ == "__main__":
    main()


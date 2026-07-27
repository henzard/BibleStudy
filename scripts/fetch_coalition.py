#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ezekiel 38 Coalition Tracker — cooperation among the named nations.
Maps to E38 (Gog Coalition Alignment, Ezek 38:1-6).

BIBLE-ONLY APPROACH:
- Ezek 38 names the coalition: Magog/Rosh (widely identified with the
  Russian sphere), Persia (Iran), Cush (Sudan region), Put (Libya region),
  Gomer/Beth-Togarmah (Anatolia/Turkey region). Identifications are the
  standard historical-geographical ones and are held loosely.
- An event is relevant only when TWO OR MORE of the named nations act
  together: joint exercises, military pacts, arms deals, formal alignment.
- Rising co-occurrence of exactly this set is the signal — not any single
  nation's activity. Observation only; no fulfillment claims (Matt 24:36).

Usage:
    python fetch_coalition.py [--days 14]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "google_news_coalition": {
        "url": ("https://news.google.com/rss/search?"
                "q=(Russia+OR+Iran+OR+Turkey+OR+Sudan+OR+Libya)"
                "+(%22joint+exercise%22+OR+%22military+pact%22+OR+alliance"
                "+OR+%22defense+agreement%22+OR+%22arms+deal%22)"
                "&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (coalition watch)",
    },
    "aljazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "name": "Al Jazeera",
    },
}

# The Ezek 38 watchlist with common aliases. Keys are canonical names.
NATIONS = {
    "Russia": ["russia", "russian", "moscow", "kremlin"],
    "Iran": ["iran", "iranian", "tehran"],
    "Turkey": ["turkey", "turkish", "ankara"],
    "Sudan": ["sudan", "sudanese", "khartoum"],
    "Libya": ["libya", "libyan", "tripoli"],
}

COOPERATION_TERMS = [
    "joint exercise", "joint drill", "joint naval", "military pact",
    "defense agreement", "defence agreement", "defense pact", "defence pact",
    "alliance", "arms deal", "weapons deal", "military cooperation",
    "strategic partnership", "summit", "axis", "coordination", "treaty",
]

MILITARY_TERMS = [
    "joint exercise", "joint drill", "joint naval", "military pact",
    "defense agreement", "defence agreement", "defense pact", "defence pact",
    "arms deal", "weapons deal", "military cooperation",
]


def classify(title: str, description: str) -> Dict:
    """Relevant only when >=2 named nations appear with a cooperation term."""
    combined = f"{title} {description}".lower()
    nations = [name for name, aliases in NATIONS.items()
               if any(a in combined for a in aliases)]
    coop = [t for t in COOPERATION_TERMS if t in combined]

    if len(nations) < 2 or not coop:
        return {"relevant": False}

    military = [t for t in MILITARY_TERMS if t in combined]
    event_type = military[0] if military else coop[0]

    if len(nations) >= 3 and military:
        confidence = "High"     # three named nations in one military frame
    elif military:
        confidence = "Med"
    else:
        confidence = "Low"

    return {
        "relevant": True,
        "node": "E38",
        "scripture": "Ezek 38:1-6",
        "nations": sorted(nations),
        "event_type": event_type,
        "confidence": confidence,
        "keywords": coop[:3],
    }


def parse(raw: str, source: str = "Unknown", days: int = 14) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into coalition-event dicts."""
    articles = []
    for item in parse_rss_items(raw, days):
        cls = classify(item["title"], item["description"])
        if not cls["relevant"]:
            continue
        articles.append({
            "title": item["title"],
            "description": item["description"],
            "date": item["date"],
            "url": item["url"],
            "source": source,
            "node": cls["node"],
            "scripture": cls["scripture"],
            "nations": cls["nations"],
            "event_type": cls["event_type"],
            "confidence": cls["confidence"],
            "keywords": cls["keywords"],
        })
    return articles


def collect(days: int = 14) -> List[Dict]:
    """Fetch + parse + dedupe across all configured sources."""
    all_articles = []
    for info in SOURCES.values():
        raw = fetch_feed(info["url"])
        all_articles.extend(parse(raw, info["name"], days))
    return dedupe_items(all_articles)


def main():
    days = 14
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_coalition.py [--days 14]")
            sys.exit(1)

    print(f"Ezek 38 coalition watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        nations={'+'.join(a['nations'])}  type={a['event_type']}")
    print(f"\n{len(articles)} coalition event(s) among named nations. "
          "Identifications held loosely; observation only (Matt 24:36).")


if __name__ == "__main__":
    main()

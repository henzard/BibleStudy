#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EU Institutional Consolidation Watch.
Maps to D2 (Fourth Kingdom Consolidation, Dan 2:40-43; 7:23-24).

BIBLE-ONLY APPROACH:
- The classic Revived-Rome reading expects executive centralization in
  Europe. This fetcher keeps that hypothesis honest with observable events:
  treaty changes, defense/fiscal union steps, moves from unanimity to
  qualified-majority voting.
- Routine EU business is ignored; only *centralization of authority* counts.
- Observation only; no identification claims (2 Thess 2:3 — revealed later).

Usage:
    python fetch_eu_consolidation.py [--days 30]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "euractiv": {
        "url": "https://www.euractiv.com/feed/",
        "name": "Euractiv",
    },
    "google_news_eu": {
        "url": ("https://news.google.com/rss/search?"
                "q=EU+(%22treaty+change%22+OR+%22defense+union%22"
                "+OR+%22fiscal+union%22+OR+%22EU+army%22"
                "+OR+%22qualified+majority%22)&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (EU consolidation)",
    },
}

EU_TERMS = ["eu ", "european union", "brussels", "european commission",
            "eurozone", "european council", "european parliament"]

CONSOLIDATION_TERMS = [
    "treaty change", "treaty reform", "defense union", "defence union",
    "fiscal union", "eu army", "european army", "qualified majority",
    "abolish veto", "end unanimity", "federal europe", "federalize",
    "central authority", "joint borrowing", "common debt", "banking union",
    "political union", "transfer of sovereignty", "emergency powers",
]


def classify(title: str, description: str) -> Dict:
    """Relevant only for EU-frame articles about centralization of power."""
    combined = f"{title} {description}".lower()
    eu = [t for t in EU_TERMS if t in combined]
    consolidation = [t for t in CONSOLIDATION_TERMS if t in combined]

    if not eu or not consolidation:
        return {"relevant": False}

    category = consolidation[0]
    if len(consolidation) >= 2:
        confidence = "Med"
    else:
        confidence = "Low"
    # Sovereignty-transfer language is the strongest centralization signal.
    if any(t in combined for t in
           ("transfer of sovereignty", "abolish veto", "end unanimity",
            "emergency powers")):
        confidence = "High"

    return {
        "relevant": True,
        "node": "D2",
        "scripture": "Dan 2:40-43; 7:23-24",
        "category": category,
        "confidence": confidence,
        "keywords": consolidation[:3],
    }


def parse(raw: str, source: str = "Unknown", days: int = 30) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into consolidation-event dicts."""
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
            "category": cls["category"],
            "confidence": cls["confidence"],
            "keywords": cls["keywords"],
        })
    return articles


def collect(days: int = 30) -> List[Dict]:
    """Fetch + parse + dedupe across all configured sources."""
    all_articles = []
    for info in SOURCES.values():
        raw = fetch_feed(info["url"])
        all_articles.extend(parse(raw, info["name"], days))
    return dedupe_items(all_articles)


def main():
    days = 30
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_eu_consolidation.py [--days 30]")
            sys.exit(1)

    print(f"EU consolidation watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        {a['category']}  {a['url']}")
    print(f"\n{len(articles)} consolidation event(s). Observation only.")


if __name__ == "__main__":
    main()

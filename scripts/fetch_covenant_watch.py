#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Covenant / Treaty Watch — Israel-involving diplomatic frameworks.
Maps to D1 (Covenant Confirmation, Dan 9:27) and J3.

BIBLE-ONLY APPROACH:
- Dan 9:27: "he shall confirm a covenant with many for one week" — in the
  futurist reading this is the single most specific observable trigger in
  end-time prophecy.
- This fetcher tracks *observable diplomacy*: treaties, normalization deals,
  security guarantees, and multi-party frameworks involving Israel.
- Observation only. No fulfillment claims, no date-setting (Matt 24:36).

Usage:
    python fetch_covenant_watch.py [--days 7]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:  # direct script execution
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "times_of_israel": {
        "url": "https://www.timesofisrael.com/feed/",
        "name": "Times of Israel",
    },
    "jerusalem_post": {
        "url": "https://www.jpost.com/rss",
        "name": "Jerusalem Post",
    },
    "google_news_treaty": {
        "url": ("https://news.google.com/rss/search?"
                "q=Israel+(treaty+OR+normalization+OR+accord+OR+%22peace+deal%22"
                "+OR+%22security+guarantee%22)&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (Israel diplomacy)",
    },
}

# An article is relevant only if it names Israel AND a covenant-shaped action.
ISRAEL_TERMS = ["israel", "israeli", "jerusalem"]

COVENANT_TERMS = [
    "treaty", "accord", "accords", "normalization", "normalisation",
    "peace deal", "peace agreement", "peace plan", "covenant",
    "security guarantee", "defense pact", "defence pact", "framework agreement",
    "diplomatic relations", "recognition deal", "seven-year", "7-year",
]

# Stronger signals: multi-party or enforced/guaranteed frameworks.
STRONG_TERMS = [
    "signed", "confirms", "confirmed", "ratified", "guarantee", "guarantors",
    "multi-party", "regional agreement", "with many",
]


def classify(title: str, description: str) -> Dict:
    """Classify one article for covenant relevance (pure function)."""
    combined = f"{title} {description}".lower()
    israel = [t for t in ISRAEL_TERMS if t in combined]
    covenant = [t for t in COVENANT_TERMS if t in combined]
    strong = [t for t in STRONG_TERMS if t in combined]

    relevant = bool(israel) and bool(covenant)
    if not relevant:
        return {"relevant": False}

    treaty_type = covenant[0] if covenant else "diplomatic"
    if strong and len(covenant) >= 2:
        confidence = "High"
    elif strong or len(covenant) >= 2:
        confidence = "Med"
    else:
        confidence = "Low"

    return {
        "relevant": True,
        "node": "D1",
        "scripture": "Dan 9:27",
        "treaty_type": treaty_type,
        "confidence": confidence,
        "keywords": (israel[:1] + covenant)[:4],
    }


def parse(raw: str, source: str = "Unknown", days: int = 7) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into covenant-relevant dicts."""
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
            "treaty_type": cls["treaty_type"],
            "confidence": cls["confidence"],
            "keywords": cls["keywords"],
        })
    return articles


def collect(days: int = 7) -> List[Dict]:
    """Fetch + parse + dedupe across all configured sources."""
    all_articles = []
    for info in SOURCES.values():
        raw = fetch_feed(info["url"])
        all_articles.extend(parse(raw, info["name"], days))
    return dedupe_items(all_articles)


def main():
    days = 7
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_covenant_watch.py [--days 7]")
            sys.exit(1)

    print(f"Covenant/treaty watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        type={a['treaty_type']}  {a['url']}")
    print(f"\n{len(articles)} covenant-relevant article(s). "
          "Observation only — no fulfillment claimed (Matt 24:36).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBDC / Digital-ID Infrastructure Tracker.
Maps to B2 (Commerce Control / Mark, Rev 13:16-17).

BIBLE-ONLY APPROACH:
- Rev 13:16-17 describes a system where buying and selling require a mark of
  authorization. This fetcher tracks the *measurable infrastructure* that
  would make such control technically possible: CBDC launches/pilots,
  mandatory digital ID, biometric payment requirements.
- Infrastructure observation only — a CBDC is not "the mark"; it is capacity.
- No fulfillment claims, no date-setting (Matt 24:36).

Usage:
    python fetch_cbdc.py [--days 14]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "bis_press": {
        "url": "https://www.bis.org/doclist/all_rss.rss",
        "name": "Bank for International Settlements",
    },
    "google_news_cbdc": {
        "url": ("https://news.google.com/rss/search?"
                "q=(CBDC+OR+%22digital+currency%22+OR+%22digital+ID%22)"
                "+(launch+OR+pilot+OR+mandatory+OR+rollout)"
                "&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (CBDC / digital ID)",
    },
}

CBDC_TERMS = [
    "cbdc", "central bank digital currency", "digital currency",
    "digital euro", "digital dollar", "digital yuan", "e-cny",
    "digital rupee", "digital pound", "programmable money",
]

ID_TERMS = [
    "digital id", "digital identity", "biometric payment", "biometric id",
    "national id", "digital wallet", "age verification", "identity verification",
]

# Stage words: how far along the rollout is (drives status + confidence).
STAGE_TERMS = {
    "launched": ["launch", "launched", "live", "rollout", "issued"],
    "mandatory": ["mandatory", "required", "compulsory", "must use", "phase out cash"],
    "pilot": ["pilot", "trial", "test", "sandbox"],
    "research": ["research", "explore", "study", "consultation", "white paper"],
}


def classify(title: str, description: str) -> Dict:
    """Classify one article for commerce-control infrastructure relevance."""
    combined = f"{title} {description}".lower()
    cbdc = [t for t in CBDC_TERMS if t in combined]
    ident = [t for t in ID_TERMS if t in combined]
    if not (cbdc or ident):
        return {"relevant": False}

    status = "reported"
    for stage, terms in STAGE_TERMS.items():
        if any(t in combined for t in terms):
            status = stage
            break

    category = "CBDC" if cbdc else "Digital ID"
    if status == "mandatory":
        confidence = "High"      # compulsion is the Rev 13 shape
    elif status == "launched":
        confidence = "High" if (cbdc and ident) else "Med"
    elif status == "pilot":
        confidence = "Med"
    else:
        confidence = "Low"

    return {
        "relevant": True,
        "node": "B2",
        "scripture": "Rev 13:16-17",
        "category": category,
        "status": status,
        "confidence": confidence,
        "keywords": (cbdc + ident)[:4],
    }


def parse(raw: str, source: str = "Unknown", days: int = 14) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into infrastructure-event dicts."""
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
            "status": cls["status"],
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
            print("Usage: python fetch_cbdc.py [--days 14]")
            sys.exit(1)

    print(f"CBDC / digital-ID infrastructure watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        {a['category']} / {a['status']}  {a['url']}")
    print(f"\n{len(articles)} infrastructure event(s). "
          "Capacity observation only — infrastructure is not 'the mark'.")


if __name__ == "__main__":
    main()

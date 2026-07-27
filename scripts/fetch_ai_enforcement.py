#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Enforcement Watch — AI coupled to compulsion.
Maps to B4 (Image of the Beast, Rev 13:15) and MS1 (Lying Wonders).

BIBLE-ONLY APPROACH:
- Rev 13:15: an image that is given breath, speaks, and *causes* those who
  refuse worship to be killed. The prophetic shape is not AI progress — it
  is AI coupled to enforcement: systems that judge, compel, punish, or are
  venerated.
- Tracked categories: algorithmic enforcement (payments/penalties),
  surveillance mandates, autonomous-system incidents (breakouts, harms),
  and AI veneration (worship movements around synthetic personas).
- Capability announcements and vendor hype are deliberately ignored.
- Observation only; the beast is a man (Rev 13:18) — AI is instrumentation.

Usage:
    python fetch_ai_enforcement.py [--days 14]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "google_news_ai_enforcement": {
        "url": ("https://news.google.com/rss/search?"
                "q=AI+(surveillance+mandate+OR+%22facial+recognition%22+required"
                "+OR+%22social+credit%22+OR+%22predictive+policing%22"
                "+OR+%22automated+enforcement%22)&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (AI enforcement)",
    },
    "google_news_ai_incident": {
        "url": ("https://news.google.com/rss/search?"
                "q=AI+(%22escaped+sandbox%22+OR+%22autonomous+incident%22"
                "+OR+%22AI+worship%22+OR+%22AI+church%22+OR+%22AI+religion%22)"
                "&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (AI incidents/veneration)",
    },
}

AI_TERMS = ["ai ", " ai", "artificial intelligence", "algorithm", "algorithmic",
            "machine learning", "autonomous", "facial recognition", "deepfake",
            "chatbot", "language model"]

CATEGORY_TERMS = {
    "enforcement": [
        "automated enforcement", "algorithmic enforcement", "predictive policing",
        "social credit", "automated fine", "payment blocked", "account frozen",
        "denied by algorithm", "ai judge", "automated sanction",
    ],
    "surveillance_mandate": [
        "surveillance mandate", "mandatory facial recognition",
        "facial recognition required", "biometric surveillance",
        "mass surveillance", "surveillance law", "monitoring requirement",
    ],
    "incident": [
        "escaped sandbox", "escaped test", "breakout", "unexpected behavior",
        "autonomous incident", "safety incident", "loss of control",
        "self-replicat", "unauthorized action",
    ],
    "veneration": [
        "ai worship", "ai church", "ai religion", "ai god", "ai deity",
        "ai prophet", "digital messiah", "worship the ai",
    ],
    "deception": [
        "deepfake", "synthetic media", "impersonation", "voice clone",
        "fake video", "disinformation campaign",
    ],
}


def classify(title: str, description: str) -> Dict:
    """Relevant only when AI terms co-occur with compulsion/incident terms."""
    combined = f" {title} {description}".lower()
    ai = [t for t in AI_TERMS if t in combined]
    if not ai:
        return {"relevant": False}

    category = None
    matched: List[str] = []
    for cat, terms in CATEGORY_TERMS.items():
        hits = [t for t in terms if t in combined]
        if hits and category is None:
            category = cat
            matched = hits
    if category is None:
        return {"relevant": False}

    # Enforcement and mandates are the Rev 13:15 shape; deception maps MS1.
    node = "MS1" if category == "deception" else "B4"
    scripture = ("2 Thess 2:9-12" if node == "MS1" else "Rev 13:15")
    if category in ("enforcement", "surveillance_mandate") and len(matched) >= 2:
        confidence = "High"
    elif category in ("enforcement", "surveillance_mandate", "incident"):
        confidence = "Med"
    else:
        confidence = "Low"

    return {
        "relevant": True,
        "node": node,
        "scripture": scripture,
        "category": category,
        "confidence": confidence,
        "keywords": matched[:3],
    }


def parse(raw: str, source: str = "Unknown", days: int = 14) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into AI-enforcement event dicts."""
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
            print("Usage: python fetch_ai_enforcement.py [--days 14]")
            sys.exit(1)

    print(f"AI-enforcement watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        {a['category']} → {a['node']}  {a['url']}")
    print(f"\n{len(articles)} AI-compulsion event(s). "
          "AI is instrumentation, not the beast (Rev 13:18).")


if __name__ == "__main__":
    main()

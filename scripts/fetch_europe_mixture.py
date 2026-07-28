#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iron/Clay Mixture Watch — political mingling-without-adhering in Europe.
Maps to D3 (Iron and Clay Mixture, Dan 2:41-43).

BIBLE-ONLY APPROACH:
- Dan 2:43: "they shall mingle themselves with the seed of men, but they
  shall not cleave one to another, even as iron is not mixed with clay."
  The end-time form of the fourth kingdom is a *political structure* that is
  partly strong, partly brittle — a mixture that does not adhere.
- This fetcher watches STRUCTURES, not people: confessional political blocs
  forming inside European states, formal recognition of religious law in
  European jurisdictions, EU-Middle East political integration, and
  non-adherence events (secession, coalition fragmentation).
- Composition/demography is handled separately (fetch_europe_demographics)
  and reports numbers only. Neither sensor claims intent, coordination, or
  fulfilment — observation only (Matt 24:36).

Usage:
    python fetch_europe_mixture.py [--days 30]
"""

from __future__ import annotations

import sys
from typing import Dict, List

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "google_news_mixture": {
        "url": ("https://news.google.com/rss/search?"
                "q=(Europe+OR+EU)+(%22sharia+council%22+OR+%22religious+law%22"
                "+OR+%22islamic+party%22+OR+%22muslim+party%22"
                "+OR+%22religious+court%22)&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (confessional politics / religious law)",
    },
    "google_news_integration": {
        "url": ("https://news.google.com/rss/search?"
                "q=EU+(Turkey+OR+%22Middle+East%22+OR+%22North+Africa%22)"
                "+(accession+OR+membership+OR+%22political+integration%22)"
                "&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (EU-MENA integration)",
    },
    "google_news_fragmentation": {
        "url": ("https://news.google.com/rss/search?"
                "q=(Europe+OR+EU)+(secession+OR+%22leave+the+EU%22"
                "+OR+%22coalition+collapses%22+OR+%22government+collapses%22)"
                "&hl=en-US&gl=US&ceid=US:en"),
        "name": "Google News (non-adherence / fragmentation)",
    },
}

# European frame: the old Roman space. Country cues keep precision when the
# words "Europe"/"EU" are absent from a headline.
EUROPE_TERMS = [
    "europe", "european", "eu ", "brussels", "eurozone",
    "france", "french", "germany", "german", "britain", "british", "uk ",
    "netherlands", "dutch", "belgium", "belgian", "sweden", "swedish",
    "denmark", "danish", "austria", "austrian", "italy", "italian",
    "spain", "spanish", "greece", "greek",
]

# Checked in order: most specific first, so a court-recognition story that
# also mentions a council classifies as legal_recognition, not politics.
CATEGORY_TERMS = {
    # Formal legal recognition of religious jurisdiction.
    "legal_recognition": [
        "sharia court", "sharia law recognized", "religious court",
        "religious law", "religious tribunal", "blasphemy law",
    ],
    # Political integration of the EU with the Middle East / North Africa.
    "integration_pact": [
        "accession", "eu membership", "political integration",
        "customs union", "association agreement",
    ],
    # Confessional political structures forming inside European states.
    "confessional_politics": [
        "islamic party", "muslim party", "religious party",
        "sharia council", "confessional bloc", "religious bloc",
    ],
    # The clay refusing to adhere: fragmentation of the mixture.
    "non_adherence": [
        "secession", "leave the eu", "exit referendum",
        "coalition collapses", "government collapses", "separatist",
    ],
}

# Integration pacts need a MENA counterparty to count.
MENA_TERMS = ["turkey", "turkish", "middle east", "north africa", "morocco",
              "tunisia", "egypt", "algeria", "lebanon", "jordan"]


def classify(title: str, description: str) -> Dict:
    """Relevant only for Europe-frame political-mixture events."""
    combined = f" {title} {description}".lower()
    europe = [t for t in EUROPE_TERMS if t in combined]
    if not europe:
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
    if category == "integration_pact" and not any(
            t in combined for t in MENA_TERMS):
        return {"relevant": False}

    if category in ("legal_recognition", "integration_pact"):
        confidence = "High" if len(matched) >= 2 else "Med"
    elif category == "confessional_politics":
        confidence = "Med"
    else:
        confidence = "Low"       # fragmentation news is common and noisy

    country = europe[0].strip().title() if europe else ""
    return {
        "relevant": True,
        "node": "D3",
        "scripture": "Dan 2:41-43",
        "category": category,
        "country": country,
        "confidence": confidence,
        "keywords": matched[:3],
    }


def parse(raw: str, source: str = "Unknown", days: int = 30) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into mixture-event dicts."""
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
            "country": cls["country"],
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
            print("Usage: python fetch_europe_mixture.py [--days 30]")
            sys.exit(1)

    print(f"Iron/clay mixture watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        print(f"  [{a['confidence']}] {a['date']} — {a['title']}")
        print(f"        {a['category']}  {a['url']}")
    print(f"\n{len(articles)} mixture event(s). Structures, not people; "
          "observation only (Matt 24:36).")


if __name__ == "__main__":
    main()

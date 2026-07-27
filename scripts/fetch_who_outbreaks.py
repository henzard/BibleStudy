#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WHO Disease Outbreak News — pestilence monitoring.
Maps to J0 (Beginning of Sorrows; Luke 21:11 "pestilences").

BIBLE-ONLY APPROACH:
- Luke 21:11 pairs pestilences with the earthquakes and famines already
  tracked; this completes the quartet (wars, famines, pestilences,
  earthquakes).
- Source: WHO Disease Outbreak News, the canonical structured feed of
  verified outbreak events (disease, country, date).
- Observation only; disease outbreaks are constant history — the signal is
  frequency/severity acceleration, which the trends stage computes.

Usage:
    python fetch_who_outbreaks.py [--days 30]
"""

from __future__ import annotations

import re
import sys
from typing import Dict, List, Optional

try:
    from scripts.newswatch import (fetch_feed, parse_rss_items, dedupe_items)
except ImportError:
    from newswatch import fetch_feed, parse_rss_items, dedupe_items

SOURCES = {
    "who_don": {
        "url": "https://www.who.int/feeds/entity/csr/don/en/rss.xml",
        "name": "WHO Disease Outbreak News",
    },
    "who_news": {
        "url": "https://www.who.int/rss-feeds/news-english.xml",
        "name": "WHO News",
    },
}

# High-lethality / high-spread diseases get elevated severity.
SEVERE_DISEASES = [
    "ebola", "marburg", "cholera", "plague", "h5n1", "avian influenza",
    "mers", "sars", "nipah", "lassa", "yellow fever", "anthrax",
    "hemorrhagic", "haemorrhagic", "polio",
]

DISEASE_TERMS = SEVERE_DISEASES + [
    "outbreak", "epidemic", "pandemic", "measles", "dengue", "malaria",
    "influenza", "mpox", "monkeypox", "meningitis", "hepatitis", "typhoid",
    "diphtheria", "zika", "chikungunya",
]

# WHO DON titles usually look like "Cholera – Sudan" or
# "Disease Outbreak News: Ebola virus disease – Democratic Republic of the Congo"
_TITLE_SPLIT = re.compile(r"\s+[–—-]\s+")


def _extract_disease_country(title: str) -> (str, Optional[str]):
    text = re.sub(r"(?i)^disease outbreak news[:\s]*", "", title).strip()
    parts = _TITLE_SPLIT.split(text)
    if len(parts) >= 2:
        return parts[0].strip(), parts[-1].strip()
    return text, None


def classify(title: str, description: str) -> Dict:
    """Classify one item for outbreak relevance (pure function)."""
    combined = f"{title} {description}".lower()
    hits = [t for t in DISEASE_TERMS if t in combined]
    if not hits:
        return {"relevant": False}

    disease, country = _extract_disease_country(title)
    severe = any(t in combined for t in SEVERE_DISEASES)
    spreading = any(t in combined for t in
                    ("pandemic", "spread to", "multiple countries", "region"))

    if severe and spreading:
        severity, confidence = "Severe", "High"
    elif severe:
        severity, confidence = "Severe", "Med"
    elif spreading:
        severity, confidence = "Spreading", "Med"
    else:
        severity, confidence = "Reported", "Low"

    return {
        "relevant": True,
        "node": "J0",
        "scripture": "Luke 21:11",
        "disease": disease,
        "country": country,
        "severity": severity,
        "confidence": confidence,
        "keywords": hits[:3],
    }


def parse(raw: str, source: str = "Unknown", days: int = 30) -> List[Dict]:
    """Pure parse of ONE feed's RSS text into outbreak dicts."""
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
            "disease": cls["disease"],
            "country": cls["country"],
            "severity": cls["severity"],
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
            print("Usage: python fetch_who_outbreaks.py [--days 30]")
            sys.exit(1)

    print(f"WHO outbreak watch (past {days} days)...\n")
    articles = collect(days)
    for a in articles:
        loc = f" — {a['country']}" if a["country"] else ""
        print(f"  [{a['severity']}] {a['date']} — {a['disease']}{loc}")
    print(f"\n{len(articles)} outbreak report(s). "
          "Signal is acceleration, not existence (Luke 21:11).")


if __name__ == "__main__":
    main()

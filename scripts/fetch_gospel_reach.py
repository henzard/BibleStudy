#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gospel-Reach Tracker — Bible translation / access progress.
Maps to M14 (Gospel to All Nations, Matt 24:14).

BIBLE-ONLY APPROACH:
- Matt 24:14: "this gospel of the kingdom will be preached in all the world
  as a witness to all nations, AND THEN the end will come." This is the one
  precondition Jesus stated affirmatively — a positive-signal tracker.
- Metrics come from published translation statistics (Wycliffe Global
  Alliance / progress.bible publish annual counts: languages with full
  Bibles, NTs, portions, and languages remaining with no Scripture).
- Slow-moving by nature (annual cadence); freshness allows 400 days.
- Observation only. Progress toward "all nations" is measurable; the
  threshold is not (Matt 24:36 — the Father alone knows the day).

Data format expected by parse(): a JSON document like
    {"as_of": "2026-10-01",
     "metrics": [{"name": "languages_full_bible", "value": 780,
                  "description": "..."},
                 {"name": "languages_no_scripture", "value": 880, ...}]}

Usage:
    python fetch_gospel_reach.py [--url URL]
"""

from __future__ import annotations

import json
import sys
from typing import Dict, List

try:
    from scripts.newswatch import fetch_feed
except ImportError:
    from newswatch import fetch_feed

# Published-statistics endpoint (JSON). Override with --url; when the
# endpoint is unreachable the collector degrades to an empty list and the
# freshness stage flags the source rather than the pipeline failing.
DEFAULT_URL = "https://progress.bible/api/statistics.json"

KNOWN_METRICS = {
    "languages_full_bible": "Languages with a complete Bible",
    "languages_new_testament": "Languages with a complete New Testament",
    "languages_portions": "Languages with some translated Scripture",
    "languages_no_scripture": "Languages with no Scripture at all",
    "languages_in_progress": "Languages with active translation projects",
    "people_without_scripture": "People without Scripture in their language",
}


def parse(raw: str, source: str = "progress.bible") -> List[Dict]:
    """Pure parse of a statistics JSON document into metric dicts."""
    if not raw:
        return []
    try:
        doc = json.loads(raw)
    except (ValueError, TypeError):
        return []

    as_of = str(doc.get("as_of") or doc.get("date") or "")[:10]
    if not as_of:
        return []

    records = []
    for m in doc.get("metrics", []):
        name = str(m.get("name", "")).strip()
        value = m.get("value")
        if not name or value is None:
            continue
        try:
            value = float(value)
        except (ValueError, TypeError):
            continue
        records.append({
            "date": as_of,
            "metric_name": name,
            "value": value,
            "description": (m.get("description")
                            or KNOWN_METRICS.get(name, name)),
            "url": str(doc.get("source_url") or ""),
            "source": source,
            "node": "M14",
            "scripture": "Matt 24:14",
            # Statistics published by the translation agencies themselves.
            "confidence": "High",
        })
    return records


def collect(days: int = 400, url: str = DEFAULT_URL) -> List[Dict]:
    """Fetch + parse the published statistics (days kept for interface
    symmetry; the metrics document carries its own as-of date)."""
    raw = fetch_feed(url)
    return parse(raw)


def main():
    url = DEFAULT_URL
    if "--url" in sys.argv:
        try:
            url = sys.argv[sys.argv.index("--url") + 1]
        except IndexError:
            print("Usage: python fetch_gospel_reach.py [--url URL]")
            sys.exit(1)

    print("Gospel-reach statistics...\n")
    records = collect(url=url)
    for r in records:
        print(f"  {r['date']}  {r['metric_name']} = {r['value']:.0f}")
        print(f"        {r['description']}")
    if not records:
        print("  (no statistics available — source will be flagged stale)")
    print(f"\n{len(records)} metric(s). Matt 24:14 — the one precondition "
          "stated affirmatively; the threshold is not ours to compute.")


if __name__ == "__main__":
    main()

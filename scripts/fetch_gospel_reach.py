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
import os
import re
import sys
from typing import Dict, List, Optional

try:
    from scripts.newswatch import fetch_feed, clean_html
except ImportError:
    from newswatch import fetch_feed, clean_html

# Candidate sources, tried in order. A JSON endpoint (overridable with
# GOSPEL_STATS_URL or --url) is preferred; the Wycliffe statistics pages are
# the reliable public fallback — annual HTML pages with headline numbers.
# When nothing is reachable the collector degrades to an empty list and the
# freshness stage flags the source rather than the pipeline failing.
JSON_URL = os.environ.get("GOSPEL_STATS_URL",
                          "https://progress.bible/api/statistics.json")
HTML_URLS = [
    "https://wycliffe.org.uk/statistics/",
    "https://www.wycliffe.net/resources/statistics/",
]
DEFAULT_URL = JSON_URL  # backwards-compatible alias

KNOWN_METRICS = {
    "languages_full_bible": "Languages with a complete Bible",
    "languages_new_testament": "Languages with a complete New Testament",
    "languages_portions": "Languages with some translated Scripture",
    "languages_no_scripture": "Languages with no Scripture at all",
    "languages_waiting": "Languages waiting for translation to begin",
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


# --- HTML fallback: Wycliffe statistics pages ------------------------------
# Headline sentences look like "The full Bible is now available in 776
# languages" / "544 languages remain on the waiting list". Both word orders
# (number-first and phrase-first) are matched.

_NUM = r"([\d][\d,]{1,9})"

_HTML_METRICS = [
    ("languages_full_bible",
     [rf"(?:full|complete|whole)\s+Bible[^.]{{0,90}}?{_NUM}\s+languages?",
      rf"{_NUM}\s+languages?[^.]{{0,90}}?(?:full|complete|whole)\s+Bible"]),
    ("languages_new_testament",
     [rf"New\s+Testament[^.]{{0,90}}?{_NUM}\s+languages?",
      rf"{_NUM}\s+languages?[^.]{{0,90}}?New\s+Testament"]),
    ("languages_portions",
     [rf"(?:portions?|some\s+Scripture|selections?)[^.]{{0,90}}?{_NUM}\s+(?:more\s+)?languages?",
      rf"{_NUM}\s+(?:more\s+)?languages?[^.]{{0,90}}?(?:portions?|some\s+(?:translated\s+)?Scripture)"]),
    ("languages_waiting",
     [rf"{_NUM}\s+(?:of\s+the\s+world[^.]{{0,40}}?)?(?:living\s+)?languages?[^.]{{0,90}}?"
      r"(?:waiting\s+list|no\s+Scripture|translation\s+to\s+begin|remain)",
      rf"(?:waiting\s+list|no\s+Scripture)[^.]{{0,90}}?{_NUM}\s+languages?"]),
]

_AS_OF = re.compile(
    r"(?:[Aa]s\s+of|[Ss]eptember|[Aa]ugust|[Oo]ctober)\s*[^.]{0,30}?(20\d\d)")
_YEAR = re.compile(r"\b(20\d\d)\b")


def _to_number(text: str) -> Optional[float]:
    try:
        return float(text.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def parse_html(raw: str, source: str = "Wycliffe statistics",
               url: str = "") -> List[Dict]:
    """Pure parse of a Wycliffe-style statistics page into metric dicts."""
    if not raw:
        return []
    text = clean_html(raw)
    if "Bible" not in text or "language" not in text.lower():
        return []

    m = _AS_OF.search(text) or _YEAR.search(text)
    if not m:
        return []
    as_of = f"{m.group(1)}-08-01"   # stats are refreshed each August/September

    records = []
    for name, patterns in _HTML_METRICS:
        value = None
        for pat in patterns:
            hit = re.search(pat, text, re.IGNORECASE)
            if hit:
                value = _to_number(hit.group(1))
                break
        if value is None:
            continue
        records.append({
            "date": as_of,
            "metric_name": name,
            "value": value,
            "description": KNOWN_METRICS.get(name, name),
            "url": url,
            "source": source,
            "node": "M14",
            "scripture": "Matt 24:14",
            "confidence": "High",
        })
    return records


def collect(days: int = 400, url: str = None) -> List[Dict]:
    """Fetch + parse the published statistics (days kept for interface
    symmetry; the metrics document carries its own as-of date).

    Tries the JSON endpoint first, then the Wycliffe HTML pages."""
    records = parse(fetch_feed(url or JSON_URL))
    if records:
        return records
    for html_url in HTML_URLS:
        records = parse_html(fetch_feed(html_url), url=html_url)
        if records:
            return records
    return []


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

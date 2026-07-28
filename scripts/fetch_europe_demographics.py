#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Europe Religious-Demography Metrics.
Maps to D3 (Iron and Clay Mixture, Dan 2:41-43) — the composition backdrop.

BIBLE-ONLY APPROACH:
- Companion to fetch_europe_mixture: that sensor watches political events;
  this one records the slow-moving composition numbers behind them
  (published survey/census figures such as Pew Research's European
  estimates and projections).
- Numbers only. Composition change is measurable; claims about intent or
  coordination are not measurable and are never made here.
- Annual cadence; freshness allows 400 days.

Data format expected by parse(): a JSON document like
    {"as_of": "2026-01-01",
     "metrics": [{"name": "muslim_share_pct", "value": 4.9,
                  "description": "..."}]}
An HTML fallback extracts headline figures from a survey article page.

Usage:
    python fetch_europe_demographics.py [--url URL]
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

JSON_URL = os.environ.get("EUROPE_DEMOGRAPHICS_URL", "")
HTML_URLS = [
    "https://www.pewresearch.org/religion/2017/11/29/europes-growing-muslim-population/",
]

KNOWN_METRICS = {
    "muslim_share_pct": "Muslim share of Europe's population (%)",
    "muslim_population_millions": "Muslim population of Europe (millions)",
    "muslim_share_2050_high_pct":
        "Projected 2050 Muslim share, high-migration scenario (%)",
    "muslim_share_2050_low_pct":
        "Projected 2050 Muslim share, zero-migration scenario (%)",
}


def parse(raw: str, source: str = "survey") -> List[Dict]:
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
        records.append(_record(as_of, name, value,
                               m.get("description"), doc.get("source_url", ""),
                               source))
    return records


# --- HTML fallback ---------------------------------------------------------
# Headline sentences look like "Muslims made up about 4.9% of Europe's
# population in 2016" / "could reach 14% by 2050" / "25.8 million Muslims".

_SHARE_NOW = re.compile(
    r"Muslims?\s+(?:made\s+up|make\s+up|constitute[d]?)\s+"
    r"(?:about\s+|roughly\s+|an?\s+estimated\s+)?([\d.]+)%", re.IGNORECASE)
_SHARE_2050 = re.compile(
    r"(?:reach|rise\s+to|grow\s+to|as\s+high\s+as)\s+"
    r"(?:about\s+|roughly\s+)?([\d.]+)%[^.]{0,60}?\b(?:by\s+)?2050",
    re.IGNORECASE)
_POP_MILLIONS = re.compile(
    r"([\d.]+)\s+million\s+Muslims?", re.IGNORECASE)
_AS_OF_YEAR = re.compile(r"\bin\s+(20\d\d)\b")
_YEAR = re.compile(r"\b(20\d\d)\b")


def parse_html(raw: str, source: str = "Pew Research",
               url: str = "") -> List[Dict]:
    """Pure parse of a survey article page into metric dicts."""
    if not raw:
        return []
    text = clean_html(raw)
    if "Muslim" not in text or "Europe" not in text:
        return []
    m = _AS_OF_YEAR.search(text) or _YEAR.search(text)
    if not m:
        return []
    as_of = f"{m.group(1)}-01-01"

    records = []
    hit = _SHARE_NOW.search(text)
    if hit:
        records.append(_record(as_of, "muslim_share_pct",
                               float(hit.group(1)), None, url, source))
    hit = _SHARE_2050.search(text)
    if hit:
        records.append(_record(as_of, "muslim_share_2050_high_pct",
                               float(hit.group(1)), None, url, source))
    hit = _POP_MILLIONS.search(text)
    if hit:
        records.append(_record(as_of, "muslim_population_millions",
                               float(hit.group(1)), None, url, source))
    return records


def _record(as_of: str, name: str, value: float, description: Optional[str],
            url: str, source: str) -> Dict:
    return {
        "date": as_of,
        "metric_name": name,
        "value": value,
        "description": description or KNOWN_METRICS.get(name, name),
        "url": url,
        "source": source,
        "node": "D3",
        "scripture": "Dan 2:41-43",
        "confidence": "High",     # published survey figures
    }


def collect(days: int = 400, url: str = None) -> List[Dict]:
    """Fetch + parse published figures: JSON endpoint (if configured),
    then survey-page HTML fallbacks."""
    target = url or JSON_URL
    if target:
        records = parse(fetch_feed(target))
        if records:
            return records
    for html_url in HTML_URLS:
        records = parse_html(fetch_feed(html_url), url=html_url)
        if records:
            return records
    return []


def main():
    url = None
    if "--url" in sys.argv:
        try:
            url = sys.argv[sys.argv.index("--url") + 1]
        except IndexError:
            print("Usage: python fetch_europe_demographics.py [--url URL]")
            sys.exit(1)

    print("Europe religious-demography metrics...\n")
    records = collect(url=url)
    for r in records:
        print(f"  {r['date']}  {r['metric_name']} = {r['value']}")
        print(f"        {r['description']}")
    if not records:
        print("  (no figures available — source will be flagged stale)")
    print(f"\n{len(records)} metric(s). Composition numbers only — "
          "no intent claims.")


if __name__ == "__main__":
    main()

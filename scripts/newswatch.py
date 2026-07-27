#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared RSS plumbing for the news-watch fetchers.

The trigger-layer fetchers (covenant, coalition, CBDC, EU, AI-enforcement)
all follow the same shape: fetch RSS feeds, parse items, classify by keyword.
This module holds the fetch/clean/date/item-extraction pieces so each fetcher
only contains its sources and its classifier.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List


def fetch_feed(feed_url: str, timeout: int = 10) -> str:
    """Fetch a single RSS/Atom feed (network I/O only)."""
    try:
        req = urllib.request.Request(
            feed_url, headers={"User-Agent": "BibleStudy-EarlyWarning/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"Error fetching feed {feed_url}: {e}", file=sys.stderr)
        return ""


def clean_html(text: str) -> str:
    """Remove HTML tags and common entities from text."""
    if text is None:
        return ""
    clean = re.sub("<.*?>", "", text)
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&quot;", '"').replace("&#39;", "'")
    clean = clean.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", clean).strip()


def parse_pubdate(pubdate_text: str) -> datetime:
    """Parse an RSS/Atom publication date; fall back to utcnow."""
    clean = clean_html(pubdate_text or "")
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(clean, fmt)
            return parsed.replace(tzinfo=None)
        except ValueError:
            continue
    return datetime.utcnow()


def parse_rss_items(xml_content: str, days_back: int = 7) -> List[Dict]:
    """Extract {title, description, date, url} items from raw RSS text.

    Date-filters to the lookback window; tolerates malformed feeds by
    returning an empty list.
    """
    if not xml_content:
        return []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return []

    cutoff = datetime.utcnow() - timedelta(days=days_back)
    items = []
    for item in root.findall(".//item"):
        title_elem = item.find("title")
        link_elem = item.find("link")
        if title_elem is None or link_elem is None:
            continue
        pubdate_elem = item.find("pubDate")
        pub_date = parse_pubdate(pubdate_elem.text if pubdate_elem is not None
                                 else "")
        if pub_date < cutoff:
            continue
        desc_elem = item.find("description")
        description = clean_html(desc_elem.text) if desc_elem is not None else ""
        items.append({
            "title": clean_html(title_elem.text),
            "description": description[:300],
            "date": pub_date.strftime("%Y-%m-%d"),
            "url": (link_elem.text or "").strip(),
        })
    return items


def dedupe_items(items: List[Dict]) -> List[Dict]:
    """Drop duplicate title/url pairs, newest first."""
    seen = set()
    unique = []
    for it in items:
        key = (it["title"].lower(), it["url"])
        if key not in seen:
            seen.add(key)
            unique.append(it)
    unique.sort(key=lambda x: x["date"], reverse=True)
    return unique

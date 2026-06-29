#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline unit test for the pure FRED news RSS parser.

Reads a recorded RSS fixture and exercises ``fetch_fred_news.parse``
without any network access.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_fred_news  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "fred_news_sample.rss"


def _load() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_returns_announcements_with_fields():
    items = fetch_fred_news.parse(_load(), days=365 * 1000)

    assert len(items) >= 1
    for item in items:
        for field in ("title", "description", "category", "date", "url", "relevant"):
            assert field in item, f"missing field: {field}"


def test_parse_marks_economic_items_relevant():
    items = fetch_fred_news.parse(_load(), days=365 * 1000)

    titles = {i["title"]: i for i in items}
    # Future pubDates (2099) keep all three items past the date filter.
    assert len(items) == 3

    cpi = next(i for i in items if "Consumer Price Index" in i["title"])
    assert cpi["relevant"] is True
    assert cpi["category"] == "Inflation"

    museum = next(i for i in items if "museum" in i["title"].lower())
    assert museum["relevant"] is False

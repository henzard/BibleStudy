#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for the World Bank news fetch script.

Pure parsing only — no network calls are performed.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_worldbank_news  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "worldbank_sample.rss"

EXPECTED_FIELDS = {
    "title", "description", "date", "url",
    "nodes", "keywords", "confidence",
}


def test_parse_returns_records():
    raw = FIXTURE.read_text(encoding="utf-8")
    records = fetch_worldbank_news.parse(raw, days_back=7)

    assert len(records) >= 1
    for rec in records:
        assert EXPECTED_FIELDS.issubset(rec.keys())


def test_parse_assigns_nodes():
    raw = FIXTURE.read_text(encoding="utf-8")
    records = fetch_worldbank_news.parse(raw, days_back=7)

    # Every relevant record carries at least one prophecy node (J0/H0).
    assert all(rec["nodes"] for rec in records)

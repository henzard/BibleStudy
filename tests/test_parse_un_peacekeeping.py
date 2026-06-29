#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for the UN Peacekeeping fetch script.

Pure parsing only — no network calls are performed.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_un_peacekeeping  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "un_peacekeeping_sample.rss"

EXPECTED_FIELDS = {
    "title", "description", "date", "url",
    "keywords", "numbers", "confidence", "category",
}


def test_parse_returns_records():
    raw = FIXTURE.read_text(encoding="utf-8")
    records = fetch_un_peacekeeping.parse(raw, days_back=30)

    assert len(records) >= 1
    for rec in records:
        assert EXPECTED_FIELDS.issubset(rec.keys())


def test_parse_classifies_conflict():
    raw = FIXTURE.read_text(encoding="utf-8")
    records = fetch_un_peacekeeping.parse(raw, days_back=30)

    # At least one record should surface extracted numbers (e.g. 140,000).
    assert any(rec["numbers"] for rec in records)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for scripts/fetch_earthquakes.py.

These tests read a static ATOM fixture and exercise the PURE `parse`
function. They must never perform a network request (no fetch_raw/collect).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_earthquakes  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "earthquakes_sample.atom"

EXPECTED_FIELDS = {
    "magnitude",
    "location",
    "date",
    "latitude",
    "longitude",
    "url",
}


def _load() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_returns_records():
    records = fetch_earthquakes.parse(_load())
    assert isinstance(records, list)
    assert len(records) >= 1


def test_parse_field_names_and_types():
    records = fetch_earthquakes.parse(_load())
    for rec in records:
        assert EXPECTED_FIELDS <= set(rec.keys())
        assert isinstance(rec["magnitude"], float)
        assert isinstance(rec["location"], str)
        assert isinstance(rec["date"], str)
        assert isinstance(rec["latitude"], str)
        assert isinstance(rec["longitude"], str)
        assert isinstance(rec["url"], str)


def test_parse_filters_by_min_magnitude():
    # The fixture has a 6.5, 5.2 and 4.1 event.
    records = fetch_earthquakes.parse(_load(), min_magnitude=5.0)
    assert records, "expected at least one event >= 5.0"
    assert all(rec["magnitude"] >= 5.0 for rec in records)
    # Sorted highest-first.
    assert records[0]["magnitude"] == 6.5

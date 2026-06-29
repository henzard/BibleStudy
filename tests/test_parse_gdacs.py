#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for scripts/fetch_gdacs.py.

These tests read a static GDACS RSS fixture and exercise the PURE `parse`
function. They must never perform a network request (no fetch_raw/collect).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_gdacs  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gdacs_sample.rss"

EXPECTED_FIELDS = {
    "type",
    "alert_level",
    "title",
    "description",
    "severity",
    "country",
    "population_affected",
    "date",
    "url",
}


def _load() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_returns_records():
    records = fetch_gdacs.parse(_load())
    assert isinstance(records, list)
    assert len(records) >= 1


def test_parse_field_names_and_types():
    records = fetch_gdacs.parse(_load())
    for rec in records:
        assert EXPECTED_FIELDS <= set(rec.keys())
        for key in EXPECTED_FIELDS:
            assert isinstance(rec[key], str)


def test_parse_filters_by_alert_level():
    # Fixture has Red, Orange and Green alerts.
    records = fetch_gdacs.parse(_load(), min_alert_level="Orange")
    assert records, "expected at least one Orange+ alert"
    assert all(rec["alert_level"] in ("Red", "Orange") for rec in records)
    # Sorted Red first.
    assert records[0]["alert_level"] == "Red"
    assert records[0]["type"] == "Earthquake"

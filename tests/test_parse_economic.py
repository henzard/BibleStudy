#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline unit test for the pure FRED economic parser.

Loads a recorded FRED observations JSON fixture and exercises
``fetch_economic.parse_observations`` without any network access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_economic  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "fred_observations_sample.json"

# CPIAUCSL config from the script's INDICATORS table (inflation / YoY logic).
CONFIG = fetch_economic.INDICATORS["inflation"]["CPIAUCSL"]


def _load() -> dict:
    with FIXTURE.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_parse_observations_returns_documented_fields():
    result = fetch_economic.parse_observations(_load(), "CPIAUCSL", CONFIG)

    assert isinstance(result, dict)
    for field in (
        "series_id",
        "name",
        "description",
        "status",
        "confidence",
        "latest_value",
        "latest_date",
        "yoy_change",
        "assessment",
    ):
        assert field in result, f"missing field: {field}"

    assert result["series_id"] == "CPIAUCSL"
    assert result["name"] == CONFIG["name"]
    assert result["latest_value"] == 312.5
    assert result["latest_date"] == "2026-01-01"
    # 12 valid observations remain after dropping the '.' placeholder, so YoY
    # is computed: (312.5 - 291.0) / 291.0 * 100 ~= 7.39%.
    assert result["yoy_change"] is not None
    assert 7.0 < result["yoy_change"] < 8.0


def test_parse_observations_sensible_status_and_confidence():
    result = fetch_economic.parse_observations(_load(), "CPIAUCSL", CONFIG)

    # +7.4% YoY is above threshold_high (5.0) but below critical (10.0).
    assert result["status"] == "CONCERN"
    assert result["confidence"] == "Med"


def test_assess_indicator_alias_matches():
    a = fetch_economic.parse_observations(_load(), "CPIAUCSL", CONFIG)
    b = fetch_economic.assess_indicator("CPIAUCSL", _load(), CONFIG)
    assert a == b

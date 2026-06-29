#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for fetch_spaceweather (no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_spaceweather  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "spaceweather_sample.json"


def _load():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_parse_returns_alerts():
    # Large window so the date cutoff never filters out the fixture rows.
    alerts = fetch_spaceweather.parse(_load(), days=36500)
    assert len(alerts) >= 1
    for alert in alerts:
        assert "issue_datetime" in alert
        assert "severity" in alert
        assert "confidence" in alert
        assert "description" in alert


def test_parse_classifies_severe():
    alerts = fetch_spaceweather.parse(_load(), days=36500)
    severities = {a["severity"] for a in alerts}
    # The fixture contains a G4 event -> SEVERE.
    assert "SEVERE" in severities

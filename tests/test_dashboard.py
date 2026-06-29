#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the HTML dashboard renderer."""

from __future__ import annotations

import json

from earlywarning.dashboard import render_html, render_shell, _DATA_TOKEN


SAMPLE = {
    "generated_at": "2026-06-29 08:00 UTC",
    "report_title": "Prophecy Early-Warning Report",
    "report_summary": "Overall pattern strength is 33/100.",
    "event_count": 9,
    "cluster_count": 9,
    "threat": {
        "overall_intensity": 33.0, "phase": "EARLY Beginning of Sorrows",
        "emoji": "🟡", "note": "Some J0 markers present",
        "nodes": [
            {"node_id": "J0", "label": "Beginning of Sorrows",
             "scripture": "Matt 24:6-8", "intensity": 65.0, "confidence": "Med",
             "description": "4 events", "contributing_domains": ["war"]},
        ],
        "cross_validation": {"J0": 2},
    },
    "findings": [
        {"domain": "war", "headline": "Wars: escalating", "assessment": "...",
         "key_facts": ["Sudan offensive"], "confidence": "Med",
         "escalation": "escalating", "node_ids": ["J0"], "source_backend": "heuristic"},
    ],
    "trends": {
        "available": True, "summary": "1 metric accelerating",
        "metrics": {"earthquakes": {"available": True, "recent_week": 8,
                    "baseline_avg": 5.0, "acceleration_pct": 60.0,
                    "direction": "escalating", "weekly_series": [3, 4, 5, 8]}},
    },
    "delivered": [],
}


def test_render_html_embeds_data():
    page = render_html(SAMPLE)
    assert page.startswith("<!DOCTYPE html>")
    assert _DATA_TOKEN not in page          # token was replaced
    assert "EARLY Beginning of Sorrows" in page
    # The embedded JSON must be valid and present.
    assert json.dumps(SAMPLE["report_title"], ensure_ascii=False)[1:-1] in page


def test_render_shell_uses_fetch():
    shell = render_shell()
    assert shell.startswith("<!DOCTYPE html>")
    assert _DATA_TOKEN in shell             # data left null
    assert "fetch('latest.json'" in shell


def test_render_html_escapes_and_is_self_contained():
    evil = dict(SAMPLE)
    evil["report_summary"] = "<script>alert(1)</script>"
    page = render_html(evil)
    # No CDN / external asset references.
    assert "http://" not in page.split("<script>")[0]
    assert "https://" not in page.split("<style>")[0]
    # Raw payload is JSON-encoded, so the literal tag is escaped in the data.
    assert "<script>alert(1)</script>" not in page.replace(
        json.dumps(evil["report_summary"]), "")

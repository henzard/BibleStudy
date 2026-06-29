#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Tier-1 early-warning: change detection, freshness, routing, state."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from earlywarning.changes import compute_level, detect_changes
from earlywarning.config import OutputConfig
from earlywarning.freshness import analyze_freshness
from earlywarning.models import (
    NodeAssessment, ResearchFinding, ThreatAssessment, ChangeReport,
    AlertChange, FreshnessReport, ExecutiveReport, PipelineResult,
)
from earlywarning.outputs.dispatcher import _should_notify, _within_cooldown
from earlywarning.schema import ensure_schema
from earlywarning.state import load_previous, save_run


def _threat(overall, nodes):
    return ThreatAssessment(
        overall_intensity=overall, phase="P", emoji="🟢", note="n",
        nodes=[NodeAssessment(nid, nid, "s", inten, conf, "d")
               for nid, inten, conf in nodes],
        cross_validation={},
    )


def test_compute_level_bands_and_node_bump():
    assert compute_level(_threat(10, [])) == "GREEN"
    assert compute_level(_threat(35, [])) == "WATCH"
    assert compute_level(_threat(55, [])) == "AMBER"
    assert compute_level(_threat(75, [])) == "RED"
    # A single hot node escalates the level even if overall is low.
    assert compute_level(_threat(20, [("J0", 81, "Med")])) == "AMBER"
    assert compute_level(_threat(20, [("J0", 90, "High")])) == "RED"


def test_detect_changes_first_run():
    cr = detect_changes(_threat(20, [("J0", 20, "Low")]), [], None)
    assert cr.is_first_run and cr.previous_level is None and not cr.rose


def test_detect_changes_escalation_and_crossings():
    prev = {"alert_level": "GREEN", "generated_at": "2026-06-27 10:00 UTC",
            "threat": {"overall_intensity": 10, "phase": "P",
                       "nodes": [{"node_id": "J0", "intensity": 10}]},
            "findings": [{"domain": "war", "escalation": "steady"}]}
    cur = _threat(40, [("J0", 75, "Med")])
    findings = [ResearchFinding("war", "h", "a", [], "Med", "escalating", ["J0"])]
    cr = detect_changes(cur, findings, prev)
    assert cr.rose and cr.previous_level == "GREEN"
    kinds = {c.kind for c in cr.changes}
    assert "node_crossing" in kinds
    assert "new_escalation" in kinds
    assert any(c.kind == "overall_delta" for c in cr.changes)


def test_detect_changes_steady_when_unchanged():
    prev = {"alert_level": "WATCH", "generated_at": "2026-06-27 10:00 UTC",
            "threat": {"overall_intensity": 35, "phase": "P",
                       "nodes": [{"node_id": "J0", "intensity": 35}]},
            "findings": []}
    cr = detect_changes(_threat(35, [("J0", 35, "Low")]), [], prev)
    assert not cr.rose and not cr.changes


def test_freshness_flags_stale(seeded_db):
    # Seeded dates are 2026-06; relative to "now" they are stale.
    fr = analyze_freshness(seeded_db)
    assert isinstance(fr, FreshnessReport)
    assert fr.any_stale
    assert "earthquakes" in {i["source"] for i in fr.items}


def test_state_save_and_load(tmp_path):
    db = tmp_path / "s.db"
    conn = sqlite3.connect(db); ensure_schema(conn); conn.close()
    save_run(db, {"threat": {"overall_intensity": 42}, "alert_level": "WATCH"},
             "WATCH", "2026-06-28 10:00 UTC", 42.0, "P")
    prev = load_previous(db)
    assert prev["alert_level"] == "WATCH"
    assert prev["threat"]["overall_intensity"] == 42


def _result(level, changes):
    fr = FreshnessReport([], [], False)
    rep = ExecutiveReport("t", "2026-06-28 10:00 UTC", "s", [], "md")
    return PipelineResult(
        generated_at="2026-06-28 10:00 UTC", events=[], clusters=[],
        findings=[], threat=_threat(60, []), trends={}, report=rep,
        alert_level=level, changes=changes, freshness=fr,
    )


def test_routing_below_threshold_suppressed():
    cfg = OutputConfig(slack_min_level="AMBER")
    watch = ChangeReport("WATCH", "GREEN", True, False, [], "up")
    assert _should_notify(_result("WATCH", watch), "AMBER", None, cfg) is False


def test_routing_fires_when_rose_above_threshold():
    cfg = OutputConfig(slack_min_level="AMBER")
    rose = ChangeReport("AMBER", "GREEN", True, False,
                        [AlertChange("node_crossing", "amber", "m")], "up")
    assert _should_notify(_result("AMBER", rose), "AMBER", None, cfg) is True


def test_routing_steady_suppressed_no_change():
    cfg = OutputConfig(slack_min_level="AMBER", notify_only_on_change=True)
    steady = ChangeReport("AMBER", "AMBER", False, False, [], "steady")
    assert _should_notify(_result("AMBER", steady), "AMBER", None, cfg) is False


def test_cooldown_blocks_same_level_repeat():
    cfg = OutputConfig(slack_min_level="AMBER", cooldown_hours=6)
    steady = ChangeReport("AMBER", "AMBER", False, False,
                          [AlertChange("node_crossing", "amber", "m")], "x")
    res = _result("AMBER", steady)
    prev = {"alert_level": "AMBER", "generated_at": "2026-06-28 07:00 UTC"}
    assert _within_cooldown(res, prev, 6) is True
    # within cooldown + not rose -> suppressed despite a fresh change
    assert _should_notify(res, "AMBER", prev, cfg) is False

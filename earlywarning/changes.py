#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Change detection and alert-level computation.

Turns two consecutive runs into a :class:`ChangeReport`: the current alert
level (GREEN/WATCH/AMBER/RED), whether it *rose*, and a list of specific
changes (threshold crossings, phase shifts, new escalations). This is what lets
the system *warn on change* instead of merely re-stating current conditions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import (
    ALERT_LEVEL_ORDER,
    AlertChange,
    ChangeReport,
    ResearchFinding,
    ThreatAssessment,
)

# Intensity band boundaries (shared with the phase thresholds).
_BANDS = [0, 30, 50, 70]
_BAND_LEVEL = {0: "GREEN", 1: "WATCH", 2: "AMBER", 3: "RED"}


def _band(intensity: float) -> int:
    b = 0
    for i, edge in enumerate(_BANDS):
        if intensity >= edge:
            b = i
    return b


def compute_level(threat: ThreatAssessment) -> str:
    """Base level from overall intensity, escalated by any hot single node."""
    level = _BAND_LEVEL[_band(threat.overall_intensity)]
    for n in threat.nodes:
        if n.intensity >= 85 and n.confidence == "High":
            level = _raise(level, "RED")
        elif n.intensity >= 70 and n.confidence in ("Med", "High"):
            level = _raise(level, "AMBER")
    return level


def _raise(a: str, b: str) -> str:
    return a if ALERT_LEVEL_ORDER[a] >= ALERT_LEVEL_ORDER[b] else b


def _sev_for_band(target_band: int) -> str:
    return {3: "red", 2: "amber", 1: "watch", 0: "info"}[target_band]


def detect_changes(threat: ThreatAssessment,
                   findings: List[ResearchFinding],
                   previous: Optional[Dict[str, Any]]) -> ChangeReport:
    level = compute_level(threat)
    changes: List[AlertChange] = []

    if previous is None:
        return ChangeReport(
            level=level, previous_level=None, rose=False, is_first_run=True,
            changes=[AlertChange("baseline", "info",
                                 f"First run — baseline established at {level} "
                                 f"({threat.overall_intensity:.0f}/100).")],
            summary=f"Baseline established: {level}.",
        )

    prev_threat = previous.get("threat", {}) or {}
    prev_level = previous.get("alert_level")
    prev_overall = float(prev_threat.get("overall_intensity", 0) or 0)
    prev_nodes = {n["node_id"]: n for n in prev_threat.get("nodes", [])}
    prev_findings = {f["domain"]: f for f in previous.get("findings", [])}

    # Phase shift.
    prev_phase = prev_threat.get("phase")
    if prev_phase and prev_phase != threat.phase:
        up = threat.overall_intensity >= prev_overall
        changes.append(AlertChange(
            "phase_change", "amber" if up else "info",
            f"Phase {'↑' if up else '↓'} {prev_phase} → {threat.phase}."))

    # Overall delta.
    delta = threat.overall_intensity - prev_overall
    if abs(delta) >= 5:
        sev = "amber" if delta >= 10 else ("watch" if delta > 0 else "info")
        changes.append(AlertChange(
            "overall_delta", sev,
            f"Overall {delta:+.0f} ({prev_overall:.0f} → "
            f"{threat.overall_intensity:.0f}/100)."))

    # Per-node band crossings.
    for n in threat.nodes:
        prev_n = prev_nodes.get(n.node_id)
        prev_i = float(prev_n["intensity"]) if prev_n else 0.0
        cur_band, prev_band = _band(n.intensity), _band(prev_i)
        if cur_band > prev_band:
            changes.append(AlertChange(
                "node_crossing", _sev_for_band(cur_band),
                f"{n.node_id} {n.label} crossed up into "
                f"{_BAND_LEVEL[cur_band]} ({prev_i:.0f} → {n.intensity:.0f}).",
                node_id=n.node_id))
        elif cur_band < prev_band:
            changes.append(AlertChange(
                "node_crossing", "info",
                f"{n.node_id} {n.label} eased to {_BAND_LEVEL[cur_band]} "
                f"({prev_i:.0f} → {n.intensity:.0f}).", node_id=n.node_id))

    # New escalations.
    for f in findings:
        was = prev_findings.get(f.domain, {}).get("escalation")
        if f.escalation == "escalating" and was != "escalating":
            changes.append(AlertChange(
                "new_escalation", "watch",
                f"{f.domain} is now escalating."))

    rose = (prev_level is not None
            and ALERT_LEVEL_ORDER.get(level, 0) > ALERT_LEVEL_ORDER.get(prev_level, 0))

    if not changes:
        summary = f"No material change — steady at {level}."
    else:
        head = "↑ ALERT RAISED" if rose else "Update"
        summary = f"{head}: {level} ({len(changes)} change(s))."

    return ChangeReport(
        level=level, previous_level=prev_level, rose=rose, is_first_run=False,
        changes=changes, summary=summary,
    )

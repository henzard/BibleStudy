#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Threat scoring and prophecy-node intensity.

Combines the evidence clusters and specialist findings into:

* a per-node intensity (0-100) with a cross-validated confidence, and
* an overall "beginning of sorrows" pattern strength + phase.

Confidence is driven by **independent-source corroboration**: a node backed by
a single source is capped at Low/Med no matter how loud it is; High requires
multiple independent sources. This encodes the project's existing
"cross-verify before High confidence" rule.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import (
    EvidenceCluster,
    ResearchFinding,
    NodeAssessment,
    ThreatAssessment,
)
from .taxonomy import NODES, node_label, node_scripture

# Phase thresholds preserved from the original fig-tree analyser.
_PHASES = [
    (70, "ADVANCED Beginning of Sorrows", "🔴",
     "Multiple J0 markers elevated simultaneously"),
    (50, "ACTIVE Beginning of Sorrows", "🟠", "Clear J0 patterns observed"),
    (30, "EARLY Beginning of Sorrows", "🟡", "Some J0 markers present"),
    (0, "MONITORING Phase", "🟢", "Routine activity, no significant patterns"),
]


def _node_intensity(clusters: List[EvidenceCluster]) -> float:
    """0-100 intensity for one node from its clusters."""
    if not clusters:
        return 0.0
    event_total = sum(c.size for c in clusters)
    max_sources = max((c.source_count for c in clusters), default=0)
    high_sev = sum(
        1 for c in clusters
        if (c.max_magnitude or 0) >= 6.0
        or any(e.confidence == "High" for e in c.events)
    )
    # Frequency component (saturating), corroboration + severity bonuses.
    frequency = min(event_total * 8, 55)
    corroboration = min(max_sources * 12, 24)
    severity = min(high_sev * 12, 21)
    return float(min(frequency + corroboration + severity, 100))


def _node_confidence(clusters: List[EvidenceCluster]) -> str:
    max_sources = max((c.source_count for c in clusters), default=0)
    any_high = any(
        e.confidence == "High" for c in clusters for e in c.events
    )
    if max_sources >= 3:
        return "High"
    if max_sources >= 2 or any_high:
        return "Med"
    return "Low"


def score_threat(clusters: List[EvidenceCluster],
                 findings: List[ResearchFinding]) -> ThreatAssessment:
    # Group clusters by node (a cluster can touch multiple nodes).
    by_node: Dict[str, List[EvidenceCluster]] = defaultdict(list)
    for c in clusters:
        for node_id in (c.node_ids or []):
            if node_id in NODES:
                by_node[node_id].append(c)

    domains_by_node: Dict[str, set] = defaultdict(set)
    for f in findings:
        for node_id in f.node_ids:
            domains_by_node[node_id].add(f.domain)

    node_assessments: List[NodeAssessment] = []
    overall = 0.0
    for node_id, node in NODES.items():
        node_clusters = by_node.get(node_id, [])
        intensity = _node_intensity(node_clusters)
        confidence = _node_confidence(node_clusters)
        if node_clusters:
            descr = (
                f"{sum(c.size for c in node_clusters)} event(s), "
                f"{max((c.source_count for c in node_clusters), default=0)} "
                f"max independent source(s)"
            )
        else:
            descr = "No qualifying signals in window"
        node_assessments.append(
            NodeAssessment(
                node_id=node_id,
                label=node_label(node_id),
                scripture=node_scripture(node_id),
                intensity=intensity,
                confidence=confidence,
                description=descr,
                contributing_domains=sorted(domains_by_node.get(node_id, [])),
            )
        )
        overall += intensity * node.weight

    overall = round(min(overall, 100.0), 1)
    phase, emoji, note = _phase_for(overall)

    cross_validation = {
        na.node_id: max(
            (c.source_count for c in by_node.get(na.node_id, [])), default=0
        )
        for na in node_assessments
    }

    node_assessments.sort(key=lambda n: n.intensity, reverse=True)
    return ThreatAssessment(
        overall_intensity=overall,
        phase=phase,
        emoji=emoji,
        note=note,
        nodes=node_assessments,
        cross_validation=cross_validation,
    )


def _phase_for(overall: float):
    for threshold, phase, emoji, note in _PHASES:
        if overall >= threshold:
            return phase, emoji, note
    return _PHASES[-1][1:]

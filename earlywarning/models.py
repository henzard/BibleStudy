#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data models shared across the early-warning pipeline.

These are plain dataclasses (no third-party deps) so every stage exchanges a
well-defined, serialisable contract instead of re-parsing markdown strings.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# Confidence levels are deliberately a small ordered vocabulary so they can be
# compared and aggregated consistently across stages.
CONFIDENCE_ORDER = {"Low": 0, "Med": 1, "High": 2}


def _stable_id(*parts: str) -> str:
    """Deterministic short id from the given parts (used for dedupe keys)."""
    digest = hashlib.sha1("␟".join(p or "" for p in parts).encode("utf-8"))
    return digest.hexdigest()[:16]


@dataclass
class RawSignal:
    """A single raw item emitted by a collector before normalization.

    Collectors produce these directly from a source (a DB row, an RSS item,
    an API record). Keep this loose: ``extra`` carries source-specific fields.
    """

    source: str                      # collector name, e.g. "earthquakes"
    title: str
    summary: str = ""
    occurred_at: Optional[str] = None  # ISO-ish timestamp string if known
    location: str = ""
    url: str = ""
    node_id: str = ""                # prophecy node hint from the source
    scripture: str = ""
    confidence: str = "Low"
    magnitude: Optional[float] = None  # numeric severity if applicable
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedEvent:
    """A cleaned, uniformly-shaped event used by every downstream stage."""

    event_id: str
    source: str
    title: str
    summary: str
    occurred_at: Optional[str]
    location: str
    url: str
    node_id: str
    scripture: str
    confidence: str
    magnitude: Optional[float]
    domain: str                       # research domain, e.g. "war"
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def make_id(source: str, title: str, occurred_at: Optional[str]) -> str:
        return _stable_id(source, title.lower().strip(), occurred_at or "")


@dataclass
class EvidenceCluster:
    """A group of corroborating events about the same underlying situation.

    ``source_count`` (distinct collectors) is the cross-validation signal that
    drives confidence: one source = Low, two = Med, three+ = High.
    """

    cluster_id: str
    domain: str
    label: str
    node_ids: List[str]
    events: List[NormalizedEvent]
    entities: List[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len({e.source for e in self.events})

    @property
    def size(self) -> int:
        return len(self.events)

    @property
    def latest(self) -> Optional[str]:
        stamps = [e.occurred_at for e in self.events if e.occurred_at]
        return max(stamps) if stamps else None

    @property
    def max_magnitude(self) -> Optional[float]:
        mags = [e.magnitude for e in self.events if e.magnitude is not None]
        return max(mags) if mags else None


@dataclass
class ResearchFinding:
    """Output of one specialist research agent for one domain."""

    domain: str
    headline: str
    assessment: str
    key_facts: List[str]
    confidence: str
    escalation: str                   # "escalating" | "steady" | "easing" | "unknown"
    node_ids: List[str] = field(default_factory=list)
    cluster_ids: List[str] = field(default_factory=list)
    source_backend: str = ""          # which LLM backend produced this
    caveats: List[str] = field(default_factory=list)


@dataclass
class NodeAssessment:
    """Per prophecy-node intensity + confidence (feeds the threat picture)."""

    node_id: str
    label: str
    scripture: str
    intensity: float                  # 0-100
    confidence: str
    description: str
    contributing_domains: List[str] = field(default_factory=list)


@dataclass
class ThreatAssessment:
    """Overall "beginning of sorrows" pattern strength across nodes."""

    overall_intensity: float          # 0-100 weighted
    phase: str
    emoji: str
    note: str
    nodes: List[NodeAssessment]
    cross_validation: Dict[str, int] = field(default_factory=dict)


@dataclass
class ExecutiveReport:
    """The human-facing synthesis written at the end of the pipeline."""

    title: str
    generated_at: str
    summary: str
    sections: List[Dict[str, str]]    # [{"heading":..., "body":...}, ...]
    markdown: str
    backend: str = ""


@dataclass
class PipelineResult:
    """Everything the pipeline produced in one run."""

    generated_at: str
    events: List[NormalizedEvent]
    clusters: List[EvidenceCluster]
    findings: List[ResearchFinding]
    threat: ThreatAssessment
    trends: Dict[str, Any]
    report: ExecutiveReport
    delivered: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "event_count": len(self.events),
            "cluster_count": len(self.clusters),
            "findings": [asdict(f) for f in self.findings],
            "threat": asdict(self.threat),
            "trends": self.trends,
            "report_title": self.report.title,
            "delivered": self.delivered,
        }

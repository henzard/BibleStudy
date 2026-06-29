#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deduplication of normalized events.

Collapses near-duplicate reports (same situation surfaced by the same source,
or trivially-restated titles) into a single representative event while keeping
a tally of how many raw reports backed it. This is the "deduplicate" stage
that precedes clustering.

We intentionally do NOT merge across different collectors here — cross-source
agreement is signal we want to preserve for the evidence graph and confidence
scoring. Dedupe is within-source noise reduction only.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from .models import NormalizedEvent

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> Set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if len(t) > 2}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def deduplicate(events: List[NormalizedEvent],
                threshold: float = 0.7) -> List[NormalizedEvent]:
    """Return a de-duplicated list. Duplicate count is recorded in
    ``event.extra['report_count']`` on the surviving representative."""
    by_source: Dict[str, List[NormalizedEvent]] = {}
    for ev in events:
        by_source.setdefault(ev.source, []).append(ev)

    survivors: List[NormalizedEvent] = []
    for source_events in by_source.values():
        kept: List[tuple[NormalizedEvent, Set[str]]] = []
        for ev in source_events:
            sig = _tokens(ev.title) | _tokens(ev.summary)
            duplicate_of = None
            for rep, rep_sig in kept:
                if ev.event_id == rep.event_id or _jaccard(sig, rep_sig) >= threshold:
                    duplicate_of = rep
                    break
            if duplicate_of is None:
                ev.extra.setdefault("report_count", 1)
                kept.append((ev, sig))
            else:
                duplicate_of.extra["report_count"] = (
                    duplicate_of.extra.get("report_count", 1) + 1
                )
        survivors.extend(ev for ev, _ in kept)

    return survivors

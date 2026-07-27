#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalization: RawSignal -> NormalizedEvent.

Produces uniformly-shaped events: stable ids, parsed timestamps, a research
``domain``, extracted keywords and coarse entities (locations / proper nouns).
Pure-Python and dependency-free so it stays deterministic and testable.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from .models import RawSignal, NormalizedEvent
from .taxonomy import DOMAINS, domain_for_collector

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+")
_PROPER = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")

_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "near", "over",
    "into", "amid", "after", "before", "report", "reports", "news", "new",
    "update", "status", "magnitude", "earthquake", "world", "bank",
}


def _safe_str(value: Optional[str]) -> str:
    """Coerce optional string fields to stripped text (None -> '')."""
    if value is None:
        return ""
    return value.strip()


def _parse_timestamp(value: Optional[str]) -> Optional[str]:
    """Best-effort normalisation of varied timestamp strings to ISO date."""
    if not value:
        return None
    value = value.strip()
    candidates = [
        "%Y-%m-%d %H:%M UTC", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    # Fall back to the leading YYYY-MM-DD if present.
    m = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    return m.group(1) if m else value


def _extract_keywords(text: str, domain_key: str) -> List[str]:
    lowered = text.lower()
    found = []
    domain = DOMAINS.get(domain_key)
    if domain:
        for kw in domain.keywords:
            if kw in lowered:
                found.append(kw)
    # Generic salient words (longer, non-stopword tokens).
    for word in _WORD.findall(lowered):
        if len(word) >= 6 and word not in _STOPWORDS and word not in found:
            found.append(word)
    return found[:8]


<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
def _text(value: Optional[str]) -> str:
    return (value or "").strip()
=======
def _safe_str(value: Optional[str]) -> str:
    """Coerce optional string fields to a stripped str (None -> '')."""
    return value.strip() if value else ""
>>>>>>> origin/cursor/biblestudy-automation-routine-46bc
=======
def _safe_str(value: Optional[str]) -> str:
    """Coerce optional string fields to a stripped str (None -> '')."""
    return value.strip() if value else ""
>>>>>>> origin/cursor/biblestudy-automation-routine-2f46
=======
def _safe_str(value: Optional[str]) -> str:
    """Return stripped string or empty string when value is None."""
    return value.strip() if value else ""
>>>>>>> origin/cursor/biblestudy-automation-routine-3269
=======
def _safe_str(value: Optional[str]) -> str:
    return value.strip() if value else ""
>>>>>>> origin/cursor/biblestudy-automation-routine-513b
=======
def _safe_str(value: Optional[str]) -> str:
    return (value or "").strip()
>>>>>>> origin/cursor/biblestudy-automation-routine-6ab9


def _extract_entities(text: str, location: str) -> List[str]:
    entities = []
    if location:
        # First location segment, e.g. "15 km SSE of Fern Forest, Hawaii".
        primary = location.split(",")[-1].strip() or location.strip()
        if primary:
            entities.append(primary)
    for match in _PROPER.findall(text):
        if match not in entities and match not in _STOPWORDS:
            entities.append(match)
    return entities[:6]


def _safe_str(value: Optional[str]) -> str:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    return value.strip() if value else ""
=======
    return (value or "").strip()
>>>>>>> origin/cursor/biblestudy-automation-routine-8122
=======
    return (value or "").strip()
>>>>>>> origin/cursor/biblestudy-automation-routine-b3e9
=======
    return (value or "").strip()
>>>>>>> origin/cursor/biblestudy-automation-routine-e729
=======
    return (value or "").strip()
>>>>>>> origin/cursor/biblestudy-automation-routine-3369


def normalize_signal(signal: RawSignal) -> NormalizedEvent:
    domain_key = domain_for_collector(signal.source)
    title = _safe_str(signal.title)
    summary = _safe_str(signal.summary)
    location = _safe_str(signal.location)
    url = _safe_str(signal.url)
    text = f"{title} {summary}"
    keywords = _extract_keywords(text, domain_key)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    location = _text(signal.location)
    title = _text(signal.title)
    entities = _extract_entities(text, location)
=======
    entities = _extract_entities(text, signal.location or "")
>>>>>>> origin/cursor/biblestudy-automation-routine-d4cc
=======
    entities = _extract_entities(text, signal.location or "")
>>>>>>> origin/cursor/biblestudy-automation-routine-a795
=======
    entities = _extract_entities(text, signal.location or "")
>>>>>>> origin/cursor/biblestudy-automation-routine-1b53
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-be27
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-50ff
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-8122
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-b3e9
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-e729
=======
    location = _safe_str(signal.location)
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-3e5c
=======
    location = _safe_str(signal.location)
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-46bc
=======
    location = _safe_str(signal.location)
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-2f46
=======
    entities = _extract_entities(text, _safe_str(signal.location))
>>>>>>> origin/cursor/biblestudy-automation-routine-513b
=======
    location = _safe_str(signal.location)
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-6ab9
=======
    entities = _extract_entities(text, location)
>>>>>>> origin/cursor/biblestudy-automation-routine-3369
    occurred = _parse_timestamp(signal.occurred_at)
    title = _safe_str(signal.title)
    return NormalizedEvent(
        event_id=NormalizedEvent.make_id(signal.source, title, occurred),
        source=signal.source,
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        title=title,
        summary=_text(signal.summary),
        occurred_at=occurred,
        location=location,
        url=_text(signal.url),
        node_id=_text(signal.node_id),
        scripture=_text(signal.scripture),
        confidence=_text(signal.confidence) or "Low",
=======
        title=(signal.title or "").strip(),
        summary=(signal.summary or "").strip(),
        occurred_at=occurred,
=======
        title=(signal.title or "").strip(),
        summary=(signal.summary or "").strip(),
        occurred_at=occurred,
>>>>>>> origin/cursor/biblestudy-automation-routine-a795
=======
        title=(signal.title or "").strip(),
        summary=(signal.summary or "").strip(),
        occurred_at=occurred,
>>>>>>> origin/cursor/biblestudy-automation-routine-1b53
        location=(signal.location or "").strip(),
        url=(signal.url or "").strip(),
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-be27
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-50ff
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-8122
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-b3e9
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-e729
=======
        title=_safe_str(signal.title),
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=location,
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-3e5c
=======
        title=_safe_str(signal.title),
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=location,
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-46bc
=======
        title=_safe_str(signal.title),
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=location,
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-2f46
=======
        title=_safe_str(signal.title),
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=_safe_str(signal.location),
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-3269
=======
        title=_safe_str(signal.title),
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=_safe_str(signal.location),
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-513b
=======
        title=title,
        summary=_safe_str(signal.summary),
        occurred_at=occurred,
        location=location,
        url=_safe_str(signal.url),
>>>>>>> origin/cursor/biblestudy-automation-routine-6ab9
=======
        title=title,
        summary=summary,
        occurred_at=occurred,
        location=location,
        url=url,
>>>>>>> origin/cursor/biblestudy-automation-routine-3369
        node_id=signal.node_id or "",
        scripture=signal.scripture or "",
        confidence=signal.confidence or "Low",
>>>>>>> origin/cursor/biblestudy-automation-routine-d4cc
        magnitude=signal.magnitude,
        domain=domain_key,
        keywords=keywords,
        entities=entities,
        extra=dict(signal.extra),
    )


def normalize_all(signals: List[RawSignal]) -> List[NormalizedEvent]:
    return [normalize_signal(s) for s in signals]

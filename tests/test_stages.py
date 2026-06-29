#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for individual pipeline stages."""

from __future__ import annotations

from earlywarning.collectors import collect_all
from earlywarning.dedupe import deduplicate
from earlywarning.evidence_graph import build_clusters
from earlywarning.llm import LLMClient, _extract_json
from earlywarning.config import LLMConfig
from earlywarning.models import RawSignal
from earlywarning.normalize import normalize_all, normalize_signal
from earlywarning.research import ResearchCoordinator
from earlywarning.scoring import score_threat
from earlywarning.trends import analyze_trends


def test_collectors_read_seeded_db(seeded_db):
    signals = collect_all(seeded_db, lookback_days=30)
    sources = {s.source for s in signals}
    assert "earthquakes" in sources
    assert "conflicts" in sources
    assert "economic" in sources
    # 3 quakes + 2 conflicts + 1 economic
    assert len(signals) == 6


def test_collectors_missing_db_is_empty(tmp_path):
    assert collect_all(tmp_path / "nope.db") == []


def test_normalize_assigns_domain_and_entities():
    sig = RawSignal(source="earthquakes", title="M6.5 earthquake: Antofagasta, Chile",
                    occurred_at="2026-06-27 10:00 UTC", location="Antofagasta, Chile",
                    magnitude=6.5, node_id="J0")
    ev = normalize_signal(sig)
    assert ev.domain == "disaster"
    assert ev.occurred_at == "2026-06-27 10:00"
    assert "Chile" in ev.entities
    assert ev.event_id  # stable id present


def test_dedupe_collapses_within_source():
    sigs = [
        RawSignal(source="conflicts", title="Fighting in Sudan offensive",
                  summary="Heavy fighting reported in Sudan offensive"),
        RawSignal(source="conflicts", title="Fighting in Sudan offensive today",
                  summary="Heavy fighting reported in Sudan offensive"),
        RawSignal(source="conflicts", title="Floods in Bangladesh",
                  summary="Monsoon floods displace thousands"),
    ]
    events = normalize_all(sigs)
    deduped = deduplicate(events, threshold=0.6)
    assert len(deduped) == 2
    counts = sorted(e.extra.get("report_count", 1) for e in deduped)
    assert counts == [1, 2]


def test_dedupe_keeps_cross_source(seeded_db):
    events = normalize_all(collect_all(seeded_db, 30))
    deduped = deduplicate(events)
    # Cross-source events must not be merged away.
    assert len({e.source for e in deduped}) >= 3


def test_evidence_graph_clusters_shared_entities(seeded_db):
    events = normalize_all(collect_all(seeded_db, 30))
    clusters = build_clusters(events)
    # The two Chile quakes share an entity -> one disaster cluster.
    disaster = [c for c in clusters if c.domain == "disaster"]
    assert disaster
    chile = max(disaster, key=lambda c: c.size)
    assert chile.size >= 2
    # The two Sudan conflicts corroborate within the war domain.
    war = [c for c in clusters if c.domain == "war"]
    assert any(c.size >= 2 for c in war)


def test_scoring_caps_confidence_without_corroboration(seeded_db):
    events = normalize_all(collect_all(seeded_db, 30))
    clusters = build_clusters(events)
    findings = ResearchCoordinator(
        LLMClient.from_config(LLMConfig(provider="none"))).run(clusters)
    threat = score_threat(clusters, findings)
    j0 = next(n for n in threat.nodes if n.node_id == "J0")
    assert j0.intensity > 0
    # Single-source J0 evidence cannot reach High confidence.
    assert j0.confidence in ("Low", "Med")
    assert 0 <= threat.overall_intensity <= 100


def test_trends_handle_empty_db(empty_db):
    result = analyze_trends(empty_db, weeks=4)
    assert result["available"] is True
    assert result["metrics"]["earthquakes"]["available"] is True


def test_llm_offline_uses_fallback():
    client = LLMClient.from_config(LLMConfig(provider="none"))
    assert client.online is False
    out = client.complete_json("sys", "prompt", {"x": 1, "y": "z"})
    assert out == {"x": 1, "y": "z"}


def test_extract_json_tolerates_fences_and_prose():
    assert _extract_json('here you go ```json\n{"a": 1}\n``` done') == {"a": 1}
    assert _extract_json('noise {"b": 2} trailing') == {"b": 2}
    assert _extract_json("no json here") is None

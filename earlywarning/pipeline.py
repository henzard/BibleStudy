#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pipeline orchestrator.

Wires the stages together:

    collect -> normalize -> dedupe -> evidence graph ->
    research agents (parallel) -> threat scoring -> trend memory ->
    executive report -> deliver

Each call returns a :class:`PipelineResult` describing everything produced.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from .changes import detect_changes
from .collectors import collect_all, collect_live
from .config import PipelineConfig
from .dedupe import deduplicate
from .evidence_graph import build_clusters
from .freshness import analyze_freshness
from .llm import LLMClient
from .models import PipelineResult
from .normalize import normalize_all
from .outputs import deliver
from .persist import persist_signals
from .report import build_report
from .research import ResearchCoordinator
from .scoring import score_threat
from .state import load_previous, save_run
from .trends import analyze_trends


def run_pipeline(config: Optional[PipelineConfig] = None,
                 log: Optional[Callable[[str], None]] = None,
                 live: bool = False) -> PipelineResult:
    cfg = config or PipelineConfig.from_env()
    emit = log or (lambda _m: None)

    llm = LLMClient.from_config(cfg.llm)
    emit(f"LLM backend: {llm.backend_name} (online={llm.online})")

    # 1. Collect raw signals.
    if live:
        # Hybrid mode: fetch from the network, persist for offline replay,
        # then analyse the fresh data.
        raw = collect_live(cfg.lookback_days)
        inserted = persist_signals(cfg.db_path, raw)
        emit(f"Live-collected {len(raw)} signal(s); persisted "
             f"{sum(inserted.values())} new row(s)")
    else:
        # Offline mode: replay from the SQLite store.
        raw = collect_all(cfg.db_path, cfg.lookback_days)
        emit(f"Collected {len(raw)} raw signal(s) from store")

    # 2. Normalize -> 3. Deduplicate.
    events = normalize_all(raw)
    events = deduplicate(events)
    emit(f"Normalized + deduped to {len(events)} event(s)")

    # 4. Evidence graph / clustering.
    clusters = build_clusters(events)
    emit(f"Built {len(clusters)} evidence cluster(s)")

    # 5. Parallel specialist research.
    coordinator = ResearchCoordinator(llm, max_workers=cfg.max_workers)
    findings = coordinator.run(clusters)
    emit(f"Produced {len(findings)} research finding(s)")

    # 6. Threat scoring.
    threat = score_threat(clusters, findings)
    emit(f"Overall pattern strength: {threat.overall_intensity:.0f}/100 "
         f"({threat.phase})")

    # 7. Trend memory.
    trends = analyze_trends(cfg.db_path, cfg.trend_weeks)

    # 8. Change detection + source health (vs the previous stored run).
    previous = load_previous(cfg.db_path)
    changes = detect_changes(threat, findings, previous)
    freshness = analyze_freshness(cfg.db_path)
    emit(f"Alert level: {changes.level} — {changes.summary}")
    if freshness.any_stale:
        emit(f"Stale sources: {', '.join(freshness.stale_sources)}")

    # 9. Executive report.
    report = build_report(threat, findings, trends, llm,
                          changes=changes, freshness=freshness)

    result = PipelineResult(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        events=events,
        clusters=clusters,
        findings=findings,
        threat=threat,
        trends=trends,
        report=report,
        alert_level=changes.level,
        changes=changes,
        freshness=freshness,
    )

    # 10. Deliver (level/change/cooldown-aware routing).
    result.delivered = deliver(result, cfg.outputs, cfg.output_dir, previous)
    emit(f"Delivered: {', '.join(result.delivered) or 'nothing'}")

    # 11. Persist this run's state for the next comparison.
    save_run(cfg.db_path, result.to_dict(), changes.level, result.generated_at,
             threat.overall_intensity, threat.phase)

    return result

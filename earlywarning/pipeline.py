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

from .collectors import collect_all
from .config import PipelineConfig
from .dedupe import deduplicate
from .evidence_graph import build_clusters
from .llm import LLMClient
from .models import PipelineResult
from .normalize import normalize_all
from .outputs import deliver
from .report import build_report
from .research import ResearchCoordinator
from .scoring import score_threat
from .trends import analyze_trends


def run_pipeline(config: Optional[PipelineConfig] = None,
                 log: Optional[Callable[[str], None]] = None) -> PipelineResult:
    cfg = config or PipelineConfig.from_env()
    emit = log or (lambda _m: None)

    llm = LLMClient.from_config(cfg.llm)
    emit(f"LLM backend: {llm.backend_name} (online={llm.online})")

    # 1. Collect raw signals from the SQLite store.
    raw = collect_all(cfg.db_path, cfg.lookback_days)
    emit(f"Collected {len(raw)} raw signal(s)")

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

    # 8. Executive report.
    report = build_report(threat, findings, trends, llm)

    result = PipelineResult(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        events=events,
        clusters=clusters,
        findings=findings,
        threat=threat,
        trends=trends,
        report=report,
    )

    # 9. Deliver.
    result.delivered = deliver(result, cfg.outputs, cfg.output_dir)
    emit(f"Delivered: {', '.join(result.delivered) or 'nothing'}")

    return result

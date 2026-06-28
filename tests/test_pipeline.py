#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end pipeline tests (offline / heuristic backend)."""

from __future__ import annotations

import json

from earlywarning.config import PipelineConfig, LLMConfig
from earlywarning.pipeline import run_pipeline


def _config(db, tmp_path):
    cfg = PipelineConfig.from_env(db_path=db, lookback_days=30)
    cfg.llm = LLMConfig(provider="none")
    cfg.output_dir = tmp_path / "ew"
    cfg.outputs.dashboard_path = str(tmp_path / "dash" / "latest.json")
    cfg.outputs.dry_run = True
    return cfg


def test_pipeline_runs_offline_and_writes_artifacts(seeded_db, tmp_path):
    cfg = _config(seeded_db, tmp_path)
    result = run_pipeline(cfg)

    assert result.events
    assert result.clusters
    assert result.findings
    assert result.report.backend == "heuristic"
    assert "Executive Summary" in result.report.markdown
    # Guardrails must always be present.
    assert "No date-setting" in result.report.markdown

    # Local artefacts written.
    md = tmp_path / "ew"
    assert any(md.glob("*_early_warning.md"))
    dash = tmp_path / "dash" / "latest.json"
    assert dash.exists()
    payload = json.loads(dash.read_text(encoding="utf-8"))
    assert payload["event_count"] == len(result.events)


def test_pipeline_dry_run_does_not_send_outward(seeded_db, tmp_path):
    cfg = _config(seeded_db, tmp_path)
    cfg.outputs.slack_webhook = "https://hooks.example/x"
    cfg.outputs.dry_run = True
    result = run_pipeline(cfg)
    assert "slack:dry-run" in result.delivered
    assert not any(d.startswith("slack:sent") for d in result.delivered)


def test_pipeline_handles_empty_db(empty_db, tmp_path):
    cfg = _config(empty_db, tmp_path)
    result = run_pipeline(cfg)
    assert result.events == []
    assert result.findings == []
    # Still produces a coherent report.
    assert result.threat.overall_intensity == 0
    assert "MONITORING Phase" in result.report.markdown


def test_to_dict_is_json_serialisable(seeded_db, tmp_path):
    result = run_pipeline(_config(seeded_db, tmp_path))
    json.dumps(result.to_dict())  # must not raise

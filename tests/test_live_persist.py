#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hybrid live → persist → replay path (all offline)."""

from __future__ import annotations

from earlywarning.collectors import collect_all, live
from earlywarning.collectors.live import build_live_collectors
from earlywarning.config import PipelineConfig, LLMConfig
from earlywarning import pipeline as pipeline_mod
from earlywarning.persist import persist_signals


SAMPLES = {
    "_m_earthquakes": {"magnitude": 6.5, "location": "Antofagasta, Chile",
                       "date": "2099-06-27 10:00 UTC", "url": "http://u/eq1"},
    "_m_gdacs": {"type": "Flood", "alert_level": "Orange",
                 "description": "Severe flood", "severity": "Severe flood",
                 "country": "Bangladesh", "population_affected": "2.5M",
                 "date": "2099-06-26", "url": "http://u/g1"},
    "_m_un": {"title": "Sudan offensive displaces thousands",
              "description": "Heavy fighting", "date": "2099-06-25",
              "url": "http://u/u1", "confidence": "High",
              "category": "Active Conflict"},
    "_m_worldbank": {"title": "Food crisis deepens",
                     "description": "Famine risk rising", "date": "2099-06-24",
                     "url": "http://u/w1", "nodes": ["J0"], "confidence": "Med"},
    "_m_economic": {"series_id": "CPIAUCSL", "name": "CPI", "status": "Crisis",
                    "confidence": "High", "latest_value": 312.5,
                    "latest_date": "2099-06-01", "yoy_change": 7.2,
                    "assessment": "Critical inflation"},
    "_m_fred_news": {"title": "New CPI release", "description": "data",
                     "category": "Data", "date": "2099-06-20",
                     "url": "http://u/f1", "relevant": True},
    "_m_spaceweather": {"severity": "SEVERE", "confidence": "High",
                        "description": "G4 storm",
                        "issue_datetime": "2099-06-20 12:00:00.000",
                        "product_id": "K04"},
    "_m_eff": {"title": "Facial recognition mandate", "description": "biometric",
               "link": "http://u/e1",
               "pub_date": "Thu, 20 Jun 2099 12:00:00 +0000",
               "category": "Digital ID", "confidence": "Low"},
    "_m_temple_mount": {"title": "Temple Mount access dispute",
                        "description": "tensions", "date": "2099-06-19",
                        "url": "http://u/t1", "source": "Times of Israel",
                        "node": "J3", "scripture": "Dan 9:27",
                        "category": "Temple Mount", "confidence": "High"},
    "_m_covenant": {"title": "Regional accord signed with Israel",
                    "description": "multi-party framework",
                    "date": "2099-06-18", "url": "http://u/cv1",
                    "treaty_type": "accord", "confidence": "High"},
    "_m_cbdc": {"title": "Digital euro made mandatory",
                "description": "CBDC required for payments",
                "date": "2099-06-17", "url": "http://u/cb1",
                "category": "CBDC", "status": "mandatory",
                "country": "Eurozone", "confidence": "High"},
    "_m_coalition": {"title": "Russia-Iran joint exercise",
                     "description": "naval drill", "date": "2099-06-16",
                     "url": "http://u/co1", "nations": ["Russia", "Iran"],
                     "event_type": "joint exercise", "confidence": "Med"},
    "_m_eu": {"title": "EU treaty change proposed",
              "description": "end unanimity", "date": "2099-06-15",
              "url": "http://u/eu1", "category": "treaty change",
              "confidence": "High"},
    "_m_ai_enforcement": {"title": "AI fines drivers automatically",
                          "description": "algorithmic enforcement",
                          "date": "2099-06-14", "url": "http://u/ai1",
                          "category": "enforcement", "node": "B4",
                          "confidence": "Med"},
    "_m_gospel": {"metric_name": "languages_no_scripture", "value": 880,
                  "description": "Languages with no Scripture",
                  "date": "2099-06-13", "url": "http://u/g2",
                  "confidence": "High"},
    "_m_who_outbreaks": {"disease": "Cholera", "country": "Sudan",
                         "description": "outbreak reported",
                         "date": "2099-06-12", "url": "http://u/wo1",
                         "severity": "Severe", "confidence": "Med"},
}


def _signals():
    return [getattr(live, fn)(rec) for fn, rec in SAMPLES.items()]


ALL_SOURCES = {
    "earthquakes", "disasters", "conflicts", "worldbank", "economic",
    "fred_news", "spaceweather", "eff", "temple_mount",
    "covenant", "cbdc", "coalition", "eu", "ai_enforcement", "gospel",
    "who_outbreaks",
}


def test_build_live_collectors_count():
    cols = build_live_collectors()
    assert len(cols) == 16
    assert {c.name for c in cols} == ALL_SOURCES


def test_mappers_normalize_dates_to_iso():
    sigs = {s.source: s for s in _signals()}
    # RSS-style pub_date must become sortable ISO so DB filters work.
    assert sigs["eff"].occurred_at.startswith("2099-06-20")
    assert sigs["spaceweather"].occurred_at == "2099-06-20"


def test_persist_round_trip_activates_all_sources(tmp_path):
    db = tmp_path / "live.db"
    inserted = persist_signals(db, _signals())
    assert sum(inserted.values()) == 16

    raw = collect_all(db, lookback_days=40000)
    assert {s.source for s in raw} == ALL_SOURCES


def test_persist_is_idempotent(tmp_path):
    db = tmp_path / "live.db"
    first = persist_signals(db, _signals())
    second = persist_signals(db, _signals())
    assert sum(first.values()) == 16
    assert sum(second.values()) == 0  # nothing new on re-run


def test_persist_ignores_unknown_source(tmp_path):
    from earlywarning.models import RawSignal
    db = tmp_path / "live.db"
    out = persist_signals(db, [RawSignal(source="mystery", title="x")])
    assert out == {}


def test_pipeline_live_mode_persists_then_analyses(tmp_path, monkeypatch):
    # Stub the network collector so live mode runs fully offline.
    monkeypatch.setattr(pipeline_mod, "collect_live", lambda days: _signals())

    cfg = PipelineConfig.from_env(db_path=tmp_path / "p.db", lookback_days=40000)
    cfg.llm = LLMConfig(provider="none")
    cfg.output_dir = tmp_path / "ew"
    cfg.outputs.dashboard_path = str(tmp_path / "d" / "latest.json")
    cfg.outputs.dry_run = True

    result = run = pipeline_mod.run_pipeline(cfg, live=True)
    domains = {f.domain for f in result.findings}
    assert {"war", "famine", "financial", "cosmic", "digital_control",
            "middle_east", "disaster", "covenant", "coalition", "eu_power",
            "ai_enforcement", "gospel", "health"} <= domains
    # Data was persisted -> an offline replay sees the same sources.
    raw = collect_all(tmp_path / "p.db", lookback_days=40000)
    assert len(raw) == 16

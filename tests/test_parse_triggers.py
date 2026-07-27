#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for the trigger-layer fetchers (no network).

Covers: covenant watch, CBDC, Ezek 38 coalition, EU consolidation,
AI enforcement, WHO outbreaks, gospel reach, and the temple-preparation
marker extension.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import (  # noqa: E402
    fetch_ai_enforcement,
    fetch_cbdc,
    fetch_coalition,
    fetch_covenant_watch,
    fetch_eu_consolidation,
    fetch_gospel_reach,
    fetch_temple_mount_news,
    fetch_who_outbreaks,
)

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# --- covenant watch --------------------------------------------------------

def test_covenant_parse_requires_israel_and_covenant_terms():
    articles = fetch_covenant_watch.parse(
        _load("covenant_sample.rss"), source="Sample", days=365000)
    titles = [a["title"] for a in articles]
    # Tech-sector item has Israel but no covenant term -> excluded.
    assert not any("Tech Sector" in t for t in titles)
    assert any("Normalization Accord" in t for t in titles)
    assert any("Water Treaty" in t for t in titles)


def test_covenant_multiparty_signed_is_high_confidence():
    articles = fetch_covenant_watch.parse(
        _load("covenant_sample.rss"), source="Sample", days=365000)
    accord = next(a for a in articles if "Normalization Accord" in a["title"])
    assert accord["node"] == "D1"
    assert accord["scripture"] == "Dan 9:27"
    assert accord["confidence"] == "High"


# --- cbdc ------------------------------------------------------------------

def test_cbdc_parse_filters_and_stages():
    articles = fetch_cbdc.parse(
        _load("cbdc_sample.rss"), source="Sample", days=365000)
    by_title = {a["title"]: a for a in articles}
    assert not any("Interest Rates" in t for t in by_title)
    mandatory = next(a for a in articles if "Mandatory" in a["title"])
    assert mandatory["status"] == "mandatory"
    assert mandatory["confidence"] == "High"       # compulsion = Rev 13 shape
    pilot = next(a for a in articles if "Pilot" in a["title"])
    assert pilot["status"] == "pilot"
    assert pilot["confidence"] == "Med"


# --- coalition -------------------------------------------------------------

def test_coalition_requires_two_named_nations():
    articles = fetch_coalition.parse(
        _load("coalition_sample.rss"), source="Sample", days=365000)
    titles = [a["title"] for a in articles]
    # Single-nation grain story excluded even though Russia is named.
    assert not any("Grain" in t for t in titles)
    assert len(articles) == 2


def test_coalition_three_nations_military_is_high():
    articles = fetch_coalition.parse(
        _load("coalition_sample.rss"), source="Sample", days=365000)
    trilateral = next(a for a in articles if "Joint Naval" in a["title"])
    assert set(trilateral["nations"]) == {"Russia", "Iran", "Turkey"}
    assert trilateral["confidence"] == "High"
    assert trilateral["node"] == "E38"
    bilateral = next(a for a in articles if "Iran and Sudan" in a["title"])
    assert set(bilateral["nations"]) == {"Iran", "Sudan"}
    assert bilateral["confidence"] == "Med"


# --- eu consolidation ------------------------------------------------------

def test_eu_parse_only_centralization_events():
    articles = fetch_eu_consolidation.parse(
        _load("eu_consolidation_sample.rss"), source="Sample", days=365000)
    titles = [a["title"] for a in articles]
    assert not any("Agricultural" in t for t in titles)
    treaty = next(a for a in articles if "Treaty Change" in a["title"])
    assert treaty["node"] == "D2"
    assert treaty["confidence"] == "High"   # sovereignty-transfer language


# --- ai enforcement --------------------------------------------------------

def test_ai_enforcement_categories_and_nodes():
    articles = fetch_ai_enforcement.parse(
        _load("ai_enforcement_sample.rss"), source="Sample", days=365000)
    by_cat = {a["category"]: a for a in articles}
    assert "enforcement" in by_cat
    assert "incident" in by_cat
    assert "veneration" in by_cat
    # Vendor-revenue story is ignored: AI progress alone is not the signal.
    assert not any("Revenue" in a["title"] for a in articles)
    assert by_cat["enforcement"]["node"] == "B4"
    assert by_cat["enforcement"]["confidence"] == "High"


# --- who outbreaks ---------------------------------------------------------

def test_who_parse_extracts_disease_and_country():
    articles = fetch_who_outbreaks.parse(
        _load("who_outbreaks_sample.rss"), source="Sample", days=365000)
    assert not any("Budget" in a["title"] for a in articles)
    ebola = next(a for a in articles if "Ebola" in a["title"])
    assert "Congo" in ebola["country"]
    assert ebola["severity"] == "Severe"
    assert ebola["confidence"] == "High"       # severe + spreading
    cholera = next(a for a in articles if "Cholera" in a["title"])
    assert cholera["country"] == "Sudan"
    assert cholera["node"] == "J0"


# --- gospel reach ----------------------------------------------------------

def test_gospel_parse_metrics():
    records = fetch_gospel_reach.parse(_load("gospel_reach_sample.json"))
    assert len(records) == 4
    names = {r["metric_name"] for r in records}
    assert "languages_no_scripture" in names
    for r in records:
        assert r["date"] == "2099-10-01"
        assert r["node"] == "M14"
        assert isinstance(r["value"], float)


def test_gospel_parse_tolerates_garbage():
    assert fetch_gospel_reach.parse("") == []
    assert fetch_gospel_reach.parse("not json") == []
    assert fetch_gospel_reach.parse('{"metrics": []}') == []  # no as_of


# --- temple preparation markers -------------------------------------------

def test_temple_preparation_markers_classify_high():
    cls = fetch_temple_mount_news.classify_article(
        "Red Heifer Inspection Completed by Temple Institute Priests",
        "The Temple Institute announced the red heifer passed inspection as "
        "priestly garments and altar preparations continue.",
        "Sample")
    assert cls["relevant"] is True
    assert cls["node"] == "J3"
    assert cls["category"] == "Temple Preparation"
    assert cls["confidence"] == "High"

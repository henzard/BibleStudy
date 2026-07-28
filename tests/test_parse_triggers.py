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
    fetch_europe_demographics,
    fetch_europe_mixture,
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


def test_who_classify_news_style_title():
    # Google News style: publisher suffix + "in <Country>" phrase.
    cls = fetch_who_outbreaks.classify(
        "Cholera outbreak kills 30 in South Sudan - Reuters",
        "Health officials confirmed the outbreak is spreading.")
    assert cls["relevant"] is True
    assert cls["disease"] == "Cholera"
    assert cls["country"] == "South Sudan"
    assert cls["severity"] == "Severe"


def test_eu_classify_self_framing_terms_need_no_eu_cue():
    # "Von der Leyen pushes defence union" has no literal "EU"/"Brussels".
    cls = fetch_eu_consolidation.classify(
        "Von der Leyen pushes for defence union after summit",
        "The proposal outlines a joint command structure.")
    assert cls["relevant"] is True
    assert cls["node"] == "D2"
    # But generic centralization language without any EU frame stays out.
    generic = fetch_eu_consolidation.classify(
        "City council approves emergency powers for mayor",
        "The measure centralizes local authority.")
    assert generic["relevant"] is False


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


def test_gospel_parse_html_wycliffe_page():
    records = fetch_gospel_reach.parse_html(
        _load("gospel_reach_sample.html"), url="https://example.org/stats")
    by_name = {r["metric_name"]: r["value"] for r in records}
    assert by_name["languages_full_bible"] == 776
    assert by_name["languages_new_testament"] == 1798
    assert by_name["languages_portions"] == 1433
    assert by_name["languages_waiting"] == 544
    assert all(r["date"] == "2099-08-01" for r in records)


def test_gospel_parse_html_tolerates_garbage():
    assert fetch_gospel_reach.parse_html("") == []
    assert fetch_gospel_reach.parse_html("<html><p>nothing here</p></html>") == []


# --- europe mixture (D3) ---------------------------------------------------

def test_europe_mixture_categories():
    articles = fetch_europe_mixture.parse(
        _load("europe_mixture_sample.rss"), source="Sample", days=365000)
    by_cat = {a["category"]: a for a in articles}
    assert "legal_recognition" in by_cat
    assert "confessional_politics" in by_cat
    assert "integration_pact" in by_cat
    assert "non_adherence" in by_cat
    # Non-European religious-court story is excluded: Europe frame required.
    assert not any("Jakarta" in a["title"] for a in articles)
    legal = by_cat["legal_recognition"]
    assert legal["node"] == "D3"
    assert legal["confidence"] == "High"     # court + tribunal + council
    assert by_cat["non_adherence"]["confidence"] == "Low"   # noisy category


def test_europe_mixture_integration_needs_mena_counterparty():
    cls = fetch_europe_mixture.classify(
        "EU opens accession talks with Norway",
        "Membership discussions resume in Brussels.")
    assert cls["relevant"] is False          # accession, but no MENA party


# --- europe demographics (D3) ----------------------------------------------

def test_europe_demographics_parse_html():
    records = fetch_europe_demographics.parse_html(
        _load("europe_demographics_sample.html"), url="https://example.org/x")
    by_name = {r["metric_name"]: r["value"] for r in records}
    assert by_name["muslim_share_pct"] == 4.9
    assert by_name["muslim_share_2050_high_pct"] == 14.0
    assert by_name["muslim_population_millions"] == 25.8
    assert all(r["node"] == "D3" for r in records)
    assert all(r["date"] == "2016-01-01" for r in records)


def test_europe_demographics_parse_json_and_garbage():
    doc = ('{"as_of": "2099-01-01", "metrics": '
           '[{"name": "muslim_share_pct", "value": 5.2}]}')
    records = fetch_europe_demographics.parse(doc)
    assert len(records) == 1
    assert records[0]["value"] == 5.2
    assert fetch_europe_demographics.parse("not json") == []
    assert fetch_europe_demographics.parse_html("<p>no data</p>") == []


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

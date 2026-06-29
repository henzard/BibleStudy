#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for fetch_eff_news (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_eff_news  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "eff_sample.rss"


def _load():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_returns_articles():
    # Large window so the date cutoff never filters out the fixture rows.
    articles = fetch_eff_news.parse(_load(), days=36500)
    assert len(articles) >= 1
    for art in articles:
        for field in ("title", "link", "pub_date", "keywords",
                      "description", "category", "confidence", "relevance"):
            assert field in art
        assert art["keywords"]  # at least one B2 keyword matched

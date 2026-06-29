#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline parse tests for fetch_temple_mount_news (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import fetch_temple_mount_news  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "temple_mount_sample.rss"


def _load():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_returns_articles():
    # Large window so the date cutoff never filters out the fixture rows.
    articles = fetch_temple_mount_news.parse(
        _load(), source="Sample Feed", days=36500)
    assert len(articles) >= 1
    for art in articles:
        for field in ("title", "description", "date", "url", "source",
                      "node", "scripture", "category", "confidence",
                      "keywords"):
            assert field in art


def test_parse_maps_temple_mount_to_j3():
    articles = fetch_temple_mount_news.parse(
        _load(), source="Sample Feed", days=36500)
    nodes = {a["node"] for a in articles}
    assert "J3" in nodes  # Temple Mount / Al-Aqsa item maps to J3

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persist collected signals into the SQLite store.

Used by the hybrid live mode: a live run fetches from the network, persists the
results here, and every later *offline* run replays them from the database.

Each source routes to its table. Tables with a UNIQUE ``event_id`` use
``INSERT OR IGNORE`` for idempotency; the few legacy tables without one
(conflicts, economic_indicators, worldbank_news) get an explicit existence
check on a natural key so repeated runs don't accumulate duplicates.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List

from .models import RawSignal
from .schema import ensure_schema


def _event_id(signal: RawSignal) -> str:
    existing = signal.extra.get("event_id")
    if existing:
        return str(existing)
    basis = f"{signal.source}|{signal.title}|{signal.occurred_at or ''}"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:20]


def _exists(conn: sqlite3.Connection, table: str, where: str,
            params: tuple) -> bool:
    row = conn.execute(
        f"SELECT 1 FROM {table} WHERE {where} LIMIT 1", params
    ).fetchone()
    return row is not None


def _date(signal: RawSignal) -> str:
    return signal.occurred_at or ""


# --- per-source persisters -------------------------------------------------
# Each returns 1 if a new row was written, else 0.

def _p_earthquakes(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO earthquakes "
        "(event_id, date_utc, magnitude, location, latitude, longitude, "
        "source_url, node_id) VALUES (?,?,?,?,?,?,?, 'J0')",
        (_event_id(s), _date(s), s.magnitude or 0.0, s.location,
         s.extra.get("latitude"), s.extra.get("longitude"), s.url),
    )
    return cur.rowcount or 0


def _p_disasters(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO disasters "
        "(event_id, date_utc, disaster_type, location, alert_level, "
        "severity_description, population_affected, source_url, node_id) "
        "VALUES (?,?,?,?,?,?,?,?, 'J0')",
        (_event_id(s), _date(s), s.extra.get("type", "Unknown"),
         s.location or s.extra.get("country", ""), s.extra.get("alert_level"),
         s.summary, _as_int(s.extra.get("population_affected")), s.url),
    )
    return cur.rowcount or 0


def _p_conflicts(conn, s: RawSignal) -> int:
    if _exists(conn, "conflicts", "date=? AND location=? AND description=?",
               (_date(s), s.location, s.summary)):
        return 0
    conn.execute(
        "INSERT INTO conflicts "
        "(date, location, conflict_type, casualties, description, source_url, "
        "confidence, node_id) VALUES (?,?,?,?,?,?,?, 'J0')",
        (_date(s), s.location, s.extra.get("conflict_type", "Conflict"),
         _as_int(s.extra.get("casualties")), s.summary, s.url, s.confidence),
    )
    return 1


def _p_economic(conn, s: RawSignal) -> int:
    name = s.extra.get("indicator_name", s.title)
    if _exists(conn, "economic_indicators", "date=? AND indicator_name=?",
               (_date(s), name)):
        return 0
    conn.execute(
        "INSERT INTO economic_indicators "
        "(date, indicator_name, indicator_category, value, yoy_change, status, "
        "confidence, node_id) VALUES (?,?,?,?,?,?,?, 'H0')",
        (_date(s), name, s.extra.get("category", "Economic"),
         s.magnitude or 0.0, _as_float(s.extra.get("yoy_change")),
         s.extra.get("status", "Unknown"), s.confidence),
    )
    return 1


def _p_worldbank(conn, s: RawSignal) -> int:
    if _exists(conn, "worldbank_news", "date=? AND headline=?",
               (_date(s), s.title)):
        return 0
    conn.execute(
        "INSERT INTO worldbank_news "
        "(date, headline, description, category, keywords, confidence, "
        "source_url, node_id) VALUES (?,?,?,?,?,?,?,?)",
        (_date(s), s.title, s.summary, s.extra.get("category", "General"),
         _as_text(s.extra.get("keywords")), s.confidence, s.url,
         s.node_id or "J0"),
    )
    return 1


def _p_spaceweather(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO space_weather "
        "(event_id, date, severity, description, confidence, source_url, node_id) "
        "VALUES (?,?,?,?,?,?, 'J6')",
        (_event_id(s), _date(s), s.extra.get("severity", "INFO"), s.summary,
         s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_digital_rights(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO digital_rights "
        "(event_id, date, title, description, category, keywords, confidence, "
        "source_url, node_id) VALUES (?,?,?,?,?,?,?,?, 'B2')",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("category"),
         _as_text(s.extra.get("keywords")), s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_temple_mount(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO temple_mount_news "
        "(event_id, date, title, description, source, category, keywords, "
        "confidence, scripture, source_url, node_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("source"),
         s.extra.get("category"), _as_text(s.extra.get("keywords")),
         s.confidence, s.scripture, s.url, s.node_id or "J3"),
    )
    return cur.rowcount or 0


def _p_fred_news(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO fred_news "
        "(event_id, date, title, description, category, confidence, source_url, "
        "node_id) VALUES (?,?,?,?,?,?,?, 'H0')",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("category"),
         s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_covenant(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO covenant_watch "
        "(event_id, date, title, description, parties, treaty_type, keywords, "
        "confidence, source_url, node_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary, s.location,
         s.extra.get("treaty_type"), _as_text(s.extra.get("keywords")),
         s.confidence, s.url, s.node_id or "D1"),
    )
    return cur.rowcount or 0


def _p_cbdc(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO cbdc_tracker "
        "(event_id, date, title, description, country, status, category, "
        "confidence, source_url) VALUES (?,?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary,
         s.extra.get("country") or s.location, s.extra.get("status"),
         s.extra.get("category"), s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_coalition(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO coalition_events "
        "(event_id, date, title, description, nations, event_type, "
        "confidence, source_url) VALUES (?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary,
         _as_text(s.extra.get("nations")) or s.location,
         s.extra.get("event_type"), s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_eu(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO eu_consolidation "
        "(event_id, date, title, description, category, confidence, "
        "source_url) VALUES (?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("category"),
         s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_ai_enforcement(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO ai_enforcement "
        "(event_id, date, title, description, category, confidence, "
        "source_url, node_id) VALUES (?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("category"),
         s.confidence, s.url, s.node_id or "B4"),
    )
    return cur.rowcount or 0


def _p_gospel(conn, s: RawSignal) -> int:
    metric = s.extra.get("metric_name", s.title)
    if _exists(conn, "gospel_reach", "date=? AND metric_name=?",
               (_date(s), metric)):
        return 0
    conn.execute(
        "INSERT INTO gospel_reach "
        "(date, metric_name, value, description, source_url) "
        "VALUES (?,?,?,?,?)",
        (_date(s), metric, s.magnitude or 0.0, s.summary, s.url),
    )
    return 1


def _p_who_outbreaks(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO disease_outbreaks "
        "(event_id, date, disease, country, description, severity, "
        "confidence, source_url) VALUES (?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.extra.get("disease", "Unknown"),
         s.location, s.summary, s.extra.get("severity"), s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_europe_mixture(conn, s: RawSignal) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO europe_mixture_events "
        "(event_id, date, title, description, category, country, "
        "confidence, source_url) VALUES (?,?,?,?,?,?,?,?)",
        (_event_id(s), _date(s), s.title, s.summary, s.extra.get("category"),
         s.location, s.confidence, s.url),
    )
    return cur.rowcount or 0


def _p_europe_demographics(conn, s: RawSignal) -> int:
    metric = s.extra.get("metric_name", s.title)
    if _exists(conn, "europe_demographics", "date=? AND metric_name=?",
               (_date(s), metric)):
        return 0
    conn.execute(
        "INSERT INTO europe_demographics "
        "(date, metric_name, value, description, source_url) "
        "VALUES (?,?,?,?,?)",
        (_date(s), metric, s.magnitude or 0.0, s.summary, s.url),
    )
    return 1


_PERSISTERS = {
    "earthquakes": _p_earthquakes,
    "disasters": _p_disasters,
    "conflicts": _p_conflicts,
    "economic": _p_economic,
    "worldbank": _p_worldbank,
    "spaceweather": _p_spaceweather,
    "eff": _p_digital_rights,
    "temple_mount": _p_temple_mount,
    "fred_news": _p_fred_news,
    "covenant": _p_covenant,
    "cbdc": _p_cbdc,
    "coalition": _p_coalition,
    "eu": _p_eu,
    "ai_enforcement": _p_ai_enforcement,
    "gospel": _p_gospel,
    "who_outbreaks": _p_who_outbreaks,
    "europe_mixture": _p_europe_mixture,
    "europe_demographics": _p_europe_demographics,
}


def _as_int(v):
    try:
        return int(float(v)) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _as_float(v):
    try:
        return float(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _as_text(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v)
    return str(v)


def persist_signals(db_path: Path,
                    signals: Iterable[RawSignal]) -> Dict[str, int]:
    """Write signals to their tables. Returns {source: rows_inserted}."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    inserted: Dict[str, int] = {}
    try:
        ensure_schema(conn)
        for s in signals:
            persister = _PERSISTERS.get(s.source)
            if persister is None:
                continue
            try:
                inserted[s.source] = inserted.get(s.source, 0) + persister(conn, s)
            except sqlite3.Error:
                continue
        conn.commit()
    finally:
        conn.close()
    return inserted

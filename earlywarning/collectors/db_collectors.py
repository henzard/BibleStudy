#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite-backed collectors.

Each collector reads one table that the ``fetch_*.py`` ingestion scripts
populate and emits :class:`RawSignal` objects. Reading the store (rather than
re-running network fetches) makes the analysis pipeline deterministic and
runnable offline.
"""

from __future__ import annotations

from typing import List

from ..models import RawSignal
from .base import Collector, CollectorContext


class EarthquakeCollector(Collector):
    name = "earthquakes"
    node_id = "J0"
    scripture = "Matt 24:7-8"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "earthquakes"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date_utc, magnitude, location, source_url
            FROM earthquakes
            WHERE date_utc >= ?
            ORDER BY magnitude DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for event_id, date_utc, magnitude, location, url in rows:
            conf = "High" if (magnitude or 0) >= 6.0 else (
                "Med" if (magnitude or 0) >= 5.0 else "Low"
            )
            signals.append(
                RawSignal(
                    source=self.name,
                    title=f"M{magnitude} earthquake: {location}",
                    summary=f"Magnitude {magnitude} earthquake near {location}.",
                    occurred_at=date_utc,
                    location=location or "",
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=conf,
                    magnitude=float(magnitude) if magnitude is not None else None,
                    extra={"event_id": event_id},
                )
            )
        return signals


class DisasterCollector(Collector):
    name = "disasters"
    node_id = "J0"
    scripture = "Matt 24:7-8"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "disasters"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date_utc, disaster_type, location, alert_level,
                   severity_description, population_affected, source_url
            FROM disasters
            WHERE date_utc >= ?
            ORDER BY date_utc DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        level_conf = {"Red": "High", "Orange": "Med", "Green": "Low"}
        signals = []
        for (event_id, date_utc, dtype, location, alert, sev, pop,
             url) in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=f"{dtype} ({alert}) — {location}",
                    summary=sev or f"{dtype} affecting {location}.",
                    occurred_at=date_utc,
                    location=location or "",
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=level_conf.get(alert or "", "Low"),
                    extra={"event_id": event_id, "type": dtype,
                           "alert_level": alert, "population_affected": pop},
                )
            )
        return signals


class ConflictCollector(Collector):
    name = "conflicts"
    node_id = "J0"
    scripture = "Matt 24:6-7"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "conflicts"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT date, location, conflict_type, casualties, description,
                   source_url, confidence
            FROM conflicts
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for date, location, ctype, casualties, desc, url, conf in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=f"{ctype}: {location}",
                    summary=desc or f"{ctype} reported in {location}.",
                    occurred_at=date,
                    location=location or "",
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    magnitude=float(casualties) if casualties else None,
                    extra={"conflict_type": ctype, "casualties": casualties},
                )
            )
        return signals


class EconomicCollector(Collector):
    name = "economic"
    node_id = "H0"
    scripture = "Rev 17-18"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "economic_indicators"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT date, indicator_name, indicator_category, value, yoy_change,
                   status, confidence
            FROM economic_indicators
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for date, name, category, value, yoy, status, conf in rows:
            yoy_txt = f" ({yoy:+.1f}% YoY)" if yoy is not None else ""
            signals.append(
                RawSignal(
                    source=self.name,
                    title=f"{name}: {status}",
                    summary=f"{name} = {value}{yoy_txt} — status {status}.",
                    occurred_at=date,
                    url="",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    magnitude=float(value) if value is not None else None,
                    extra={"category": category, "status": status,
                           "yoy_change": yoy},
                )
            )
        return signals


class WorldBankCollector(Collector):
    name = "worldbank"
    node_id = "J0"
    scripture = "Matt 24:7-8 / Rev 17-18"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "worldbank_news"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT date, headline, description, category, keywords, confidence,
                   source_url, node_id
            FROM worldbank_news
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for date, headline, desc, category, keywords, conf, url, node in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=headline or "World Bank report",
                    summary=desc or "",
                    occurred_at=date,
                    url=url or "",
                    node_id=node or self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    extra={"category": category, "keywords": keywords},
                )
            )
        return signals


class SpaceWeatherCollector(Collector):
    name = "spaceweather"
    node_id = "J6"
    scripture = "Matt 24:29; Luke 21:25"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "space_weather"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date, severity, description, confidence, source_url
            FROM space_weather
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for event_id, date, severity, desc, conf, url in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=f"Space weather: {severity}",
                    summary=desc or "",
                    occurred_at=date,
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    extra={"event_id": event_id, "severity": severity},
                )
            )
        return signals


class DigitalRightsCollector(Collector):
    name = "eff"
    node_id = "B2"
    scripture = "Rev 13:16-17"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "digital_rights"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date, title, description, category, keywords,
                   confidence, source_url
            FROM digital_rights
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for event_id, date, title, desc, category, keywords, conf, url in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=title or "Digital rights update",
                    summary=desc or "",
                    occurred_at=date,
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    extra={"event_id": event_id, "category": category,
                           "keywords": keywords},
                )
            )
        return signals


class TempleMountCollector(Collector):
    name = "temple_mount"
    node_id = "J3"
    scripture = "Dan 9:27; Matt 24:15; 2 Thess 2:3-4"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "temple_mount_news"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date, title, description, source, category,
                   keywords, confidence, scripture, source_url, node_id
            FROM temple_mount_news
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for (event_id, date, title, desc, source, category, keywords, conf,
             scripture, url, node) in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=title or "Middle East update",
                    summary=desc or "",
                    occurred_at=date,
                    url=url or "",
                    node_id=node or self.node_id,
                    scripture=scripture or self.scripture,
                    confidence=(conf or "Low").title(),
                    extra={"event_id": event_id, "source": source,
                           "category": category, "keywords": keywords},
                )
            )
        return signals


class FredNewsCollector(Collector):
    name = "fred_news"
    node_id = "H0"
    scripture = "Rev 17-18"

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        if not self.table_exists(ctx.conn, "fred_news"):
            return []
        rows = ctx.conn.execute(
            """
            SELECT event_id, date, title, description, category, confidence,
                   source_url
            FROM fred_news
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (ctx.cutoff_date,),
        ).fetchall()
        signals = []
        for event_id, date, title, desc, category, conf, url in rows:
            signals.append(
                RawSignal(
                    source=self.name,
                    title=title or "FRED announcement",
                    summary=desc or "",
                    occurred_at=date,
                    url=url or "",
                    node_id=self.node_id,
                    scripture=self.scripture,
                    confidence=(conf or "Low").title(),
                    extra={"event_id": event_id, "category": category},
                )
            )
        return signals


ALL_DB_COLLECTORS = [
    EarthquakeCollector,
    DisasterCollector,
    ConflictCollector,
    EconomicCollector,
    WorldBankCollector,
    SpaceWeatherCollector,
    DigitalRightsCollector,
    TempleMountCollector,
    FredNewsCollector,
]

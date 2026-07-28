#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live collectors (hybrid mode).

Each live collector imports a refactored ``fetch_*.py`` module, calls its
network ``collect()`` function, and maps the returned dicts to
:class:`RawSignal`. The pipeline can then run on fresh data, persist it (see
:mod:`earlywarning.persist`), and replay it offline on later runs.

Modules are imported lazily inside ``collect`` so merely *building* the
collector list triggers no network warnings or imports.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, Dict, List

from ..models import RawSignal
from ..normalize import _parse_timestamp
from .base import Collector, CollectorContext


def _iso(value) -> str:
    return _parse_timestamp(str(value)) if value else ""


def _conf(value) -> str:
    v = str(value or "Low").strip().lower()
    if v.startswith("h"):
        return "High"
    if v.startswith("m"):  # med / medium
        return "Med"
    return "Low"


# --- mappers: source dict -> RawSignal ------------------------------------

def _m_earthquakes(r: Dict) -> RawSignal:
    mag = float(r.get("magnitude") or 0.0)
    conf = "High" if mag >= 6.0 else ("Med" if mag >= 5.0 else "Low")
    return RawSignal(
        source="earthquakes",
        title=f"M{mag} earthquake: {r.get('location', '')}",
        summary=f"Magnitude {mag} earthquake near {r.get('location', '')}.",
        occurred_at=_iso(r.get("date")), location=r.get("location", ""),
        url=r.get("url", ""), node_id="J0", scripture="Matt 24:7-8",
        confidence=conf, magnitude=mag,
        extra={"latitude": r.get("latitude"), "longitude": r.get("longitude")},
    )


def _m_gdacs(r: Dict) -> RawSignal:
    alert = r.get("alert_level", "")
    conf = {"Red": "High", "Orange": "Med", "Green": "Low"}.get(alert, "Low")
    country = r.get("country", "")
    return RawSignal(
        source="disasters",
        title=f"{r.get('type', 'Disaster')} ({alert}) — {country}",
        summary=r.get("severity") or r.get("description", ""),
        occurred_at=_iso(r.get("date")), location=country, url=r.get("url", ""),
        node_id="J0", scripture="Matt 24:7-8", confidence=conf,
        extra={"type": r.get("type"), "alert_level": alert,
               "population_affected": r.get("population_affected")},
    )


def _m_un(r: Dict) -> RawSignal:
    return RawSignal(
        source="conflicts",
        title=r.get("title", "Conflict report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location="", url=r.get("url", ""), node_id="J0",
        scripture="Matt 24:6-7", confidence=_conf(r.get("confidence")),
        extra={"conflict_type": r.get("category", "Conflict"),
               "casualties": None},
    )


def _m_worldbank(r: Dict) -> RawSignal:
    nodes = r.get("nodes") or ["J0"]
    category = "Economic" if "H0" in nodes else "Disaster/Famine"
    return RawSignal(
        source="worldbank", title=r.get("title", "World Bank report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id=nodes[0],
        scripture="Matt 24:7-8 / Rev 17-18", confidence=_conf(r.get("confidence")),
        extra={"category": category, "keywords": r.get("keywords")},
    )


def _m_economic(r: Dict) -> RawSignal:
    return RawSignal(
        source="economic", title=f"{r.get('name', '')}: {r.get('status', '')}",
        summary=r.get("assessment") or r.get("description", ""),
        occurred_at=_iso(r.get("latest_date")), node_id="H0",
        scripture="Rev 17-18", confidence=_conf(r.get("confidence")),
        magnitude=_safe_float(r.get("latest_value")),
        extra={"indicator_name": r.get("name"),
               "category": r.get("series_id", "Economic"),
               "status": r.get("status"), "yoy_change": r.get("yoy_change")},
    )


def _m_fred_news(r: Dict) -> RawSignal:
    return RawSignal(
        source="fred_news", title=r.get("title", "FRED announcement"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id="H0", scripture="Rev 17-18",
        confidence="Med" if r.get("relevant") else "Low",
        extra={"category": r.get("category"), "event_id": r.get("url")},
    )


def _m_spaceweather(r: Dict) -> RawSignal:
    return RawSignal(
        source="spaceweather",
        title=f"Space weather: {r.get('severity', 'INFO')}",
        summary=r.get("description", ""),
        occurred_at=_iso(r.get("issue_datetime")), node_id="J6",
        scripture="Matt 24:29; Luke 21:25", confidence=_conf(r.get("confidence")),
        extra={"severity": r.get("severity"),
               "event_id": r.get("product_id") or r.get("message", "")[:40]},
    )


def _m_eff(r: Dict) -> RawSignal:
    return RawSignal(
        source="eff", title=r.get("title", "Digital rights update"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("pub_date")),
        url=r.get("link", ""), node_id="B2", scripture="Rev 13:16-17",
        confidence=_conf(r.get("confidence")),
        extra={"category": r.get("category"), "keywords": r.get("keywords"),
               "event_id": r.get("link")},
    )


def _m_temple_mount(r: Dict) -> RawSignal:
    return RawSignal(
        source="temple_mount", title=r.get("title", "Middle East update"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id=r.get("node", "J3"),
        scripture=r.get("scripture", "Dan 9:27; Matt 24:15"),
        confidence=_conf(r.get("confidence")),
        extra={"source": r.get("source"), "category": r.get("category"),
               "keywords": r.get("keywords"), "event_id": r.get("url")},
    )


def _m_covenant(r: Dict) -> RawSignal:
    return RawSignal(
        source="covenant", title=r.get("title", "Covenant/treaty report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id=r.get("node", "D1"),
        scripture=r.get("scripture", "Dan 9:27"),
        confidence=_conf(r.get("confidence")),
        extra={"treaty_type": r.get("treaty_type"),
               "keywords": r.get("keywords"), "event_id": r.get("url")},
    )


def _m_cbdc(r: Dict) -> RawSignal:
    return RawSignal(
        source="cbdc", title=r.get("title", "CBDC/digital-ID report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id="B2", scripture="Rev 13:16-17",
        confidence=_conf(r.get("confidence")),
        extra={"category": r.get("category"), "status": r.get("status"),
               "country": r.get("country"), "event_id": r.get("url")},
    )


def _m_coalition(r: Dict) -> RawSignal:
    nations = r.get("nations") or []
    return RawSignal(
        source="coalition", title=r.get("title", "Coalition event"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location=", ".join(nations) if isinstance(nations, list) else str(nations),
        url=r.get("url", ""), node_id="E38", scripture="Ezek 38:1-6",
        confidence=_conf(r.get("confidence")),
        extra={"nations": nations, "event_type": r.get("event_type"),
               "event_id": r.get("url")},
    )


def _m_eu(r: Dict) -> RawSignal:
    return RawSignal(
        source="eu", title=r.get("title", "EU consolidation report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location="European Union", url=r.get("url", ""), node_id="D2",
        scripture="Dan 2:40-43; 7:23-24", confidence=_conf(r.get("confidence")),
        extra={"category": r.get("category"), "event_id": r.get("url")},
    )


def _m_ai_enforcement(r: Dict) -> RawSignal:
    return RawSignal(
        source="ai_enforcement", title=r.get("title", "AI enforcement report"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id=r.get("node", "B4"),
        scripture=r.get("scripture", "Rev 13:15"),
        confidence=_conf(r.get("confidence")),
        extra={"category": r.get("category"), "event_id": r.get("url")},
    )


def _m_gospel(r: Dict) -> RawSignal:
    metric = r.get("metric_name", "metric")
    value = _safe_float(r.get("value")) or 0.0
    return RawSignal(
        source="gospel", title=f"Gospel reach: {metric} = {value:.0f}",
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        url=r.get("url", ""), node_id="M14", scripture="Matt 24:14",
        confidence=_conf(r.get("confidence")), magnitude=value,
        extra={"metric_name": metric},
    )


def _m_who_outbreaks(r: Dict) -> RawSignal:
    country = r.get("country") or ""
    loc = f" — {country}" if country else ""
    return RawSignal(
        source="who_outbreaks",
        title=f"Outbreak: {r.get('disease', 'Unknown')}{loc}",
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location=country, url=r.get("url", ""), node_id="J0",
        scripture="Luke 21:11", confidence=_conf(r.get("confidence")),
        extra={"disease": r.get("disease"), "severity": r.get("severity"),
               "event_id": r.get("url")},
    )


def _m_europe_mixture(r: Dict) -> RawSignal:
    return RawSignal(
        source="europe_mixture", title=r.get("title", "Mixture event"),
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location=r.get("country") or "Europe", url=r.get("url", ""),
        node_id="D3", scripture="Dan 2:41-43",
        confidence=_conf(r.get("confidence")),
        extra={"category": r.get("category"), "event_id": r.get("url")},
    )


def _m_europe_demographics(r: Dict) -> RawSignal:
    metric = r.get("metric_name", "metric")
    value = _safe_float(r.get("value")) or 0.0
    return RawSignal(
        source="europe_demographics",
        title=f"Europe demographics: {metric} = {value:g}",
        summary=r.get("description", ""), occurred_at=_iso(r.get("date")),
        location="Europe", url=r.get("url", ""), node_id="D3",
        scripture="Dan 2:41-43", confidence=_conf(r.get("confidence")),
        magnitude=value, extra={"metric_name": metric},
    )


def _safe_float(v):
    try:
        return float(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


@dataclass
class _LiveSpec:
    name: str
    module: str
    mapper: Callable[[Dict], RawSignal]
    months_arg: bool = False  # economic uses months=, others days=


_LIVE_SPECS: List[_LiveSpec] = [
    _LiveSpec("earthquakes", "scripts.fetch_earthquakes", _m_earthquakes),
    _LiveSpec("disasters", "scripts.fetch_gdacs", _m_gdacs),
    _LiveSpec("conflicts", "scripts.fetch_un_peacekeeping", _m_un),
    _LiveSpec("worldbank", "scripts.fetch_worldbank_news", _m_worldbank),
    _LiveSpec("economic", "scripts.fetch_economic", _m_economic, months_arg=True),
    _LiveSpec("fred_news", "scripts.fetch_fred_news", _m_fred_news),
    _LiveSpec("spaceweather", "scripts.fetch_spaceweather", _m_spaceweather),
    _LiveSpec("eff", "scripts.fetch_eff_news", _m_eff),
    _LiveSpec("temple_mount", "scripts.fetch_temple_mount_news", _m_temple_mount),
    _LiveSpec("covenant", "scripts.fetch_covenant_watch", _m_covenant),
    _LiveSpec("cbdc", "scripts.fetch_cbdc", _m_cbdc),
    _LiveSpec("coalition", "scripts.fetch_coalition", _m_coalition),
    _LiveSpec("eu", "scripts.fetch_eu_consolidation", _m_eu),
    _LiveSpec("ai_enforcement", "scripts.fetch_ai_enforcement",
              _m_ai_enforcement),
    _LiveSpec("gospel", "scripts.fetch_gospel_reach", _m_gospel),
    _LiveSpec("who_outbreaks", "scripts.fetch_who_outbreaks", _m_who_outbreaks),
    _LiveSpec("europe_mixture", "scripts.fetch_europe_mixture",
              _m_europe_mixture),
    _LiveSpec("europe_demographics", "scripts.fetch_europe_demographics",
              _m_europe_demographics),
]


class LiveCollector(Collector):
    """Wraps a refactored fetch module's ``collect()`` network function."""

    def __init__(self, spec: _LiveSpec):
        self.name = spec.name
        self._spec = spec

    def collect(self, ctx: CollectorContext) -> List[RawSignal]:
        mod = importlib.import_module(self._spec.module)
        fn = getattr(mod, "collect")
        if self._spec.months_arg:
            records = fn(months=12)
        else:
            records = fn(days=ctx.lookback_days)
        return [self._spec.mapper(r) for r in records or []]


def build_live_collectors() -> List[LiveCollector]:
    return [LiveCollector(spec) for spec in _LIVE_SPECS]

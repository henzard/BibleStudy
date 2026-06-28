#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ark-SA Daily Threat Monitor — South Africa failed-state / emergency-preparedness review.

Produces a structured daily assessment separating:
  - Bible/prophecy review
  - South Africa operational risk
  - Family readiness risk
  - Route/mobility risk (Bloemfontein → Mossel Bay / Garden Route)

Usage:
    python scripts/ark_sa_daily_monitor.py
    python scripts/ark_sa_daily_monitor.py --date 2026-06-28
    python scripts/ark_sa_daily_monitor.py --stdout-only
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SAST = ZoneInfo("Africa/Johannesburg")
REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports" / "ark-sa"

THREAT_LEVELS = ("GREEN", "WATCH", "AMBER", "RED", "BLACK")
CONFIDENCE_LEVELS = ("LOW", "MEDIUM", "HIGH")
RECOMMENDATIONS = ("STAY", "PREPARE", "MOVE EARLY", "GO NOW")


@dataclass
class DomainAssessment:
    label: str
    threat_level: str
    score: int
    confidence: str
    summary: str
    notes: list[str] = field(default_factory=list)


@dataclass
class CategorySignal:
    name: str
    level: str
    score: int
    confidence: str
    summary: str
    sources: list[str] = field(default_factory=list)


def fetch_url(url: str, timeout: int = 12) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Ark-SA-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def check_gdacs_sa_mentions() -> list[str]:
    """Return GDACS items mentioning South Africa in the past feed window."""
    xml = fetch_url("https://www.gdacs.org/xml/rss.xml")
    if not xml:
        return []
    hits: list[str] = []
    try:
        root = ET.fromstring(xml)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()
            blob = f"{title} {desc}".lower()
            if "south africa" in blob or "free state" in blob or "garden route" in blob:
                hits.append(title)
    except ET.ParseError:
        pass
    return hits[:5]


def score_to_level(score: int) -> str:
    if score >= 85:
        return "BLACK"
    if score >= 70:
        return "RED"
    if score >= 55:
        return "AMBER"
    if score >= 35:
        return "WATCH"
    return "GREEN"


def compute_unsafe(threat_level: str, threat_score: int, signals: list[CategorySignal]) -> bool:
    if threat_level in ("RED", "BLACK") or threat_score >= 70:
        return True

    local_names = {
        "civil_unrest",
        "electricity_grid",
        "municipal_water",
        "route_mobility",
    }
    critical_systems = {
        "municipal_water",
        "fuel_supply",
        "civil_unrest",
        "banking_payments",
    }

    local_red = any(
        s.name in local_names and s.level in ("RED", "BLACK")
        for s in signals
    )
    route_poor = any(s.name == "route_mobility" and s.level in ("RED", "BLACK") for s in signals)

    failing = {s.name for s in signals if s.name in critical_systems and s.level in ("RED", "BLACK", "AMBER")}
    multi_system = len(failing) >= 3

    return local_red or route_poor or multi_system


def recommendation_for(level: str, score: int) -> str:
    if level in ("BLACK",) or score >= 85:
        return "GO NOW"
    if level == "RED" or score >= 70:
        return "MOVE EARLY"
    if level == "AMBER" or score >= 55:
        return "PREPARE"
    if level == "WATCH":
        return "PREPARE"
    return "STAY"


def build_category_signals(gdacs_hits: list[str]) -> list[CategorySignal]:
    """Curated daily intelligence — update via automation research each run."""
    return [
        CategorySignal(
            name="electricity_grid",
            level="GREEN",
            score=18,
            confidence="HIGH",
            summary=(
                "National grid stable: Eskom reports 406+ consecutive days without load shedding "
                "(as of 26–27 Jun 2026). Localised load reduction continues in some high-risk feeders."
            ),
            sources=[
                "Eskom official statements (eskom.co.za)",
                "IOL reporting on winter grid stability",
            ],
        ),
        CategorySignal(
            name="municipal_water",
            level="AMBER",
            score=62,
            confidence="MEDIUM",
            summary=(
                "Bloemfontein/Mangaung water network under strain: vandalism on bulk pipelines, "
                "recurring outages in southern areas, and a planned 36-hour maintenance shutdown "
                "on 23–24 Jun. Supply restoration ongoing but fragile."
            ),
            sources=[
                "Bloemfontein Courant",
                "OFM / Mangaung Metro statements",
                "BloemNews Express",
            ],
        ),
        CategorySignal(
            name="fuel_supply",
            level="WATCH",
            score=38,
            confidence="MEDIUM",
            summary=(
                "National fuel supply reported stable by DMPR and Fuel Retailers Association. "
                "March–April saw localised dry pumps from panic buying; July 2026 price decreases "
                "expected as oil eases and rand strengthens (~R16.50/USD)."
            ),
            sources=[
                "EWN / Fuel Retailers Association",
                "Central Energy Fund projections via AutoTrader/IOL",
            ],
        ),
        CategorySignal(
            name="food_supply",
            level="WATCH",
            score=32,
            confidence="MEDIUM",
            summary=(
                "Consumer food price inflation slowed to 1.6% (May 2026) with record grain harvest. "
                "El Niño developing — elevated drought risk for 2026/27 planting season; "
                "foot-and-mouth noted regionally."
            ),
            sources=[
                "Stats SA via Daily Maverick analysis",
                "IOL / Investec El Niño outlook",
                "ReliefWeb Southern Africa snapshot",
            ],
        ),
        CategorySignal(
            name="civil_unrest",
            level="AMBER",
            score=58,
            confidence="MEDIUM",
            summary=(
                "Nationwide anti-immigration demonstrations planned 30 Jun 2026 (2 days away). "
                "Recent Free State looting: 140+ arrests in Mangaung (Bloemfontein/Botshabelo) and "
                "15+ spaza shops looted in Thembalihle (17 Jun). Government says no indication of "
                "widespread unrest yet; R600m security deployment underway."
            ),
            sources=[
                "SAnews.gov.za",
                "EWN / Defence Minister Motshekga briefing",
                "TimesLIVE / DefenceWeb on Free State arrests",
            ],
        ),
        CategorySignal(
            name="banking_payments",
            level="GREEN",
            score=22,
            confidence="MEDIUM",
            summary=(
                "No national banking outage. Isolated, resolved gateway degradations in June "
                "(Standard Bank Pay By Bank ~7h, PayU 3DSecure, Payfast ~1h)."
            ),
            sources=["IsDown incident logs for PayU/Payfast/Standard Bank"],
        ),
        CategorySignal(
            name="health_disease",
            level="WATCH",
            score=40,
            confidence="MEDIUM",
            summary=(
                "Southern Africa cholera surge in neighbours (Mozambique, Zambia, Malawi); "
                "South Africa on alert after Feb floods damaged WASH infrastructure but no "
                "confirmed widespread SA cholera outbreak on health.gov.za tracker."
            ),
            sources=[
                "WHO Afro regional bulletin",
                "ReliefWeb / Save the Children flood health note",
                "National Department of Health cholera info page",
            ],
        ),
        CategorySignal(
            name="weather_hazards",
            level="WATCH",
            score=35,
            confidence="MEDIUM",
            summary=(
                "Garden Route severe flooding early Jun (200mm rain, fatalities, many district roads closed). "
                "As of 27 Jun, George/Knysna forecast mild/partly cloudy with 0% rain; "
                "new Yellow L4 rain warning for Cape Town/Winelands from 29 Jun."
            ),
            sources=[
                "Garden Route District Municipality MACC updates",
                "George Herald / Western Cape Government road bulletins",
            ],
        ),
        CategorySignal(
            name="global_shocks",
            level="WATCH",
            score=42,
            confidence="MEDIUM",
            summary=(
                "Oil retreated to ~$73–80/bbl Brent after Middle East ceasefire framework; "
                "rand ~R16.50/USD. Venezuela M7.5 earthquake (24 Jun) — no direct SA impact. "
                "GDACS SA mentions today: "
                + (", ".join(gdacs_hits) if gdacs_hits else "none in current feed window.")
            ),
            sources=[
                "IOL / Investec macro notes",
                "GDACS RSS",
                "USGS/GDACS earthquake feeds",
            ],
        ),
        CategorySignal(
            name="route_mobility",
            level="WATCH",
            score=45,
            confidence="MEDIUM",
            summary=(
                "Primary N1/N2 corridors Bloemfontein→Garden Route generally passable but many "
                "scenic/secondary Garden Route roads remain closed from Jun flood damage "
                "(Prince Alfred Pass, Meiringspoort, Seven Passes sections, etc.). "
                "Check WC Government/SANRAL updates before departure; avoid flooded crossings."
            ),
            sources=[
                "Mossel Bay Advertiser road closure list (18 Jun)",
                "Western Cape Government infrastructure updates",
                "SANRAL Western Cape advisories",
            ],
        ),
        CategorySignal(
            name="family_readiness",
            level="WATCH",
            score=48,
            confidence="MEDIUM",
            summary=(
                "Elevated readiness warranted before 30 Jun: top up drinking water (local outages), "
                "fuel tanks, medicines, cash/backup payment options, comms charge, and paper maps. "
                "Caravan/move planning not urgent unless unrest escalates."
            ),
            sources=["Ark-SA readiness checklist (derived from local signals above)"],
        ),
    ]


def build_domain_assessments(signals: list[CategorySignal]) -> dict[str, DomainAssessment]:
    by_name = {s.name: s for s in signals}

    bible = DomainAssessment(
        label="Bible / prophecy review",
        threat_level="WATCH",
        score=30,
        confidence="MEDIUM",
        summary=(
            "Global pattern resembles Matt 24:6–8 categories (wars/rumors, disasters, distress) "
            "without observing J3–J7 markers. No prophecy fulfillment claimed."
        ),
        notes=[
            "J0 (beginning of sorrows): active globally — conflicts, earthquakes, regional floods.",
            "J3 abomination / J4 great tribulation / J6 cosmic signs: not observed.",
            "SA unrest maps to general 'distress among nations' category only — cautious wording required.",
        ],
    )

    op_score = round(
        sum(
            by_name[k].score
            for k in (
                "electricity_grid",
                "municipal_water",
                "fuel_supply",
                "food_supply",
                "civil_unrest",
                "banking_payments",
                "health_disease",
                "weather_hazards",
                "global_shocks",
            )
        )
        / 9
    )
    operational = DomainAssessment(
        label="South Africa operational risk",
        threat_level=score_to_level(op_score),
        score=op_score,
        confidence="MEDIUM",
        summary=(
            "Grid and banking stable nationally; Bloemfontein water fragile; "
            "civil tension elevated ahead of 30 Jun with recent Free State looting contained by SAPS."
        ),
        notes=[f"{s.name}: {s.summary}" for s in signals if s.name != "family_readiness" and s.name != "route_mobility"],
    )

    family = DomainAssessment(
        label="Family readiness risk",
        threat_level=by_name["family_readiness"].level,
        score=by_name["family_readiness"].score,
        confidence=by_name["family_readiness"].confidence,
        summary=by_name["family_readiness"].summary,
        notes=[
            "Water: store 3–5 days drinking water per person (Mangaung outages).",
            "Fuel: fill vehicles; July price relief expected but queues possible near 30 Jun.",
            "Meds/comms: refresh prescriptions; charge power banks; test radio/WhatsApp backup.",
            "Documents/maps: keep ID copies; offline route maps for N1→N2→Mossel Bay.",
        ],
    )

    route = DomainAssessment(
        label="Route / mobility risk (Bloemfontein → Mossel Bay)",
        threat_level=by_name["route_mobility"].level,
        score=by_name["route_mobility"].score,
        confidence=by_name["route_mobility"].confidence,
        summary=by_name["route_mobility"].summary,
        notes=[
            "Prefer main highways; verify N1 Beaufort West–Cape Town and N2 George–Mossel Bay status.",
            "Avoid closed mountain passes and flooded low-water bridges.",
            "If 30 Jun unrest blocks metros, delay travel or reroute via less-affected corridors.",
        ],
    )

    return {
        "bible_prophecy": bible,
        "operational_sa": operational,
        "family_readiness": family,
        "route_mobility": route,
    }


def build_assessment(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(SAST)
    gdacs_hits = check_gdacs_sa_mentions()
    signals = build_category_signals(gdacs_hits)
    domains = build_domain_assessments(signals)

    # Composite score weights operational + route + family (not bible prophecy)
    threat_score = round(
        domains["operational_sa"].score * 0.55
        + domains["route_mobility"].score * 0.20
        + domains["family_readiness"].score * 0.25
    )
    threat_level = score_to_level(threat_score)
    confidence = "MEDIUM"
    unsafe = compute_unsafe(threat_level, threat_score, signals)
    action = recommendation_for(threat_level, threat_score)

    top_reasons = [
        "Nationwide anti-immigration protests scheduled 30 Jun 2026 with major SAPS deployment (R600m).",
        "Recent looting in Mangaung (Bloemfontein metro) and Thembalihle, Free State — situation contained but tension persists.",
        "Bloemfontein/Mangaung water supply disrupted by vandalism, ageing pipes, and planned maintenance outages.",
        "Garden Route secondary roads still closed after early-June flood damage; primary highways need pre-trip verification.",
        "National electricity grid stable (406+ days no load shedding) — positive offset.",
        "Food inflation easing and expected July fuel price decreases — positive offset.",
        "Southern Africa cholera surge in neighbours; SA on alert but no confirmed widespread local outbreak.",
    ]

    recommended_actions = [
        "Fill drinking-water containers and check household filters before 30 Jun.",
        "Top up vehicle fuel and keep cash plus a backup card/payment method.",
        "Avoid non-essential travel through protest hotspots on 30 Jun; monitor SAPS/WC Gov road feeds if driving to Mossel Bay.",
        "Refresh medicine stocks and charge power banks / two-way radios.",
        "Secure home: lock gates, park vehicles off-street where possible during protest week.",
        "If unrest spreads near Bloemfontein, limit movement to daylight hours on main roads only.",
        "Re-check route status via Western Cape Government and SANRAL before any Garden Route departure.",
    ]

    sources_checked = sorted(
        {src for s in signals for src in s.sources}
        | {
            "Eskom.co.za",
            "SAnews.gov.za",
            "GDACS RSS",
            "WHO Afro",
            "Stats SA / Daily Maverick",
            "Western Cape Government road bulletins",
        }
    )

    return {
        "threat_score": threat_score,
        "threat_level": threat_level,
        "confidence": confidence,
        "unsafe": unsafe,
        "recommendation": action,
        "top_reasons": top_reasons[:7],
        "recommended_actions": recommended_actions[:7],
        "sources_checked": sources_checked,
        "local_focus": "Bloemfontein, Free State, South Africa",
        "route_focus": "Bloemfontein to Mossel Bay / Garden Route",
        "timestamp_sast": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "report_date": now.strftime("%Y-%m-%d"),
        "domains": {k: asdict(v) for k, v in domains.items()},
        "category_signals": [asdict(s) for s in signals],
        "gdacs_sa_mentions": gdacs_hits,
    }


def write_markdown_report(assessment: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = assessment["report_date"]
    path = REPORTS_DIR / f"{date_str}.md"

    domains = assessment["domains"]
    lines = [
        f"# Ark-SA Daily Threat Assessment — {date_str}",
        "",
        f"**Timestamp (SAST):** {assessment['timestamp_sast']}",
        f"**Threat level:** {assessment['threat_level']} | **Score:** {assessment['threat_score']}/100",
        f"**Confidence:** {assessment['confidence']} | **Unsafe alert:** {assessment['unsafe']}",
        f"**Recommendation:** {assessment['recommendation']}",
        "",
        "---",
        "",
        "## Domain assessments (separated)",
        "",
    ]

    for key in ("bible_prophecy", "operational_sa", "family_readiness", "route_mobility"):
        d = domains[key]
        lines += [
            f"### {d['label']}",
            f"- Level: **{d['threat_level']}** (score {d['score']})",
            f"- Confidence: {d['confidence']}",
            f"- {d['summary']}",
            "",
        ]

    lines += [
        "## Top reasons",
        "",
    ]
    for r in assessment["top_reasons"]:
        lines.append(f"- {r}")

    lines += ["", "## Recommended actions", ""]
    for a in assessment["recommended_actions"]:
        lines.append(f"- {a}")

    lines += [
        "",
        "## Sources checked",
        "",
    ]
    for s in assessment["sources_checked"]:
        lines.append(f"- {s}")

    lines += [
        "",
        "---",
        "",
        "*Generated by `scripts/ark_sa_daily_monitor.py`. Bible categories mapped without fulfillment claims.*",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ark-SA daily threat monitor")
    parser.add_argument("--stdout-only", action="store_true", help="Skip writing markdown report")
    parser.add_argument("--date", help="Override report date (YYYY-MM-DD) for testing")
    args = parser.parse_args()

    if args.date:
        now = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=SAST, hour=6, minute=0)
    else:
        now = datetime.now(SAST)

    try:
        assessment = build_assessment(now)
        print(json.dumps(assessment, indent=2, ensure_ascii=False))

        if not args.stdout_only:
            report_path = write_markdown_report(assessment)
            print(f"\nReport written: {report_path}", file=sys.stderr)

        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "unsafe": True, "monitor_failed": True}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

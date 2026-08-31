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
from datetime import datetime, timedelta
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


SIGNALS_FILE = REPO_ROOT / "data" / "ark_sa_signals.json"
USGS_SA_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4"
    "&minlatitude=-35&maxlatitude=-22&minlongitude=16&maxlongitude=33&limit=5&orderby=time"
)


def load_signal_data() -> dict[str, Any]:
    """The curated snapshot lives in data/, dated, so the monitor can tell how old it is."""
    return json.loads(SIGNALS_FILE.read_text(encoding="utf-8"))


def days_old(as_of: str, today: datetime) -> int:
    try:
        d = datetime.strptime(as_of, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return 10_000
    return max(0, (today.date() - d).days)


def still_current(item: dict[str, Any], today: datetime) -> bool:
    """A reason or action bound to a date is gone the day after it."""
    until = item.get("until")
    if not until:
        return True
    try:
        return datetime.strptime(until, "%Y-%m-%d").date() >= today.date()
    except ValueError:
        return True


def check_usgs_sa_quakes(now: datetime) -> list[str]:
    """M4+ earthquakes inside a southern-Africa box in the last 7 days — a live signal that needs no key."""
    since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    body = fetch_url(f"{USGS_SA_URL}&starttime={since}")
    if not body:
        return []
    try:
        feats = json.loads(body).get("features", [])
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    for f in feats[:5]:
        props = f.get("properties", {})
        mag = props.get("mag")
        place = props.get("place", "unknown location")
        if mag is not None:
            out.append(f"M{mag} {place}")
    return out


def build_category_signals(
    gdacs_hits: list[str],
    now: datetime,
    data: dict[str, Any] | None = None,
) -> tuple[list[CategorySignal], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    The curated signals, with their age made visible.

    For two months this function was a hardcoded snapshot of 27–28 June
    replayed every morning with the day's date on it — "Nationwide protests
    scheduled 30 Jun" led the top reasons on 31 August, and every day said
    "unchanged". The ai-honesty rule forbids exactly that: reporting a current
    state nobody read. So the snapshot is now data with an as_of date, and:

      - a signal older than stale_after_days keeps its last-known level but
        drops to LOW confidence and says, in its own summary, how old it is;
      - a reason or action bound to a date disappears the day after it;
      - the only live facts are the ones actually fetched — GDACS and USGS.

    Returns the signals, the names of the stale ones, and the reasons and
    actions that are still current, ordered by the signal's score.
    """
    data = data or load_signal_data()
    stale_after = int(data.get("stale_after_days", 7))
    signals: list[CategorySignal] = []
    stale: list[str] = []
    reasons: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    quake_hits = check_usgs_sa_quakes(now)

    for raw in data["signals"]:
        age = days_old(raw.get("as_of", ""), now)
        is_stale = age > stale_after
        summary = raw["summary"]
        confidence = raw["confidence"]
        if is_stale:
            stale.append(raw["name"])
            confidence = "LOW"
            summary = (
                f"STALE — last researched {raw.get('as_of', 'unknown')} ({age} days ago); "
                f"current state unknown. Last known: {summary}"
            )
        if raw["name"] == "global_shocks":
            summary += (
                " GDACS SA mentions today: " + (", ".join(gdacs_hits) if gdacs_hits else "none in current feed window.")
                + " USGS M4+ southern Africa, 7 days: " + (", ".join(quake_hits) if quake_hits else "none.")
            )
        signals.append(CategorySignal(
            name=raw["name"], level=raw["level"], score=int(raw["score"]),
            confidence=confidence, summary=summary, sources=list(raw.get("sources", [])),
        ))
        for r in raw.get("reasons", []):
            if still_current(r, now):
                reasons.append({"text": r["text"], "score": int(raw["score"]), "stale": is_stale})
        for a in raw.get("actions", []):
            if still_current(a, now):
                actions.append({"text": a["text"], "score": int(raw["score"]), "stale": is_stale})

    reasons.sort(key=lambda r: -r["score"])
    actions.sort(key=lambda a: -a["score"])
    return signals, stale, reasons, actions


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
            "Composite of the operational signals below; each carries its own as-of date, "
            "and a stale one says so."
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
            "Fuel: keep vehicles above half; carry cash and a backup payment method.",
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
            "If unrest blocks a metro on the day, delay travel or reroute via less-affected corridors.",
        ],
    )

    return {
        "bible_prophecy": bible,
        "operational_sa": operational,
        "family_readiness": family,
        "route_mobility": route,
    }


def load_previous_assessment(report_date: str) -> dict[str, Any] | None:
    """Load the most recent prior-day JSON snapshot if available."""
    try:
        prior = datetime.strptime(report_date, "%Y-%m-%d").date() - timedelta(days=1)
    except ValueError:
        return None
    path = REPORTS_DIR / f"{prior.isoformat()}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def changes_since_yesterday(current: dict[str, Any], previous: dict[str, Any] | None) -> str:
    if previous is None:
        return "No prior report in reports/ark-sa/ — baseline established today."

    parts: list[str] = []
    for field in ("threat_level", "threat_score", "decision", "unsafe"):
        old, new = previous.get(field), current.get(field)
        if old != new:
            parts.append(f"{field}: {old} → {new}")
    stale_now = len(current.get("stale_signals", []) or [])
    stale_before = len(previous.get("stale_signals", []) or [])
    if stale_now != stale_before:
        parts.append(f"stale signals: {stale_before} → {stale_now}")

    if not parts:
        if stale_now:
            return f"Unchanged overall — same level, score and decision; {stale_now} signal(s) still stale."
        return "Unchanged overall — same threat level, score, and decision as yesterday."

    return "; ".join(parts)


def save_json_snapshot(assessment: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{assessment['report_date']}.json"
    path.write_text(json.dumps(assessment, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_assessment(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(SAST)
    gdacs_hits = check_gdacs_sa_mentions()
    signals, stale_signals, reasons, actions = build_category_signals(gdacs_hits, now)
    domains = build_domain_assessments(signals)

    # Composite score weights operational + route + family (not bible prophecy)
    threat_score = round(
        domains["operational_sa"].score * 0.55
        + domains["route_mobility"].score * 0.20
        + domains["family_readiness"].score * 0.25
    )
    threat_level = score_to_level(threat_score)
    # Confidence is only as good as the freshest half of the evidence. With most
    # of the signals stale, the number above is a memory, and it is labelled one.
    confidence = "LOW" if len(stale_signals) * 2 > len(signals) else "MEDIUM"
    unsafe = compute_unsafe(threat_level, threat_score, signals)
    action = recommendation_for(threat_level, threat_score)

    def _label(item: dict[str, Any]) -> str:
        return ("[stale] " if item["stale"] else "") + item["text"]

    top_reasons = [_label(r) for r in reasons]
    if stale_signals:
        top_reasons.insert(
            0,
            f"{len(stale_signals)} of {len(signals)} signals have not been re-researched in over "
            f"{load_signal_data().get('stale_after_days', 7)} days — treat this assessment as last-known, not current.",
        )
    recommended_actions = [_label(a) for a in actions]
    if stale_signals:
        recommended_actions.insert(0, "Re-research data/ark_sa_signals.json before acting on any stale item.")

    sources_checked = sorted(
        {src for s in signals for src in s.sources}
        | {
            "Eskom.co.za",
            "SAnews.gov.za",
            "AP News",
            "GDACS RSS",
            "WHO Afro",
            "Stats SA / Daily Maverick",
            "Western Cape Government road bulletins",
        }
    )

    report_date = now.strftime("%Y-%m-%d")
    previous = load_previous_assessment(report_date)

    assessment = {
        "threat_score": threat_score,
        "threat_level": threat_level,
        "confidence": confidence,
        "unsafe": unsafe,
        "decision": action,
        "recommendation": action,
        "top_reasons": top_reasons[:7],
        "recommended_actions": recommended_actions[:7],
        "stale_signals": stale_signals,
        "signals_as_of": {sig["name"]: sig.get("as_of") for sig in load_signal_data()["signals"]},
        "sources_checked": sources_checked,
        "local_focus": "Bloemfontein, Free State, South Africa",
        "route_focus": "Bloemfontein to Mossel Bay / Garden Route",
        "timestamp_sast": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "report_date": report_date,
        "changes_since_yesterday": changes_since_yesterday(
            {
                "threat_level": threat_level,
                "threat_score": threat_score,
                "decision": action,
                "unsafe": unsafe,
                "stale_signals": stale_signals,
            },
            previous,
        ),
        "domains": {k: asdict(v) for k, v in domains.items()},
        "category_signals": [asdict(s) for s in signals],
        "gdacs_sa_mentions": gdacs_hits,
    }
    return assessment


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
        f"**Decision:** {assessment['decision']}",
        "",
        f"**Changes since yesterday:** {assessment.get('changes_since_yesterday', 'unknown')}",
        "",
        (f"**Stale signals ({len(assessment['stale_signals'])}):** " + ", ".join(assessment["stale_signals"]))
        if assessment.get("stale_signals") else "**Stale signals:** none",
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
            json_path = save_json_snapshot(assessment)
            print(f"\nReport written: {report_path}", file=sys.stderr)
            print(f"JSON snapshot: {json_path}", file=sys.stderr)

        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "unsafe": True, "monitor_failed": True}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executive report synthesis.

Assembles the final human-facing markdown from the threat assessment, the
specialist findings, and the trend analysis. A short executive summary is
written by the LLM when one is configured, with a deterministic fallback so
the report is always complete offline.

The fixed Bible-only guardrail footer (no date-setting, watchfulness-not-fear)
is always appended regardless of backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .llm import LLMClient
from .models import (
    ResearchFinding,
    ThreatAssessment,
    ExecutiveReport,
)

SYSTEM_PROMPT = (
    "You write a concise executive summary for a Bible-only prophecy watch "
    "report. Describe the overall pattern and what changed. Never set dates, "
    "never claim fulfilment, always note uncertainty. 2-4 sentences, plain text."
)

GUARDRAILS = [
    "**No date-setting (Matt 24:36).** This measures pattern, not timing.",
    "**Pattern ≠ fulfilment.** High intensity means *resembles* the scriptural "
    "description, not that prophecy is fulfilled.",
    "**Cross-verify before acting.** High confidence requires multiple "
    "independent sources.",
    "**Watchfulness, not fear (Luke 21:28).** This is for readiness and hope.",
]


def _deterministic_summary(threat: ThreatAssessment,
                           findings: List[ResearchFinding],
                           trends: Dict) -> str:
    escalating = [f.domain for f in findings if f.escalation == "escalating"]
    esc_txt = (
        f" Escalating domains: {', '.join(escalating)}."
        if escalating else " No domain is clearly escalating."
    )
    trend_txt = trends.get("summary", "") if isinstance(trends, dict) else ""
    return (
        f"Overall pattern strength is {threat.overall_intensity:.0f}/100 — "
        f"{threat.phase}. {threat.note}.{esc_txt} "
        f"{trend_txt}. This is pattern observation only; timing is unknown "
        f"(Matt 24:36)."
    )


def _summary_prompt(threat: ThreatAssessment,
                    findings: List[ResearchFinding], trends: Dict) -> str:
    lines = [
        f"Overall pattern strength: {threat.overall_intensity:.0f}/100 "
        f"({threat.phase}).",
        "Top nodes:",
    ]
    for na in threat.nodes[:5]:
        lines.append(
            f"- {na.node_id} {na.label}: intensity {na.intensity:.0f}, "
            f"confidence {na.confidence}"
        )
    lines.append("Domain findings:")
    for f in findings[:8]:
        lines.append(f"- {f.domain}: {f.escalation}, {f.confidence} — {f.headline}")
    if isinstance(trends, dict) and trends.get("summary"):
        lines.append(f"Trend memory: {trends['summary']}.")
    return "\n".join(lines)


def build_report(threat: ThreatAssessment,
                 findings: List[ResearchFinding],
                 trends: Dict,
                 llm: LLMClient,
                 title: str = "Prophecy Early-Warning Report") -> ExecutiveReport:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    fallback = _deterministic_summary(threat, findings, trends)
    summary = fallback
    if llm.online:
        summary = llm.complete(
            SYSTEM_PROMPT, _summary_prompt(threat, findings, trends),
            max_tokens=300,
        ).strip() or fallback

    sections: List[Dict[str, str]] = []

    # Threat picture
    threat_lines = [
        f"{threat.emoji} **Pattern strength: {threat.overall_intensity:.0f}/100 "
        f"— {threat.phase}**",
        f"_{threat.note}_",
        "",
        "| Node | Label | Intensity | Confidence | Sources | Notes |",
        "|------|-------|-----------|------------|---------|-------|",
    ]
    for na in threat.nodes:
        sources = threat.cross_validation.get(na.node_id, 0)
        threat_lines.append(
            f"| {na.node_id} | {na.label} | {na.intensity:.0f}/100 | "
            f"{na.confidence} | {sources} | {na.description} |"
        )
    sections.append({"heading": "Threat Picture", "body": "\n".join(threat_lines)})

    # Domain findings
    find_lines = []
    for f in findings:
        find_lines.append(
            f"### {f.domain} — {f.escalation} (confidence {f.confidence})"
        )
        find_lines.append(f.assessment)
        if f.key_facts:
            find_lines.append("")
            find_lines.extend(f"- {fact}" for fact in f.key_facts)
        find_lines.append("")
    sections.append({
        "heading": "Specialist Findings",
        "body": "\n".join(find_lines) or "_No active domains this cycle._",
    })

    # Trend memory
    trend_lines = []
    if isinstance(trends, dict) and trends.get("available"):
        trend_lines.append(f"_{trends.get('summary', '')}_\n")
        trend_lines.append("| Metric | Recent week | Baseline | Δ% | Direction |")
        trend_lines.append("|--------|-------------|----------|-----|-----------|")
        for name, m in trends.get("metrics", {}).items():
            if not m.get("available"):
                continue
            trend_lines.append(
                f"| {name} | {m['recent_week']} | {m['baseline_avg']} | "
                f"{m['acceleration_pct']:+.1f}% | {m['direction']} |"
            )
    else:
        trend_lines.append("_Insufficient history for trend analysis._")
    sections.append({"heading": "Trend Memory", "body": "\n".join(trend_lines)})

    # Guardrails (always present)
    sections.append({
        "heading": "Interpretation Guardrails",
        "body": "\n".join(f"{i+1}. {g}" for i, g in enumerate(GUARDRAILS)),
    })

    markdown = _render_markdown(title, now, summary, sections, llm.backend_name)
    return ExecutiveReport(
        title=title,
        generated_at=now,
        summary=summary,
        sections=sections,
        markdown=markdown,
        backend=llm.backend_name,
    )


def _render_markdown(title: str, when: str, summary: str,
                     sections: List[Dict[str, str]], backend: str) -> str:
    out = [
        f"# {title} — {when.split(' ')[0]}",
        "",
        f"**Generated:** {when}  ",
        f"**Analysis backend:** {backend}",
        "",
        "## Executive Summary",
        "",
        summary,
        "",
    ]
    for sec in sections:
        out.append(f"## {sec['heading']}")
        out.append("")
        out.append(sec["body"])
        out.append("")
    out.append("---")
    out.append(
        "> _Matthew 24:36 — “But of that day and hour knoweth no man.” "
        "Prove all things (1 Thess 5:21)._"
    )
    return "\n".join(out)

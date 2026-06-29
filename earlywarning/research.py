#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parallel specialist research agents.

A coordinator fans out one specialist agent per active research domain
(war, financial, disaster, cosmic, digital-control, ...). Each agent receives
only its domain's evidence clusters and produces a :class:`ResearchFinding`.

Every agent first computes a **deterministic finding** from the structured
cluster data. When a real LLM backend is configured, that deterministic
finding is passed to the model as a fallback and the model is asked to sharpen
the narrative — but the pipeline produces meaningful output even with no LLM.

Guardrail: the system prompt enforces Bible-only framing, no date-setting,
and explicit uncertainty.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from .llm import LLMClient
from .models import EvidenceCluster, ResearchFinding
from .taxonomy import DOMAINS, node_label

SYSTEM_PROMPT = (
    "You are a careful watch-analyst for a Bible-only prophecy-tracking "
    "early-warning system. You summarise current real-world signals in one "
    "domain. Rules: (1) Describe patterns, never set dates or claim a prophecy "
    "is 'fulfilled'. (2) Distinguish observation from speculation. (3) State "
    "uncertainty plainly. (4) Prefer multi-source corroborated facts. Respond "
    "with strict JSON only."
)


def _escalation(clusters: List[EvidenceCluster]) -> str:
    """Heuristic escalation read from severity + corroboration."""
    if not clusters:
        return "unknown"
    strong = sum(1 for c in clusters if c.source_count >= 2)
    high_sev = sum(
        1 for c in clusters
        if (c.max_magnitude or 0) >= 6.0
        or any(e.confidence == "High" for e in c.events)
    )
    if strong >= 2 or high_sev >= 2:
        return "escalating"
    if strong >= 1 or high_sev >= 1:
        return "steady"
    return "easing"


def _confidence(clusters: List[EvidenceCluster]) -> str:
    """Cross-validation confidence: best corroboration across clusters."""
    best_sources = max((c.source_count for c in clusters), default=0)
    best_event_conf = "Low"
    for c in clusters:
        for e in c.events:
            if e.confidence == "High":
                best_event_conf = "High"
            elif e.confidence == "Med" and best_event_conf != "High":
                best_event_conf = "Med"
    if best_sources >= 3:
        return "High"
    if best_sources >= 2 or best_event_conf == "High":
        return "Med"
    return "Low"


def _deterministic_finding(domain_key: str,
                           clusters: List[EvidenceCluster]) -> ResearchFinding:
    domain = DOMAINS[domain_key]
    total_events = sum(c.size for c in clusters)
    key_facts: List[str] = []
    for c in clusters[:5]:
        top = c.events[0]
        corrob = f"{c.source_count} source(s)"
        when = top.occurred_at or "date n/a"
        key_facts.append(f"{c.label}: {top.title} [{when}, {corrob}]")

    node_txt = ", ".join(
        f"{n} {node_label(n)}" for n in domain.node_ids
    )
    escalation = _escalation(clusters)
    confidence = _confidence(clusters)
    headline = (
        f"{domain.title}: {total_events} event(s) across "
        f"{len(clusters)} situation(s) — {escalation}"
    )
    assessment = (
        f"Observed {total_events} normalized event(s) grouped into "
        f"{len(clusters)} corroboration cluster(s) for the {domain.title} "
        f"domain (nodes {node_txt}). Cross-source confidence is {confidence}; "
        f"trend reads as {escalation}. This is pattern observation, not a "
        f"claim of prophetic fulfilment or timing (Matt 24:36)."
    )
    return ResearchFinding(
        domain=domain_key,
        headline=headline,
        assessment=assessment,
        key_facts=key_facts or ["No qualifying events in the lookback window."],
        confidence=confidence,
        escalation=escalation,
        node_ids=list(domain.node_ids),
        cluster_ids=[c.cluster_id for c in clusters],
    )


def _agent_prompt(domain_key: str, clusters: List[EvidenceCluster]) -> str:
    domain = DOMAINS[domain_key]
    lines = [
        f"Domain: {domain.title}",
        f"Prophecy nodes: {', '.join(domain.node_ids)}",
        "Evidence clusters (most-corroborated first):",
    ]
    for c in clusters[:8]:
        lines.append(
            f"- [{c.cluster_id}] {c.label} | sources={c.source_count} "
            f"events={c.size} latest={c.latest or 'n/a'}"
        )
        for e in c.events[:3]:
            lines.append(f"    * {e.title} ({e.source}, {e.confidence})")
    lines.append(
        "\nReturn JSON with keys: headline (str), assessment (str, <=120 words), "
        "key_facts (list of <=5 short strings), confidence (one of "
        "Low/Med/High), escalation (one of escalating/steady/easing/unknown)."
    )
    return "\n".join(lines)


class ResearchCoordinator:
    """Fans specialist agents out across domains in parallel."""

    def __init__(self, llm: LLMClient, max_workers: int = 6):
        self.llm = llm
        self.max_workers = max_workers

    def _run_agent(self, domain_key: str,
                   clusters: List[EvidenceCluster]) -> ResearchFinding:
        fallback = _deterministic_finding(domain_key, clusters)
        if not self.llm.online:
            fallback.source_backend = self.llm.backend_name
            return fallback

        fb_dict = {
            "headline": fallback.headline,
            "assessment": fallback.assessment,
            "key_facts": fallback.key_facts,
            "confidence": fallback.confidence,
            "escalation": fallback.escalation,
        }
        result = self.llm.complete_json(
            SYSTEM_PROMPT, _agent_prompt(domain_key, clusters), fb_dict
        )
        return ResearchFinding(
            domain=domain_key,
            headline=str(result.get("headline", fallback.headline)),
            assessment=str(result.get("assessment", fallback.assessment)),
            key_facts=list(result.get("key_facts", fallback.key_facts))[:5],
            confidence=str(result.get("confidence", fallback.confidence)),
            escalation=str(result.get("escalation", fallback.escalation)),
            node_ids=fallback.node_ids,
            cluster_ids=fallback.cluster_ids,
            source_backend=self.llm.backend_name,
        )

    def run(self, clusters: List[EvidenceCluster]) -> List[ResearchFinding]:
        by_domain: Dict[str, List[EvidenceCluster]] = {}
        for c in clusters:
            by_domain.setdefault(c.domain, []).append(c)

        # Only research domains that actually have evidence this cycle.
        active = [(d, cs) for d, cs in by_domain.items() if cs]
        if not active:
            return []

        findings: List[ResearchFinding] = []
        with ThreadPoolExecutor(max_workers=max(1, self.max_workers)) as pool:
            futures = {
                pool.submit(self._run_agent, d, cs): d for d, cs in active
            }
            for future in futures:
                try:
                    findings.append(future.result())
                except Exception:
                    d = futures[future]
                    findings.append(_deterministic_finding(d, by_domain[d]))

        findings.sort(
            key=lambda f: ({"escalating": 0, "steady": 1, "easing": 2,
                            "unknown": 3}[f.escalation],
                           {"High": 0, "Med": 1, "Low": 2}[f.confidence])
        )
        return findings

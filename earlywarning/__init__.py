"""
earlywarning — multi-agent evidence-driven pipeline for BibleStudy.

This package refactors the previous "run each fetch script, parse stdout,
glue markdown together" flow into a staged pipeline inspired by multi-agent
research orchestration (the "MiroFish" architecture analysis):

    collectors -> normalize -> dedupe -> evidence graph ->
    research agents (parallel) -> prophecy mapping -> threat scoring ->
    trend analysis -> executive report -> output channels

Design goals
------------
* **Provider-agnostic LLM.** Specialist research agents and the executive
  report go through ``earlywarning.llm.LLMClient``, which auto-selects an
  Anthropic or OpenAI backend when keys are present and otherwise falls back
  to a deterministic, offline heuristic backend. The whole pipeline therefore
  runs (and is testable) with no API keys and no network access.
* **Clean separation of ingestion and analysis.** The existing ``fetch_*.py``
  scripts remain the network ingestion layer that populates the SQLite store.
  The pipeline *reads* that store, so analysis is deterministic and offline.
* **Guardrails preserved.** Bible-only interpretation, no date-setting,
  explicit uncertainty, and multi-source cross-verification are encoded as
  first-class concepts (see ``scoring`` and ``report``).
"""

from .models import (
    RawSignal,
    NormalizedEvent,
    EvidenceCluster,
    ResearchFinding,
    NodeAssessment,
    ThreatAssessment,
    ExecutiveReport,
    PipelineResult,
)

__all__ = [
    "RawSignal",
    "NormalizedEvent",
    "EvidenceCluster",
    "ResearchFinding",
    "NodeAssessment",
    "ThreatAssessment",
    "ExecutiveReport",
    "PipelineResult",
]

__version__ = "0.1.0"

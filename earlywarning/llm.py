#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provider-agnostic LLM client.

The pipeline never imports a vendor SDK directly. It talks to ``LLMClient``,
which selects a backend at runtime:

* ``anthropic`` — uses the ``anthropic`` SDK when ``ANTHROPIC_API_KEY`` is set.
* ``openai``    — uses the ``openai`` SDK when ``OPENAI_API_KEY`` is set.
* ``heuristic`` — a deterministic, offline backend that returns the caller's
  supplied fallback. This lets every stage run (and be unit-tested) with no
  credentials and no network.

SDK imports are lazy, so neither ``anthropic`` nor ``openai`` needs to be
installed unless that backend is actually selected.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from .config import LLMConfig


class LLMBackend:
    """Interface every backend implements."""

    name = "base"

    def complete(self, system: str, prompt: str, max_tokens: int) -> str:
        raise NotImplementedError


class HeuristicBackend(LLMBackend):
    """Offline backend. Returns nothing useful from ``complete`` directly;
    callers rely on ``LLMClient.complete_json``'s deterministic fallback path.
    """

    name = "heuristic"

    def complete(self, system: str, prompt: str, max_tokens: int) -> str:
        # No model available — signal "empty" so complete_json uses fallback.
        return ""


class AnthropicBackend(LLMBackend):
    name = "anthropic"

    def __init__(self, cfg: LLMConfig):
        import anthropic  # lazy

        self._client = anthropic.Anthropic(
            api_key=cfg.anthropic_api_key, timeout=cfg.timeout
        )
        self._model = cfg.anthropic_model
        self._temperature = cfg.temperature

    def complete(self, system: str, prompt: str, max_tokens: int) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=self._temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "".join(parts).strip()


class OpenAIBackend(LLMBackend):
    name = "openai"

    def __init__(self, cfg: LLMConfig):
        from openai import OpenAI  # lazy

        self._client = OpenAI(api_key=cfg.openai_api_key, timeout=cfg.timeout)
        self._model = cfg.openai_model
        self._temperature = cfg.temperature

    def complete(self, system: str, prompt: str, max_tokens: int) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()


def _select_backend(cfg: LLMConfig) -> LLMBackend:
    """Choose a backend from config, degrading gracefully to heuristic."""
    provider = (cfg.provider or "auto").lower()

    def try_anthropic() -> Optional[LLMBackend]:
        if not cfg.anthropic_api_key:
            return None
        try:
            return AnthropicBackend(cfg)
        except Exception:
            return None

    def try_openai() -> Optional[LLMBackend]:
        if not cfg.openai_api_key:
            return None
        try:
            return OpenAIBackend(cfg)
        except Exception:
            return None

    if provider == "anthropic":
        return try_anthropic() or HeuristicBackend()
    if provider == "openai":
        return try_openai() or HeuristicBackend()
    if provider == "none":
        return HeuristicBackend()

    # auto: prefer anthropic, then openai, then heuristic.
    return try_anthropic() or try_openai() or HeuristicBackend()


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model response, tolerating prose
    and ```json fences."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        match = _JSON_BLOCK.search(text)
        candidate = match.group(0) if match else None
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


class LLMClient:
    """Thin orchestration layer over a selected backend."""

    def __init__(self, backend: LLMBackend, cfg: LLMConfig):
        self._backend = backend
        self._cfg = cfg

    @classmethod
    def from_config(cls, cfg: Optional[LLMConfig] = None) -> "LLMClient":
        cfg = cfg or LLMConfig.from_env()
        return cls(_select_backend(cfg), cfg)

    @property
    def backend_name(self) -> str:
        return self._backend.name

    @property
    def online(self) -> bool:
        """True when a real model backend is active."""
        return self._backend.name not in ("heuristic", "base")

    def complete(self, system: str, prompt: str,
                 max_tokens: Optional[int] = None) -> str:
        try:
            return self._backend.complete(
                system, prompt, max_tokens or self._cfg.max_tokens
            )
        except Exception:
            # Never let a transient LLM failure break the pipeline.
            return ""

    def complete_json(self, system: str, prompt: str,
                      fallback: Dict[str, Any],
                      max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Return a JSON object from the model, or ``fallback`` if the model
        is offline / errors / returns unparExtractable output.

        The model is instructed to return strict JSON. Whatever keys it omits
        are backfilled from ``fallback`` so callers always get a complete dict.
        """
        if not self.online:
            return dict(fallback)

        guided = (
            prompt
            + "\n\nReturn ONLY a single valid JSON object. Do not include prose "
            "or markdown fences."
        )
        raw = self.complete(system, guided, max_tokens)
        parsed = _extract_json(raw)
        if not parsed:
            return dict(fallback)

        merged = dict(fallback)
        merged.update({k: v for k, v in parsed.items() if v not in (None, "")})
        return merged

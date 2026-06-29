#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration loading for the early-warning pipeline.

All knobs come from environment variables (optionally loaded from a ``.env``
file via python-dotenv when available). Nothing here requires network access
or API keys to import — missing keys simply disable the corresponding feature.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Best-effort .env loading. python-dotenv is a declared dependency but the
# pipeline must still import if it is absent.
try:  # pragma: no cover - trivial import guard
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "prophecy_tracking.db"


def _env(*names: str, default: str = "") -> str:
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    return default


def _flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class LLMConfig:
    """Provider-agnostic LLM settings.

    ``provider`` may be ``auto`` (default), ``anthropic``, ``openai`` or
    ``none``. ``auto`` picks the first provider that has credentials, then
    falls back to the offline heuristic backend.
    """

    provider: str = "auto"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    openai_model: str = "gpt-4o-mini"
    max_tokens: int = 1024
    temperature: float = 0.2
    timeout: float = 60.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            provider=_env("LLM_PROVIDER", default="auto").lower(),
            anthropic_api_key=_env("ANTHROPIC_API_KEY", "LLM_API_KEY"),
            openai_api_key=_env("OPENAI_API_KEY"),
            anthropic_model=_env("ANTHROPIC_MODEL", default="claude-opus-4-8"),
            openai_model=_env("OPENAI_MODEL", default="gpt-4o-mini"),
            max_tokens=int(_env("LLM_MAX_TOKENS", default="1024") or "1024"),
            temperature=float(_env("LLM_TEMPERATURE", default="0.2") or "0.2"),
            timeout=float(_env("LLM_TIMEOUT", default="60") or "60"),
        )


@dataclass
class OutputConfig:
    """Delivery channel settings. Each channel is enabled only when both its
    flag is on *and* the required credentials are present."""

    slack_webhook: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    dashboard_path: str = ""
    dry_run: bool = True
    # Minimum alert level that triggers each outward channel.
    slack_min_level: str = "AMBER"
    telegram_min_level: str = "RED"
    email_min_level: str = "AMBER"
    # Only notify outward when the level rose / a fresh change occurred.
    notify_only_on_change: bool = True
    # Suppress repeat notifications at the same level within this window.
    cooldown_hours: float = 6.0

    @classmethod
    def from_env(cls) -> "OutputConfig":
        to_raw = _env("ALERT_EMAIL_TO")
        return cls(
            slack_min_level=_env("SLACK_MIN_LEVEL", default="AMBER").upper(),
            telegram_min_level=_env("TELEGRAM_MIN_LEVEL", default="RED").upper(),
            email_min_level=_env("EMAIL_MIN_LEVEL", default="AMBER").upper(),
            notify_only_on_change=_flag("ALERT_NOTIFY_ONLY_ON_CHANGE",
                                        default=True),
            cooldown_hours=float(_env("ALERT_COOLDOWN_HOURS",
                                      default="6") or "6"),
            slack_webhook=_env("SLACK_WEBHOOK_URL"),
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
            email_smtp_host=_env("ALERT_SMTP_HOST"),
            email_smtp_port=int(_env("ALERT_SMTP_PORT", default="587") or "587"),
            email_username=_env("ALERT_SMTP_USER"),
            email_password=_env("ALERT_SMTP_PASSWORD"),
            email_from=_env("ALERT_EMAIL_FROM"),
            email_to=[a.strip() for a in to_raw.split(",") if a.strip()],
            dashboard_path=_env(
                "DASHBOARD_PATH",
                default=str(REPO_ROOT / "tracking" / "dashboard" / "latest.json"),
            ),
            # Dry-run by default: nothing is sent outward unless explicitly
            # turned off. Outward-facing delivery should be a deliberate choice.
            dry_run=_flag("ALERTS_DRY_RUN", default=True),
        )


@dataclass
class PipelineConfig:
    db_path: Path = DEFAULT_DB_PATH
    lookback_days: int = 7
    trend_weeks: int = 8
    max_workers: int = 6
    output_dir: Path = REPO_ROOT / "tracking" / "early-warning"
    llm: LLMConfig = field(default_factory=LLMConfig.from_env)
    outputs: OutputConfig = field(default_factory=OutputConfig.from_env)

    @classmethod
    def from_env(cls, db_path: Optional[Path] = None,
                 lookback_days: Optional[int] = None) -> "PipelineConfig":
        return cls(
            db_path=Path(db_path or _env("PROPHECY_DB_PATH",
                                         default=str(DEFAULT_DB_PATH))),
            lookback_days=lookback_days
            or int(_env("PIPELINE_LOOKBACK_DAYS", default="7") or "7"),
            trend_weeks=int(_env("PIPELINE_TREND_WEEKS", default="8") or "8"),
            max_workers=int(_env("PIPELINE_MAX_WORKERS", default="6") or "6"),
            llm=LLMConfig.from_env(),
            outputs=OutputConfig.from_env(),
        )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Output dispatch.

Writes local artefacts (markdown report + dashboard JSON) unconditionally, and
sends outward notifications (Slack / Telegram / email) only when configured and
not in dry-run mode. Returns a list of channel labels that delivered.
"""

from __future__ import annotations

import json
import smtplib
import urllib.error
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from ..config import OutputConfig
from ..dashboard import render_html, render_shell
from ..models import PipelineResult, ALERT_LEVEL_ORDER


def _post_json(url: str, payload: dict, timeout: float = 10.0) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError):
        return False


def _write_markdown(result: PipelineResult, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    day = result.generated_at.split(" ")[0]
    path = out_dir / f"{day}_early_warning.md"
    path.write_text(result.report.markdown, encoding="utf-8")
    return f"markdown:{path}"


def _write_html_snapshot(result: PipelineResult, out_dir: Path) -> str:
    """A self-contained HTML report (data embedded) that opens with no server."""
    out_dir.mkdir(parents=True, exist_ok=True)
    day = result.generated_at.split(" ")[0]
    path = out_dir / f"{day}_early_warning.html"
    path.write_text(render_html(result.to_dict()), encoding="utf-8")
    return f"html:{path}"


def _write_dashboard(result: PipelineResult, dashboard_path: str) -> str:
    """Write latest.json plus an index.html shell (live dashboard when served)."""
    path = Path(dashboard_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    index = path.parent / "index.html"
    if not index.exists():
        index.write_text(render_shell(), encoding="utf-8")
    return f"dashboard:{path}"


def _alert_text(result: PipelineResult) -> str:
    t = result.threat
    lines = [
        f"{t.emoji} Prophecy Early-Warning — {result.alert_level} · {t.phase} "
        f"({t.overall_intensity:.0f}/100)",
    ]
    if result.changes:
        lines.append(result.changes.summary)
        for ch in result.changes.changes[:6]:
            if ch.severity in ("amber", "red", "watch"):
                lines.append(f"• {ch.message}")
    if result.freshness and result.freshness.any_stale:
        lines.append(f"⚠️ Stale sources: {', '.join(result.freshness.stale_sources)}")
    lines.append(result.report.summary)
    return "\n".join(lines)


def _send_slack(cfg: OutputConfig, text: str) -> bool:
    return _post_json(cfg.slack_webhook, {"text": text})


def _send_telegram(cfg: OutputConfig, text: str) -> bool:
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    return _post_json(url, {"chat_id": cfg.telegram_chat_id, "text": text})


def _send_email(cfg: OutputConfig, subject: str, body: str) -> bool:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = cfg.email_from or cfg.email_username
    msg["To"] = ", ".join(cfg.email_to)
    try:
        with smtplib.SMTP(cfg.email_smtp_host, cfg.email_smtp_port, timeout=15) as s:
            s.starttls()
            if cfg.email_username:
                s.login(cfg.email_username, cfg.email_password)
            s.sendmail(msg["From"], cfg.email_to, msg.as_string())
        return True
    except (smtplib.SMTPException, OSError):
        return False


_SEV_RANK = {"info": 0, "watch": 1, "amber": 2, "red": 3}
_LEVEL_SEV_FLOOR = {"GREEN": 0, "WATCH": 1, "AMBER": 2, "RED": 3}


def _within_cooldown(result: PipelineResult, previous: Optional[dict],
                     cooldown_hours: float) -> bool:
    """True if the previous run was at the same level within the cooldown."""
    if not previous:
        return False
    if previous.get("alert_level") != result.alert_level:
        return False
    prev_at, cur_at = previous.get("generated_at"), result.generated_at
    if not prev_at or not cur_at:
        return False
    try:
        fmt = "%Y-%m-%d %H:%M UTC"
        delta = datetime.strptime(cur_at, fmt) - datetime.strptime(prev_at, fmt)
    except ValueError:
        return False
    return 0 <= delta.total_seconds() < cooldown_hours * 3600


def _should_notify(result: PipelineResult, min_level: str,
                   previous: Optional[dict], cfg: OutputConfig) -> bool:
    """Decide whether an outward channel should fire for this run."""
    level = result.alert_level
    if ALERT_LEVEL_ORDER[level] < ALERT_LEVEL_ORDER[min_level]:
        return False  # below the channel's threshold

    ch = result.changes
    rose = bool(ch and ch.rose)
    first = bool(ch and ch.is_first_run)
    # A fresh change at/above this channel's severity floor justifies a page.
    floor = _LEVEL_SEV_FLOOR[min_level]
    fresh_change = bool(ch and any(
        _SEV_RANK.get(c.severity, 0) >= floor for c in ch.changes))

    if cfg.notify_only_on_change and not (rose or first or fresh_change):
        return False
    # Debounce repeats at the same level, unless the level rose.
    if not rose and _within_cooldown(result, previous, cfg.cooldown_hours):
        return False
    return True


def deliver(result: PipelineResult, cfg: OutputConfig, out_dir: Path,
            previous: Optional[dict] = None) -> List[str]:
    delivered: List[str] = []

    # Local artefacts are always written.
    delivered.append(_write_markdown(result, out_dir))
    try:
        delivered.append(_write_html_snapshot(result, out_dir))
    except OSError:
        pass
    try:
        delivered.append(_write_dashboard(result, cfg.dashboard_path))
    except OSError:
        pass

    text = _alert_text(result)
    subject = (f"[{result.alert_level}] Prophecy Early-Warning — "
               f"{result.threat.phase}")

    channels = [
        ("slack", cfg.slack_min_level, bool(cfg.slack_webhook),
         lambda: _send_slack(cfg, text)),
        ("telegram", cfg.telegram_min_level,
         bool(cfg.telegram_bot_token and cfg.telegram_chat_id),
         lambda: _send_telegram(cfg, text)),
        ("email", cfg.email_min_level,
         bool(cfg.email_smtp_host and cfg.email_to),
         lambda: _send_email(cfg, subject, text)),
    ]

    for name, min_level, configured, send in channels:
        if not configured:
            continue
        if not _should_notify(result, min_level, previous, cfg):
            delivered.append(f"{name}:suppressed({result.alert_level})")
            continue
        if cfg.dry_run:
            delivered.append(f"{name}:would-send({result.alert_level})")
            continue
        delivered.append(f"{name}:sent" if send()
                         else f"{name}:failed")

    return delivered

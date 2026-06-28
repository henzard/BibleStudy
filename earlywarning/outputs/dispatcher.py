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
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from ..config import OutputConfig
from ..models import PipelineResult


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


def _write_dashboard(result: PipelineResult, dashboard_path: str) -> str:
    path = Path(dashboard_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return f"dashboard:{path}"


def _alert_text(result: PipelineResult) -> str:
    t = result.threat
    return (
        f"{t.emoji} Prophecy Early-Warning — {t.phase} "
        f"({t.overall_intensity:.0f}/100)\n{result.report.summary}"
    )


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


def deliver(result: PipelineResult, cfg: OutputConfig,
            out_dir: Path) -> List[str]:
    delivered: List[str] = []

    # Local artefacts are always written.
    delivered.append(_write_markdown(result, out_dir))
    try:
        delivered.append(_write_dashboard(result, cfg.dashboard_path))
    except OSError:
        pass

    text = _alert_text(result)
    subject = f"Prophecy Early-Warning — {result.threat.phase}"

    # Outward channels: opt-in only.
    if cfg.dry_run:
        for name, configured in (
            ("slack", bool(cfg.slack_webhook)),
            ("telegram", bool(cfg.telegram_bot_token and cfg.telegram_chat_id)),
            ("email", bool(cfg.email_smtp_host and cfg.email_to)),
        ):
            if configured:
                delivered.append(f"{name}:dry-run")
        return delivered

    if cfg.slack_webhook and _send_slack(cfg, text):
        delivered.append("slack:sent")
    if (cfg.telegram_bot_token and cfg.telegram_chat_id
            and _send_telegram(cfg, text)):
        delivered.append("telegram:sent")
    if cfg.email_smtp_host and cfg.email_to and _send_email(cfg, subject, text):
        delivered.append("email:sent")

    return delivered

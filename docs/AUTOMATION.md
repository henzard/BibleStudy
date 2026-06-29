# Automation Guide

This document holds the scheduled-automation prompt for the BibleStudy
early-warning stack (for Cursor automations or Claude Code routines), plus the
operational notes around it.

It runs three things off a **single daily 06:00 SAST trigger**:

| Task | Command | Cadence |
|------|---------|---------|
| Ark-SA operational threat report | `scripts/ark_sa_daily_monitor.py` | every day |
| Prophecy early-warning report | `scripts/run_pipeline.py --days 7 --live` | every day |
| Weekly review + newsletter | `scripts/weekly_update.py --days 7` | Mondays only (conditional in-run) |

After a successful run it commits the run-state, opens a PR to `main`, and
**auto-merges** it so PRs don't accumulate.

> Prefer two schedules? Split the prompt into a daily block (ark + prophecy) and
> a separate Monday-only block that runs `weekly_update.py`.

---

## The automation prompt

Paste this as the routine/automation instruction. Set the schedule and secrets
in the platform UI (see [Secrets](#secrets--env) below).

```text
Run the existing BibleStudy automation stack. Do not recreate the Ark-SA monitor
or the early-warning pipeline from scratch. Extend, do not replace.

Repository: https://github.com/henzard/BibleStudy
Schedule: daily at 06:00 South Africa time (SAST). The monitor uses SAST
internally, so no --date is needed in production.

Read and obey the existing repo rules in .cursor/rules/ (Bible-only, news
methodology, source credibility, AI honesty). Then:

========================= DAILY — CHANNEL 1: SA OPERATIONAL =========================
1. Run the existing daily monitor (writes files AND prints JSON to stdout):
     python scripts/ark_sa_daily_monitor.py
2. Capture exit code. On non-zero exit, go to FAILURE HANDLING below.
3. Parse the JSON printed to stdout.
4. Confirm it generated:
     reports/ark-sa/<YYYY-MM-DD>.md
     reports/ark-sa/<YYYY-MM-DD>.json
5. Send a Slack message:
   Title:
     unsafe=false -> "Ark-SA Daily Threat Report"
     unsafe=true  -> "URGENT: Ark-SA Threat Alert"
   Include: threat_level, threat_score, confidence, decision, unsafe,
     changes_since_yesterday, top_reasons, recommended_actions, local_focus,
     route_focus, and a sources_checked summary (count + a few names).
   Send EVERY day, not only on unsafe days.

========================= DAILY — CHANNEL 2: PROPHECY EARLY-WARNING =========================
Keep this SEPARATE from the SA operational message above (separate Slack post).
6. Run the global prophecy early-warning pipeline:
     python scripts/run_pipeline.py --days 7 --live
7. Send a SECOND Slack message from tracking/dashboard/latest.json:
   Title:
     alert_level in (GREEN, WATCH, AMBER) -> "Prophecy Early-Warning — <alert_level>"
     alert_level == RED                   -> "URGENT: Prophecy Early-Warning — RED"
   Include: alert_level, threat.phase, threat.overall_intensity (x/100),
     changes.summary, the change list (changes.changes[].message),
     freshness.stale_sources (if any), report_summary.
   Send every day. Pattern observation only.

========================= WEEKLY — MONDAY ONLY =========================
On Mondays, after the daily channels, also run weekly_update.py.
Before running, scan scripts/weekly_update.py and scripts/generate_newsletter.py
for merge-conflict markers (<<<<<<<, =======, >>>>>>>). They are already fixed
on the working branch; if you find any (e.g. on main), fix them first.
     python scripts/weekly_update.py --days 7
Confirm it produced:
     tracking/weekly-reviews/<YYYY-MM-DD>_weekly_review.md
     tracking/newsletters/<YYYY-MM-DD>_weekly_watch.md

========================= COMMIT, PR & AUTO-MERGE =========================
Only if the run SUCCEEDED (daily monitor exit 0 and the pipeline did not error):
1. Create a dated branch for this run:
     git switch -c automation/daily-<YYYY-MM-DD>
2. Stage state + outputs (state MUST be committed so the next run can compute
   "changes since yesterday"):
     git add reports/ark-sa/*.md reports/ark-sa/*.json data/prophecy_tracking.db
     git add -f tracking/dashboard/latest.json tracking/early-warning/*.html
     # On Mondays also: git add tracking/weekly-reviews/*.md tracking/newsletters/*.md
3. Commit and push:
     git commit -m "chore(daily): <YYYY-MM-DD> — Ark-SA <threat_level> / EW <alert_level>"
     git push -u origin automation/daily-<YYYY-MM-DD>
4. Open a PR to main and AUTO-MERGE it (do NOT leave it open):
     - Use the platform GitHub integration (gh CLI or GitHub MCP).
     - Title: "Automated daily run <YYYY-MM-DD>"
     - Squash-merge as soon as it is mergeable (enable auto-merge if checks are
       pending; merge immediately if already green). Delete the head branch
       after merge.
5. Sweep: merge any OTHER open PRs created by this automation that are mergeable,
   so PRs do not accumulate. Squash-merge + delete the branch.
     - Scope to automation-authored PRs only.
     - If a PR has conflicts or failing checks, do NOT force it — leave it open
       and report it in the Slack message.

========================= MAINTENANCE (INCREMENTAL) =========================
If scripts/ark_sa_daily_monitor.py still uses static category signals, improve it
incrementally by reusing the EXISTING refactored collectors — each fetch script
now exposes collect(days=...) (and earlywarning/collectors wraps them), so import
and call those instead of scraping stdout:
   fetch_earthquakes, fetch_gdacs, fetch_worldbank_news, fetch_un_peacekeeping,
   fetch_fred_news, fetch_economic, fetch_spaceweather, fetch_eff_news,
   fetch_temple_mount_news (and monitor_antichrist_patterns — framework only).
One small, reviewable change per PR. Do not replace the architecture.

========================= FAILURE HANDLING =========================
If the daily monitor exits non-zero OR the pipeline raises:
1. Do NOT create or merge any PR.
2. Slack title: "Ark-SA Monitor Failed" (or "Early-Warning Pipeline Failed").
3. Include the error (the monitor prints {"error":..., "monitor_failed":true} to
   STDERR on failure; capture stderr + exit code).
4. Include the next manual command to run:
     python scripts/ark_sa_daily_monitor.py
     python scripts/run_pipeline.py --days 7 --live
5. Do not silently fail.

========================= RULES =========================
- Do not claim prophecy fulfillment. Do not set dates (Matt 24:36).
- Keep Bible/prophecy review SEPARATE from SA operational, family-readiness, and
  route/mobility risk (two distinct Slack messages, as above).
- Follow the repo's Bible-only, news-methodology, source-credibility, and
  AI-honesty rules. If sources are weak or unavailable, say "unknown".
- Only auto-merge automation-authored PRs; never force-merge over conflicts or
  red checks.

========================= SECRETS / ENV =========================
FRED_API_KEY, EINNEWS_RSS_KEY (optional). For pipeline narrative (optional):
ANTHROPIC_API_KEY or OPENAI_API_KEY. Slack is sent by the routine from parsed
JSON, so keep the pipeline's own dispatch off: ALERTS_DRY_RUN=true.
```

---

## Notes

### Why state must be committed
- `reports/ark-sa/*.json` is the Ark-SA day-over-day state — `changes_since_yesterday`
  reads the prior day's snapshot from there.
- `data/prophecy_tracking.db` is the early-warning pipeline's historical store
  **and** run-state (`pipeline_runs` table) — change detection diffs the latest
  stored run.

Without committing both, "changes since yesterday" / alert change-detection
resets to a baseline on every run.

### Auto-merge caveats
1. **Branch protection.** If `main` requires reviews or status checks, auto-merge
   waits (or is blocked) instead of merging instantly. For true unattended
   merging, either relax protection for the automation or rely on GitHub's
   "merge when checks pass" auto-merge.
2. **Scope.** The sweep is scoped to **automation-authored** PRs so it never
   blind-merges a human PR mid-review. To merge *all* open PRs regardless of
   author, change "automation-authored PRs only" to "all open PRs".

### Secrets / env
Set as automation secrets (never commit real keys):

| Variable | Purpose | Required |
|----------|---------|----------|
| `FRED_API_KEY` | Economic indicators | for economic data |
| `EINNEWS_RSS_KEY` | World Bank news feed | optional |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Pipeline narrative summaries | optional (runs offline without) |
| `ALERTS_DRY_RUN=true` | Let the routine own Slack messaging | recommended |

See `.env.example` for the full list, including the alert-routing knobs
(`SLACK_MIN_LEVEL`, `ALERT_COOLDOWN_HOURS`, …) used when the pipeline sends its
own alerts instead of the routine.

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

After a successful run it commits the run-state and opens a PR to `main`.
`.github/workflows/merge-daily-run.yml` marks that PR ready and squash-merges
it the moment it opens — so a draft is fine, and PRs cannot accumulate.

> Prefer two schedules? Split the prompt into a daily block (ark + prophecy) and
> a separate Monday-only block that runs `weekly_update.py`.

---

## The automation prompt

Paste this as the routine/automation instruction. Set the schedule and secrets
in the platform UI (see [Secrets](#secrets--env) below).

```text
Run the existing BibleStudy automation stack. Do not recreate the Ark-SA monitor
or the early-warning pipeline from scratch. DO NOT MODIFY CODE (see RULES).

Repository: https://github.com/henzard/BibleStudy
Schedule: daily at 06:00 South Africa time (SAST). The monitor uses SAST
internally, so no --date is needed in production.

Read and obey the existing repo rules in .cursor/rules/ (Bible-only, news
methodology, source credibility, AI honesty). Then:

========================= STEP 0: SYNC & IDEMPOTENCY =========================
1. git fetch origin && git switch -c automation/daily-<YYYY-MM-DD> origin/main
   The branch MUST be cut from up-to-date origin/main — a stale base makes
   every PR conflict and the sweep useless.
2. If branch automation/daily-<YYYY-MM-DD> or a PR titled
   "Automated daily run <YYYY-MM-DD>" already exists, do NOT create a second
   one: reuse/update the existing branch and PR instead.

========================= DAILY — CHANNEL 1: SA OPERATIONAL =========================
0. RESEARCH FIRST, then run. The monitor's signals live in
     data/ark_sa_signals.json   (DATA — editing it is required, not a code change)
   For each signal, search current South African news (news-methodology: at
   least 3 independent sources, cross-spectrum where political) and update
   level, score, confidence, summary, sources and `as_of` = today. Set `until`
   on any reason or action tied to a date. If you cannot verify a signal today,
   LEAVE IT — the monitor will mark it STALE after 7 days and lower confidence.
   Never refresh `as_of` without having actually read current sources.
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
     changes_since_yesterday, stale_signals, top_reasons, recommended_actions,
     local_focus, route_focus, and a sources_checked summary (count + names).
   Send EVERY day, not only on unsafe days.

========================= DAILY — CHANNEL 2: PROPHECY EARLY-WARNING =========================
Keep this SEPARATE from the SA operational message above (separate Slack post).
6. Run the global prophecy early-warning pipeline:
     python scripts/run_pipeline.py --days 7 --live
   Note: on a total feed outage the pipeline replays the store instead of
   reporting a false GREEN; stale sources appear in freshness.stale_sources.
7. Send a SECOND Slack message from tracking/dashboard/latest.json:
   Title:
     alert_level in (GREEN, WATCH, AMBER) -> "Prophecy Early-Warning — <alert_level>"
     alert_level == RED                   -> "URGENT: Prophecy Early-Warning — RED"
   Include: alert_level, threat.phase, threat.overall_intensity (x/100),
     changes.summary, the change list (changes.changes[].message),
     freshness.stale_sources (if any), report_summary.
   Send every day. Pattern observation only.

========================= WEEKLY — MONDAY ONLY =========================
On Mondays, after the daily channels, also run:
     python scripts/weekly_update.py --days 7
Confirm it produced:
     tracking/weekly-reviews/<YYYY-MM-DD>_weekly_review.md
     tracking/newsletters/<YYYY-MM-DD>_weekly_watch.md

========================= COMMIT, PR & AUTO-MERGE =========================
Only if the run SUCCEEDED (daily monitor exit 0 and the pipeline did not error):
1. Stage state + outputs (state MUST be committed so the next run can compute
   "changes since yesterday"):
     git add reports/ark-sa/*.md reports/ark-sa/*.json data/prophecy_tracking.db data/ark_sa_signals.json
     git add -f tracking/dashboard/latest.json
     git add -f tracking/early-warning/*.html tracking/early-warning/*.md
     # On Mondays also: git add tracking/weekly-reviews/*.md tracking/newsletters/*.md
2. Commit and push:
     git commit -m "chore(daily): <YYYY-MM-DD> — Ark-SA <threat_level> / EW <alert_level>"
     git push -u origin automation/daily-<YYYY-MM-DD>
3. Open a PR to main and AUTO-MERGE it (do NOT leave it open, do NOT leave it
   as a draft):
     - Use the platform GitHub integration (gh CLI or GitHub MCP).
     - Title: "Automated daily run <YYYY-MM-DD>"
     - Squash-merge as soon as it is mergeable (enable auto-merge if checks are
       pending; merge immediately if already green). Delete the head branch
       after merge.
4. Sweep (cap: 5 PRs, then stop and report the rest): squash-merge any OTHER
   open automation-authored PRs that are mergeable; delete their branches.
     - If a PR has conflicts or failing checks, do NOT force it and do NOT try
       to resolve conflicts yourself — leave it open and list it in the Slack
       message.

========================= BUDGET & RATE LIMITS =========================
- This is a report-and-publish routine, not a project: the whole run should be
  a bounded, linear pass. Run each step ONCE; on transient failure retry ONCE;
  then follow FAILURE HANDLING. Never loop.
- If the platform or model rate-limits you mid-run: stop cleanly, send ONE
  short Slack message ("Daily run aborted: rate-limited at step <n>"), and
  exit. Do not wait-and-retry in a loop; tomorrow's run will catch up — the
  pipeline's change detection tolerates a missed day.
- Do not re-read the whole repo, re-review architecture docs, or explore code
  beyond what the steps above require.

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
- DO NOT MODIFY CODE. No maintenance, no refactors, no bug fixes — if a bug
  blocks the run, report it via FAILURE HANDLING and stop. Code changes happen
  in interactive sessions, not in the daily routine.
  data/ark_sa_signals.json is data, not code: updating it IS the run (step 0).
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

### Why the routine may not modify code
An earlier version of this prompt had a standing "incremental maintenance"
clause. Combined with branches cut from a stale base (pre-fetch), it caused the
agent to re-diagnose and re-apply the same one-line fix for ~2 weeks straight
while its PRs sat unmergeable — the single largest source of wasted tokens in
the automation's history. The routine now reports bugs and stops; fixes happen
in interactive sessions.

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

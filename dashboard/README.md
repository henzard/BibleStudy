# Early-Warning Dashboard

A polished, dependency-free UI for the prophecy early-warning pipeline. No build
step, no CDN, no framework — a single self-contained `index.html` (inline CSS +
vanilla JS) that visualises the pipeline's output.

## What it shows

- **Pattern strength gauge** — the overall "beginning of sorrows" score (0–100),
  phase, and colour (green → yellow → orange → red).
- **Executive summary** + headline stats (events, clusters, domains, active nodes).
- **Prophecy node cards** — per-node intensity bars, confidence, source
  corroboration count, and scripture anchor.
- **Specialist findings** — one card per research domain with escalation /
  confidence badges and key facts.
- **Trend memory** — recent-vs-baseline table with direction arrows and
  sparklines.
- **Interpretation guardrails** — the Bible-only, no-date-setting reminders.

## How to view it

The pipeline produces two kinds of UI artefact on every run:

1. **Self-contained snapshot** — `tracking/early-warning/<date>_early_warning.html`
   has the data baked in. Just open it in a browser (works from `file://`,
   easy to share).
2. **Live dashboard** — `tracking/dashboard/index.html` + `latest.json`. Because
   browsers block `fetch()` from `file://`, serve the folder:

   ```bash
   python scripts/run_pipeline.py --days 7      # writes latest.json
   python scripts/serve_dashboard.py            # -> http://127.0.0.1:8000/
   ```

This `dashboard/index.html` is the canonical, version-controlled copy of the
UI. `serve_dashboard.py` and the pipeline write a copy next to `latest.json`
when one isn't already present. If you open it directly with no data, it shows
an empty state with a "Load a report JSON…" picker so you can browse any
exported `latest.json`.

## Customising

Everything lives in `earlywarning/dashboard.py` (`TEMPLATE` + `render_html` /
`render_shell`). Edit the inline `<style>` for theming or the `render()` JS for
layout; both the snapshot and the live shell come from that one template.

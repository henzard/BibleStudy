#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the early-warning pipeline.

This is the new master entrypoint that replaces the old "run every fetch
script and glue stdout together" flow with the staged multi-agent pipeline in
the ``earlywarning`` package.

Usage:
    python scripts/run_pipeline.py [--days 7] [--db PATH] [--json]

Notes:
    * Reads the SQLite store populated by the fetch_*.py ingestion scripts, so
      run ``python scripts/ingest_data.py`` first to refresh data.
    * Runs fully offline with a deterministic LLM fallback when no
      ANTHROPIC_API_KEY / OPENAI_API_KEY is configured.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

# Allow "python scripts/run_pipeline.py" without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from earlywarning.config import PipelineConfig  # noqa: E402
from earlywarning.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run prophecy early-warning pipeline")
    parser.add_argument("--days", type=int, default=7,
                        help="lookback window in days (default: 7)")
    parser.add_argument("--db", type=str, default=None,
                        help="path to the SQLite store")
    parser.add_argument("--json", action="store_true",
                        help="print machine-readable JSON summary instead of the report")
    parser.add_argument("--live", action="store_true",
                        help="fetch fresh data from the network, persist it, then "
                             "analyse (default: replay from the SQLite store)")
    args = parser.parse_args()

    cfg = PipelineConfig.from_env(
        db_path=Path(args.db) if args.db else None,
        lookback_days=args.days,
    )

    result = run_pipeline(cfg, log=lambda m: print(f"  · {m}", flush=True),
                          live=args.live)

    print()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(result.report.markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

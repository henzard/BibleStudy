#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serve the early-warning dashboard locally.

Serves the directory containing ``latest.json`` + ``index.html`` over HTTP so
the live dashboard can fetch its data (browsers block ``fetch()`` from
``file://``). Writes a fresh ``index.html`` shell if one is missing.

Usage:
    python scripts/serve_dashboard.py [--dir tracking/dashboard] [--port 8000]
"""

from __future__ import annotations

import argparse
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from earlywarning.dashboard import render_shell  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the early-warning dashboard")
    parser.add_argument("--dir", default="tracking/dashboard",
                        help="directory holding latest.json (default: tracking/dashboard)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    root = Path(args.dir)
    root.mkdir(parents=True, exist_ok=True)

    index = root / "index.html"
    if not index.exists():
        index.write_text(render_shell(), encoding="utf-8")
        print(f"Wrote dashboard shell: {index}")

    if not (root / "latest.json").exists():
        print(f"⚠️  {root / 'latest.json'} not found — run "
              f"'python scripts/run_pipeline.py' first. The dashboard will show "
              f"an empty state until then.")

    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"📊 Dashboard: {url}  (serving {root})")
    print("   Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

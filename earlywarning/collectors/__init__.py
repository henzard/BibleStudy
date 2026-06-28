"""Collectors turn data sources into :class:`RawSignal` objects.

The default collectors read the SQLite store that the existing ``fetch_*.py``
scripts populate. This keeps the network-facing ingestion layer untouched
while giving the pipeline a clean, deterministic, offline-testable input.
"""

from .base import Collector, CollectorContext
from .registry import build_default_collectors, collect_all

__all__ = [
    "Collector",
    "CollectorContext",
    "build_default_collectors",
    "collect_all",
]

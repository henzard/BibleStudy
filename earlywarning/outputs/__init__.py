"""Delivery channels for the executive report.

Every channel is opt-in: it only acts when its credentials are present and
``ALERTS_DRY_RUN`` is off. The markdown and dashboard channels always write
local files (they are not outward-facing).
"""

from .dispatcher import deliver

__all__ = ["deliver"]

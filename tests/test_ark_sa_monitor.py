"""The Ark-SA monitor must never report June as if it were today."""
from datetime import datetime
from zoneinfo import ZoneInfo

import scripts.ark_sa_daily_monitor as m

SAST = ZoneInfo("Africa/Johannesburg")


def _data(as_of: str) -> dict:
    return {
        "stale_after_days": 7,
        "signals": [
            {"name": "civil_unrest", "level": "AMBER", "score": 58, "confidence": "MEDIUM", "as_of": as_of,
             "summary": "Protests planned.", "sources": ["AP"],
             "reasons": [{"text": "Protests scheduled 30 Jun 2026", "until": "2026-06-30"},
                         {"text": "Tension persists"}],
             "actions": [{"text": "Avoid hotspots on 30 Jun", "until": "2026-06-30"}]},
            {"name": "global_shocks", "level": "WATCH", "score": 42, "confidence": "MEDIUM", "as_of": as_of,
             "summary": "Oil steady.", "sources": ["IOL"], "reasons": [], "actions": []},
        ],
    }


def test_a_date_bound_reason_is_gone_the_day_after(monkeypatch):
    monkeypatch.setattr(m, "check_usgs_sa_quakes", lambda now: [])
    now = datetime(2026, 8, 31, 6, 0, tzinfo=SAST)
    _, _, reasons, actions = m.build_category_signals([], now, _data("2026-08-30"))
    texts = [r["text"] for r in reasons]
    assert "Protests scheduled 30 Jun 2026" not in texts
    assert "Tension persists" in texts
    assert actions == []


def test_a_date_bound_reason_survives_until_its_day(monkeypatch):
    monkeypatch.setattr(m, "check_usgs_sa_quakes", lambda now: [])
    now = datetime(2026, 6, 30, 6, 0, tzinfo=SAST)
    _, _, reasons, _ = m.build_category_signals([], now, _data("2026-06-28"))
    assert "Protests scheduled 30 Jun 2026" in [r["text"] for r in reasons]


def test_stale_signals_say_so_and_lose_confidence(monkeypatch):
    monkeypatch.setattr(m, "check_usgs_sa_quakes", lambda now: [])
    now = datetime(2026, 8, 31, 6, 0, tzinfo=SAST)
    signals, stale, reasons, _ = m.build_category_signals([], now, _data("2026-06-28"))
    assert set(stale) == {"civil_unrest", "global_shocks"}
    unrest = next(s for s in signals if s.name == "civil_unrest")
    assert unrest.confidence == "LOW"
    assert unrest.summary.startswith("STALE — last researched 2026-06-28 (64 days ago)")
    assert unrest.level == "AMBER", "last-known level is kept, not invented"
    assert all(r["stale"] for r in reasons)


def test_fresh_signals_are_untouched(monkeypatch):
    monkeypatch.setattr(m, "check_usgs_sa_quakes", lambda now: [])
    now = datetime(2026, 8, 31, 6, 0, tzinfo=SAST)
    signals, stale, _, _ = m.build_category_signals([], now, _data("2026-08-29"))
    assert stale == []
    assert all(s.confidence == "MEDIUM" for s in signals)


def test_the_shipped_data_file_loads_and_is_dated():
    data = m.load_signal_data()
    assert data["stale_after_days"] == 7
    names = {s["name"] for s in data["signals"]}
    assert {"civil_unrest", "municipal_water", "route_mobility", "family_readiness"} <= names
    for s in data["signals"]:
        datetime.strptime(s["as_of"], "%Y-%m-%d")

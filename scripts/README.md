# Automation Scripts

Scripts for fetching and parsing data from various sources to assist with weekly news reviews.

---

## Earthquake Tracking

### `fetch_earthquakes.py`

**Purpose:** Fetch and parse earthquake data from USGS ATOM feed; filter for magnitude 4.0+ earthquakes.

**Usage:**
```bash
# Default: magnitude 4.0+, past 7 days
python scripts/fetch_earthquakes.py

# Custom magnitude threshold
python scripts/fetch_earthquakes.py --min-mag 5.0

# Custom time range
python scripts/fetch_earthquakes.py --days 30

# Combine options
python scripts/fetch_earthquakes.py --min-mag 4.5 --days 14
```

**Output:**
- Markdown table of earthquakes (sorted by magnitude)
- Pre-formatted rows for daily review classification table
- Confidence assessment (High/Med based on magnitude)
- Cross-verification reminder

**Data source:** [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) (Tier 1)

**Maps to:** Node J0 (Beginning of sorrows — earthquakes in divers places)

**Scripture anchor:** Matthew 24:7-8

---

## Multi-Hazard Disaster Tracking

### `fetch_gdacs.py`

**Purpose:** Fetch and parse multi-hazard disaster alerts from GDACS; covers earthquakes, floods, cyclones, droughts, volcanoes.

**Usage:**
```bash
# Default: Green+ alerts, past 30 days
python scripts/fetch_gdacs.py

# Only Orange and Red alerts (medium/severe)
python scripts/fetch_gdacs.py --alert-level Orange

# Only Red alerts (severe humanitarian impact)
python scripts/fetch_gdacs.py --alert-level Red

# Custom time range
python scripts/fetch_gdacs.py --days 60

# Combine options
python scripts/fetch_gdacs.py --alert-level Orange --days 7
```

**Output:**
- Markdown tables grouped by disaster type (Earthquake, Flood, Cyclone, Drought, Volcano)
- Alert levels with emojis (🔴 Red, 🟠 Orange, 🟢 Green)
- Population affected and severity descriptions
- Pre-formatted rows for daily review classification table
- Confidence assessment based on alert level

**Data source:** [GDACS](https://www.gdacs.org/) (Global Disaster Alert and Coordination System, EC-JRC) — Tier 1

**Maps to:** Node J0 (Beginning of sorrows — famines, pestilences, earthquakes)

**Scripture anchor:** Matthew 24:7-8

**Alert levels:**
- **Red:** Severe humanitarian impact — HIGH confidence
- **Orange:** Medium humanitarian impact — MEDIUM confidence
- **Green:** Minor impact — LOW confidence

**Requirements:**
- Python 3.6+
- No external dependencies (uses standard library only)

---

## Installation

No installation required. Scripts use Python standard library only.

**Verify Python is installed:**
```bash
python --version
# or
python3 --version
```

---

## Workflow Integration

### Weekly Review Workflow

1. **Run earthquake script:**
   ```bash
   python scripts/fetch_earthquakes.py
   ```

2. **Copy output** to `tracking/daily-reviews/YYYY-MM-DD.md`

3. **Cross-verify** with:
   - Reuters earthquake reports
   - BBC World News
   - EMSC (European-Mediterranean Seismological Centre)

4. **Mark J0 as "Observed"** in `tracking/END_TIMES_TODO.md` if:
   - Magnitude 5.0+ detected
   - Cross-verified with 2+ Tier 1 sources
   - Confidence: Med or High

---

## Future Scripts (Planned)

### Persecution Tracking
- `fetch_persecution.py` — Parse Open Doors World Watch List + VOM alerts

### Economic Indicators
- `fetch_economic.py` — Query FRED API for inflation, unemployment, trade disruption data

### Space Weather
- `fetch_spaceweather.py` — Parse NOAA Space Weather alerts (solar flares, geomagnetic storms)

### Digital ID News
- `fetch_biometric_news.py` — Scrape Biometric Update RSS + EFF blog

---

## Contributing

When adding new scripts:

1. **Use Python standard library** when possible (no external dependencies unless necessary)
2. **Include docstrings** (module, functions, classes)
3. **Add usage examples** to this README
4. **Output markdown-ready format** for easy copy-paste into daily reviews
5. **Include source credibility tier** in output
6. **Map to node IDs** from `tracking/END_TIMES_TODO.md`
7. **Cite Scripture anchors**

---

## Notes

### Why Python?
- Cross-platform (Windows, Mac, Linux)
- Standard library is powerful (no dependencies needed)
- Easy to read and modify
- Widely available

### Why no external dependencies?
- Easier setup (no `pip install` required)
- Fewer security concerns
- Scripts remain functional long-term (no dependency rot)

### Exception: When external libraries are justified
- API clients (e.g., `requests` for FRED API)
- Data parsing (e.g., `feedparser` for complex RSS)
- Only add if standard library solution is too complex

---

**Last updated:** 2025-12-26


# Automation Scripts

## 🚀 Quick Start: Weekly Update (RECOMMENDED)

### Run All Scripts with One Command

```bash
python scripts/weekly_update.py --days 7
```

**What it does:**
- Automatically runs all 8 data collection scripts
- Compiles results into a single markdown file
- Runs **Fig Tree Pattern Analysis** (Matt 24:33)
- Generates **Weekly Newsletter** with pattern assessment
- Takes ~60-90 seconds

**Output:**
- `tracking/weekly-reviews/YYYY-MM-DD_weekly_review.md` (raw data compilation)
- `tracking/newsletters/YYYY-MM-DD_weekly_watch.md` (public-ready newsletter)
- Console: Fig Tree Pattern Analysis with seasonal assessment

**Scripts included:**
1. ✅ USGS Earthquakes (mag 4.0+)
2. ✅ GDACS Multi-Hazard (EQ, flood, cyclone, drought, volcano, wildfire)
3. ✅ World Bank News (poverty, disasters, economic crisis)
4. ✅ UN Peacekeeping (conflicts, casualties, humanitarian crises)
5. ✅ FRED Economic News (data announcements)
6. ✅ FRED Economic Data (inflation, unemployment, GDP, trade balance)
7. ✅ NOAA Space Weather (solar flares, geomagnetic storms, radiation)
8. ✅ EFF Digital Rights (digital ID, biometrics, surveillance)
9. ✅ Fig Tree Pattern Analysis (multi-node intensity scoring)
10. ✅ Newsletter Generator (automated newsletter with fig tree data)

**Example output:**
- Summary statistics (scripts run, success/fail count)
- Results organized by category with node IDs and Scripture anchors
- Pre-formatted classification tables
- Fig Tree Pattern Strength score (0-100)
- Seasonal metaphor (Winter/Early Spring/Mid Spring/Late Spring)
- Public-ready newsletter with compelling headline
- Next steps checklist
- Scripture reminders

---

## Individual Scripts (for manual/targeted queries)

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

## Conflict & War Tracking

### `fetch_un_peacekeeping.py`

**Purpose:** Monitor UN peacekeeping operations for active conflicts, casualties, and humanitarian crises.

**Usage:**
```bash
# Default: past 30 days
python scripts/fetch_un_peacekeeping.py

# Custom time range
python scripts/fetch_un_peacekeeping.py --days 60
```

**Output:**
- Active conflict zones and peacekeeping operations
- Civilian and peacekeeping casualties (with verifiable numbers)
- Humanitarian crises in conflict zones
- Pre-formatted rows for daily review classification table
- Auto-categorized (Active Conflict, Casualties, Humanitarian Crisis)

**Recent examples (past 30 days):**
- **6,279 landmine casualties** (4-year high, 90% civilians, almost half children)
- **6 peacekeepers killed** in Sudan drone attack
- **DR Congo M23 offensives** (1.5 million displaced)
- **Lebanon violations** following Israeli airstrikes

**Data source:** [UN Peacekeeping Operations](https://peacekeeping.un.org/) — Tier 1

**Maps to:** Node J0 (Beginning of sorrows — wars and rumors of wars)

**Scripture anchor:** Matthew 24:6-7 — "wars and rumours of wars… nation shall rise against nation"

**Confidence levels:**
- **High:** Active conflict with casualties OR verifiable casualty numbers
- **Med:** Humanitarian crisis with numbers OR ongoing conflict zones
- **Low:** General peacekeeping updates

**Why UN Peacekeeping matters:**
- Official conflict zone monitoring (UN presence = verified conflict)
- Verifiable casualty data (official reports)
- Direct "wars and rumors of wars" tracking
- Tier 1 international authority

---

## Economic Indicators Tracking

### `fetch_fred_news.py`

**Purpose:** Monitor FRED (Federal Reserve Economic Data) announcements for new economic data series.

**Usage:**
```bash
# Default: past 30 days
python scripts/fetch_fred_news.py

# Custom time range
python scripts/fetch_fred_news.py --days 60
```

**Output:**
- List of FRED announcements
- Flags relevant economic indicators (inflation, unemployment, GDP, trade)
- Links to new data series

**Data source:** [FRED (St. Louis Fed)](https://fred.stlouisfed.org/) — Tier 1

**Maps to:** Node H0 (Babylon-like trade/economic patterns)

**Scripture anchor:** Revelation 17-18 (merchants/trade)

**Note:** This monitors **announcements** about new data. For actual economic data, use FRED API (see below).

---

### `fetch_worldbank_news.py`

**Purpose:** Monitor World Bank news for poverty, disasters, and economic crisis reports.

**Usage:**
```bash
# Default: past 7 days
python scripts/fetch_worldbank_news.py

# Custom time range
python scripts/fetch_worldbank_news.py --days 14
```

**Output:**
- Poverty forecasts and famine indicators
- Official disaster damage assessments (with $ amounts)
- Economic crisis reports by country
- Pre-formatted rows for daily review classification table
- Automatic classification by prophecy node (J0 for disasters/poverty, H0 for economic crisis)

**Data source:** [World Bank](https://www.worldbank.org/) (via EIN News) — Tier 1

**Maps to:** 
- Node J0 (Beginning of sorrows — famines, disasters)
- Node H0 (Babylon/merchants — economic patterns)

**Scripture anchors:** 
- Matthew 24:7-8 (famines, pestilences, earthquakes)
- Revelation 17-18 (merchants/trade collapse)

**Confidence levels:**
- **High:** Disaster with $ damage figures or death toll
- **Med:** Poverty forecasts, economic instability
- **Low:** General aid/humanitarian projects

**Why World Bank matters:**
- Authoritative poverty data (official "famines" proxy)
- Disaster damage assessments (verifiable $ amounts)
- Economic crisis indicators by country
- Tier 1 international organization

---

### FRED API Integration (Planned)

**Purpose:** Fetch actual economic indicator data (inflation, unemployment, GDP, trade deficits).

**Status:** ⏳ Pending — requires API key

**Setup:**
1. Create free FRED account: https://fredaccount.stlouisfed.org/
2. Request API key (free)
3. Store key in `.env` file (not committed to git)

**Planned indicators to track:**
- **Inflation:** CPI-U (Consumer Price Index), PCE (Personal Consumption Expenditures)
- **Unemployment:** U-3 official rate, U-6 broader measure
- **GDP:** Real GDP growth rate, GDP per capita
- **Trade:** Trade deficit/surplus, imports/exports
- **Supply chain:** Supply Chain Pressure Index
- **Debt:** Federal debt, deficit as % of GDP

**Maps to:** Node H0 — economic crisis indicators for "Babylon/merchants" pattern

**Confidence threshold:**
- **High:** Multiple indicators show crisis (e.g., high inflation + recession)
- **Med:** Single indicator elevated
- **Low:** Normal fluctuations

**Scripture anchor:** Revelation 18:11-19 — "merchants weep and mourn… no man buyeth their merchandise"

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


# Project Roadmap

**Purpose:** Track planned features, source integrations, and rule enhancements for the BibleStudy prophecy tracking system.

**Status key:**
- ✅ Completed
- 🔄 In progress
- ⏳ Pending evaluation
- ❌ Rejected

---

## 🎯 Current Phase: Source Integration

We have a comprehensive rule system (7 rules). Next priority: integrate specialized sources for better multi-category coverage.

---

## 📋 Roadmap Items

### Rules & Standards

| Item | Status | Priority | Notes |
|------|--------|----------|-------|
| Bible-only-66 interpretation rule | ✅ Completed | - | 66 books only; no tradition |
| Multi-source news verification | ✅ Completed | - | 3+ sources; cross-spectrum |
| AI honesty & anti-hallucination | ✅ Completed | - | "I don't know" is acceptable |
| Clean folder structure | ✅ Completed | - | Root = README only |
| Weekly review workflow | ✅ Completed | - | 7 categories; systematic |
| Date-setting prevention (Matt 24:36) | ✅ Completed | - | Forbids date predictions |
| Source credibility assessment | ✅ Completed | - | 4-tier system; reject fake news |
| Git workflow automation | ✅ Completed | - | Commit + push after changes; standardized messages |
| Historical baseline tracking | ⏳ Pending | Low | Track "normal" vs "escalating" frequency |
| Image/video verification | ⏳ Pending | Low | Deepfake/AI-generated detection |

---

### Sources: Christian Persecution Tracking

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| Open Doors World Watch List | ⏳ Pending | **High** | RSS or manual monthly check | 50 countries ranked; documented cases |
| Voice of the Martyrs | ⏳ Pending | **High** | Email alerts + weekly check | Regional alerts; specific incidents |
| International Christian Concern (ICC) | ⏳ Pending | Medium | Database access | Investigative; legal advocacy |
| US State Dept Religious Freedom Report | ⏳ Pending | Low | Manual annual check | Comprehensive but not real-time |

**Goal:** Cross-verify persecution headlines with both advocacy (Open Doors/VOM) AND secular news (Reuters/BBC).

---

### Sources: Earthquake & Natural Disaster Tracking

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| USGS Earthquake API | ✅ Completed | - | Python script created | `scripts/fetch_earthquakes.py` |
| GDACS (Global Disaster Alert) | ✅ Completed | - | Python script created | `scripts/fetch_gdacs.py` — multi-hazard (EQ, flood, cyclone, drought, volcano, wildfire) |
| EMSC (Euro-Med Seismological) | ⏳ Pending | Medium | API or RSS | Faster than USGS for Europe/Asia |
| ReliefWeb (UN OCHA) | ⏳ Pending | Medium | API or RSS | Humanitarian impact data |

**Goal:** Automate daily checks for mag 4.0+ earthquakes; auto-add to review if 6.0+.

**Status:** USGS + GDACS integration complete with automation scripts

---

### Sources: Economic & Trade Data

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| FRED News Monitor | ✅ Completed | - | Python script created | `scripts/fetch_fred_news.py` — tracks new data announcements |
| World Bank News | ✅ Completed | - | Python script created | `scripts/fetch_worldbank_news.py` — poverty, disasters, economic crisis |
| FRED API (Federal Reserve) | ⏳ Pending | **High** | Free API key | US + global indicators; authoritative |
| World Bank Open Data API | ⏳ Pending | Medium | API (free) | Global poverty, famine proxies (raw data) |
| IMF Financial Stability Report | ⏳ Pending | Low | Manual quarterly check | Crisis indicators |

**Goal:** Map economic crises to H0 (Babylon/merchants); track inflation, supply chain disruptions, poverty increases.

**Status:** FRED news + World Bank news monitors complete; API integrations require user setup

---

### Sources: Israel & Temple News

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| Jerusalem Post | ✅ Completed | - | Already using via search | Right-leaning; good for temple mount |
| Times of Israel | ✅ Completed | - | Already using via search | Center-left; comprehensive coverage |
| Temple Institute | ⏳ Pending | Medium | Manual check | Primary source for their activities |
| Arutz Sheva | ⏳ Pending | Low | Manual check | Religious Zionist perspective |

**Goal:** Track temple mount, red heifer, third temple preparations for J3 mapping.

---

### Sources: Digital ID, Surveillance, Biometrics

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| Biometric Update | ✅ Completed | - | Already using via search | Trade publication; rollout tracking |
| EFF (Electronic Frontier Foundation) | ⏳ Pending | **High** | RSS feed | Digital rights; surveillance alerts |
| IEEE Spectrum | ⏳ Pending | Medium | Manual or RSS | Emerging tech; AI; biometrics |
| Privacy International | ⏳ Pending | Low | Reports (manual check) | Surveillance state tracking |

**Goal:** Map to B2 (commerce control systems) with disclaimer: "NOT claiming this IS the mark."

---

### Sources: Cosmic & Space Weather Events

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| NOAA Space Weather Prediction Center | ⏳ Pending | **High** | Alerts or RSS | Solar flares, geomagnetic storms |
| NASA NEO (Near-Earth Objects) | ⏳ Pending | Low | API or manual | Asteroid close approaches |
| Spaceweather.com | ⏳ Pending | Low | RSS or manual | Aurora, meteor showers, solar activity |

**Goal:** Map to J6 (cosmic signs); be cautious — most solar activity is routine, not prophetic.

---

### Sources: Humanitarian & Refugee Data

| Source | Status | Priority | Setup needs | Notes |
|--------|--------|----------|-------------|-------|
| UN World Food Programme | ⏳ Pending | **High** | Reports + alerts | Famine early warning; food insecurity |
| UNHCR (UN Refugee Agency) | ⏳ Pending | Medium | API + reports | Displacement statistics |
| OCHA (UN Humanitarian Affairs) | ⏳ Pending | Low | Reports (via ReliefWeb) | Crisis overviews |

**Goal:** Map to J0 (famines, tribulation); A2 (believers suffering in world).

---

## 🎯 Immediate Next Steps

### Phase 1: High-Priority Sources (next 1-2 weeks)
1. ✅ ~~Set up **USGS Earthquake API**~~ — **COMPLETED** (`scripts/fetch_earthquakes.py`)
2. ✅ ~~Set up **GDACS**~~ — **COMPLETED** (`scripts/fetch_gdacs.py`)
3. ✅ ~~Set up **FRED News Monitor**~~ — **COMPLETED** (`scripts/fetch_fred_news.py`)
4. ✅ ~~Set up **World Bank News**~~ — **COMPLETED** (`scripts/fetch_worldbank_news.py`)
5. ⏳ Get **FRED API key** + create `fetch_economic.py` (requires user account)
6. ⏳ Subscribe to **EFF Blog RSS** (digital rights/surveillance)
7. ⏳ Bookmark **Open Doors World Watch List** (monthly manual check)

### Phase 2: Medium-Priority Sources (next month)
8. ⏳ Integrate **ReliefWeb API** (humanitarian impact)
9. ⏳ Subscribe to **NOAA Space Weather** alerts
10. ⏳ Bookmark **World Food Programme** famine alerts

### Phase 3: Optional Enhancements (as needed)
9. ⏳ Add **historical baseline tracking** rule (know "normal" vs "escalating")
10. ⏳ Add **image verification** rule (deepfakes, AI-generated content)
11. ⏳ Consider automated alerts for specific keywords
12. ⏳ Build trend visualization (chart J0/J1 intensity over time)

---

## 🤖 Automation Scripts

### Completed
- ✅ **`scripts/fetch_earthquakes.py`** — USGS earthquake feed parser
  - Fetches magnitude 4.0+ earthquakes
  - Outputs markdown-ready tables
  - Provides confidence assessment
  - Maps to node J0 (Matt 24:7-8)

- ✅ **`scripts/fetch_gdacs.py`** — GDACS multi-hazard alert parser
  - Covers earthquakes, floods, cyclones, droughts, volcanoes, wildfires
  - Alert levels: Red (severe), Orange (medium), Green (minor)
  - Population affected + severity descriptions
  - Maps to node J0 (Matt 24:7-8)

- ✅ **`scripts/fetch_fred_news.py`** — FRED economic data announcements monitor
  - Tracks new FRED data series announcements
  - Flags relevant economic indicators
  - Maps to node H0 (Rev 17-18)

- ✅ **`scripts/fetch_worldbank_news.py`** — World Bank news monitor
  - Poverty forecasts + famine indicators
  - Official disaster damage assessments
  - Economic crisis reports
  - Auto-classifies to J0 (disasters/poverty) or H0 (economic crisis)
  - Maps to nodes J0 (Matt 24:7-8) + H0 (Rev 17-18)

### Planned
- ⏳ `scripts/fetch_economic.py` — FRED API for actual economic data (requires API key from user)
- ⏳ `scripts/fetch_persecution.py` — Parse Open Doors WWL + VOM alerts
- ⏳ `scripts/fetch_spaceweather.py` — NOAA space weather alerts
- ⏳ `scripts/fetch_biometric_news.py` — Biometric Update + EFF RSS

See `scripts/README.md` for usage instructions.

---

## 💡 Open Questions (Community Input Welcome)

**What else should we track?**
- ❓ Social media sentiment analysis (for "love waxing cold" trends)?
- ❓ Gospel expansion tracking (mission agencies, Bible translation progress)?
- ❓ False prophet/deception tracking (cult activity, false miracles)?
- ❓ Pandemic/disease tracking (WHO alerts, CDC data)?
- ❓ Water scarcity data (for "Wormwood" / bitter waters)?

**Technical improvements:**
- ❓ Build dashboard for trend visualization?
- ❓ Create automated weekly email digest?
- ❓ Integrate with RSS readers (Feedly, Inoreader)?

---

## 📅 Version History

See README.md for detailed version history of rules and sources.

---

**Last updated:** 2025-12-26  
**Contributors:** [Your name here]  
**License:** Personal project (Bible-only, non-commercial)

---

*"But of that day and hour knoweth no man, no, not the angels of heaven, but my Father only." (Matthew 24:36)*


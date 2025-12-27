# News Sources & APIs — Master List

**Purpose:** Track all sources and tools for weekly news reviews.

**Status key:**
- ✅ Active (currently using)
- 🔄 Setup needed (API key, RSS, etc.)
- ⏳ Pending (user to evaluate)
- ❌ Rejected (not suitable)

---

## Category 1: News Search Tools (currently active)

| Tool | Status | Purpose | Notes |
|------|--------|---------|-------|
| `web_search` | ✅ Active | General web search | Built-in |
| `brave_web_search` | ✅ Active | Comprehensive web results | MCP tool |
| `brave_news_search` | ✅ Active | News-specific search | MCP tool; supports freshness filter |
| `brave_local_search` | ✅ Active | Location-based events | MCP tool; good for disaster tracking |
| `brave_summarizer` | ✅ Active | AI summaries of articles | MCP tool; requires search key |

---

## Category 2: Christian Persecution Tracking

| Source | Status | URL / Access | Credibility | Notes |
|--------|--------|--------------|-------------|-------|
| **Open Doors World Watch List** | ⏳ Pending | https://www.opendoors.org/en-US/persecution/countries/ | High (advocacy but documented) | Annual + monthly reports; 50 countries ranked |
| **Voice of the Martyrs** | ⏳ Pending | https://www.persecution.com/ | High (advocacy but verified) | Regional alerts; prayer guides; specific incidents |
| **International Christian Concern (ICC)** | ⏳ Pending | https://www.persecution.org/ | High (investigative) | Database of cases; legal advocacy |
| **Release International** | ⏳ Pending | https://releaseinternational.org/ | Moderate | UK-based; fewer reports than VOM |
| **US State Dept Religious Freedom Report** | 🔄 Setup | https://www.state.gov/international-religious-freedom-reports/ | Tier 1 (official) | Annual; comprehensive; no real-time alerts |
| **Barnabas Fund** | ⏳ Pending | https://barnabasfund.org/ | Moderate | Relief org; some news coverage |

**Setup needed:**
- RSS feeds (if available)
- Email alert subscription
- Weekly manual check vs. automated scraping

**Cross-verification requirement:** Always verify persecution claims with secular news (Reuters, BBC, regional outlets).

---

## Category 3: Earthquake & Natural Disaster Tracking

| Source | Status | URL / Access | Type | Notes |
|--------|--------|--------------|------|-------|
| **USGS Earthquake Hazards** | 🔄 Setup | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php | API (JSON) | Real-time; filter by magnitude (4.0+ recommended) |
| **EMSC (Euro-Med Seismological)** | 🔄 Setup | https://www.emsc-csem.org/ | Web + API | Global coverage; faster than USGS for Europe/Asia |
| **GDACS (Global Disaster Alert)** | 🔄 Setup | https://www.gdacs.org/ | RSS + API | Covers earthquakes, floods, cyclones, tsunamis |
| **ReliefWeb** | 🔄 Setup | https://reliefweb.int/ | RSS + API | UN OCHA; comprehensive disaster + humanitarian news |
| **NOAA Weather Alerts** | 🔄 Setup | https://www.weather.gov/ | Web | US-focused; severe weather alerts |

**Setup priority:**
1. USGS API (easiest integration; JSON format)
2. GDACS RSS (multi-hazard)
3. ReliefWeb API (humanitarian impact data)

**Automation potential:** Daily check for mag 4.0+ earthquakes; auto-add to news review if 6.0+.

---

## Category 4: Economic & Trade Data

| Source | Status | URL / Access | Type | Notes |
|--------|--------|--------------|------|-------|
| **World Bank Open Data** | 🔄 Setup | https://data.worldbank.org/ | API | Poverty, GDP, trade; historical + forecasts |
| **IMF Data** | 🔄 Setup | https://www.imf.org/en/Data | API | Financial stability, debt, crisis indicators |
| **Trading Economics** | ⏳ Pending | https://tradingeconomics.com/ | Web (API paid) | Aggregates official stats; free tier limited |
| **BLS (US Labor Statistics)** | 🔄 Setup | https://www.bls.gov/developers/ | API | US unemployment, inflation, wages |
| **Eurostat** | 🔄 Setup | https://ec.europa.eu/eurostat | API | EU economic data |
| **Federal Reserve Economic Data (FRED)** | 🔄 Setup | https://fred.stlouisfed.org/ | API | US + global indicators; highly authoritative |

**Setup priority:**
1. FRED API (easiest; most comprehensive for US)
2. World Bank API (global poverty/famine proxies)
3. Manual check: IMF Financial Stability Report (quarterly)

**Use case:** Map economic crises to H0 (Babylon/merchants/trade); track inflation, supply chain disruptions.

---

## Category 5: Israel & Temple News

| Source | Status | URL / Access | Credibility | Notes |
|--------|--------|--------------|-------------|-------|
| **Jerusalem Post** | ✅ Active | https://www.jpost.com/ | Tier 2 (bias: right) | Good for temple mount, red heifer, Israeli politics |
| **Times of Israel** | ✅ Active | https://www.timesofisrael.com/ | Tier 2 (bias: center-left) | Comprehensive Israel coverage |
| **Arutz Sheva (Israel National News)** | ⏳ Pending | https://www.israelnationalnews.com/ | Tier 2 (bias: right) | Religious Zionist perspective |
| **Temple Institute** | ⏳ Pending | https://templeinstitute.org/ | Advocacy | Third temple preparations; not news but primary source for their actions |
| **Haaretz** | ⏳ Pending | https://www.haaretz.com/ | Tier 2 (bias: left) | Israeli mainstream; paywall |

**Cross-verification strategy:**
- Use JPost + Times of Israel as base
- Verify with Reuters/BBC for major events (e.g., temple mount violence)
- Temple Institute = primary source for their own activities (not neutral news)

**Focus keywords:** "temple mount," "red heifer," "third temple," "Al-Aqsa," "Western Wall"

---

## Category 6: Digital ID, Surveillance, Biometrics

| Source | Status | URL / Access | Type | Notes |
|--------|--------|--------------|------|-------|
| **Biometric Update** | ✅ Active (via search) | https://www.biometricupdate.com/ | Trade publication | Tracks digital ID rollouts, facial recognition, biometric payments |
| **EFF (Electronic Frontier Foundation)** | 🔄 Setup | https://www.eff.org/ | Advocacy (high credibility) | Digital rights, surveillance tracking; blog + alerts |
| **IEEE Spectrum** | ⏳ Pending | https://spectrum.ieee.org/ | Tech journal | Emerging tech; AI; biometrics; credible but technical |
| **Privacy International** | 🔄 Setup | https://privacyinternational.org/ | Advocacy | Surveillance state tracking; global coverage |
| **Access Now** | ⏳ Pending | https://www.accessnow.org/ | Advocacy | Digital rights; shutdowns; surveillance |

**Setup priority:**
1. EFF blog RSS (daily updates)
2. Biometric Update RSS (industry news)
3. Weekly manual check: Privacy International reports

**Use case:** Map to B2 (mark of beast category — commerce control systems); maintain "NOT claiming this IS the mark" disclaimer.

---

## Category 7: Cosmic & Space Weather Events

| Source | Status | URL / Access | Type | Notes |
|--------|--------|--------------|------|-------|
| **NOAA Space Weather Prediction Center** | 🔄 Setup | https://www.swpc.noaa.gov/ | Official | Solar flares, geomagnetic storms, CMEs |
| **NASA Astronomy Picture of the Day** | ⏳ Pending | https://apod.nasa.gov/apod/ | Educational | Occasionally reports unusual phenomena |
| **NASA JPL Near-Earth Object Program** | 🔄 Setup | https://cneos.jpl.nasa.gov/ | Official | Asteroid close approaches |
| **Spaceweather.com** | ⏳ Pending | https://spaceweather.com/ | Independent (credible) | Aurora forecasts, meteor showers, solar activity |

**Setup priority:**
1. NOAA Space Weather alerts (G3+ geomagnetic storms)
2. NASA NEO close approach data (for "signs in the heavens" category)

**Use case:** Map to J6 (cosmic signs); be cautious — most solar flares are routine, not prophetic.

---

## Category 8: Humanitarian & Refugee Data

| Source | Status | URL / Access | Type | Notes |
|--------|--------|--------------|------|-------|
| **UNHCR (UN Refugee Agency)** | 🔄 Setup | https://www.unhcr.org/data.html | API + reports | Displacement statistics; crisis tracking |
| **UN World Food Programme** | 🔄 Setup | https://www.wfp.org/ | Reports + alerts | Famine early warning; food insecurity |
| **OCHA (UN Humanitarian Affairs)** | 🔄 Setup | https://www.unocha.org/ | Reports | Coordinates ReliefWeb; crisis overviews |
| **ACAPS (humanitarian analysis)** | ⏳ Pending | https://www.acaps.org/ | Reports | Crisis severity rankings |

**Setup priority:**
1. WFP famine alerts (monthly reports)
2. UNHCR displacement data (annual + emergency updates)

**Use case:** Map to J0 (famines, tribulation in the world); A2 (believers suffering in world).

---

## Cross-Cutting: Tier 1 News Agencies (always check)

| Source | Status | Purpose |
|--------|--------|---------|
| **Reuters** | ✅ Active | Primary fact-checking source; Tier 1 |
| **Associated Press (AP)** | ✅ Active | Primary fact-checking source; Tier 1 |
| **BBC News** | ✅ Active | International perspective; Tier 1 |
| **Agence France-Presse (AFP)** | ⏳ Pending | Tier 1; strong Europe/Middle East coverage |

**Protocol:** Before marking any node as "Observed," verify with at least one Tier 1 source.

---

## Setup Priorities (user action needed)

### High priority (do first):
1. ✅ USGS Earthquake API — Real-time mag 4.0+ alerts
2. ✅ EFF Blog RSS — Digital rights/surveillance tracking
3. ✅ Open Doors WWL — Christian persecution (monthly manual check)
4. ✅ FRED API — Economic crisis indicators

### Medium priority (next):
5. ⏳ GDACS RSS — Multi-hazard disaster alerts
6. ⏳ NOAA Space Weather — Solar flare alerts
7. ⏳ ReliefWeb API — Humanitarian crisis news
8. ⏳ World Food Programme — Famine alerts

### Low priority (optional):
9. ⏳ NASA NEO — Asteroid close approaches
10. ⏳ IMF reports — Quarterly economic analysis
11. ⏳ Privacy International — Surveillance state tracking

---

## Missing categories (user feedback requested)

What else should we track?
- ❓ Social media sentiment analysis (for "love waxing cold" trends)?
- ❓ Gospel expansion tracking (mission agencies, Bible translation progress)?
- ❓ False prophet/deception tracking (cult activity, false miracles reported)?
- ❓ Pandemic/disease tracking (WHO alerts, CDC data)?
- ❓ Water scarcity data (for "Wormwood" / bitter waters)?

---

## API Key Requirements

Some sources require API keys (free tier usually available):

| Source | API Key Needed? | Free Tier? | Signup URL |
|--------|----------------|------------|------------|
| USGS Earthquakes | No | Yes (public) | N/A |
| FRED (Federal Reserve) | Yes | Yes | https://fred.stlouisfed.org/docs/api/api_key.html |
| World Bank | No | Yes (public) | N/A |
| GDACS | No | Yes (public) | N/A |
| EFF | No (RSS) | Yes | N/A |

**Action:** User to decide which APIs to set up based on priority list above.

---

**Last updated:** 2025-12-26  
**Next review:** After user feedback on priorities


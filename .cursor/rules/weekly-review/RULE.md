---
description: "Weekly news review schedule and workflow: systematic search across categories, multi-tool usage, trend analysis, and summary generation."
alwaysApply: true
---

## Weekly review cadence

**Recommended schedule:** Every **Friday** or **Monday** (user's choice)

**Duration:** Allow 30-60 minutes for thorough multi-source verification

## Weekly workflow (step-by-step)

### Step 1: Search across categories (use all tools)

For each category below, run searches using multiple MCP tools:

| Category | Search queries | Tools to use |
|----------|----------------|--------------|
| **Wars/conflicts** | "Israel Gaza Ukraine Russia conflict war 2025", "Middle East tensions", "military operations" | `brave_news_search`, `brave_web_search` |
| **Natural disasters** | "earthquake flood tsunami famine 2025", "natural disasters", "extreme weather" | `brave_news_search`, `web_search` |
| **Persecution** | "Christian persecution religious freedom attacks 2025", "believers killed faith" | `brave_news_search`, `brave_web_search` |
| **Economic crises** | "economic crisis inflation trade disruption 2025", "global economy recession" | `brave_news_search`, `brave_web_search` |
| **Digital ID/surveillance** | "digital ID biometric surveillance 2025", "facial recognition payment system" | `brave_web_search`, `brave_news_search` |
| **Cosmic/unusual events** | "solar flare cosmic event meteor asteroid 2025", "unusual weather phenomenon" | `web_search`, `brave_news_search` |
| **Temple/Israel-specific** | "Israel temple mount red heifer third temple 2025" | `brave_news_search`, `brave_web_search` |

**Action:** For EACH category, search with at least 2 different tools and compile results.

### Step 2: Cross-spectrum verification

For each headline identified:

1. **Identify source bias** (left/right/center)
2. **Search for same event in opposite-bias sources**
3. **Compare factual details** (ignore opinion/spin)
4. **Note discrepancies** (if sources disagree, mark confidence: Low)

**Tools for bias-balanced search:**
- Use `brave_news_search` with `country` parameter to get international perspectives
- Use `web_search` with specific source names (e.g., "Reuters Ukraine" vs "Fox News Ukraine")

### Step 3: Classify and map

For each verified headline:

1. **Write factual summary** (no interpretation yet)
2. **Map to node IDs** (from `tracking/END_TIMES_TODO.md`)
3. **Cite Scripture anchors** (exact references)
4. **Assign confidence level** (Low/Med/High based on source count and cross-verification)
5. **List sources** in notes column

**Use template:** `templates/DAILY_NEWS_REVIEW_TEMPLATE.md`

### Step 4: Trend analysis (week-over-week)

Compare this week's headlines to previous weeks:

- **J0 (wars/disasters):** Rising, stable, or declining?
- **J1 (persecution):** New regions affected?
- **J2 (gospel preached):** Any expansion/restriction news?
- **B2 (digital ID/surveillance):** New implementations?
- **H0 (economic/trade):** Crisis deepening or stabilizing?

**Action:** Update trend notes in `tracking/DAILY_NEWS_LOG.md`

### Step 5: Update master checklist

Based on verified headlines (confidence: Med or High):

1. Open `tracking/END_TIMES_TODO.md`
2. Mark nodes as "Observed" if criteria met (3+ sources, cross-verified)
3. Add date and brief note to checklist item
4. **Do NOT tick boxes for Low-confidence items**

### Step 6: Generate weekly summary (optional)

Use `brave_summarizer` to create concise summaries of complex events (when needed).

**When to use summarizer:**
- Long investigative articles that need distillation
- Complex geopolitical situations requiring synthesis
- Technical reports (e.g., economic data, scientific studies)

**How to use:**
1. First run `brave_web_search` with `summary=true` parameter
2. Extract the `key` from results
3. Run `brave_summarizer` with that key
4. Include summary in your notes with citation

## Weekly output format

Create a new file: `tracking/daily-reviews/YYYY-MM-DD.md` (use template)

**Required sections:**
1. Headlines (15-20 raw headlines minimum)
2. Classification table (with sources listed)
3. Trend analysis
4. Scripture recalibration (1-3 passages read)
5. Obedience application

## Quality checklist (before saving weekly review)

- [ ] Searched across ALL 7 categories?
- [ ] Used at least 2 different MCP tools per category?
- [ ] Verified each headline with 3+ sources?
- [ ] Cross-spectrum verification achieved (left + right + center)?
- [ ] Sources listed in notes column for every entry?
- [ ] Confidence levels assigned (Low/Med/High)?
- [ ] Only Med/High confidence items used to tick boxes?
- [ ] Trend analysis completed (week-over-week comparison)?
- [ ] Scripture anchors cited for every node ID?
- [ ] Obedience application written (no speculation, plain action)?

## What's missing? (User feedback requested)

**Current tools covered:**
- ✅ `web_search`
- ✅ `brave_web_search`
- ✅ `brave_news_search`
- ✅ `brave_local_search` (for location-specific events)
- ✅ `brave_summarizer` (for complex articles)

**Potential additions:**
- ❓ Specific RSS feeds or APIs for Christian persecution monitoring?
- ❓ Earthquake/disaster tracking services (USGS, etc.)?
- ❓ Economic indicators API for real-time data?
- ❓ Social media sentiment analysis (to gauge "love waxing cold" trends)?

**User:** Please suggest additional tools, sources, or categories we should track.

## Frequency adjustments

If weekly is too frequent or not frequent enough:

- **Increase to daily:** If major events accelerate (e.g., J3 abomination appears)
- **Decrease to bi-weekly:** If trends are stable and repetitive
- **Event-driven:** Set up alerts for specific keywords and review only when triggered

**Default: Weekly is recommended** for sustainable long-term tracking without burnout.


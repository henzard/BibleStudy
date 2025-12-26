# BibleStudy

**Personal project (just for fun!)** — tracking end-times prophecy against daily news using AI + MCP tools.

## What this project does

This workspace contains a **Bible-only (66 books) end-times prophecy tracking checklist** derived from a comprehensive flowchart, plus a **daily news review system** that maps headlines to relevant prophetic categories without claiming definitive fulfillment.

We use:
- **MCP (Model Context Protocol) tools** to search real-time news (Brave News Search)
- **Cursor project rules** (`.cursor/rules/bible-only-66/`) to enforce Bible-only interpretation (no tradition, no speculation)
- **AI assistance** to help classify headlines, map them to Scripture nodes, and maintain restraint

## How close is "the end"? (Bible-only assessment)

Based on current tracking (as of Dec 26, 2025):

### ✅ What we're observing (Matthew 24 markers)
- **J0 — Beginning of sorrows**: Wars/rumors (Gaza, Ukraine), earthquakes (Myanmar, Asia), famines/disasters (150M+ affected) ✅
- **J1 — Persecution/hatred**: Christian persecution (Nigeria) ✅
- **J2 — Gospel preached**: Ongoing globally ✅

### ❌ What we have NOT observed yet (still future)
- **J3 — Abomination of desolation** (Dan 9:27; Matt 24:15) ❌
- **J4 — Great tribulation** (Matt 24:16-22) ❌
- **J6 — Cosmic signs** (sun darkened, etc.) ❌
- **J7 — Son of Man appears** (Matt 24:30-31) ❌

### 📍 Current phase
**"Beginning of sorrows"** (Matt 24:8) — Jesus explicitly said: *"all these are the beginning of sorrows"* and *"the end is not yet"* (Matt 24:6).

According to the text, the end comes AFTER:
1. Gospel preached in all the world (Matt 24:14) — ongoing ✅
2. Abomination of desolation (Matt 24:15) — not observed ❌
3. Great tribulation (Matt 24:21-22) — not observed ❌
4. Cosmic signs (Matt 24:29) — not observed ❌
5. THEN the Son of Man appears (Matt 24:30) — not observed ❌

**Honest assessment**: We're in the early warning phase. Major markers (J3–J7) remain future.

## 📁 Folder structure

```
BibleStudy/
├── README.md                                    # You are here
├── ROADMAP.md                                   # Public todo list
├── tracking/                                    # Active tracking files
│   ├── END_TIMES_TODO.md                       # Master checklist (all nodes)
│   ├── DAILY_NEWS_LOG.md                       # Append-only running log
│   └── daily-reviews/                          # Individual daily reviews
│       └── 2025-12-26.md                       # (example)
├── templates/                                   # Reusable templates
│   └── DAILY_NEWS_REVIEW_TEMPLATE.md           # Daily review template
├── reference/                                   # Source materials
│   ├── End_Of_Time_Chart.md                    # Original flowchart
│   ├── SOURCES_MASTER_LIST.md                  # 40+ sources (8 categories)
│   ├── QUICK_REFERENCE.md                      # One-page workflow guide
│   └── SETUP_COMPLETE.md                       # Setup documentation
├── scripts/                                     # Automation tools
│   ├── README.md                               # Scripts documentation
│   └── fetch_earthquakes.py                   # USGS earthquake feed parser
├── archive/                                     # Old/deprecated files
└── .cursor/rules/                              # Project rules (auto-applied)
    ├── README.md                               # All rules explained
    ├── bible-only-66/                          # Bible-only interpretation
    ├── news-methodology/                       # Multi-source verification
    ├── ai-honesty/                             # No hallucination policy
    ├── folder-structure/                       # Organization standards
    ├── weekly-review/                          # Systematic workflow
    ├── no-date-setting/                        # Matt 24:36 enforcement
    ├── source-credibility/                     # Quality control
    └── git-workflow/                           # Version control
```

## 🚀 Quick start

1. **Read current status**: `tracking/END_TIMES_TODO.md`
2. **See latest news review**: `tracking/daily-reviews/[latest-date].md`
3. **One-page workflow guide**: `reference/QUICK_REFERENCE.md` 📋 ← **Print this!**
4. **All rules explained**: `.cursor/rules/README.md` (5 rules)
5. **News methodology**: `.cursor/rules/news-methodology/RULE.md`

## 🔧 How to use this project

1. **Weekly news gathering** (recommended: every Friday or Monday)
   - Run searches using MCP tools: `brave_news_search`, `brave_web_search`, `web_search`
   - Search across 7 categories: wars, disasters, persecution, economy, digital ID, cosmic events, temple news
   - Verify with 3+ sources (left + right + center spectrum)

2. **Daily review creation**
   - Copy template: `templates/DAILY_NEWS_REVIEW_TEMPLATE.md`
   - Fill classification table with verified headlines
   - Map to node IDs from `tracking/END_TIMES_TODO.md`
   - Save as `tracking/daily-reviews/YYYY-MM-DD.md`

3. **Update master checklist**
   - Open `tracking/END_TIMES_TODO.md`
   - Mark nodes as "Observed" only if Med/High confidence
   - Add date + brief note to each marked item

4. **Append to running log**
   - Copy one section from daily review
   - Paste into `tracking/DAILY_NEWS_LOG.md` (append-only)

**AI assistance:** The AI will help search news, classify headlines, and enforce Bible-only guardrails automatically.

## Guardrails (Bible-only honesty)

### 🛡️ Core rules (enforced by AI)

1. **No "this is that" claims** — we map headlines to *categories*, not fulfillment
2. **66 books only** — no tradition, no extra-biblical symbolism
3. **Scripture compares with Scripture** (Isa 28:10) — line upon line
4. **Multi-source verification** — minimum 3 sources, cross-spectrum (left + right + center)
5. **"I don't know" is acceptable** — uncertainty is honest and biblical (Deut 29:29)
6. **Confidence levels required** — Low/Med/High for every headline
7. **No hallucination** — AI must search real data; cannot make up sources or verses

### 📰 News verification standards

**To mark a prophecy node as "Observed":**
- ✅ Minimum **3 independent sources**
- ✅ **Cross-spectrum verification** (at least one left-leaning AND one right-leaning source)
- ✅ **Factual consistency** across sources
- ✅ **Confidence: Med or High**

**News tools used:**
- `web_search`, `brave_web_search`, `brave_news_search`, `brave_local_search`, `brave_summarizer`

### 🤖 AI honesty policy

The AI assistant will:
- ✅ Always search for current data before claiming news exists
- ✅ Say "I don't know" when Scripture is silent or sources are insufficient
- ✅ Distinguish "what the text says" from "what it might mean"
- ✅ Correct errors immediately when discovered
- ✅ Never use forbidden phrases like "scholars agree" or "it's well-known"

See `.cursor/rules/ai-honesty/RULE.md` for full policy.

---

## 📋 Project Roadmap

See **`ROADMAP.md`** for planned features, source integrations, and enhancement priorities.

---

## 📌 Version History

### v2.1.0 — 2025-12-26
**Minor update: Git workflow automation**

**Added:**
- ✅ `git-workflow/` rule — Automatic commit and push after file changes; standardized commit messages

**Changed:**
- ✅ Now 8 project rules total (added to rules README)

### v2.0.0 — 2025-12-26
**Major update: Comprehensive rules system + source roadmap**

**Added:**
- ✅ 5 new project rules (7 total):
  - `news-methodology/` — Multi-source verification (3+ sources, cross-spectrum)
  - `ai-honesty/` — Anti-hallucination ("I don't know" is acceptable)
  - `folder-structure/` — Organization standards (root = README only)
  - `weekly-review/` — Systematic workflow (7 categories)
  - `no-date-setting/` — Matt 24:36 enforcement (forbid date predictions)
  - `source-credibility/` — 4-tier credibility system (Tier 1 sources preferred)
- ✅ Reorganized folder structure (clean root; subdirectories: tracking, templates, reference, archive)
- ✅ `reference/SOURCES_MASTER_LIST.md` — Comprehensive source tracking (8 categories, 40+ sources)
- ✅ `reference/QUICK_REFERENCE.md` — One-page visual workflow guide
- ✅ `ROADMAP.md` — Public todo list and feature roadmap

**Changed:**
- Moved all tracking files to `tracking/` subdirectory
- Moved all templates to `templates/` subdirectory
- Moved all reference materials to `reference/` subdirectory
- Renamed files for consistency (e.g., `End Of time Chart.md` → `End_Of_Time_Chart.md`)

### v1.0.0 — 2025-12-26
**Initial release: Bible-only prophecy tracking system**

**Added:**
- ✅ `END_TIMES_TODO.md` — Master checklist (all prophecy nodes A–N, IS, M)
- ✅ `DAILY_NEWS_LOG.md` — Append-only running log
- ✅ `DAILY_NEWS_REVIEW_TEMPLATE.md` — Daily news classification template
- ✅ `.cursor/rules/bible-only-66/` — Bible-only interpretation rule (66 books, no tradition)
- ✅ First daily review (2025-12-26) with this week's news mapped to node IDs
- ✅ MCP tools integration: `brave_news_search`, `brave_web_search`, `web_search`, `brave_local_search`, `brave_summarizer`

---

*Disclaimer: This is a personal, exploratory project for learning and reflection. It is not authoritative teaching and should not be used to set dates or make predictions. "But of that day and hour knoweth no man" (Matt 24:36).*


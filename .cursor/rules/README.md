# Cursor Rules Summary

This document summarizes all project rules located in `.cursor/rules/`. These rules are **automatically applied** to every AI chat session in this project.

---

## 1. Bible-Only Interpretation (`bible-only-66/`)

**Always applied:** ✅

**Key guardrails:**
- Use only the 66 books of the Christian Bible
- No tradition, church history, or extra-biblical sources
- Map events to biblical *categories*, not definitive fulfillment
- Quote Scripture references (book/chapter/verse) for precision
- Compare Scripture with Scripture (Isa 28:10)
- Wait humbly when Scripture is silent (Deut 29:29)

**Forbidden:**
- ❌ Declaring "this headline fulfills prophecy" definitively
- ❌ Using tradition or "scholars say" as authority
- ❌ Asserting connections the text doesn't explicitly make

---

## 2. News Methodology (`news-methodology/`)

**Always applied:** ✅

**Multi-source verification requirement:**
To mark a prophecy node as "Observed":
- ✅ Minimum **3 independent sources**
- ✅ **Cross-spectrum verification** (left + right + center news sources)
- ✅ **Factual consistency** across sources
- ✅ **Confidence: Med or High** (not Low)

**News tools to use:**
- `web_search`
- `brave_web_search`
- `brave_news_search`
- `brave_local_search` (for location-specific events)
- `brave_summarizer` (for complex articles)

**Confidence levels:**
- **Low:** 1-2 sources; single-bias; vague claims
- **Med:** 3+ sources; cross-spectrum; consistent details
- **High:** 5+ sources; cross-spectrum + international; official data

**Forbidden:**
- ❌ Citing single source as proof
- ❌ Using only left OR only right sources
- ❌ Ticking boxes based on speculation
- ❌ Ignoring contradictory sources

---

## 3. AI Honesty & Anti-Hallucination (`ai-honesty/`)

**Always applied:** ✅

**Core principle:** "I don't know" is a valid and preferred answer when:
- Current data not available
- Scripture is silent
- Sources conflict or are insufficient
- Confidence is low

**Mandatory protocols:**
- ✅ Search for current information using tools (don't guess)
- ✅ Quote Scripture accurately with references
- ✅ Cite actual news sources by name
- ✅ Distinguish "what the text says" from "what I think it means"
- ✅ Acknowledge uncertainty clearly

**Forbidden phrases:**
- ❌ "It's well-known that..."
- ❌ "The Bible clearly teaches..." (unless you can quote exact verse)
- ❌ "Scholars agree..."
- ❌ "This obviously refers to..."
- ❌ "According to prophecy experts..."

**Biblical foundation:**
- "The secret things belong unto the LORD" (Deut 29:29)
- "Who is this that darkeneth counsel by words without knowledge?" (Job 38:2)

---

## 4. Folder Structure (`folder-structure/`)

**Always applied:** ✅

**Root folder policy:** Only `README.md` belongs in the project root.

**Required structure:**
```
BibleStudy/
├── README.md                    # Only file in root
├── tracking/                    # Active tracking
│   ├── END_TIMES_TODO.md
│   ├── DAILY_NEWS_LOG.md
│   └── daily-reviews/
├── templates/                   # Reusable templates
├── reference/                   # Source materials
├── archive/                     # Old files
└── .cursor/rules/              # Project rules
```

**File naming conventions:**
- `lowercase-with-hyphens.md` for general files
- `UPPERCASE_WITH_UNDERSCORES.md` for primary tracking
- `YYYY-MM-DD.md` for daily logs

---

## 5. Weekly Review Workflow (`weekly-review/`)

**Always applied:** ✅

**Schedule:** Every Friday or Monday (user's choice)

**7 categories to search weekly:**
1. Wars/conflicts
2. Natural disasters (earthquakes, floods, famines)
3. Persecution/religious freedom
4. Economic crises/trade disruptions
5. Digital ID/surveillance technology
6. Cosmic/unusual weather events
7. Temple/Israel-specific news

**Workflow steps:**
1. **Search** across all categories with multiple tools
2. **Verify** cross-spectrum (left + right + center sources)
3. **Classify** and map to node IDs
4. **Analyze** trends (week-over-week)
5. **Update** master checklist (`tracking/END_TIMES_TODO.md`)
6. **Generate** weekly summary (optional, using `brave_summarizer`)

**Quality checklist before saving:**
- [ ] Searched all 7 categories?
- [ ] Used 2+ MCP tools per category?
- [ ] 3+ sources per headline?
- [ ] Cross-spectrum verified?
- [ ] Sources listed in notes?
- [ ] Confidence levels assigned?
- [ ] Only Med/High confidence items tick boxes?
- [ ] Scripture anchors cited?

---

## 6. No Date-Setting (`no-date-setting/`)

**Always applied:** ✅

**Biblical foundation:**
- "But of that day and hour knoweth no man" (Matt 24:36)
- "It is not for you to know the times or the seasons" (Acts 1:7)

**Explicitly forbidden:**
- ❌ "Jesus will return on [specific date]"
- ❌ "The tribulation starts in [year]"
- ❌ "We have exactly [X] years left"
- ❌ Date calculations based on blood moons, fig tree generation, etc.

**Permitted:**
- ✅ "We observe 'beginning of sorrows' patterns (Matt 24:8)"
- ✅ "Current trends suggest [category] rising, but timing unknown"
- ✅ "Jesus commanded us to watch (Matt 24:42) but not set dates"

**AI enforcement:** Will refuse to participate in date-setting; will quote Matt 24:36 immediately if user attempts it.

---

## 7. Source Credibility (`source-credibility/`)

**Always applied:** ✅

**Source credibility tiers:**
- **Tier 1 (high):** Reuters, AP, AFP, BBC News, official govt/UN sources
- **Tier 2 (moderate):** Mainstream outlets (note bias); specialty outlets
- **Tier 3 (low):** No named authors; clickbait; extreme partisan
- **Tier 4 (reject):** Fake news, satire as fact, AI-generated fake articles

**Red flag checklist:**
- No named author?
- No sources cited?
- Extreme language? ("Shocking!" "They don't want you to know!")
- Domain suspicious?
- No other outlets confirm?

**Cross-verification protocol:**
- Minimum: 3 sources including 1 Tier 1
- Ideal: 1 Tier 1 + 1 left + 1 right (all agree on facts)

**AI enforcement:** Will assess source credibility before citing; will warn if only Tier 2/3 available; will refuse to cite Tier 4.

## 8. Git Workflow (`git-workflow/`)

**Always applied:** ✅

**Core principle:** Every file change → Commit → Push

**When to commit:**
- ✅ After creating/editing any project file
- ✅ After completing daily/weekly news review
- ✅ After adding/updating rules
- ✅ After adding sources to master list

**Commit message format:**
```
<type>: <short description>

<optional details>
```

**Types:**
- `feat:` New feature
- `update:` Update existing content
- `fix:` Bug fix
- `docs:` Documentation
- `version:` Version bump

**AI enforcement:** Will automatically commit and push after completing file operations; will use proper commit message format.

---

## 9. Newsletter Structure (`newsletter-structure/`)

**Always applied:** ✅

**Purpose:** Generate weekly newsletters that are attention-grabbing, scannable, and habit-forming while maintaining ethical guardrails.

**Core principles:**
- **Hooked Model:** Trigger → Action → Variable Reward → Investment
- **Bang! Principles:** Cut through noise, memorable hooks, emotional connection, simplicity

**Required sections:**
1. Headline (attention-grabbing but honest)
2. TL;DR (2-3 sentences)
3. This Week's Highlights (bullet format with emojis)
4. Scripture Focus
5. "What Changed?" Tracker
6. Current Phase Assessment
7. Action Points (Prayer, Study, Watch)
8. Closing Reminder (Matt 24:36)

**Ethical guardrails:**
- ❌ No date-setting
- ❌ No fear-mongering
- ❌ No clickbait
- ❌ No speculation

---

## 10. Database Structure (`database-structure/`)

**Always applied:** ✅

**Purpose:** Define standards for SQLite database schema, data ingestion, and trend analysis.

**7 Core tables:**
- `earthquakes` (USGS data)
- `disasters` (GDACS multi-hazard)
- `conflicts` (UN Peacekeeping)
- `economic_indicators` (FRED API)
- `worldbank_news` (poverty/disasters)
- `weekly_assessments` (manual reviews)
- `trends` (ML predictions)

**Data quality standards:**
- Validate all inputs
- UTC timestamps only
- Source URL required
- Confidence levels recorded

---

## 11. AI Thought Partner (`ai-thought-partner/`)

**Always applied:** ✅

**Purpose:** Encourage AI to challenge assumptions, ask clarifying questions, and push back constructively.

**AI MUST challenge when:**
- Date-setting attempted (Matt 24:36)
- Speculation without Scripture
- Source credibility low
- Bible-only interpretation violated
- Fear-mongering detected

**AI SHOULD ask clarifying questions about:**
- User intent ("What problem are you solving?")
- Missing requirements ("Which prophecy node?")
- Better alternatives ("Have you considered...?")

---

## 12. Public Repo Safety (`public-repo-safety/`) ⭐ NEW

**Always applied:** ✅

**Purpose:** Ensure repository remains safe for public sharing on GitHub by preventing accidental commits of secrets.

**NEVER commit:**
- ❌ API keys (OpenAI, FRED, etc.)
- ❌ `.env` files
- ❌ Personal information
- ❌ Database files with personal data

**REQUIRED practices:**
- ✅ Store secrets in `.env` (gitignored)
- ✅ Provide `.env.example` template
- ✅ Use `python-dotenv` to load environment variables
- ✅ Update `.gitignore` for all secret patterns

**Pre-commit checklist:**
- [ ] No hardcoded API keys in scripts
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has placeholder values only
- [ ] No personal information in code

---

## Quick Reference Card

| Rule | Purpose | Key requirement |
|------|---------|-----------------|
| **Bible-only-66** | Interpretation framework | 66 books only; no tradition |
| **News methodology** | Verification standards | 3+ sources; cross-spectrum |
| **AI honesty** | Anti-hallucination | "I don't know" is acceptable |
| **Folder structure** | Organization | Root = README only |
| **Weekly review** | Systematic tracking | 7 categories; weekly cadence |
| **No date-setting** | Prevent speculation | Matt 24:36 enforcement |
| **Source credibility** | Quality control | Tier 1 sources preferred |
| **Git workflow** | Version control | Commit + push after changes |
| **Newsletter structure** | Engaging content | Hooked + Bang! principles |
| **Database structure** | Data standards | 7 tables; UTC timestamps |
| **AI thought partner** | Challenge assumptions | Push back on speculation |
| **Public repo safety** ⭐ NEW | Security | Secrets in .env (gitignored) |

---

## How these rules work

When you chat with the AI in this project:

1. **All 12 rules are automatically loaded** into the AI's context (because `alwaysApply: true`)
2. The AI **must follow** these rules in every response
3. If the AI violates a rule (e.g., cites single source, makes up data), you can reference this document to correct it
4. Rules are **version-controlled** in `.cursor/rules/` and shared across all team members (if applicable)

---

## Editing rules

To modify a rule:
1. Navigate to `.cursor/rules/[rule-name]/RULE.md`
2. Edit the markdown file
3. Save (changes apply immediately to new chat sessions)

To add a new rule:
1. Create folder: `.cursor/rules/new-rule-name/`
2. Add file: `RULE.md` with frontmatter:
   ```markdown
   ---
   description: "Short description"
   alwaysApply: true
   ---
   
   [Rule content]
   ```
3. Save and restart chat session

---

**Last updated:** 2025-12-26 (Added public-repo-safety rule #12)


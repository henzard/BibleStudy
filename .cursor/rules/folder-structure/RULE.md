---
description: "Project folder structure and organization: keep root folder clean with only README; organize documents, tracking files, and reference materials into clear subdirectories."
alwaysApply: true
---

## Root folder policy: README only

**Rule:** The project root (`C:\Project\BibleStudy\`) should contain ONLY:
- `README.md` (project overview and navigation)
- `.cursor/` folder (rules, settings)
- Subdirectories (organized by purpose)

**All other files go into subdirectories.**

## Recommended folder structure

```
C:\Project\BibleStudy\
│
├── README.md                          # Only file in root
│
├── .cursor/
│   └── rules/
│       ├── bible-only-66/
│       ├── news-methodology/
│       ├── ai-honesty/
│       └── folder-structure/
│
├── tracking/                          # Active daily/weekly tracking
│   ├── END_TIMES_TODO.md             # Master checklist
│   ├── DAILY_NEWS_LOG.md             # Append-only running log
│   └── daily-reviews/                # Individual daily reviews
│       ├── 2025-12-26.md
│       ├── 2025-12-27.md
│       └── ...
│
├── templates/                         # Reusable templates
│   └── DAILY_NEWS_REVIEW_TEMPLATE.md
│
├── reference/                         # Source materials and charts
│   ├── End_Of_Time_Chart.md          # Original flowchart
│   └── scripture-index.md            # (future) Verse cross-reference
│
└── archive/                           # Old or deprecated files
    └── (move old versions here)
```

## File naming conventions

**Use:**
- `lowercase-with-hyphens.md` for general files
- `UPPERCASE_WITH_UNDERSCORES.md` for primary tracking files (makes them stand out)
- `YYYY-MM-DD.md` for daily logs

**Avoid:**
- Spaces in filenames (use hyphens)
- Special characters (except hyphens and underscores)
- Vague names like "notes.md" or "document1.md"

## When creating new files

**Before creating a file, ask:**
1. What is its purpose? (tracking / template / reference / archive)
2. Does it go in an existing folder or need a new subfolder?
3. Is the name descriptive and follows conventions?

**AI instruction:** When the user asks you to create a new file, propose the location following this structure. If the folder doesn't exist, create it first.

## Migration plan (when reorganizing existing files)

If files are currently in the root folder:

1. **Create subdirectories** (tracking, templates, reference, archive)
2. **Move files** (not copy — move to preserve history)
3. **Update README.md** with new folder structure and navigation
4. **Update internal links** (if any markdown files reference other files)

## README.md structure (required sections)

The root `README.md` should always include:

1. **Title and one-sentence description**
2. **"How close is the end?" current assessment**
3. **Tech stack explanation** (MCP tools, AI, rules)
4. **Folder navigation** (where to find tracking, templates, reference)
5. **Guardrails summary** (Bible-only, multi-source, no hallucination)
6. **Disclaimers** (personal project, no date-setting)

## Folder descriptions (for README navigation)

Include this in README:

```markdown
## 📁 Folder structure

- **`tracking/`** — Active tracking files (master todo, daily logs)
- **`templates/`** — Reusable templates for daily news reviews
- **`reference/`** — Source materials (flowcharts, charts, verse indexes)
- **`archive/`** — Deprecated or old versions
- **`.cursor/rules/`** — Project rules (Bible-only, news methodology, AI honesty)
```

## Enforcement

- When the user asks to create a file, **always propose the correct subfolder location**
- If the root folder gets cluttered, **proactively suggest reorganization**
- Keep the root clean: **only README.md belongs there**


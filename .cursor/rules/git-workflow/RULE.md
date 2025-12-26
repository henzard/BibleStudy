---
description: "Git commit and push workflow: commit after every significant file change; push regularly to keep remote in sync; maintain clear commit messages."
alwaysApply: true
---

## Core principle: Version everything

**Purpose:** Every meaningful change should be committed and pushed so the project history is preserved and shareable.

## When to commit

**Commit immediately after:**
- ✅ Creating/editing any project file
- ✅ Adding/updating rules
- ✅ Completing a daily/weekly news review
- ✅ Adding sources to the master list
- ✅ Updating the ROADMAP
- ✅ Fixing errors or bugs

**Exception:** Do NOT commit:
- ❌ Temporary scratch files
- ❌ In the middle of AI-assisted edits (wait until edit is complete)
- ❌ Files with sensitive data (API keys should go in .gitignore)

## Commit message standards

### Format

```
<type>: <short description>

<optional detailed explanation>
<optional list of changes>
```

### Types (use these prefixes)

| Type | When to use | Example |
|------|-------------|---------|
| `feat:` | New feature or rule | `feat: Add USGS earthquake API integration` |
| `update:` | Update existing file/content | `update: Add 5 headlines to daily review 2025-12-27` |
| `fix:` | Bug fix or error correction | `fix: Correct Scripture reference in J3 node` |
| `docs:` | Documentation changes | `docs: Update README with v2.1.0 changes` |
| `refactor:` | Code/file reorganization | `refactor: Move old reviews to archive/` |
| `chore:` | Maintenance tasks | `chore: Clean up duplicate files` |
| `version:` | Version bumps | `version: Bump to v2.1.0` |

### Good commit message examples

✅ **Good:**
```
update: Daily review 2025-12-27 with 8 verified headlines

- 3 wars/conflicts (Gaza, Ukraine, Sudan)
- 2 earthquakes (Turkey 5.2, Japan 4.8)
- 1 persecution (Pakistan church attack)
- 2 digital ID (EU wallet rollout, India Aadhaar mandate)

All cross-verified with Reuters + BBC. Marked J0, J1, B2 as observed.
```

✅ **Good:**
```
feat: Add USGS earthquake API integration

- Created scripts/fetch_earthquakes.py
- Filters for magnitude 4.0+
- Auto-adds to daily review if mag 6.0+
- Updated ROADMAP: USGS marked as completed
```

❌ **Bad:**
```
update files
```
*Too vague; no context*

❌ **Bad:**
```
added stuff to readme and changed some other things
```
*Unprofessional; not descriptive*

## Push frequency

**Push after every commit** (or at minimum, at the end of each work session).

**Why:**
- Keeps remote repo in sync
- Backs up your work
- Allows others to see progress
- Prevents "forgot to push" scenarios

**Command:**
```bash
git add -A
git commit -m "type: description"
git push origin main
```

## AI workflow (automated by AI assistant)

When the AI makes file changes:

1. **Complete the edit fully** (don't commit mid-edit)
2. **Stage all changes**: `git add -A`
3. **Write clear commit message** (use format above)
4. **Commit**: `git commit -m "..."`
5. **Push**: `git push origin main`
6. **Confirm to user**: "Committed and pushed to GitHub"

**AI must do this automatically** after completing any significant file operation (creating, editing, moving files).

## Version bumping

When to bump version in README:

| Change | Version bump |
|--------|--------------|
| New rule added | Minor (2.0 → 2.1) |
| Major source integration (5+ sources) | Minor (2.0 → 2.1) |
| Breaking change (folder restructure, etc.) | Major (2.0 → 3.0) |
| Small updates (daily reviews, minor edits) | Patch (2.0.0 → 2.0.1) |

**Format:** `vMAJOR.MINOR.PATCH` (e.g., v2.1.3)

**Update in README.md** under "Version History" section.

## .gitignore recommendations

**Always ignore:**
```
# Sensitive data
.env
*.key
api_keys.txt
config/secrets.json

# OS files
.DS_Store
Thumbs.db

# IDE files (optional)
.vscode/
*.swp
*.swo

# Temporary files
*.tmp
scratch/
temp/
```

**Note:** API keys for USGS, FRED, etc. should be stored in `.env` or separate config file (not committed).

## Branch strategy (optional, for future)

For now, work directly on `main` branch (simple workflow).

**Future consideration:** Use feature branches for major changes:
```bash
git checkout -b feature/usgs-api-integration
# ... make changes ...
git commit -m "feat: Add USGS API integration"
git push origin feature/usgs-api-integration
# ... create pull request ...
```

## Rollback protocol (if mistakes happen)

**Undo last commit (before push):**
```bash
git reset --soft HEAD~1
```

**Undo last commit (after push):**
```bash
git revert HEAD
git push origin main
```

**Restore deleted file:**
```bash
git checkout HEAD~1 -- path/to/file
```

**Important:** Never use `git push --force` on shared branches.

## Daily review workflow (specific example)

1. **Complete daily review** (create `tracking/daily-reviews/YYYY-MM-DD.md`)
2. **Update master checklist** (mark nodes in `tracking/END_TIMES_TODO.md`)
3. **Append to running log** (`tracking/DAILY_NEWS_LOG.md`)
4. **Stage all**: `git add -A`
5. **Commit**: `git commit -m "update: Daily review 2025-12-27 with 8 verified headlines"`
6. **Push**: `git push origin main`

## File modification tracking

**Before starting work:**
```bash
git status   # See what's modified
```

**After completing work:**
```bash
git status   # Confirm what will be committed
git add -A   # Stage everything
git commit -m "..."
git push origin main
```

## Enforcement

**AI assistant must:**
- ✅ Commit and push after every file creation/edit session
- ✅ Use proper commit message format
- ✅ Update README version history for significant changes
- ✅ Notify user: "Committed and pushed to GitHub"

**User should:**
- ✅ Review commits before approving (Cursor will show diffs)
- ✅ Pull regularly if working from multiple machines
- ✅ Keep commit messages descriptive

## Summary

**Rule:** Every file change → Commit → Push

**Format:** `type: description` (with optional detail)

**Frequency:** After every significant edit (not mid-work)

**AI automation:** Always commit and push after completing file operations

---

*"Commit early, commit often, push always."*


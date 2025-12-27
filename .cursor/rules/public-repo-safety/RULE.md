---
description: "Public repository safety: Never commit secrets, API keys, or sensitive data. Use environment variables and .env files."
alwaysApply: true
---

## Purpose

Ensure this repository remains safe for public sharing on GitHub by:
- Preventing accidental commits of API keys, tokens, and secrets
- Using environment variables for sensitive configuration
- Maintaining a `.env.example` template for contributors

---

## Critical Rules

### ❌ NEVER COMMIT:

1. **API Keys**
   - OpenAI API keys
   - FRED API keys
   - Any third-party service credentials
   - Database passwords (if applicable)

2. **Personal Information**
   - Email addresses
   - Phone numbers
   - Personal identifiers

3. **Environment Files**
   - `.env` (contains actual secrets)
   - `*.key` files
   - `credentials.json`
   - Any file with "secret" or "private" in the name

4. **Database Files** (if containing personal data)
   - `*.db` files in `data/` folder
   - Backup files with real data

---

## ✅ REQUIRED PRACTICES

### 1. Environment Variables

**All secrets MUST be stored in `.env` file:**

```bash
# .env (NEVER commit this file!)
OPENAI_API_KEY=sk-proj-abc123...
FRED_API_KEY=your_actual_fred_api_key_here
```

### 2. .env.example Template

**Provide a template WITHOUT real values:**

```bash
# .env.example (safe to commit)
OPENAI_API_KEY=your_openai_api_key_here
FRED_API_KEY=your_fred_api_key_here
```

### 3. .gitignore Configuration

**Ensure `.gitignore` includes:**

```gitignore
# Environment variables (secrets)
.env
.env.local
.env.*.local

# Database files (may contain personal data)
data/*.db
data/*.db-journal

# API key files
*.key
credentials.json
```

### 4. Loading Environment Variables in Python

**Use `python-dotenv` library:**

```python
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access secrets
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Validate (optional but recommended)
if not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY not found in .env file")
```

**Installation:**
```bash
pip install python-dotenv
```

---

## Setup Instructions (for new users)

### Step 1: Install Dependencies
```bash
pip install python-dotenv
```

### Step 2: Create .env File
```bash
# Copy template
cp .env.example .env

# Edit with your actual keys
# (Use nano, vim, or any text editor)
```

### Step 3: Verify .gitignore
```bash
# Check that .env is ignored
git status
# .env should NOT appear in untracked files
```

---

## Pre-Commit Checklist

Before every `git commit`, verify:

- [ ] No hardcoded API keys in Python scripts
- [ ] No hardcoded passwords or tokens
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` is up-to-date (but has placeholder values)
- [ ] No `data/*.db` files are staged (use `git status`)
- [ ] No personal information in commit messages

---

## What to Do If You Accidentally Commit a Secret

### Immediate Actions:

1. **Rotate the secret immediately**
   - Generate a new API key
   - Invalidate the old one

2. **Remove from Git history** (if caught quickly)
   ```bash
   # If not pushed yet
   git reset --soft HEAD~1
   
   # If already pushed (DANGEROUS - coordinate with team)
   # Use BFG Repo-Cleaner or git filter-branch
   ```

3. **Update .env and .gitignore**
   - Move secret to `.env`
   - Ensure `.env` is in `.gitignore`

4. **Verify clean history**
   ```bash
   git log --all --full-history -- .env
   # Should show no results
   ```

---

## GitHub Security Features

### Enable on Your Repository:

1. **Secret Scanning** (GitHub automatically scans for leaked secrets)
2. **Dependabot Alerts** (for vulnerable dependencies)
3. **Branch Protection** (prevent accidental force pushes)

### GitHub Actions (if used):

Store secrets in:
- **Settings → Secrets and variables → Actions**
- Never hardcode in `.github/workflows/` files

---

## Environment Variable Naming Conventions

### Standard Format:
```
SERVICE_PURPOSE_KEY
```

### Examples:
- ✅ `OPENAI_API_KEY`
- ✅ `FRED_API_KEY`
- ✅ `DATABASE_PASSWORD`
- ❌ `key` (too vague)
- ❌ `MyApiKey` (inconsistent casing)

---

## Documentation Requirements

### README.md MUST Include:

```markdown
## Setup

### 1. Clone Repository
\`\`\`bash
git clone https://github.com/your-username/BibleStudy.git
cd BibleStudy
\`\`\`

### 2. Configure Environment Variables
\`\`\`bash
cp .env.example .env
# Edit .env with your API keys
\`\`\`

### 3. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Required API Keys
- **OpenAI API**: Get from https://platform.openai.com/api-keys
- **FRED API**: Get from https://fred.stlouisfed.org/docs/api/api_key.html
\`\`\`
```

---

## Automated Checks

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Check for potential secrets

if git diff --cached --name-only | grep -E '\.env$'; then
    echo "❌ ERROR: Attempting to commit .env file!"
    echo "   Remove with: git reset HEAD .env"
    exit 1
fi

# Check for hardcoded API keys
if git diff --cached | grep -E 'sk-proj-|api[_-]?key.*=.*["\']sk-'; then
    echo "⚠️  WARNING: Possible API key detected in commit!"
    echo "   Review changes carefully."
    exit 1
fi

exit 0
```

---

## Testing Environment Variables

### Verify Setup Script

Create `scripts/test_env.py`:

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = ['OPENAI_API_KEY', 'FRED_API_KEY']

print("Environment Variable Check:")
print("-" * 40)

for var in required_vars:
    value = os.getenv(var)
    if value:
        # Show only first/last 4 chars
        masked = f"{value[:7]}...{value[-4:]}" if len(value) > 11 else "****"
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: NOT FOUND")

print("-" * 40)
```

---

## Quality Check

Before publishing or sharing:

1. **Search for API keys:**
   ```bash
   grep -r "sk-proj-" . --exclude-dir=.git
   # Should return 0 results in tracked files
   ```

2. **Check .env is ignored:**
   ```bash
   git check-ignore .env
   # Should output: .env
   ```

3. **Verify no secrets in history:**
   ```bash
   git log --all --full-history --source -- "*api*" "*key*" "*secret*"
   ```

---

## Reference

- [GitHub Docs: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [OWASP: Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## Emergency Contact

If you discover a leaked secret in the public repository:
1. Rotate the key immediately
2. Contact repository owner
3. File a GitHub security advisory (if applicable)

**Remember:** Prevention is better than remediation. Always double-check before `git push`!


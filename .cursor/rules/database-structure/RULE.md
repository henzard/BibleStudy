---
description: "SQLite database structure and standards for historical tracking, trend analysis, and data persistence."
alwaysApply: true
---

## Purpose

Maintain a SQLite database to:
- Store historical data from all automation scripts
- Enable week-over-week trend comparison
- Track when prophecy nodes were first observed
- Build confidence over time with more data points
- Generate historical visualizations

---

## Database Location

**File:** `data/prophecy_tracking.db`

**Backup:** Automatically backed up weekly to `data/backups/`

**Git:** Database file is in `.gitignore` (too large, binary format)

---

## Schema Design

### Core Principles:
1. **Normalized structure** (avoid data duplication)
2. **Timestamp everything** (created_at, updated_at)
3. **Source attribution** (always track data source)
4. **Confidence tracking** (Low/Med/High with justification)
5. **Node mapping** (link to flowchart node IDs)

---

## Database Schema

### 1. `earthquakes` Table

Stores earthquake data from USGS.

```sql
CREATE TABLE earthquakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,        -- USGS event ID
    date_utc TEXT NOT NULL,                -- ISO 8601 format
    magnitude REAL NOT NULL,
    location TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    depth_km REAL,
    source_url TEXT,
    node_id TEXT DEFAULT 'J0',             -- Matt 24:7-8
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_earthquakes_date ON earthquakes(date_utc);
CREATE INDEX idx_earthquakes_magnitude ON earthquakes(magnitude);
```

---

### 2. `disasters` Table

Stores multi-hazard disaster data from GDACS.

```sql
CREATE TABLE disasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,         -- GDACS event ID
    date_utc TEXT NOT NULL,
    disaster_type TEXT NOT NULL,           -- Earthquake, Flood, Cyclone, Drought, Volcano, Wildfire
    location TEXT NOT NULL,
    alert_level TEXT,                      -- Red, Orange, Green
    severity_description TEXT,
    population_affected INTEGER,
    source_url TEXT,
    node_id TEXT DEFAULT 'J0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_disasters_date ON disasters(date_utc);
CREATE INDEX idx_disasters_type ON disasters(disaster_type);
CREATE INDEX idx_disasters_alert ON disasters(alert_level);
```

---

### 3. `conflicts` Table

Stores conflict and peacekeeping data from UN.

```sql
CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    location TEXT NOT NULL,
    conflict_type TEXT NOT NULL,           -- Active Conflict, Casualties, Humanitarian Crisis
    casualties INTEGER,
    description TEXT,
    source_url TEXT,
    confidence TEXT NOT NULL,              -- Low, Med, High
    node_id TEXT DEFAULT 'J0',             -- Matt 24:6-7
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conflicts_date ON conflicts(date);
CREATE INDEX idx_conflicts_location ON conflicts(location);
CREATE INDEX idx_conflicts_confidence ON conflicts(confidence);
```

---

### 4. `economic_indicators` Table

Stores economic data from FRED API.

```sql
CREATE TABLE economic_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                    -- YYYY-MM-DD
    indicator_name TEXT NOT NULL,          -- CPIAUCSL, UNRATE, GDP, etc.
    indicator_category TEXT NOT NULL,      -- inflation, unemployment, gdp, trade
    value REAL NOT NULL,
    yoy_change REAL,                       -- Year-over-year % change
    status TEXT NOT NULL,                  -- Normal, Concern, Crisis
    confidence TEXT NOT NULL,              -- Low, Med, High
    source TEXT DEFAULT 'FRED',
    node_id TEXT DEFAULT 'H0',             -- Rev 17-18
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_economic_date ON economic_indicators(date);
CREATE INDEX idx_economic_indicator ON economic_indicators(indicator_name);
CREATE INDEX idx_economic_status ON economic_indicators(status);
```

---

### 5. `worldbank_news` Table

Stores World Bank news and reports.

```sql
CREATE TABLE worldbank_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    headline TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,                -- Disaster/Famine, Economic
    keywords TEXT,                         -- Comma-separated
    confidence TEXT NOT NULL,              -- Low, Med, High
    source_url TEXT,
    node_id TEXT,                          -- J0 or H0
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_worldbank_date ON worldbank_news(date);
CREATE INDEX idx_worldbank_category ON worldbank_news(category);
```

---

### 6. `weekly_assessments` Table

Stores overall weekly assessments and node status.

```sql
CREATE TABLE weekly_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,              -- YYYY-MM-DD (Monday)
    week_end TEXT NOT NULL,                -- YYYY-MM-DD (Sunday)
    j0_status TEXT DEFAULT 'Observed',     -- Beginning of Sorrows
    j0_confidence TEXT DEFAULT 'Med',
    j1_status TEXT DEFAULT 'Observed',     -- Persecution
    j1_confidence TEXT DEFAULT 'Low',
    j2_status TEXT DEFAULT 'Observed',     -- Gospel Preached
    j2_confidence TEXT DEFAULT 'Med',
    j3_status TEXT DEFAULT 'Not Observed', -- Abomination
    j4_status TEXT DEFAULT 'Not Observed', -- Great Tribulation
    j6_status TEXT DEFAULT 'Not Observed', -- Cosmic Signs
    j7_status TEXT DEFAULT 'Not Observed', -- Son of Man Appears
    h0_status TEXT DEFAULT 'Not Observed', -- Economic Collapse
    h0_confidence TEXT DEFAULT 'Low',
    notes TEXT,
    scripture_focus TEXT,                  -- This week's focus verse
    newsletter_path TEXT,                  -- Path to generated newsletter
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weekly_start ON weekly_assessments(week_start);
```

---

### 7. `trends` Table

Stores calculated trends for visualization.

```sql
CREATE TABLE trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,             -- avg_earthquakes_per_week, conflict_zones_active
    time_period TEXT NOT NULL,             -- week, month, year
    period_start TEXT NOT NULL,            -- YYYY-MM-DD
    period_end TEXT NOT NULL,
    value REAL NOT NULL,
    comparison_to_previous REAL,           -- % change from previous period
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trends_metric ON trends(metric_name);
CREATE INDEX idx_trends_period ON trends(period_start);
```

---

## Data Ingestion Standards

### 1. Deduplication
- Always check for existing `event_id` or unique identifier
- Use `INSERT OR IGNORE` or `INSERT OR REPLACE` as appropriate
- Log skipped duplicates

### 2. Timestamps
- Store all dates in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Use UTC timezone
- Include `created_at` for audit trail

### 3. Source Attribution
- Always include `source_url` when available
- Track `source` field (USGS, GDACS, FRED, World Bank, UN)
- Maintain Tier 1 source priority

### 4. Confidence Tracking
- Store confidence level with justification in notes
- Update confidence as more data accumulates
- Never decrease confidence without documentation

---

## Trend Analysis Queries

### Week-over-Week Earthquake Comparison
```sql
SELECT 
    DATE(date_utc, 'weekday 0', '-6 days') as week_start,
    COUNT(*) as total_quakes,
    SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major_quakes,
    AVG(magnitude) as avg_magnitude
FROM earthquakes
WHERE date_utc >= date('now', '-60 days')
GROUP BY week_start
ORDER BY week_start DESC;
```

### Conflict Zones Trend
```sql
SELECT 
    DATE(date, 'weekday 0', '-6 days') as week_start,
    COUNT(DISTINCT location) as active_zones,
    SUM(casualties) as total_casualties
FROM conflicts
WHERE date >= date('now', '-90 days')
GROUP BY week_start
ORDER BY week_start DESC;
```

### Economic Status Over Time
```sql
SELECT 
    date,
    indicator_name,
    status,
    value,
    yoy_change
FROM economic_indicators
WHERE indicator_name IN ('UNRATE', 'CPIAUCSL')
ORDER BY date DESC
LIMIT 20;
```

---

## Backup Strategy

### Automatic Backups:
1. **Weekly:** Copy database to `data/backups/prophecy_tracking_YYYY-MM-DD.db`
2. **Monthly:** Keep last 12 months of weekly backups
3. **Git:** Database exports (CSV) are committed, not binary .db file

### Manual Backup:
```bash
python scripts/backup_database.py
```

---

## Data Export

### Export to CSV:
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/prophecy_tracking.db')
df = pd.read_sql_query("SELECT * FROM earthquakes", conn)
df.to_csv('data/exports/earthquakes.csv', index=False)
conn.close()
```

### Export for Analysis:
- Generate weekly CSV exports for version control
- Commit CSVs to Git (not binary .db file)
- Enable external analysis in Excel/R/Python

---

## Visualization Recommendations

### Dashboard Metrics:
1. **Earthquakes per week** (line chart)
2. **Active conflict zones** (bar chart)
3. **Economic status** (traffic light: 🟢🟠🔴)
4. **Confidence trends** (stacked area chart)
5. **Node status timeline** (Gantt-style)

### Tools:
- **Matplotlib** (Python built-in)
- **Plotly** (interactive)
- **Excel** (CSV exports)
- **Markdown tables** (for newsletters)

---

## Quality Checks

Before committing data:
- [ ] No duplicate event IDs
- [ ] All timestamps in UTC
- [ ] Source URLs included
- [ ] Confidence levels justified
- [ ] Node IDs mapped correctly
- [ ] NULL values are intentional (not missing data)

---

## Performance Considerations

### Indexing:
- Index all date columns
- Index frequently queried fields (magnitude, location, status)
- Use compound indexes for common queries

### Query Optimization:
- Use date ranges to limit result sets
- Aggregate at database level (not in Python)
- Cache trend calculations in `trends` table

### Size Management:
- SQLite handles millions of rows efficiently
- Archive data older than 5 years to separate database
- Vacuum database quarterly to reclaim space

---

## Security and Privacy

### Data Protection:
- No personal information stored (public data only)
- Source URLs are public (no authentication needed)
- Database file in `.gitignore` (not in public repo)

### Backup Encryption:
- Consider encrypting backup files if stored off-site
- Use strong passwords for cloud backups
- Keep local backups on trusted devices only

---

## Migration and Versioning

### Schema Versioning:
Store schema version in metadata table:

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial schema with 7 core tables');
```

### Future Migrations:
- Create migration scripts: `migrations/001_add_persecution_table.sql`
- Test on copy of production database
- Document all schema changes


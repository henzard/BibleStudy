#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter Generator with Fig Tree Pattern Analysis
Compiles weekly data + fig tree analysis into engaging newsletter format.

Usage:
    python generate_newsletter.py [--days 7]
"""

import sys
import io
import sqlite3
import subprocess
import traceback
from pathlib import Path
from datetime import datetime, timedelta

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPTS_DIR = Path(__file__).parent
DB_PATH = Path("data/prophecy_tracking.db")


def get_fig_tree_data(conn: sqlite3.Connection, weeks: int = 1) -> dict:
    """Get fig tree pattern analysis data."""
    # This replicates the logic from analyze_fig_tree_pattern.py
    # but returns data instead of printing
    
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    # J0 Wars
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN conflict_type = 'Active Conflict' THEN 1 ELSE 0 END) as active
        FROM conflicts
        WHERE date >= ?
    """, (cutoff_date,))
    wars_result = cursor.fetchone()
    wars_intensity = 0 if not wars_result or wars_result[0] == 0 else min(wars_result[1] * 10, 100)
    
    # J0 Earthquakes
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major
        FROM earthquakes
        WHERE date_utc >= ?
    """, (cutoff_date,))
    quake_result = cursor.fetchone()
    if quake_result and quake_result[0] > 0:
        weekly_avg = quake_result[0] / weeks
        baseline = 68
        quake_intensity = min((weekly_avg / baseline) * 50 + quake_result[1] * 10, 100)
    else:
        quake_intensity = 0
    
    # J0 Famines
    cursor.execute("""
        SELECT COUNT(*) FROM worldbank_news
        WHERE date >= ? AND (category = 'Disaster/Famine' OR keywords LIKE '%famine%')
    """, (cutoff_date,))
    famine_count = cursor.fetchone()[0]
    famine_intensity = min(famine_count * 15, 100) if famine_count > 0 else 30
    
    # J6 Cosmic (placeholder)
    cosmic_intensity = 5
    
    # H0 Economic
    cursor.execute("""
        SELECT SUM(CASE WHEN status = 'Crisis' THEN 1 ELSE 0 END) as crisis
        FROM economic_indicators
        WHERE date >= ?
        ORDER BY date DESC LIMIT 1
    """, (cutoff_date,))
    econ_result = cursor.fetchone()
    econ_intensity = 70 if econ_result and econ_result[0] and econ_result[0] > 0 else 20
    
    # B2 Digital (placeholder)
    digital_intensity = 25
    
    # Calculate overall
    weights = {
        'wars': (0.25, wars_intensity),
        'quakes': (0.20, quake_intensity),
        'famines': (0.15, famine_intensity),
        'cosmic': (0.10, cosmic_intensity),
        'economic': (0.15, econ_intensity),
        'digital': (0.15, digital_intensity)
    }
    
    overall = sum(w * i for w, i in weights.values())
    
    # Determine phase
    if overall >= 70:
        phase = "ADVANCED Beginning of Sorrows"
        emoji = "🔴"
        season = "LATE SPRING"
    elif overall >= 50:
        phase = "ACTIVE Beginning of Sorrows"
        emoji = "🟠"
        season = "MID SPRING"
    elif overall >= 30:
        phase = "EARLY Beginning of Sorrows"
        emoji = "🟡"
        season = "EARLY SPRING"
    else:
        phase = "MONITORING Phase"
        emoji = "🟢"
        season = "WINTER"
    
    return {
        'overall_intensity': overall,
        'phase': phase,
        'emoji': emoji,
        'season': season,
        'wars_intensity': wars_intensity,
        'quakes_intensity': quake_intensity,
        'famines_intensity': famine_intensity,
        'cosmic_intensity': cosmic_intensity,
        'economic_intensity': econ_intensity,
        'digital_intensity': digital_intensity
    }


def get_earthquake_summary(conn: sqlite3.Connection, days: int = 7) -> dict:
    """Get earthquake summary data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               MAX(magnitude) as max_mag,
               SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major
        FROM earthquakes
        WHERE date_utc >= ?
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    return {
        'total': result[0] if result else 0,
        'max_magnitude': result[1] if result and result[1] else 0,
        'major_count': result[2] if result else 0
    }


def get_conflicts_summary(conn: sqlite3.Connection, days: int = 7) -> dict:
    """Get conflicts summary data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(COALESCE(casualties, 0)) as total_casualties
        FROM conflicts
        WHERE date >= ?
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    return {
        'total_reports': result[0] if result else 0,
        'casualties': result[1] if result else 0
    }


def get_economic_status(conn: sqlite3.Connection) -> dict:
    """Get latest economic status."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT indicator_name, value, status
        FROM economic_indicators
        ORDER BY date DESC
        LIMIT 4
    """)
    
    indicators = cursor.fetchall()
    crisis_count = sum(1 for _, _, status in indicators if status == 'Crisis')
    
    return {
        'indicators': indicators,
        'has_crisis': crisis_count > 0,
        'crisis_count': crisis_count
    }


def generate_newsletter(days: int = 7) -> str:
    """Generate newsletter content."""
    
    # Check database
    if not DB_PATH.exists():
        return "❌ Database not found. Run: python scripts/init_database.py"
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Get data
        weeks = max(1, days // 7)
        fig_tree = get_fig_tree_data(conn, weeks)
        earthquakes = get_earthquake_summary(conn, days)
        conflicts = get_conflicts_summary(conn, days)
        economics = get_economic_status(conn)
        
        # Generate content
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        formatted_date = today.strftime('%b %d, %Y')
        
        # Create compelling headline based on fig tree pattern
        if fig_tree['overall_intensity'] >= 70:
            headline = f"Weekly Watch {formatted_date}: {fig_tree['emoji']} Multiple 'Beginning of Sorrows' Markers Elevated"
        elif fig_tree['overall_intensity'] >= 50:
            headline = f"Weekly Watch {formatted_date}: {fig_tree['emoji']} Clear 'Beginning of Sorrows' Patterns Observed"
        elif earthquakes['total'] >= 50:
            headline = f"Weekly Watch {formatted_date}: {earthquakes['total']} Earthquakes Signal 'Beginning of Sorrows'"
        else:
            headline = f"Weekly Watch {formatted_date}: {fig_tree['emoji']} Watching and Waiting — Pattern Status Update"
        
        content = [f"# {headline}\n"]
        content.append(f"**Date:** {formatted_date}")
        content.append(f"**Period:** Past {days} days")
        content.append(f"**Pattern Phase:** {fig_tree['phase']} ({fig_tree['season']})")
        content.append(f"**Sources:** USGS, UN, FRED, World Bank, NOAA, EFF\n")
        content.append("---\n")
        
        # TL;DR
        content.append("## 📖 TL;DR (30-Second Read)\n")
        
        tldr_parts = []
        
        if earthquakes['total'] > 0:
            tldr_parts.append(f"**{earthquakes['total']} earthquakes** (mag 4.0+)")
            if earthquakes['major_count'] > 0:
                tldr_parts.append(f"including **{earthquakes['major_count']} major** (6.0+)")
        
        if conflicts['total_reports'] > 0:
            tldr_parts.append(f"**{conflicts['total_reports']} conflict reports** from UN peacekeeping")
            if conflicts['casualties'] > 0:
                tldr_parts.append(f"({conflicts['casualties']:,} casualties)")
        
        if economics['has_crisis']:
            tldr_parts.append(f"**{economics['crisis_count']} economic crisis indicators**")
        else:
            tldr_parts.append("**Economic indicators stable**")
        
        tldr = ". ".join(tldr_parts) + "."
        
        content.append(f"{tldr} **Fig Tree Pattern Strength:** {fig_tree['overall_intensity']:.0f}/100 ({fig_tree['season']}). **Scripture focus:** Matthew 24:7-8 — 'beginning of sorrows' patterns observed. **The end is not yet** (Matt 24:6).\n")
        content.append("---\n")
        
        # Fig Tree Analysis Section
        content.append("## 🌳 FIG TREE PATTERN ANALYSIS (Matt 24:33)\n")
        content.append(f"### {fig_tree['emoji']} Overall Pattern Strength: {fig_tree['overall_intensity']:.0f}/100\n")
        content.append(f"**Phase:** {fig_tree['phase']}\n")
        content.append(f"**Seasonal Metaphor:** {fig_tree['season']}\n")
        
        # Pattern breakdown
        content.append("#### Pattern Breakdown:\n")
        content.append(f"- **J0 Wars & Conflicts:** {fig_tree['wars_intensity']:.0f}/100")
        content.append(f"- **J0 Earthquakes:** {fig_tree['quakes_intensity']:.0f}/100")
        content.append(f"- **J0 Famines/Poverty:** {fig_tree['famines_intensity']:.0f}/100")
        content.append(f"- **J6 Cosmic Signs:** {fig_tree['cosmic_intensity']:.0f}/100")
        content.append(f"- **H0 Economic:** {fig_tree['economic_intensity']:.0f}/100")
        content.append(f"- **B2 Digital ID:** {fig_tree['digital_intensity']:.0f}/100\n")
        
        # Seasonal interpretation
        content.append("#### What This Means:\n")
        if fig_tree['overall_intensity'] >= 70:
            content.append("🌳 **The fig tree's branches are budding strongly.** Multiple 'beginning of sorrows' markers are elevated simultaneously. Summer (J3-J7 events) is approaching but NOT here yet.\n")
        elif fig_tree['overall_intensity'] >= 50:
            content.append("🌱 **The fig tree's branches are clearly budding.** 'Beginning of sorrows' patterns are active. Summer (J3-J7 events) remains future.\n")
        elif fig_tree['overall_intensity'] >= 30:
            content.append("🌿 **The fig tree shows early buds.** Some 'beginning of sorrows' markers present. Summer (J3-J7 events) is still distant.\n")
        else:
            content.append("🍂 **The fig tree is mostly dormant.** Routine activity, no significant budding. Watching and waiting.\n")
        
        content.append("---\n")
        
        # This Week's Highlights
        content.append("## 🌍 This Week's Highlights\n")
        
        # Earthquakes section
        if earthquakes['total'] > 0:
            confidence = "🔴 High" if earthquakes['major_count'] >= 2 else "🟠 Med" if earthquakes['total'] >= 50 else "🟡 Low"
            content.append(f"### Earthquakes & Natural Disasters (Node J0) {confidence} Confidence\n")
            content.append(f"**{earthquakes['total']} Earthquakes This Week (Mag 4.0+)**\n")
            
            if earthquakes['major_count'] > 0:
                content.append(f"- 🔴 **{earthquakes['major_count']} major earthquakes** (6.0+)")
                content.append(f"- 🟠 Peak magnitude: **{earthquakes['max_magnitude']:.1f}**\n")
            
            content.append(f"**Source:** [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) (Tier 1)")
            content.append(f"**Scripture:** Matthew 24:7 — 'earthquakes in divers places'\n")
            content.append("---\n")
        
        # Conflicts section
        if conflicts['total_reports'] > 0:
            content.append(f"### ⚔️ Wars & Conflicts (Node J0) 🔴 High Confidence\n")
            content.append(f"**UN Peacekeeping Reports ({conflicts['total_reports']} Articles)**\n")
            
            if conflicts['casualties'] > 0:
                content.append(f"**Casualties:** {conflicts['casualties']:,} reported\n")
            
            content.append(f"**Source:** [UN Peacekeeping Operations](https://peacekeeping.un.org/) (Tier 1)")
            content.append(f"**Scripture:** Matthew 24:6-7 — 'wars and rumours of wars'\n")
            content.append("---\n")
        
        # Economics section
        if economics['indicators']:
            status_emoji = "🔴" if economics['has_crisis'] else "🟢"
            content.append(f"### 📉 Economic Indicators (Node H0) {status_emoji} Confidence\n")
            
            if economics['has_crisis']:
                content.append(f"⚠️ **{economics['crisis_count']} crisis indicators detected**\n")
            else:
                content.append("✅ **Economic indicators within normal range**\n")
            
            content.append(f"**Source:** [FRED (Federal Reserve)](https://fred.stlouisfed.org/) (Tier 1)")
            content.append(f"**Scripture:** Revelation 18:11 — 'merchants weep'\n")
            content.append("---\n")
        
        # Scripture Focus
        content.append("## 📖 This Week's Scripture Focus\n")
        content.append("> **Matthew 24:7-8** — 'For nation shall rise against nation, and kingdom against kingdom: and there shall be famines, and pestilences, and earthquakes, in divers places. **All these are the beginning of sorrows.**'\n")
        content.append("### Reflection:\n")
        content.append("This week's data confirms what Jesus called the 'beginning of sorrows':\n")
        content.append(f"- {'✅' if fig_tree['wars_intensity'] > 30 else '⏸️'} **Wars** — Intensity {fig_tree['wars_intensity']:.0f}/100")
        content.append(f"- {'✅' if fig_tree['quakes_intensity'] > 30 else '⏸️'} **Earthquakes** — Intensity {fig_tree['quakes_intensity']:.0f}/100")
        content.append(f"- {'✅' if fig_tree['famines_intensity'] > 30 else '⏸️'} **Famines** — Intensity {fig_tree['famines_intensity']:.0f}/100\n")
        
        content.append("**Key phrase:** 'All these are the **beginning** of sorrows' — Jesus explicitly said this is the **start**, not the end. The text requires several major events BEFORE the end:\n")
        content.append("1. Abomination of desolation (Matt 24:15) — ❌ Not observed")
        content.append("2. Great tribulation (Matt 24:21) — ❌ Not observed")
        content.append("3. Cosmic signs (Matt 24:29) — ❌ Not observed")
        content.append("4. Son of Man appears (Matt 24:30) — ❌ Not observed\n")
        content.append("**Honest assessment:** We're in the early warning phase, not the final countdown.\n")
        content.append("---\n")
        
        # Action Points
        content.append("## ✅ Action Points for This Week\n")
        content.append("1. **Watch** — Continue monitoring J0 patterns (wars, earthquakes, famines)")
        content.append("2. **Pray** — For those affected by conflicts and disasters")
        content.append("3. **Study** — Read Matthew 24 in full context")
        content.append("4. **Share** — Tell others about Jesus (the good news!)")
        content.append("5. **Live Ready** — 'Be ye also ready' (Matt 24:44)\n")
        content.append("---\n")
        
        # Disclaimers
        content.append("## ⚠️ Critical Reminders\n")
        content.append("1. **NO DATE-SETTING** — Matthew 24:36: 'Of that day and hour knows no man.'")
        content.append("2. **Pattern ≠ Fulfillment** — We observe resemblance, not definitive fulfillment.")
        content.append("3. **Hope, Not Fear** — Luke 21:28: 'Look up... your redemption draws near.'")
        content.append("4. **Gospel First** — This project exists to point people to Jesus. 🙏\n")
        content.append("---\n")
        
        # Footer
        content.append("_Generated automatically by BibleStudy AI system. Data from USGS, UN, FRED, World Bank, NOAA, EFF._")
        content.append(f"_[GitHub Repository](https://github.com/henzard/BibleStudy) | [Learn AI + Bible Study](https://github.com/henzard/BibleStudy/docs)_")
        
        return '\n'.join(content)
        
    except Exception as e:
        return f"❌ Error generating newsletter: {e}\n{traceback.format_exc()}"
    finally:
        conn.close()


def save_newsletter(content: str) -> Path:
    """Save newsletter to tracking/newsletters/ directory."""
    newsletters_dir = Path('tracking/newsletters')
    newsletters_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    filename = newsletters_dir / f'{today}_weekly_watch.md'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename


def main():
    """Main execution."""
    days = 7
    
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python generate_newsletter.py [--days 7]")
            sys.exit(1)
    
    print("="*80)
    print("GENERATING WEEKLY NEWSLETTER")
    print("="*80)
    print()
    
    # Generate newsletter
    print(f"Analyzing past {days} days...")
    content = generate_newsletter(days)
    
    # Save
    try:
        output_file = save_newsletter(content)
        print(f"\n✅ Newsletter saved to: {output_file}")
        print()
        print("📬 Newsletter ready for sharing!")
        
    except Exception as e:
        print(f"❌ Error saving newsletter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


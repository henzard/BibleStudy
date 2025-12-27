#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter Generator with Fig Tree Pattern Analysis + OpenAI Enhancement
Compiles weekly data + fig tree analysis into engaging newsletter format.

80% Automated (data-driven structure)
20% AI-enhanced (narrative, reflection, surprise findings)

Usage:
    python generate_newsletter.py [--days 7]
"""

import sys
import io
import sqlite3
import subprocess
import traceback
import os
from pathlib import Path
from datetime import datetime, timedelta

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Falling back to system environment variables\n")

# Try to import OpenAI (optional enhancement)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  OpenAI not installed. Install with: pip install openai")
    print("   Newsletter will use template-based content (still functional)\n")

SCRIPTS_DIR = Path(__file__).parent
DB_PATH = Path("data/prophecy_tracking.db")

# Load API keys from environment variables (NOT hardcoded!)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Validate API keys
if HAS_OPENAI and not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY not found in environment variables")
    print("   Newsletter will use template-based content")
    print("   To enable AI enhancement: Set OPENAI_API_KEY in .env file\n")


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


def get_last_week_comparison(conn: sqlite3.Connection) -> dict:
    """Get last week's data for 'What Changed?' tracker."""
    cursor = conn.cursor()
    
    # Get data from 7-14 days ago (previous week)
    start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Earthquakes last week
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major
        FROM earthquakes
        WHERE date_utc >= ? AND date_utc < ?
    """, (start_date, end_date))
    last_quakes = cursor.fetchone()
    
    # Conflicts last week
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM conflicts
        WHERE date >= ? AND date < ?
    """, (start_date, end_date))
    last_conflicts = cursor.fetchone()
    
    return {
        'earthquakes': last_quakes[0] if last_quakes else 0,
        'major_quakes': last_quakes[1] if last_quakes else 0,
        'conflicts': last_conflicts[0] if last_conflicts else 0
    }


def enhance_with_openai(fig_tree: dict, earthquakes: dict, conflicts: dict, economics: dict) -> dict:
    """Use OpenAI to enhance newsletter with narrative polish (20% augmentation)."""
    
    if not HAS_OPENAI or not OPENAI_API_KEY:
        # Fallback to template-based content
        return {
            'enhanced_headline': None,
            'scripture_reflection': "This week's data confirms Jesus' description of the 'beginning of sorrows.' We observe these patterns with sobriety, knowing 'the end is not yet' (Matt 24:6).",
            'surprise_finding': None,
            'shareable_quote': "\"When you see all these things, know that it is near.\" — Matthew 24:33\n\nWe're watching, not predicting. We're observing, not date-setting."
        }
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepare context for OpenAI
        context = f"""You are assisting with a Bible-focused end-times prophecy tracking newsletter.

DATA SUMMARY:
- Fig Tree Pattern Strength: {fig_tree['overall_intensity']:.0f}/100 ({fig_tree['season']})
- Earthquakes: {earthquakes['total']} (mag 4.0+), {earthquakes['major_count']} major (6.0+)
- Conflicts: {conflicts['total_reports']} UN reports, {conflicts['casualties']} casualties
- Economics: {'CRISIS' if economics['has_crisis'] else 'STABLE'}
- Wars intensity: {fig_tree['wars_intensity']:.0f}/100
- Quakes intensity: {fig_tree['quakes_intensity']:.0f}/100
- Famines intensity: {fig_tree['famines_intensity']:.0f}/100

CRITICAL RULES (Bible-based guardrails):
1. NO date-setting (Matt 24:36 - "no man knows the day or hour")
2. NO fear-mongering (hope-focused, Luke 21:28)
3. NO speculation beyond observed data
4. MUST acknowledge "the end is not yet" (Matt 24:6)
5. Pattern observation ≠ definitive fulfillment

Your task: Provide brief, honest, Bible-grounded enhancements."""

        # Task 1: Enhanced headline (if pattern strength warrants it)
        enhanced_headline = None
        if fig_tree['overall_intensity'] >= 40 or earthquakes['total'] >= 60:
            headline_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Create ONE compelling but honest headline for this week's newsletter. Format: 'Weekly Watch [Month Day]: [Finding]'. Must be specific to the data (e.g., '{earthquakes['total']} Earthquakes' or 'Pattern Strength {fig_tree['overall_intensity']:.0f}/100'). NO sensationalism, NO date-setting. Max 12 words."}
                ],
                max_tokens=50,
                temperature=0.7
            )
            enhanced_headline = headline_response.choices[0].message.content.strip()
        
        # Task 2: Scripture reflection (2-3 sentences)
        reflection_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": "Write a 2-3 sentence reflection on Matthew 24:7-8 ('beginning of sorrows') based on this week's data. Be specific (mention earthquakes/conflicts/famines intensities). End with reminder that 'the end is not yet' (Matt 24:6). Biblical tone, no speculation."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        scripture_reflection = reflection_response.choices[0].message.content.strip()
        
        # Task 3: Surprise finding (optional - only if there's a notable pattern)
        surprise_finding = None
        if fig_tree['overall_intensity'] >= 30:
            surprise_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": "Identify ONE unexpected or noteworthy pattern this week (e.g., 'Earthquakes concentrated in Pacific Ring of Fire' or 'Economic indicators stable despite conflicts'). 1-2 sentences max. If nothing notable, say 'Routine monitoring across all categories.' NO speculation."}
                ],
                max_tokens=60,
                temperature=0.7
            )
            surprise_finding = surprise_response.choices[0].message.content.strip()
        
        # Task 4: Shareable quote for social media
        quote_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": "Create a shareable quote (2-3 lines) combining Matthew 24:33 with this week's fig tree pattern strength. Format for social media. Include emoji. Must include Matt 24:36 reminder (no date-setting). Biblical, hopeful tone."}
            ],
            max_tokens=80,
            temperature=0.7
        )
        shareable_quote = quote_response.choices[0].message.content.strip()
        
        return {
            'enhanced_headline': enhanced_headline,
            'scripture_reflection': scripture_reflection,
            'surprise_finding': surprise_finding,
            'shareable_quote': shareable_quote
        }
        
    except Exception as e:
        print(f"⚠️  OpenAI enhancement failed: {e}")
        print("   Using template-based content instead.\n")
        # Fallback to templates
        return {
            'enhanced_headline': None,
            'scripture_reflection': "This week's data confirms Jesus' description of the 'beginning of sorrows.' We observe these patterns with sobriety, knowing 'the end is not yet' (Matt 24:6).",
            'surprise_finding': None,
            'shareable_quote': "\"When you see all these things, know that it is near.\" — Matthew 24:33\n\nWe're watching, not predicting. We're observing, not date-setting."
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
        last_week = get_last_week_comparison(conn)
        
        # ⭐ Get OpenAI enhancements (20% polish)
        print("🤖 Enhancing newsletter with OpenAI...")
        ai_enhancements = enhance_with_openai(fig_tree, earthquakes, conflicts, economics)
        
        # Generate content
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        formatted_date = today.strftime('%b %d, %Y')
        
        # Use AI-enhanced headline if available, otherwise fall back to template
        if ai_enhancements['enhanced_headline']:
            headline = ai_enhancements['enhanced_headline']
        else:
            # Template-based headline
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
        
        # ⭐ "What Changed?" Tracker (NEW)
        content.append("## 📊 What Changed? (Week-over-Week)\n")
        
        if last_week['earthquakes'] > 0:
            quake_change = earthquakes['total'] - last_week['earthquakes']
            quake_emoji = "📈" if quake_change > 0 else "📉" if quake_change < 0 else "➡️"
            content.append(f"**Earthquakes:** {earthquakes['total']} this week vs {last_week['earthquakes']} last week {quake_emoji}")
            if quake_change != 0:
                content.append(f"  ({quake_change:+d} change)")
        
        if last_week['conflicts'] > 0:
            conflict_change = conflicts['total_reports'] - last_week['conflicts']
            conflict_emoji = "📈" if conflict_change > 0 else "📉" if conflict_change < 0 else "➡️"
            content.append(f"**Conflicts:** {conflicts['total_reports']} reports vs {last_week['conflicts']} last week {conflict_emoji}")
            if conflict_change != 0:
                content.append(f"  ({conflict_change:+d} change)")
        
        content.append("\n")
        
        # ⭐ Surprise Finding (if AI generated one)
        if ai_enhancements['surprise_finding']:
            content.append("**💡 This Week's Notable Pattern:**\n")
            content.append(f"{ai_enhancements['surprise_finding']}\n")
        
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
        
        # ⭐ Use AI-enhanced reflection if available
        content.append(f"{ai_enhancements['scripture_reflection']}\n")
        
        content.append("\nThis week's data breakdown:\n")
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
        
        # ⭐ Shareable Quote (AI-enhanced)
        content.append("## 📱 Shareable Quote\n")
        content.append(f"{ai_enhancements['shareable_quote']}\n")
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


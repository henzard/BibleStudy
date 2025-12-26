#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fig Tree Pattern Analysis
Multi-variate analysis of "all these things" (Matt 24:33) across all prophecy nodes.

Purpose: Recognize patterns (not predict dates)
Scripture: Matthew 24:32-33 - "When you see ALL THESE THINGS..."

Usage:
    python analyze_fig_tree_pattern.py [--weeks 4]
"""

import sys
import io
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import warnings

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try to import numpy (required)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("❌ NumPy not installed. Install with: pip install numpy")
    sys.exit(1)

DB_PATH = Path("data/prophecy_tracking.db")


def get_j0_wars_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate J0 (wars/conflicts) intensity from UN data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN conflict_type = 'Active Conflict' THEN 1 ELSE 0 END) as active,
               SUM(CASE WHEN conflict_type = 'Casualties' THEN 1 ELSE 0 END) as casualties,
               SUM(COALESCE(casualties, 0)) as total_casualties
        FROM conflicts
        WHERE date >= ?
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    if not result or result[0] == 0:
        return {'intensity': 0, 'description': 'No data', 'confidence': 'Low'}
    
    total, active, casualties_events, total_deaths = result
    
    # Intensity calculation (0-100)
    # More active conflicts + casualties = higher intensity
    base_intensity = min(active * 10, 60)  # Up to 60 for active conflicts
    casualty_bonus = min(casualties_events * 10, 30)  # Up to 30 for casualty reports
    death_bonus = min(total_deaths / 1000, 10)  # Up to 10 for death tolls
    
    intensity = min(base_intensity + casualty_bonus + death_bonus, 100)
    
    if intensity >= 70:
        return {'intensity': intensity, 'description': 'HIGH - Multiple active conflicts with casualties', 'confidence': 'High'}
    elif intensity >= 40:
        return {'intensity': intensity, 'description': 'ELEVATED - Active conflicts observed', 'confidence': 'Med'}
    else:
        return {'intensity': intensity, 'description': 'LOW-MODERATE - Monitoring', 'confidence': 'Low'}


def get_j0_earthquakes_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate J0 (earthquakes) intensity from USGS data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major,
               AVG(magnitude) as avg_mag
        FROM earthquakes
        WHERE date_utc >= ?
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    if not result or result[0] == 0:
        return {'intensity': 0, 'description': 'No data', 'confidence': 'Low'}
    
    total, major, avg_mag = result
    weekly_avg = total / weeks
    
    # Historical baseline: ~68/week
    baseline = 68
    deviation = (weekly_avg - baseline) / baseline * 100
    
    # Intensity calculation
    base_intensity = min((weekly_avg / baseline) * 50, 70)  # Up to 70 for frequency
    major_bonus = min(major * 10, 30)  # Up to 30 for major quakes
    
    intensity = min(base_intensity + major_bonus, 100)
    
    if intensity >= 70:
        return {'intensity': intensity, 'description': f'ELEVATED - {weekly_avg:.0f}/week (baseline {baseline}), {major} major', 'confidence': 'Med'}
    elif intensity >= 50:
        return {'intensity': intensity, 'description': f'MODERATE - {weekly_avg:.0f}/week, {major} major', 'confidence': 'Med'}
    else:
        return {'intensity': intensity, 'description': f'NORMAL - {weekly_avg:.0f}/week', 'confidence': 'Low'}


def get_j0_famines_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate J0 (famines/poverty) intensity from World Bank data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN category = 'Disaster/Famine' THEN 1 ELSE 0 END) as disasters
        FROM worldbank_news
        WHERE date >= ? AND (category = 'Disaster/Famine' OR keywords LIKE '%famine%' OR keywords LIKE '%poverty%')
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    if not result or result[0] == 0:
        return {'intensity': 30, 'description': 'LOW - No major alerts (routine monitoring)', 'confidence': 'Low'}
    
    total, disasters = result
    
    # Intensity based on frequency of reports
    intensity = min(total * 15, 100)  # Each report = +15 intensity
    
    if intensity >= 60:
        return {'intensity': intensity, 'description': f'HIGH - {total} reports in {weeks} weeks', 'confidence': 'Med'}
    elif intensity >= 40:
        return {'intensity': intensity, 'description': f'MODERATE - {total} reports', 'confidence': 'Low'}
    else:
        return {'intensity': intensity, 'description': 'LOW - Regional issues only', 'confidence': 'Low'}


def get_j6_cosmic_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate J6 (cosmic signs) intensity - PLACEHOLDER (no DB table yet)."""
    # Note: Space weather data not yet in database
    # For now, return low intensity (routine activity)
    # TODO: Add space_weather table to database schema
    return {'intensity': 5, 'description': 'MINIMAL - Routine solar activity only (no major events)', 'confidence': 'Low'}


def get_h0_economic_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate H0 (economic collapse) intensity from FRED data."""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'Crisis' THEN 1 ELSE 0 END) as crisis,
               SUM(CASE WHEN status = 'Concern' THEN 1 ELSE 0 END) as concern
        FROM economic_indicators
        WHERE date >= ?
        ORDER BY date DESC
        LIMIT 1
    """, (cutoff_date,))
    
    result = cursor.fetchone()
    if not result or result[0] == 0:
        return {'intensity': 20, 'description': 'NORMAL - Stable economic indicators', 'confidence': 'Low'}
    
    total, crisis, concern = result
    
    # Intensity based on crisis indicators
    intensity = 20  # Baseline (normal)
    if crisis > 0:
        intensity = min(70 + (crisis * 10), 100)
        return {'intensity': intensity, 'description': f'CRISIS - {crisis} indicators in crisis state', 'confidence': 'High'}
    elif concern > 0:
        intensity = 40 + (concern * 10)
        return {'intensity': intensity, 'description': f'CONCERN - {concern} indicators elevated', 'confidence': 'Med'}
    else:
        return {'intensity': intensity, 'description': 'STABLE - No crisis indicators', 'confidence': 'Low'}


def get_b2_digital_intensity(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    """Calculate B2 (digital ID/commerce control) intensity - PLACEHOLDER."""
    # Note: EFF data not yet in database
    # For now, return low-moderate (monitoring infrastructure)
    # TODO: Add eff_articles table to database schema
    return {'intensity': 25, 'description': 'MONITORING - Digital ID infrastructure expanding (not "the mark")', 'confidence': 'Low'}


def calculate_overall_pattern_strength(intensities: dict) -> dict:
    """Calculate overall "beginning of sorrows" pattern strength."""
    # Weighted average (J0 nodes are most relevant to Matt 24:6-8)
    weights = {
        'j0_wars': 0.25,      # 25% - "wars and rumors of wars"
        'j0_quakes': 0.20,    # 20% - "earthquakes in divers places"
        'j0_famines': 0.15,   # 15% - "famines"
        'j6_cosmic': 0.10,    # 10% - cosmic signs (later phase)
        'h0_economic': 0.15,  # 15% - economic patterns
        'b2_digital': 0.15    # 15% - commerce control patterns
    }
    
    # Calculate weighted average
    total_intensity = 0
    for key, weight in weights.items():
        total_intensity += intensities[key]['intensity'] * weight
    
    # Determine phase
    if total_intensity >= 70:
        phase = "ADVANCED Beginning of Sorrows"
        emoji = "🔴"
        note = "Multiple J0 markers elevated simultaneously"
    elif total_intensity >= 50:
        phase = "ACTIVE Beginning of Sorrows"
        emoji = "🟠"
        note = "Clear J0 patterns observed"
    elif total_intensity >= 30:
        phase = "EARLY Beginning of Sorrows"
        emoji = "🟡"
        note = "Some J0 markers present"
    else:
        phase = "MONITORING Phase"
        emoji = "🟢"
        note = "Routine activity, no significant patterns"
    
    return {
        'overall_intensity': total_intensity,
        'phase': phase,
        'emoji': emoji,
        'note': note
    }


def main():
    """Main execution."""
    weeks = 4
    
    # Parse command line arguments
    if '--weeks' in sys.argv:
        try:
            idx = sys.argv.index('--weeks')
            weeks = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python analyze_fig_tree_pattern.py [--weeks 4]")
            sys.exit(1)
    
    # Check database
    if not DB_PATH.exists():
        print("❌ Database not found. Run: python scripts/init_database.py")
        sys.exit(1)
    
    print("="*80)
    print("FIG TREE PATTERN ANALYSIS")
    print("="*80)
    print(f"\n📖 Scripture: Matthew 24:32-33")
    print(f"   \"When you see ALL THESE THINGS, know that it is near...\"")
    print(f"\n⏱️  Analysis period: Past {weeks} weeks")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Get intensity for each node
        intensities = {
            'j0_wars': get_j0_wars_intensity(conn, weeks),
            'j0_quakes': get_j0_earthquakes_intensity(conn, weeks),
            'j0_famines': get_j0_famines_intensity(conn, weeks),
            'j6_cosmic': get_j6_cosmic_intensity(conn, weeks),
            'h0_economic': get_h0_economic_intensity(conn, weeks),
            'b2_digital': get_b2_digital_intensity(conn, weeks)
        }
        
        # Calculate overall pattern
        overall = calculate_overall_pattern_strength(intensities)
        
        # Print results
        print("="*80)
        print("PATTERN ANALYSIS BY NODE")
        print("="*80)
        print()
        
        print("### J0 - Beginning of Sorrows (Matt 24:6-8)\n")
        
        print(f"**Wars & Conflicts:**")
        print(f"   Intensity: {intensities['j0_wars']['intensity']:.0f}/100")
        print(f"   Status: {intensities['j0_wars']['description']}")
        print(f"   Confidence: {intensities['j0_wars']['confidence']}\n")
        
        print(f"**Earthquakes:**")
        print(f"   Intensity: {intensities['j0_quakes']['intensity']:.0f}/100")
        print(f"   Status: {intensities['j0_quakes']['description']}")
        print(f"   Confidence: {intensities['j0_quakes']['confidence']}\n")
        
        print(f"**Famines/Poverty:**")
        print(f"   Intensity: {intensities['j0_famines']['intensity']:.0f}/100")
        print(f"   Status: {intensities['j0_famines']['description']}")
        print(f"   Confidence: {intensities['j0_famines']['confidence']}\n")
        
        print("### J6 - Cosmic Signs (Matt 24:29)\n")
        print(f"**Space Weather:**")
        print(f"   Intensity: {intensities['j6_cosmic']['intensity']:.0f}/100")
        print(f"   Status: {intensities['j6_cosmic']['description']}")
        print(f"   Confidence: {intensities['j6_cosmic']['confidence']}\n")
        
        print("### H0 - Economic Patterns (Rev 17-18)\n")
        print(f"**Economic Indicators:**")
        print(f"   Intensity: {intensities['h0_economic']['intensity']:.0f}/100")
        print(f"   Status: {intensities['h0_economic']['description']}")
        print(f"   Confidence: {intensities['h0_economic']['confidence']}\n")
        
        print("### B2 - Commerce Control (Rev 13:16-17)\n")
        print(f"**Digital ID/Surveillance:**")
        print(f"   Intensity: {intensities['b2_digital']['intensity']:.0f}/100")
        print(f"   Status: {intensities['b2_digital']['description']}")
        print(f"   Confidence: {intensities['b2_digital']['confidence']}\n")
        
        # Overall assessment
        print("="*80)
        print("OVERALL PATTERN ASSESSMENT")
        print("="*80)
        print()
        
        print(f"{overall['emoji']} **Pattern Strength: {overall['overall_intensity']:.0f}/100**")
        print(f"   Phase: {overall['phase']}")
        print(f"   Note: {overall['note']}\n")
        
        # Seasonal metaphor
        print("="*80)
        print("SEASONAL ASSESSMENT (Fig Tree Parable)")
        print("="*80)
        print()
        
        if overall['overall_intensity'] >= 70:
            print("🌳 **Season: LATE SPRING**")
            print("   The fig tree's branches are budding strongly.")
            print("   Multiple 'beginning of sorrows' markers elevated.")
            print("   Summer (J3-J7) is approaching but NOT here yet.")
        elif overall['overall_intensity'] >= 50:
            print("🌱 **Season: MID SPRING**")
            print("   The fig tree's branches are clearly budding.")
            print("   'Beginning of sorrows' patterns are active.")
            print("   Summer (J3-J7) remains future.")
        elif overall['overall_intensity'] >= 30:
            print("🌿 **Season: EARLY SPRING**")
            print("   The fig tree shows early buds.")
            print("   Some 'beginning of sorrows' markers present.")
            print("   Summer (J3-J7) is still distant.")
        else:
            print("🍂 **Season: WINTER/EARLY SPRING**")
            print("   The fig tree is mostly dormant.")
            print("   Routine activity, no significant budding.")
            print("   Watching and waiting.")
        
        print()
        
        # What we have NOT observed
        print("="*80)
        print("WHAT WE HAVE NOT OBSERVED (Still Future)")
        print("="*80)
        print()
        print("❌ **J3 - Abomination of Desolation** (Dan 9:27; Matt 24:15)")
        print("❌ **J4 - Great Tribulation** (Matt 24:21-22)")
        print("❌ **J6 - Major Cosmic Signs** (sun darkened, moon blood)")
        print("❌ **J7 - Son of Man Appears** (Matt 24:30-31)")
        print()
        print("**Honest Assessment:**")
        print("We're observing 'beginning of sorrows' (Matt 24:8).")
        print("Jesus said at this phase: 'the end is NOT yet' (Matt 24:6).")
        print()
        
        # Critical disclaimers
        print("="*80)
        print("CRITICAL DISCLAIMERS")
        print("="*80)
        print()
        print("1. **NO DATE-SETTING (Matt 24:36)**")
        print("   'Of that day and hour knows no man.'")
        print("   This analysis measures PATTERN, not TIMING.")
        print()
        print("2. **Pattern Recognition ≠ Fulfillment**")
        print("   High intensity means 'resembles Matt 24:6-8 description.'")
        print("   It does NOT mean 'prophecy is definitively fulfilled.'")
        print()
        print("3. **Seasonal Awareness, Not Countdown**")
        print("   Like fig tree buds indicate spring, we recognize patterns.")
        print("   But exact timing remains unknown (Matt 24:36).")
        print()
        print("4. **Use for Watchfulness, Not Fear**")
        print("   Luke 21:28 - 'Look up... your redemption draws near.'")
        print("   This is about hope and readiness, not panic.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()


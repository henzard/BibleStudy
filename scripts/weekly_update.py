#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weekly News Update - Master Script
Runs all automation scripts and compiles results into a single weekly review.

Usage:
    python weekly_update.py [--days 7]
    
Output:
    - Runs all 5 automation scripts
    - Generates tracking/weekly-reviews/YYYY-MM-DD.md with compiled results
    - Shows summary statistics
"""

import sys
import io
import subprocess
from datetime import datetime
from pathlib import Path

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Script directory
SCRIPTS_DIR = Path(__file__).parent

# Available automation scripts
SCRIPTS = {
    'earthquakes': {
        'file': 'fetch_earthquakes.py',
        'name': 'USGS Earthquakes',
        'node': 'J0',
        'scripture': 'Matt 24:7-8'
    },
    'gdacs': {
        'file': 'fetch_gdacs.py',
        'name': 'GDACS Multi-Hazard',
        'node': 'J0',
        'scripture': 'Matt 24:7-8'
    },
    'worldbank': {
        'file': 'fetch_worldbank_news.py',
        'name': 'World Bank News',
        'node': 'J0/H0',
        'scripture': 'Matt 24:7-8 / Rev 17-18'
    },
    'un_peacekeeping': {
        'file': 'fetch_un_peacekeeping.py',
        'name': 'UN Peacekeeping',
        'node': 'J0',
        'scripture': 'Matt 24:6-7'
    },
    'fred_news': {
        'file': 'fetch_fred_news.py',
        'name': 'FRED Economic News',
        'node': 'H0',
        'scripture': 'Rev 17-18'
    },
    'economic': {
        'file': 'fetch_economic.py',
        'name': 'FRED Economic Data',
        'node': 'H0',
        'scripture': 'Rev 17-18'
    },
    'spaceweather': {
        'file': 'fetch_spaceweather.py',
        'name': 'NOAA Space Weather',
        'node': 'J6',
        'scripture': 'Matt 24:29 / Luke 21:25'
    },
    'eff_news': {
        'file': 'fetch_eff_news.py',
        'name': 'EFF Digital Rights',
        'node': 'B2',
        'scripture': 'Rev 13:16-17'
    }
}


def run_script(script_key: str, days: int = 7) -> dict:
    """Run a single automation script and capture output."""
    script_info = SCRIPTS[script_key]
    script_path = SCRIPTS_DIR / script_info['file']
    
    print(f"Running {script_info['name']}...", flush=True)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), '--days', str(days)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'name': script_info['name'],
            'node': script_info['node'],
            'scripture': script_info['scripture']
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Script timeout (30s)',
            'name': script_info['name'],
            'node': script_info['node'],
            'scripture': script_info['scripture']
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'name': script_info['name'],
            'node': script_info['node'],
            'scripture': script_info['scripture']
        }


def compile_weekly_review(results: dict, days: int) -> str:
    """Compile all results into a weekly review markdown."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    output = [f"# Weekly Prophecy Tracking Review — {today}\n"]
    output.append(f"**Period:** Past {days} days")
    output.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    output.append(f"**Scripts run:** {len(results)}\n")
    
    output.append("---\n")
    
    # Summary statistics
    successful = sum(1 for r in results.values() if r['success'])
    output.append(f"## 📊 Summary\n")
    output.append(f"- **Scripts executed:** {len(results)}")
    output.append(f"- **Successful:** {successful}")
    output.append(f"- **Failed:** {len(results) - successful}\n")
    
    output.append("---\n")
    
    # Results by category
    output.append("## 🌍 Results by Category\n")
    
    for key, result in results.items():
        script_info = SCRIPTS[key]
        output.append(f"### {script_info['name']}")
        output.append(f"**Node:** {script_info['node']} | **Scripture:** {script_info['scripture']}\n")
        
        if result['success']:
            output.append("✅ **Status:** Success\n")
            output.append("```")
            # Extract just the key parts (skip "Fetching..." line)
            lines = result['output'].split('\n')
            relevant_lines = [line for line in lines if line.strip() and not line.startswith('Fetching')]
            output.append('\n'.join(relevant_lines[:50]))  # First 50 lines
            if len(relevant_lines) > 50:
                output.append(f"\n... ({len(relevant_lines) - 50} more lines)")
            output.append("```\n")
        else:
            output.append(f"❌ **Status:** Failed")
            output.append(f"**Error:** {result['error']}\n")
        
        output.append("---\n")
    
    # Next steps
    output.append("## 📋 Next Steps\n")
    output.append("1. Review classification tables above")
    output.append("2. Cross-verify High confidence items with multiple sources")
    output.append("3. Copy relevant items to `tracking/DAILY_NEWS_LOG.md`")
    output.append("4. Update `tracking/END_TIMES_TODO.md` if any boxes should be checked")
    output.append("5. Pray and ask God for wisdom (James 1:5)\n")
    
    # Scripture reminder
    output.append("---\n")
    output.append("## 📖 Scripture Reminder\n")
    output.append("> **Matthew 24:36** — \"But of that day and hour knoweth no man, no, not the angels of heaven, but my Father only.\"\n")
    output.append("> **1 Thessalonians 5:21** — \"Prove all things; hold fast that which is good.\"\n")
    output.append("> **Matthew 24:4** — \"Take heed that no man deceive you.\"\n")
    
    return '\n'.join(output)


def save_weekly_review(content: str) -> Path:
    """Save weekly review to tracking/weekly-reviews/ directory."""
    # Create directory if it doesn't exist
    reviews_dir = Path('tracking/weekly-reviews')
    reviews_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    today = datetime.now().strftime('%Y-%m-%d')
    filename = reviews_dir / f'{today}_weekly_review.md'
    
    # Save file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename


def main():
    """Main execution."""
    days = 7
    
    # Parse command line arguments
    if '--days' in sys.argv:
        try:
            idx = sys.argv.index('--days')
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python weekly_update.py [--days 7]")
            sys.exit(1)
    
    print("="*80)
    print(f"WEEKLY PROPHECY TRACKING UPDATE — Past {days} days")
    print("="*80)
    print()
    
    # Run all scripts
    results = {}
    for key in SCRIPTS.keys():
        results[key] = run_script(key, days)
        print()  # Blank line between scripts
    
    print("="*80)
    print("COMPILATION COMPLETE")
    print("="*80)
    print()
    
    # Compile results
    print("Generating weekly review markdown...")
    review_content = compile_weekly_review(results, days)
    
    # Save to file
    try:
        output_file = save_weekly_review(review_content)
        print(f"✅ Weekly review saved to: {output_file}")
        print()
        
        # Print summary
        successful = sum(1 for r in results.values() if r['success'])
        print(f"📊 Summary:")
        print(f"   - Scripts run: {len(results)}")
        print(f"   - Successful: {successful}")
        print(f"   - Failed: {len(results) - successful}")
        
        if successful < len(results):
            print()
            print("⚠️  Some scripts failed. Check the weekly review file for details.")
        
        print()
        print(f"📖 Next: Review {output_file} and update tracking files")
        print()
        
        # Run Fig Tree Pattern Analysis
        print("="*80)
        print("RUNNING FIG TREE PATTERN ANALYSIS")
        print("="*80)
        print()
        
        fig_tree_script = SCRIPTS_DIR / 'analyze_fig_tree_pattern.py'
        weeks = max(1, days // 7)  # Convert days to weeks (min 1)
        
        try:
            result = subprocess.run(
                [sys.executable, str(fig_tree_script), '--weeks', str(weeks)],
                text=True,
                encoding='utf-8',
                timeout=30
            )
            print()
            print("✅ Fig tree pattern analysis complete!")
        except Exception as e:
            print(f"⚠️  Fig tree analysis failed: {e}")
        
        print()
        
        # Generate Newsletter with Fig Tree Analysis
        print("="*80)
        print("GENERATING WEEKLY NEWSLETTER")
        print("="*80)
        print()
        
        newsletter_script = SCRIPTS_DIR / 'generate_newsletter.py'
        
        try:
            result = subprocess.run(
                [sys.executable, str(newsletter_script), '--days', str(days)],
                text=True,
                encoding='utf-8',
                timeout=30
            )
            print()
            print("✅ Newsletter generation complete!")
            print()
            print("📬 Your weekly newsletter is ready in tracking/newsletters/")
        except Exception as e:
            print(f"⚠️  Newsletter generation failed: {e}")
        
    except Exception as e:
        print(f"❌ Error saving weekly review: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


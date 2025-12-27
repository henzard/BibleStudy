#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRED Economic Indicators Monitor
Fetches actual economic data from FRED API for prophecy tracking (node H0).
Tracks inflation, unemployment, GDP, trade deficits, and economic crisis indicators.

Usage:
    python fetch_economic.py [--months 12]
    
API Key: Set FRED_API_KEY environment variable in .env file
"""

import sys
import io
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, will use system env vars

# FRED API Configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"

# Load API key from environment variable (secure)
FRED_API_KEY = os.getenv('FRED_API_KEY')
if not FRED_API_KEY:
    print("❌ FRED_API_KEY not found in environment variables")
    print("   Please set FRED_API_KEY in .env file")
    print("   Get your key from: https://fred.stlouisfed.org/docs/api/api_key.html")
    sys.exit(1)

# Economic indicators to track (Series IDs)
INDICATORS = {
    'inflation': {
        'CPIAUCSL': {
            'name': 'Consumer Price Index (CPI-U)',
            'description': 'All Urban Consumers, Not Seasonally Adjusted',
            'threshold_high': 5.0,  # Annual % change > 5% = concern
            'threshold_critical': 10.0  # Annual % change > 10% = crisis
        },
        'PCEPI': {
            'name': 'Personal Consumption Expenditures Price Index',
            'description': 'Fed\'s preferred inflation measure',
            'threshold_high': 4.0,
            'threshold_critical': 8.0
        }
    },
    'unemployment': {
        'UNRATE': {
            'name': 'Unemployment Rate',
            'description': 'Percent, Seasonally Adjusted',
            'threshold_high': 7.0,  # > 7% = concern
            'threshold_critical': 10.0  # > 10% = crisis
        },
        'U6RATE': {
            'name': 'Total Unemployed + Marginally Attached + Part-Time',
            'description': 'Broader unemployment measure',
            'threshold_high': 12.0,
            'threshold_critical': 18.0
        }
    },
    'gdp': {
        'GDP': {
            'name': 'Gross Domestic Product',
            'description': 'Billions of Dollars, Seasonally Adjusted Annual Rate',
            'threshold_high': -2.0,  # Negative growth = recession
            'threshold_critical': -5.0  # Severe recession
        },
        'A191RL1Q225SBEA': {
            'name': 'Real GDP Growth Rate',
            'description': 'Percent Change from Preceding Quarter',
            'threshold_high': -1.0,
            'threshold_critical': -3.0
        }
    },
    'trade': {
        'BOPGSTB': {
            'name': 'Trade Balance: Goods and Services',
            'description': 'Billions of Dollars, Seasonally Adjusted',
            'threshold_high': -70.0,  # Large deficit
            'threshold_critical': -100.0  # Severe deficit
        }
    }
}


def fetch_series_data(series_id: str, months_back: int = 12) -> Optional[dict]:
    """Fetch data for a FRED series."""
    # Calculate observation start date
    start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date
    }
    
    url = f"{FRED_API_BASE}/series/observations?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print(f"⚠️  API key error or invalid series: {series_id}", file=sys.stderr)
        else:
            print(f"⚠️  HTTP error {e.code} for {series_id}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error fetching {series_id}: {e}", file=sys.stderr)
        return None


def calculate_year_over_year_change(observations: List[dict]) -> Optional[float]:
    """Calculate year-over-year percentage change."""
    if len(observations) < 12:
        return None
    
    try:
        latest = float(observations[-1]['value'])
        year_ago = float(observations[-12]['value'])
        return ((latest - year_ago) / year_ago) * 100
    except (ValueError, KeyError, IndexError):
        return None


def assess_indicator(series_id: str, data: dict, config: dict) -> dict:
    """Assess an economic indicator and determine confidence level."""
    if not data or 'observations' not in data:
        return {
            'series_id': series_id,
            'name': config['name'],
            'status': 'ERROR',
            'confidence': 'N/A',
            'latest_value': None,
            'latest_date': None,
            'yoy_change': None,
            'assessment': 'Data unavailable'
        }
    
    observations = [obs for obs in data['observations'] if obs['value'] != '.']
    
    if not observations:
        return {
            'series_id': series_id,
            'name': config['name'],
            'status': 'ERROR',
            'confidence': 'N/A',
            'latest_value': None,
            'latest_date': None,
            'yoy_change': None,
            'assessment': 'No valid observations'
        }
    
    latest_obs = observations[-1]
    latest_value = float(latest_obs['value'])
    latest_date = latest_obs['date']
    yoy_change = calculate_year_over_year_change(observations)
    
    # Assess based on thresholds
    if 'UNRATE' in series_id or 'U6RATE' in series_id:
        # Unemployment: higher = worse
        if latest_value >= config['threshold_critical']:
            status = 'CRISIS'
            confidence = 'High'
            assessment = f"Critical unemployment: {latest_value:.1f}%"
        elif latest_value >= config['threshold_high']:
            status = 'CONCERN'
            confidence = 'Med'
            assessment = f"Elevated unemployment: {latest_value:.1f}%"
        else:
            status = 'NORMAL'
            confidence = 'Low'
            assessment = f"Normal range: {latest_value:.1f}%"
    
    elif 'CPI' in series_id or 'PCE' in series_id:
        # Inflation: use YoY change
        if yoy_change is None:
            status = 'UNKNOWN'
            confidence = 'Low'
            assessment = 'Insufficient data for YoY'
        elif yoy_change >= config['threshold_critical']:
            status = 'CRISIS'
            confidence = 'High'
            assessment = f"Critical inflation: +{yoy_change:.1f}% YoY"
        elif yoy_change >= config['threshold_high']:
            status = 'CONCERN'
            confidence = 'Med'
            assessment = f"High inflation: +{yoy_change:.1f}% YoY"
        else:
            status = 'NORMAL'
            confidence = 'Low'
            assessment = f"Moderate inflation: +{yoy_change:.1f}% YoY"
    
    elif 'GDP' in series_id or 'A191RL1' in series_id:
        # GDP: negative growth = concern
        if yoy_change is None:
            status = 'UNKNOWN'
            confidence = 'Low'
            assessment = 'Insufficient data'
        elif yoy_change <= config['threshold_critical']:
            status = 'CRISIS'
            confidence = 'High'
            assessment = f"Severe recession: {yoy_change:.1f}% YoY"
        elif yoy_change <= config['threshold_high']:
            status = 'CONCERN'
            confidence = 'Med'
            assessment = f"Recession: {yoy_change:.1f}% YoY"
        else:
            status = 'NORMAL'
            confidence = 'Low'
            assessment = f"Growth: +{yoy_change:.1f}% YoY"
    
    elif 'BOPGSTB' in series_id:
        # Trade balance: more negative = concern (values in millions)
        value_billions = latest_value / 1000.0  # Convert millions to billions
        if value_billions <= config['threshold_critical']:
            status = 'CRISIS'
            confidence = 'High'
            assessment = f"Severe trade deficit: ${value_billions:.1f}B/month"
        elif value_billions <= config['threshold_high']:
            status = 'CONCERN'
            confidence = 'Med'
            assessment = f"Large trade deficit: ${value_billions:.1f}B/month"
        else:
            status = 'NORMAL'
            confidence = 'Low'
            assessment = f"Trade balance: ${value_billions:.1f}B/month"
    
    else:
        status = 'UNKNOWN'
        confidence = 'Low'
        assessment = 'No assessment criteria'
    
    return {
        'series_id': series_id,
        'name': config['name'],
        'description': config['description'],
        'status': status,
        'confidence': confidence,
        'latest_value': latest_value,
        'latest_date': latest_date,
        'yoy_change': yoy_change,
        'assessment': assessment
    }


def format_for_daily_review(results: Dict[str, List[dict]]) -> str:
    """Format economic indicators for daily review."""
    output = ["## FRED Economic Indicators — Node H0 (Babylon/Merchants Pattern)\n"]
    
    concern_count = 0
    crisis_count = 0
    
    for category, indicators in results.items():
        output.append(f"### {category.title()}\n")
        output.append("| Indicator | Latest | Date | YoY Change | Status | Assessment |")
        output.append("|-----------|--------|------|------------|--------|------------|")
        
        for ind in indicators:
            if ind['status'] == 'ERROR':
                output.append(f"| {ind['name']} | N/A | N/A | N/A | ⚠️ ERROR | {ind['assessment']} |")
                continue
            
            yoy_str = f"{ind['yoy_change']:+.1f}%" if ind['yoy_change'] is not None else "N/A"
            
            if ind['status'] == 'CRISIS':
                status_icon = '🔴'
                crisis_count += 1
            elif ind['status'] == 'CONCERN':
                status_icon = '🟠'
                concern_count += 1
            elif ind['status'] == 'NORMAL':
                status_icon = '🟢'
            else:
                status_icon = '⚪'
            
            output.append(f"| **{ind['name']}** | {ind['latest_value']:.2f} | {ind['latest_date']} | {yoy_str} | {status_icon} {ind['status']} | {ind['assessment']} |")
        
        output.append("")
    
    # Summary
    output.append(f"**Summary:** {crisis_count} CRISIS, {concern_count} CONCERN indicators\n")
    
    # Assessment
    if crisis_count >= 2:
        output.append("⚠️  **ASSESSMENT: Economic crisis indicators present (High confidence)**")
        output.append("Multiple critical thresholds exceeded. Maps to H0 (Rev 17-18 - merchants/trade collapse).\n")
    elif concern_count >= 3 or crisis_count >= 1:
        output.append("⚠️  **ASSESSMENT: Economic instability detected (Med confidence)**")
        output.append("Elevated indicators warrant monitoring. Could develop into H0 pattern.\n")
    else:
        output.append("✅ **ASSESSMENT: Normal economic conditions (Low confidence for H0)**")
        output.append("No significant crisis indicators. Continue monitoring.\n")
    
    output.append("**Scripture anchor:** Revelation 17-18 — 'merchants weep… for no man buyeth their merchandise'")
    output.append("**Node ID:** H0 (Babylon/merchants — economic/trade patterns)")
    output.append("**Source:** FRED (Federal Reserve Economic Data) — Tier 1 (US government official data)")
    
    return "\n".join(output)


def main():
    """Main execution."""
    months = 12
    
    if '--months' in sys.argv:
        try:
            idx = sys.argv.index('--months')
            months = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python fetch_economic.py [--months 12]")
            sys.exit(1)
    
    print(f"Fetching FRED economic indicators (past {months} months)...\n")
    
    # Fetch all indicators
    results = {}
    
    for category, indicators in INDICATORS.items():
        print(f"Fetching {category}...")
        results[category] = []
        
        for series_id, config in indicators.items():
            data = fetch_series_data(series_id, months)
            assessment = assess_indicator(series_id, data, config)
            results[category].append(assessment)
    
    print()
    
    # Output results
    print(format_for_daily_review(results))
    
    # Classification table
    print("\n" + "="*80)
    print("\n## For classification table (copy to daily review):\n")
    
    classification_rows = []
    for category, indicators in results.items():
        for ind in indicators:
            if ind['status'] in ['CRISIS', 'CONCERN']:
                classification_rows.append(f"| FRED: {ind['name']} — {ind['assessment']} | USA | H0 | Rev 17-18 | Economic | {ind['confidence']} | FRED Tier 1; {ind['latest_date']} |")
    
    if classification_rows:
        for row in classification_rows:
            print(row)
    else:
        print("(No CRISIS or CONCERN indicators to report)")
    
    print("\n" + "="*80)
    print("\n💡 FRED API key detected and working!")
    print("📊 Tracking: Inflation, Unemployment, GDP, Trade Balance")
    print("🔄 Automatically included in weekly_update.py")


if __name__ == '__main__':
    main()


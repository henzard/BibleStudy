#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NOAA Space Weather Alert Fetcher
Fetches space weather alerts (solar flares, geomagnetic storms, electron flux) from NOAA SWPC.

Node: J6 (Cosmic Signs)
Scripture: Matthew 24:29 — "sun shall be darkened, and the moon shall not give her light"
          Luke 21:25 — "signs in the sun, and in the moon, and in the stars"

Usage:
    python fetch_spaceweather.py [--days 7]
"""

import sys
import io
import requests
import json
from datetime import datetime, timedelta
import argparse

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NOAA_ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"
NOAA_MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"


def fetch_space_weather_alerts(days_ago=7):
    """Fetch space weather alerts from NOAA."""
    try:
        response = requests.get(NOAA_ALERTS_URL, timeout=10)
        response.raise_for_status()
        alerts = response.json()
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_ago)
        recent_alerts = []
        
        for alert in alerts:
            alert_date_str = alert.get('issue_datetime', '')
            try:
                alert_date = datetime.strptime(alert_date_str, '%Y-%m-%d %H:%M:%S.%f')
                if alert_date >= cutoff_date:
                    recent_alerts.append(alert)
            except ValueError:
                continue  # Skip if date parsing fails
        
        return recent_alerts
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching space weather alerts: {e}")
        return []


def fetch_magnetic_field_data():
    """Fetch 24-hour magnetic field data from NOAA."""
    try:
        response = requests.get(NOAA_MAG_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Data format: [["2025-12-26 12:00:00", bx, by, bz, lon, lat, bt], ...]
        # We care about bt (total magnetic field strength)
        if len(data) > 1:  # Skip header row
            latest = data[-1]
            timestamp = latest[0]
            bt = float(latest[6]) if len(latest) > 6 else None
            return {"timestamp": timestamp, "bt": bt}
        return None
    
    except (requests.exceptions.RequestException, json.JSONDecodeError, IndexError) as e:
        print(f"Error fetching magnetic field data: {e}")
        return None


def classify_alert_severity(alert):
    """Classify alert severity and map to confidence levels."""
    message = alert.get('message', '').upper()
    product_id = alert.get('product_id', '')
    
    # Geomagnetic storm scales (G-scale)
    if 'G5' in message or 'EXTREME' in message:
        return 'CRITICAL', 'High', 'G5 Extreme geomagnetic storm'
    elif 'G4' in message or 'SEVERE' in message:
        return 'SEVERE', 'High', 'G4 Severe geomagnetic storm'
    elif 'G3' in message or 'STRONG' in message:
        return 'MAJOR', 'Med', 'G3 Strong geomagnetic storm'
    elif 'G2' in message or 'MODERATE' in message:
        return 'MODERATE', 'Med', 'G2 Moderate geomagnetic storm'
    elif 'G1' in message or 'MINOR' in message:
        return 'MINOR', 'Low', 'G1 Minor geomagnetic storm'
    
    # Solar radiation storms (S-scale)
    elif 'S5' in message:
        return 'CRITICAL', 'High', 'S5 Extreme solar radiation storm'
    elif 'S4' in message:
        return 'SEVERE', 'High', 'S4 Severe solar radiation storm'
    elif 'S3' in message:
        return 'MAJOR', 'Med', 'S3 Strong solar radiation storm'
    
    # Radio blackouts (R-scale)
    elif 'R5' in message:
        return 'CRITICAL', 'High', 'R5 Extreme radio blackout'
    elif 'R4' in message:
        return 'SEVERE', 'High', 'R4 Severe radio blackout'
    elif 'R3' in message:
        return 'MAJOR', 'Med', 'R3 Strong radio blackout'
    
    # Electron flux alerts
    elif 'ELECTRON' in message and '2MEV' in message:
        flux_value = extract_flux_value(message)
        if flux_value and flux_value > 10000:
            return 'SEVERE', 'High', f'High electron flux: {flux_value} pfu'
        elif flux_value and flux_value > 5000:
            return 'MODERATE', 'Med', f'Elevated electron flux: {flux_value} pfu'
        else:
            return 'MINOR', 'Low', 'Electron flux alert'
    
    # K-index warnings (geomagnetic activity)
    elif 'K-INDEX' in message:
        if 'K-INDEX OF 8' in message or 'K-INDEX OF 9' in message:
            return 'CRITICAL', 'High', 'Extreme K-index (8-9)'
        elif 'K-INDEX OF 7' in message:
            return 'SEVERE', 'High', 'Severe K-index (7)'
        elif 'K-INDEX OF 6' in message:
            return 'MAJOR', 'Med', 'Strong K-index (6)'
        elif 'K-INDEX OF 5' in message:
            return 'MODERATE', 'Med', 'Moderate K-index (5)'
        elif 'K-INDEX OF 4' in message:
            return 'MINOR', 'Low', 'Minor K-index (4)'
    
    return 'INFO', 'Low', 'General space weather info'


def extract_flux_value(message):
    """Extract flux value from electron flux alert message."""
    try:
        # Look for pattern like "Maximum 2MeV Flux: 8651 pfu"
        if 'MAXIMUM 2MEV FLUX:' in message:
            parts = message.split('MAXIMUM 2MEV FLUX:')[1].split('PFU')[0].strip()
            return int(parts)
    except (ValueError, IndexError):
        pass
    return None


def is_prophetically_relevant(severity, description):
    """Determine if this event is potentially prophetically relevant."""
    # J6 markers: sun darkened, moon not giving light, stars falling
    # Only MAJOR+ events (G3+, S3+, R3+) might be relevant
    if severity in ['CRITICAL', 'SEVERE', 'MAJOR']:
        return True, "Potentially relevant to J6 (cosmic signs)"
    else:
        return False, "Routine space weather (not prophetic marker)"


def main():
    parser = argparse.ArgumentParser(description="Fetch NOAA space weather alerts.")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of past days to fetch alerts for (default: 7).")
    args = parser.parse_args()
    
    print(f"Fetching NOAA space weather alerts (past {args.days} days)...")
    print("\n")
    
    alerts = fetch_space_weather_alerts(args.days)
    
    if not alerts:
        print("⚠️  No space weather alerts in the past {} days.".format(args.days))
        print("   (This is NORMAL — most days have routine solar activity)")
        return
    
    print(f"## NOAA Space Weather Alerts — Node J6 (Cosmic Signs)\n")
    print(f"**Period:** Past {args.days} days")
    print(f"**Alerts found:** {len(alerts)}\n")
    
    # Group by severity
    by_severity = {
        'CRITICAL': [],
        'SEVERE': [],
        'MAJOR': [],
        'MODERATE': [],
        'MINOR': [],
        'INFO': []
    }
    
    for alert in alerts:
        severity, confidence, description = classify_alert_severity(alert)
        by_severity[severity].append({
            'alert': alert,
            'severity': severity,
            'confidence': confidence,
            'description': description
        })
    
    # Print by severity (highest first)
    for severity_level in ['CRITICAL', 'SEVERE', 'MAJOR', 'MODERATE', 'MINOR', 'INFO']:
        items = by_severity[severity_level]
        if not items:
            continue
        
        print(f"### {severity_level} Alerts ({len(items)})\n")
        print("| Date | Type | Description | Confidence | Prophetic Relevance |")
        print("|------|------|-------------|------------|---------------------|")
        
        for item in items:
            alert = item['alert']
            date = alert.get('issue_datetime', 'N/A').split('.')[0]  # Remove milliseconds
            description = item['description']
            confidence = item['confidence']
            
            relevant, relevance_note = is_prophetically_relevant(item['severity'], description)
            relevance_emoji = "🔴" if relevant else "🟢"
            
            print(f"| {date} | {item['severity']} | {description} | {confidence} | {relevance_emoji} {relevance_note} |")
        
        print()
    
    # Summary assessment
    critical_count = len(by_severity['CRITICAL'])
    severe_count = len(by_severity['SEVERE'])
    major_count = len(by_severity['MAJOR'])
    
    print("## Assessment\n")
    
    if critical_count > 0:
        print("🔴 **CRITICAL SPACE WEATHER DETECTED**")
        print(f"   {critical_count} extreme event(s) in past {args.days} days.")
        print("   **Potential J6 relevance:** HIGH")
        print("   **Action:** Cross-verify with multiple sources (NASA, ESA).")
    elif severe_count > 0:
        print("🟠 **SEVERE SPACE WEATHER DETECTED**")
        print(f"   {severe_count} severe event(s) in past {args.days} days.")
        print("   **Potential J6 relevance:** MEDIUM")
        print("   **Action:** Monitor for escalation.")
    elif major_count > 0:
        print("🟡 **MAJOR SPACE WEATHER DETECTED**")
        print(f"   {major_count} strong event(s) in past {args.days} days.")
        print("   **Potential J6 relevance:** LOW-MEDIUM")
        print("   **Action:** Note for trends, but not prophetic marker.")
    else:
        print("🟢 **ROUTINE SPACE WEATHER**")
        print("   No major events detected.")
        print("   **Potential J6 relevance:** NONE")
        print("   **Action:** Continue normal monitoring.")
    
    print("\n**Important Disclaimer:**")
    print("- Matthew 24:29 describes SUN DARKENED, MOON NOT GIVING LIGHT")
    print("- Minor geomagnetic storms (G1-G2) are ROUTINE, not prophetic")
    print("- Only EXTREME events (G5, S5, R5) might align with J6")
    print("- We have NOT observed J6 markers yet")
    
    print("\n**Scripture anchor:** Matthew 24:29, Luke 21:25")
    print("**Node ID:** J6 (Cosmic signs preceding Son of Man)")
    print("**Source:** NOAA Space Weather Prediction Center — Tier 1 (US government)")
    
    print("\n" + "="*80 + "\n")
    
    # Output for classification table
    print("## For classification table (copy to daily review):\n")
    
    has_relevant = False
    for severity_level in ['CRITICAL', 'SEVERE', 'MAJOR']:
        for item in by_severity[severity_level]:
            alert = item['alert']
            date = alert.get('issue_datetime', '').split(' ')[0]  # Just date
            print(f"| NOAA: {item['description']} on {date} | Global | J6 | Matt 24:29 | Space Weather | {item['confidence']} | NOAA SWPC Tier 1 |")
            has_relevant = True
    
    if not has_relevant:
        print("(No MAJOR+ events to report)")
    
    print("\n" + "="*80)
    print("\n💡 NOAA Space Weather tracking operational!")
    print("🌌 Monitoring: Solar flares, geomagnetic storms, electron flux")
    print("📊 Node J6 (Cosmic Signs) now tracked automatically")


if __name__ == "__main__":
    main()


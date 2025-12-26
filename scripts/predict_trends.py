#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TensorFlow Trend Predictor
Uses machine learning to analyze historical data and predict trends.

IMPORTANT: This is for PATTERN ANALYSIS, not date-setting prophecy fulfillment.
We track trends, not predict "when Jesus returns."

Usage:
    python predict_trends.py [--weeks 4]
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

# Try to import numpy first (required)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("❌ NumPy not installed. Install with: pip install numpy")
    sys.exit(1)

# Try to import TensorFlow (optional)
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("⚠️  TensorFlow not installed. Using simple statistical methods instead.")
    print("   (Optional) Install TensorFlow for ML predictions: pip install tensorflow")

DB_PATH = Path("data/prophecy_tracking.db")


def check_sufficient_data(conn: sqlite3.Connection, min_weeks: int = 4) -> bool:
    """Check if we have enough historical data for predictions."""
    cursor = conn.cursor()
    
    # Check earthquake data span
    cursor.execute("""
        SELECT 
            MIN(date(date_utc)) as first_date,
            MAX(date(date_utc)) as last_date,
            COUNT(DISTINCT date(date_utc, 'weekday 0', '-6 days')) as weeks
        FROM earthquakes
    """)
    
    result = cursor.fetchone()
    if not result or result[2] < min_weeks:
        return False, result[2] if result else 0
    
    return True, result[2]


def get_earthquake_time_series(conn: sqlite3.Connection) -> tuple:
    """Get earthquake count time series data."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            date(date_utc, 'weekday 0', '-6 days') as week_start,
            COUNT(*) as total_quakes,
            SUM(CASE WHEN magnitude >= 6.0 THEN 1 ELSE 0 END) as major_quakes,
            AVG(magnitude) as avg_magnitude
        FROM earthquakes
        GROUP BY week_start
        ORDER BY week_start ASC
    """)
    
    data = cursor.fetchall()
    
    if not data:
        return None, None, None, None
    
    weeks = [row[0] for row in data]
    total = np.array([row[1] for row in data])
    major = np.array([row[2] for row in data])
    avg_mag = np.array([row[3] for row in data])
    
    return weeks, total, major, avg_mag


def simple_moving_average(data: np.ndarray, window: int = 3) -> np.ndarray:
    """Calculate simple moving average (fallback when TensorFlow unavailable)."""
    if len(data) < window:
        return data
    
    cumsum = np.cumsum(np.insert(data, 0, 0))
    return (cumsum[window:] - cumsum[:-window]) / window


def predict_with_ml(data: np.ndarray, forecast_weeks: int = 4) -> tuple:
    """Use TensorFlow to predict future trends."""
    if not HAS_TF or len(data) < 8:
        # Fallback to simple moving average
        ma = simple_moving_average(data, window=3)
        last_value = ma[-1] if len(ma) > 0 else data[-1]
        predictions = np.array([last_value] * forecast_weeks)
        confidence = "Low (Simple MA)"
        return predictions, confidence
    
    # Prepare data for LSTM
    # Normalize
    data_mean = np.mean(data)
    data_std = np.std(data) if np.std(data) > 0 else 1.0
    normalized_data = (data - data_mean) / data_std
    
    # Create sequences (use last 4 weeks to predict next week)
    sequence_length = min(4, len(data) - 1)
    X, y = [], []
    
    for i in range(len(normalized_data) - sequence_length):
        X.append(normalized_data[i:i+sequence_length])
        y.append(normalized_data[i+sequence_length])
    
    if len(X) < 4:
        # Not enough data for ML
        ma = simple_moving_average(data, window=3)
        last_value = ma[-1] if len(ma) > 0 else data[-1]
        predictions = np.array([last_value] * forecast_weeks)
        confidence = "Low (Insufficient Data)"
        return predictions, confidence
    
    X = np.array(X).reshape(-1, sequence_length, 1)
    y = np.array(y)
    
    # Build simple LSTM model
    model = keras.Sequential([
        keras.layers.LSTM(16, input_shape=(sequence_length, 1)),
        keras.layers.Dense(8, activation='relu'),
        keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    # Train quietly
    model.fit(X, y, epochs=50, verbose=0, batch_size=2)
    
    # Predict future weeks
    predictions = []
    current_sequence = normalized_data[-sequence_length:].tolist()
    
    for _ in range(forecast_weeks):
        pred_input = np.array(current_sequence[-sequence_length:]).reshape(1, sequence_length, 1)
        pred_normalized = model.predict(pred_input, verbose=0)[0][0]
        predictions.append(pred_normalized)
        current_sequence.append(pred_normalized)
    
    # Denormalize
    predictions = np.array(predictions) * data_std + data_mean
    predictions = np.maximum(predictions, 0)  # Can't have negative earthquakes
    
    confidence = "Med (ML-based)"
    
    return predictions, confidence


def analyze_trends(conn: sqlite3.Connection, forecast_weeks: int = 4):
    """Analyze historical trends and make predictions."""
    print("📊 Analyzing Historical Trends with ML/AI")
    print("="*60)
    
    # Check data sufficiency
    sufficient, weeks_available = check_sufficient_data(conn, min_weeks=4)
    
    if not sufficient:
        print(f"\n⚠️  Insufficient data: Only {weeks_available} weeks available.")
        print("   Need at least 4 weeks for trend analysis.")
        print("   Continue collecting data with: python scripts/ingest_data.py")
        return
    
    print(f"\n✅ Data available: {weeks_available} weeks")
    print(f"📈 Forecasting next {forecast_weeks} weeks...\n")
    
    # Get earthquake time series
    weeks, total, major, avg_mag = get_earthquake_time_series(conn)
    
    if weeks is None:
        print("❌ No earthquake data available.")
        return
    
    # Predict total earthquakes
    pred_total, conf_total = predict_with_ml(total, forecast_weeks)
    
    # Predict major earthquakes
    pred_major, conf_major = predict_with_ml(major, forecast_weeks)
    
    # Generate report
    print("🌍 **EARTHQUAKE TREND ANALYSIS**\n")
    
    # Historical averages
    print(f"Historical Average (past {len(total)} weeks):")
    print(f"   Total earthquakes/week: {np.mean(total):.1f}")
    print(f"   Major (6.0+) quakes/week: {np.mean(major):.2f}")
    print(f"   Average magnitude: {np.mean(avg_mag):.2f}")
    
    # Recent trend (last 4 weeks)
    recent_total = total[-4:] if len(total) >= 4 else total
    recent_major = major[-4:] if len(major) >= 4 else major
    
    print(f"\nRecent Trend (last {len(recent_total)} weeks):")
    print(f"   Total earthquakes/week: {np.mean(recent_total):.1f}")
    print(f"   Major (6.0+) quakes/week: {np.mean(recent_major):.2f}")
    print(f"   Trend: {'📈 Increasing' if np.mean(recent_total) > np.mean(total) else '📉 Decreasing'}")
    
    # Predictions
    print(f"\n🔮 **FORECAST (Next {forecast_weeks} weeks)**\n")
    print(f"Confidence: {conf_total}")
    print()
    
    for i in range(forecast_weeks):
        week_num = i + 1
        pred_date = datetime.now() + timedelta(weeks=week_num)
        week_start = pred_date - timedelta(days=pred_date.weekday())
        
        print(f"Week {week_num} ({week_start.strftime('%Y-%m-%d')}):")
        print(f"   Predicted total: {pred_total[i]:.0f} earthquakes")
        print(f"   Predicted major: {pred_major[i]:.1f} (6.0+)")
        print()
    
    # Important disclaimers
    print("="*60)
    print("⚠️  **IMPORTANT DISCLAIMERS**")
    print("="*60)
    print()
    print("1. **Not Prophecy Fulfillment Prediction**")
    print("   This predicts earthquake FREQUENCY, not prophetic timing.")
    print("   Matthew 24:36 - No one knows the day or hour.")
    print()
    print("2. **Pattern Analysis Only**")
    print("   ML identifies trends in historical data.")
    print("   Actual events may vary significantly.")
    print()
    print("3. **Node J0 Observation**")
    print("   Jesus said 'earthquakes in divers places' (Matt 24:7).")
    print("   We're observing this pattern, not predicting 'the end.'")
    print()
    print("4. **Use for Planning**")
    print("   Helps anticipate higher/lower activity weeks.")
    print("   Useful for newsletter planning, not prophetic dates.")
    print()
    
    # Store predictions in database
    cursor = conn.cursor()
    for i in range(forecast_weeks):
        week_num = i + 1
        pred_date = datetime.now() + timedelta(weeks=week_num)
        week_start = (pred_date - timedelta(days=pred_date.weekday())).strftime('%Y-%m-%d')
        week_end = (pred_date + timedelta(days=6 - pred_date.weekday())).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO trends (metric_name, time_period, period_start, period_end, value, comparison_to_previous)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f'predicted_earthquakes_week_{week_num}',
            'week',
            week_start,
            week_end,
            float(pred_total[i]),
            None
        ))
    
    conn.commit()
    print("✅ Predictions stored in database (trends table)")


def main():
    """Main execution."""
    forecast_weeks = 4
    
    if '--weeks' in sys.argv:
        try:
            idx = sys.argv.index('--weeks')
            forecast_weeks = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Usage: python predict_trends.py [--weeks 4]")
            sys.exit(1)
    
    # Check database
    if not DB_PATH.exists():
        print("❌ Database not found. Run: python scripts/init_database.py")
        sys.exit(1)
    
    # Connect and analyze
    conn = sqlite3.connect(DB_PATH)
    
    try:
        analyze_trends(conn, forecast_weeks)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}", file=sys.stderr)
    finally:
        conn.close()


if __name__ == '__main__':
    main()


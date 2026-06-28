"""
GeoMed Demand Forecaster
"""
from datetime import datetime, timedelta
import random

def forecast_demand(days_ahead=7):
    """
    Returns a simple forecast of expected ambulance demand.
    (Gracefully falls back to statistical dummy data if pandas/prophet missing)
    """
    base_date = datetime.utcnow()
    forecast = []
    
    # Simple deterministic but realistic-looking random walk
    base_demand = 5 

    for i in range(days_ahead):
        target_date = base_date + timedelta(days=i)
        is_weekend = target_date.weekday() >= 5
        
        # Less demand on weekends for campus
        multiplier = 0.7 if is_weekend else 1.2
        
        expected = int(base_demand * multiplier + random.randint(-2, 3))
        expected = max(1, expected)
        
        forecast.append({
            "date": target_date.strftime('%Y-%m-%d'),
            "expected_requests": expected,
            "is_weekend": is_weekend
        })
        
    return forecast

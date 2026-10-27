"""
Real-time Weather Service for Sadar Cantt, Lucknow.

Primary: OpenWeatherMap API (free tier — 1000 calls/day)
Fallback: IMD (India Meteorological Department) data parsing
"""

import os
from datetime import datetime, timezone
from typing import Optional

import httpx

OWM_BASE = "https://api.openweathermap.org/data/2.5"
SADAR_CANTT_LAT = 26.85
SADAR_CANTT_LON = 80.94


def get_current_weather(api_key: Optional[str] = None) -> dict:
    """Fetch current weather for Sadar Cantt from OpenWeatherMap."""
    api_key = api_key or os.getenv("WEATHER_API_KEY", "")

    if not api_key:
        return {
            "status": "error",
            "message": (
                "OpenWeatherMap API key not configured. "
                "Get free key at https://openweathermap.org/api "
                "and set WEATHER_API_KEY in .env"
            ),
        }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{OWM_BASE}/weather",
                params={
                    "lat": SADAR_CANTT_LAT,
                    "lon": SADAR_CANTT_LON,
                    "appid": api_key,
                    "units": "metric",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return {
            "status": "success",
            "source": "openweathermap",
            "location": "Sadar Cantt, Lucknow",
            "coordinates": {"lat": SADAR_CANTT_LAT, "lon": SADAR_CANTT_LON},
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_deg": data["wind"].get("deg", 0),
            "weather_main": data["weather"][0]["main"],
            "weather_desc": data["weather"][0]["description"],
            "clouds": data.get("clouds", {}).get("all", 0),
            "visibility": data.get("visibility", 10000),
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "rain_3h": data.get("rain", {}).get("3h", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"OWM API error: {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_5day_forecast(api_key: Optional[str] = None) -> dict:
    """Fetch 5-day / 3-hour forecast from OpenWeatherMap."""
    api_key = api_key or os.getenv("WEATHER_API_KEY", "")

    if not api_key:
        return {"status": "error", "message": "OWM API key not configured"}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{OWM_BASE}/forecast",
                params={
                    "lat": SADAR_CANTT_LAT,
                    "lon": SADAR_CANTT_LON,
                    "appid": api_key,
                    "units": "metric",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        forecasts = []
        for item in data.get("list", []):
            forecasts.append({
                "datetime": item["dt_txt"],
                "temperature": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "rain_mm": item.get("rain", {}).get("3h", 0),
                "weather": item["weather"][0]["main"],
                "wind_speed": item["wind"]["speed"],
            })

        # Aggregate daily rainfall
        daily_rain = {}
        for f in forecasts:
            day = f["datetime"][:10]
            daily_rain[day] = daily_rain.get(day, 0) + f["rain_mm"]

        return {
            "status": "success",
            "source": "openweathermap",
            "forecasts": forecasts,
            "daily_rainfall_mm": daily_rain,
            "location": "Sadar Cantt, Lucknow",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_weather_for_features(api_key: Optional[str] = None) -> dict:
    """Get weather data formatted for feature engineering pipeline."""
    current = get_current_weather(api_key)
    forecast = get_5day_forecast(api_key)

    if current["status"] == "error":
        return current

    result = {
        "status": "success",
        "current": current,
        "forecast": forecast,
    }

    # Compute 7-day aggregates if forecast available
    if forecast["status"] == "success" and forecast.get("daily_rainfall_mm"):
        daily = forecast["daily_rainfall_mm"]
        rain_values = list(daily.values())[:7]
        result["rain_7d_mm"] = sum(rain_values)
        result["avg_humidity_7d"] = current.get("humidity", 50)
        result["avg_temp_7d"] = current.get("temperature", 28)

    return result

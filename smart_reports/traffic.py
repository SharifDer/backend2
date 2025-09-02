import requests
from datetime import datetime, timezone, timedelta
from config_factory import CONF

def get_last_monday_6pm_utc():
    today = datetime.now(timezone.utc)
    # Calculate days since last Monday (Monday = 0, Sunday = 6)
    days_since_monday = today.weekday()
    # If today is Monday, we want last Monday (7 days ago)
    # If today is not Monday, we want the most recent Monday
    if days_since_monday == 0:  # Today is Monday
        last_monday = today - timedelta(days=7)
    else:
        last_monday = today - timedelta(days=days_since_monday)
    local_time = last_monday.replace(hour=18, minute=0, second=0, tzinfo=timezone(timedelta(hours=3)))
    return local_time, local_time.astimezone(timezone.utc)


async def fetch_traffic_data(lat : float , lng : float ,  target_time_utc: datetime = get_last_monday_6pm_utc()[1] , retry: bool = True):
    url = CONF.tomtom_api_url
    params = {
        "key": CONF.tomtom_api_key,
        "point": f"{lat},{lng}",
        "unit": "KMPH",
        "openLr": "false",
        "time": target_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("flowSegmentData")

        current_speed = data.get("currentSpeed", 50.0) if data else 50.0  # Same default as scoring.py
        frc = data.get("frc", "FRC1") if data else "FRC1"

        return {
            "Average Vehicle Speed in km": current_speed,
            "Functional Road Class": frc
        }

    except requests.exceptions.RequestException as e:
        if retry:
            # Round coordinates slightly and retry once
            new_lat = round(lat, 5)
            new_lng = round(lng, 5)
            if (new_lat, new_lng) != (lat, lng):
                print(f"Traffic API error at {lat},{lng}: {e}. Retrying with {new_lat},{new_lng}.")
                # Avoid Recursive call with retry=False
                return await fetch_traffic_data(new_lat, new_lng, target_time_utc, retry=False)

        # If retry not allowed or still fails, return defaults
        print(f"Traffic API failed for point {lat},{lng}: {e}. Using default values.")
        return {
            "Average Vehicle Speed in km": 50.0,  # Same default as scoring.py
            "Functional Road Class": "FRC1"
        }
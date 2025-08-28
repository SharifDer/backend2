import requests
from datetime import datetime, timezone, timedelta
from config_factory import CONF

def get_last_monday_6pm_utc():
    today = datetime.now(timezone.utc)
    last_monday = today - timedelta(days=today.weekday() + 7)
    local_time = last_monday.replace(hour=18, minute=0, second=0, tzinfo=timezone(timedelta(hours=3)))
    return local_time, local_time.astimezone(timezone.utc)


async def fetch_traffic_data(lat : float , lng : float ,  target_time_utc: datetime = get_last_monday_6pm_utc()[1]):
    url = CONF.tomtom_api_url
    params = {
        "key": CONF.tomtom_api_key,
        "point": f"{lat},{lng}",
        "unit": "KMPH",
        "openLr": "false",
        "time": target_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json().get("flowSegmentData")
    current_speed = data['currentSpeed']
    frc = data['frc']
    return {
        "Average Vehicle Speed in km": current_speed,
        "Functional Road Class": frc
    }
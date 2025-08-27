"""
Reports Router Module
Handles fetching reports data from JSON file
"""

from fastapi import APIRouter
from pathlib import Path
import json

campaign_router = APIRouter()

# Path to JSON file inside assets folder
CAMPAIGN_FILE = Path(__file__).resolve().parent.parent / "campaign.json"


@campaign_router.get("/campaign-details")
async def get_campaign():
    """Fetch campaign details from JSON file"""
    with open(CAMPAIGN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

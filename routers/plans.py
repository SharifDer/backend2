"""
Reports Router Module
Handles fetching reports data from JSON file
"""

from fastapi import APIRouter
from pathlib import Path
import json

plans_router = APIRouter()

# Path to JSON file inside assets folder
PLANS_FILE = Path(__file__).resolve().parent.parent / "plans.json"


@plans_router.get("/plan-details")
async def get_campaign():
    """Fetch plans details from JSON file"""
    with open(PLANS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

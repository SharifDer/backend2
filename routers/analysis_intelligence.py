"""
Analysis & Intelligence router module
Handles analysis operations, intelligence data, sales optimization, and special features
"""

from typing import Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from all_types.request_dtypes import (
    ReqModel,
    ReqSrcDistination,
    ReqIntelligenceData,
    ReqClustersForSalesManData,
    Reqsmartreport
)
from all_types.response_dtypes import (
    ResModel,
    ResSrcDistination,
    ResIntelligenceData
)
from backend_common.request_processor import request_handling
from backend_common.auth import JWTBearer
from data_fetcher import load_distance_drive_time_polygon
from storage_methods import fetch_intelligence_by_viewport
from sales_man_problem import get_clusters_for_sales_man
from hub_expansion_analysis import (
    analyze_hub_expansion,
    ReqHubExpansion,
    ResHubExpansion,
)
from config_factory import CONF

from dine_in_suitability_analysis import analyze_dine_in_sites
from all_types.request_dtypes import ReqDineInSuitabilityAnalysis
from all_types.response_dtypes import ResDineInSuitabilityAnalysis
from all_types.internal_types import UserId
from smart_reports.reports import generate_pharmacy_report
from smart_reports.reports import generate_html_pharmacy_report
from traffic_data import get_here_traffic_score
from standalone_google_maps_traffic import analyze_traffic_at_location
from pydantic import BaseModel

analysis_router = APIRouter()


@analysis_router.post(
    CONF.distance_drive_time_polygon, response_model=ResModel[ResSrcDistination]
)
async def distance_drivetime_polygon(req: ReqModel[ReqSrcDistination]):
    response = await request_handling(
        req.request_body,
        ReqSrcDistination,
        ResModel[ResSrcDistination],
        load_distance_drive_time_polygon,
        wrap_output=True,
    )
    return response


@analysis_router.post(
    CONF.fetch_population_by_viewport,
    response_model=ResModel[dict],
    dependencies=[Depends(JWTBearer())],
)
async def ep_fetch_population_by_viewport(
    req: ReqModel[ReqIntelligenceData], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqIntelligenceData,
        ResModel[dict],
        fetch_intelligence_by_viewport,
        wrap_output=True,
    )
    return response


@analysis_router.post(
    CONF.temp_sales_man_problem,
    response_model=ResModel[Any],
    dependencies=[Depends(JWTBearer())],
)
async def ep_fetch_clusters_for_sales_man(
    req: ReqModel[ReqClustersForSalesManData], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqClustersForSalesManData,
        ResModel[Any],
        get_clusters_for_sales_man,
        wrap_output=True,
    )
    return response


@analysis_router.post(
    CONF.hub_expansion_analysis,
    response_model=ResModel[ResHubExpansion],
    dependencies=[Depends(JWTBearer())],
)
async def ep_hub_expansion_analysis(
    req: ReqModel[ReqHubExpansion], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqHubExpansion,
        ResModel[ResHubExpansion],
        analyze_hub_expansion,
        wrap_output=True,
    )
    return response


@analysis_router.post(
    "/dine_in_suitability_analysis", response_model=ResModel[ResDineInSuitabilityAnalysis]
)
async def ep_dine_in_suitability_analysis(
    req: ReqModel[ReqDineInSuitabilityAnalysis],
):
    try:
        # Direct call - bypass request_handling wrapper
        result = await analyze_dine_in_sites(req.request_body)
        
        return ResModel(
            message="Analysis completed successfully",
            request_id="dine_in_analysis",
            data=result
        )
    except ValueError as e:
        if "Failed to get traffic data from API" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@analysis_router.post(
    CONF.smart_pharmacy_report,   # <-- add a new path constant in CONF
    response_model=ResModel[ResIntelligenceData],   # assuming your function returns a file path (string)
    dependencies=[Depends(JWTBearer())],
)
async def ep_pharmacy_site_selection(
    req: ReqModel[Reqsmartreport], request: Request
):
    response = await request_handling(
        req.request_body,
        Reqsmartreport,         # request schema
        ResModel[ResIntelligenceData],          # response schema, path string wrapped
        #generate_pharmacy_report,  # your core analysis function
        generate_html_pharmacy_report,
        wrap_output=True,
    )
    return response

# New data models for traffic analysis
class ReqPointTrafficScore(BaseModel):
    lat: float
    lng: float
    target_max_speed: int = 50
    method: str = "google_maps"  # "here" or "google_maps"
    day_of_week: str | int = None # Optional e.g "Monday", 0-6
    target_time: str = None # Optional ('8:30AM', '6:00PM', '10:00PM')

class ResPointTrafficScore(BaseModel):
    score: float
    method: str
    coordinates: dict
    details: dict = {}
    image_id: Optional[str] = None  # ID to access the screenshot via static URL

@analysis_router.post(CONF.point_traffic_score, 
response_model=ResPointTrafficScore, 
dependencies=[Depends(JWTBearer())])
async def analyze_traffic_endpoint(request: ReqPointTrafficScore):
    """
    Analyze traffic conditions at a specific location using HERE API or Google Maps
    
    Args:
        request: TrafficAnalysisRequest containing coordinates and method preference
        
    Returns:
        Traffic analysis results with score and detailed breakdown
    """
    if request.method.lower() == "google_maps":
        # Use Google Maps screenshot method and save to static folder
        result = analyze_traffic_at_location(
            lat=request.lat,
            lng=request.lng,
            cleanup_screenshots=False,  # Don't cleanup when saving to static
            save_to_static=True,  # Save to static folder for web access
            day_of_week=request.day_of_week,
            target_time=request.target_time
        )
    else:
        # Use HERE API method (default)
        result = await get_here_traffic_score(
            property_lat=request.lat,
            property_lng=request.lng,
            target_max_speed=request.target_max_speed
        )
    
    return ResPointTrafficScore(
        score=result.get('score', 0),
        method=result.get('method', 'unknown'),
        coordinates=result.get('coordinates', {'lat': request.lat, 'lng': request.lng}),
        details=result,
        image_id=result.get('image_id')  # Include image ID for Google Maps method
    )

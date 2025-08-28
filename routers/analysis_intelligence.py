"""
Analysis & Intelligence router module
Handles analysis operations, intelligence data, sales optimization, and special features
"""

from typing import Any
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
    CONF.dine_in_suitability_analysis,
    response_model=ResModel[ResDineInSuitabilityAnalysis],
    dependencies=[Depends(JWTBearer())],
)
async def ep_dine_in_suitability_analysis(
    req: ReqModel[ReqDineInSuitabilityAnalysis], 
    request: Request
):
    try:
        response = await request_handling(
            req.request_body,
            ReqDineInSuitabilityAnalysis,
            ResModel[ResDineInSuitabilityAnalysis],
            analyze_dine_in_sites,
            wrap_output=True,
        )
        return response
    except ValueError as e:
        if "Failed to get traffic data from API" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        raise

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
        generate_pharmacy_report,  # your core analysis function
        wrap_output=True,
    )
    return response

"""
Data & Layers Management router module
Handles dataset fetching, layer management, and related operations
"""

from typing import Any
from fastapi import APIRouter, Request, Depends
from all_types.request_dtypes import (
    ReqModel,
    ReqFetchDataset,
    ReqPrdcerLyrMapData,
    ReqSavePrdcerLyer,
    ReqDeletePrdcerLayer,
    ReqStreeViewCheck,
    ReqLLMFetchDataset,
    ReqColorBasedon,
    ReqFilterBasedon,
    ReqLLMEditBasedon,
    ValidationResult,
)
from all_types.response_dtypes import (
    ResModel,
    ResFetchDataset,
    card_metadata,
    CityData,
    LayerInfo,
    ResLyrMapData,
    ResLLMFetchDataset,
    ResRecolorBasedon,
    ResCostEstimate,
)
from all_types.internal_types import UserId
from backend_common.request_processor import request_handling
from backend_common.auth import JWTBearer
from data_fetcher import (
    fetch_country_city_data,
    fetch_catlog_collection,
    fetch_layer_collection,
    save_lyr,
    delete_layer,
    aquire_user_lyrs,
    fetch_lyr_map_data,
    poi_categories,
    fetch_gradient_colors,
    fetch_dataset,
    load_area_intelligence_categories,
)
from data_fetcher_llm import process_llm_query
from cost_calculator import calculate_cost
from google_api_connector import check_street_view_availability
from recolor_filter import (
    recolor_based_on_agent,
    recolor_based_on,
    filter_based_on,
)
from config_factory import CONF


data_layers_router = APIRouter()


def create_formatted_example(model_class):
    """Create a formatted JSON example string"""
    schema = model_class.model_json_schema()

    def get_default_value(field_type):
        if field_type == "string":
            return "string"
        elif field_type == "integer" or field_type == "number":
            return 0
        elif field_type == "array":
            return []
        elif field_type == "object":
            return {}
        return None

    def create_example_from_properties(properties, required_fields):
        example = {}
        for field_name, field_info in properties.items():
            if field_info.get("type") == "array" and "items" in field_info:
                items = field_info["items"]
                if "$ref" in items:
                    ref_name = items["$ref"].split("/")[-1]
                    ref_schema = schema["$defs"][ref_name]
                    example[field_name] = [
                        create_example_from_properties(
                            ref_schema["properties"],
                            ref_schema.get("required", []),
                        )
                    ]
                else:
                    example[field_name] = [get_default_value(items["type"])]
            else:
                example[field_name] = get_default_value(
                    field_info.get("type", "string")
                )
        return example

    example = {
        "message": "string",
        "request_info": {},
        "request_body": create_example_from_properties(
            schema["properties"], schema.get("required", [])
        ),
    }

    return example


@data_layers_router.get(CONF.fetch_acknowlg_id, response_model=ResModel[str])
async def fetch_acknowlg_id():
    response = await request_handling(
        None, None, ResModel[str], None, wrap_output=True
    )
    return response


@data_layers_router.get(CONF.catlog_collection, response_model=ResModel[list[card_metadata]])
async def catlog_collection():
    response = await request_handling(
        None,
        None,
        ResModel[list[card_metadata]],
        fetch_catlog_collection,
        wrap_output=True,
    )
    return response


@data_layers_router.get(CONF.layer_collection, response_model=ResModel[list[card_metadata]])
async def layer_collection():
    response = await request_handling(
        None,
        None,
        ResModel[list[card_metadata]],
        fetch_layer_collection,
        wrap_output=True,
    )
    return response


@data_layers_router.get(CONF.country_city, response_model=ResModel[dict[str, list[CityData]]])
async def country_city():
    response = await request_handling(
        None,
        None,
        ResModel[dict[str, list[CityData]]],
        fetch_country_city_data,
        wrap_output=True,
    )
    return response


@data_layers_router.get(CONF.nearby_categories, response_model=ResModel[dict[str, list[str]]])
async def ep_city_categories():
    response = await request_handling(
        "",
        "",
        ResModel[dict[str, list[str]]],
        poi_categories,
        wrap_output=True,
    )
    return response


@data_layers_router.get(CONF.nearby_categories, response_model=ResModel[dict[str, list[str]]])
async def ep_load_area_intelligence_categories():
    response = await request_handling(
        "",
        "",
        ResModel[dict[str, list[str]]],
        load_area_intelligence_categories,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.fetch_dataset,
    response_model=ResModel[ResFetchDataset],
    dependencies=[Depends(JWTBearer())],
)
async def fetch_dataset_ep(req: ReqModel[ReqFetchDataset], request: Request):
    response = await request_handling(
        req.request_body,
        ReqFetchDataset,
        ResModel[ResFetchDataset],
        fetch_dataset,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.process_llm_query,
    response_model=ResModel[ResLLMFetchDataset],
    dependencies=[Depends(JWTBearer())],
)
async def process_llm_query_ep(
    req: ReqModel[ReqLLMFetchDataset], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqLLMFetchDataset,
        ResModel[ResLLMFetchDataset],
        process_llm_query,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.save_layer,
    response_model=ResModel[str],
    dependencies=[Depends(JWTBearer())],
)
async def save_layer_ep(req: ReqModel[ReqSavePrdcerLyer], request: Request):
    response = await request_handling(
        req.request_body,
        ReqSavePrdcerLyer,
        ResModel[str],
        save_lyr,
        wrap_output=True,
    )
    return response


@data_layers_router.delete(
    CONF.delete_layer,
    response_model=ResModel[str],
    dependencies=[Depends(JWTBearer())],
)
async def delete_layer_ep(
    req: ReqModel[ReqDeletePrdcerLayer], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqDeletePrdcerLayer,
        ResModel[str],
        delete_layer,
        wrap_output=True,
    )
    return response


@data_layers_router.post(CONF.user_layers, response_model=ResModel[list[LayerInfo]])
async def user_layers(req: ReqModel[UserId]):
    response = await request_handling(
        req.request_body,
        UserId,
        ResModel[list[LayerInfo]],
        aquire_user_lyrs,
        wrap_output=True,
    )
    return response


@data_layers_router.post(CONF.prdcer_lyr_map_data, response_model=ResModel[ResLyrMapData])
async def prdcer_lyr_map_data(req: ReqModel[ReqPrdcerLyrMapData]):
    response = await request_handling(
        req.request_body,
        ReqPrdcerLyrMapData,
        ResModel[ResLyrMapData],
        fetch_lyr_map_data,
        wrap_output=True,
    )
    return response


@data_layers_router.post(CONF.cost_calculator, response_model=ResModel[ResCostEstimate])
async def cost_calculator_endpoint(
    req: ReqModel[ReqFetchDataset], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqFetchDataset,
        ResModel[ResCostEstimate],
        calculate_cost,
        wrap_output=True,
    )
    return response


@data_layers_router.get(CONF.fetch_gradient_colors, response_model=ResModel[list[list[str]]])
async def ep_fetch_gradient_colors():
    response = await request_handling(
        None,
        None,
        ResModel[list[list[str]]],
        fetch_gradient_colors,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.recolor_based,
    response_model=ResModel[list[ResRecolorBasedon]],
)
async def ep_recolor_based_on(req: ReqModel[ReqColorBasedon], request: Request):
    response = await request_handling(
        req.request_body,
        ReqColorBasedon,
        ResModel[list[ResRecolorBasedon]],
        recolor_based_on,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.filter_based_on,
    response_model=ResModel[list[ResRecolorBasedon]],
)
async def ep_filter_based_on(req: ReqModel[ReqFilterBasedon], request: Request):
    response = await request_handling(
        req.request_body,
        ReqFilterBasedon,
        ResModel[list[ResRecolorBasedon]],
        filter_based_on,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.recolor_based + "_llm",
    response_model=ResModel[ValidationResult],
)
async def ep_process_color_based_on_agent(
    req: ReqModel[ReqLLMEditBasedon], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqLLMEditBasedon,
        ResModel[ValidationResult],
        recolor_based_on_agent,
        wrap_output=True,
    )
    return response


@data_layers_router.post(
    CONF.check_street_view,
    response_model=ResModel[dict[str, bool]],
    dependencies=[Depends(JWTBearer())],
)
async def check_street_view(req: ReqModel[ReqStreeViewCheck]):
    response = await request_handling(
        req.request_body,
        ReqStreeViewCheck,
        ResModel[dict[str, str]],
        check_street_view_availability,
        wrap_output=True,
    )
    return response

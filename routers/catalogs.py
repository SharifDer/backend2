"""
Catalogs Management router module
Handles catalog operations including save, delete, fetch catalog layers
"""

from typing import Union, Optional
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from all_types.request_dtypes import (
    ReqModel,
    ReqSavePrdcerCtlg,
    ReqDeletePrdcerCtlg,
    ReqFetchCtlgLyrs,
)
from all_types.response_dtypes import (
    ResModel,
    ResLyrMapData
)
from all_types.internal_types import ResUserCatalogInfo, UserId, ResPrdcerCtlg
from fastapi import HTTPException
from all_types.request_dtypes import ReqCatalogId
from all_types.internal_types import ResPrdcerCtlg
from backend_common.request_processor import request_handling
from backend_common.auth import JWTBearer
from data_fetcher import (
    save_prdcer_ctlg,
    delete_prdcer_ctlg,
    fetch_prdcer_ctlgs,
    fetch_ctlg_lyrs,
    save_draft_catalog,
    fetch_single_catalog,
)
from config_factory import CONF
import json


catalogs_router = APIRouter()


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


@catalogs_router.post(
    CONF.save_producer_catalog,
    response_model=ResModel[str],
    dependencies=[Depends(JWTBearer())],
)
async def ep_save_producer_catalog(
    req: Union[str, ReqSavePrdcerCtlg] = Form(
        ...,
        description=(
            "Expected request format:\n\n"
            "```json\n"
            f"{json.dumps(create_formatted_example(ReqSavePrdcerCtlg), indent=2)}\n"
            "```"
        ),
        example=create_formatted_example(ReqSavePrdcerCtlg),
    ),
    image: Optional[UploadFile] = File(None),
):
    if isinstance(req, str):
        req = json.loads(req)
    req_model = ReqModel(**req)
    req_model.request_body["image"] = image
    request_body = ReqSavePrdcerCtlg(**req_model.request_body)

    response = await request_handling(
        request_body,
        ReqSavePrdcerCtlg,
        ResModel[str],
        save_prdcer_ctlg,
        wrap_output=True,
    )
    return response


@catalogs_router.post(
    "/fastapi/fetch_single_catalog",
    response_model=ResModel[ResPrdcerCtlg],
    dependencies=[Depends(JWTBearer())],
)
async def fetch_single_catalog_endpoint(
    req: ReqModel[ReqCatalogId],
    request: Request
):
    response = await request_handling(
        req.request_body,
        ReqCatalogId,
        ResModel[ResPrdcerCtlg],
        fetch_single_catalog,
        wrap_output=True,
    )
    return response



@catalogs_router.delete(
    CONF.delete_producer_catalog,
    response_model=ResModel[str],
    dependencies=[Depends(JWTBearer())],
)
async def ep_delete_producer_catalog(
    req: ReqModel[ReqDeletePrdcerCtlg], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqDeletePrdcerCtlg,
        ResModel[str],
        delete_prdcer_ctlg,
        wrap_output=True,
    )
    return response


@catalogs_router.post(CONF.user_catalogs, response_model=ResModel[list[ResUserCatalogInfo]])
async def user_catalogs(req: ReqModel[UserId]):
    response = await request_handling(
        req.request_body,
        UserId,
        ResModel[list[ResUserCatalogInfo]],
        fetch_prdcer_ctlgs,
        wrap_output=True,
    )
    return response


@catalogs_router.post(CONF.fetch_ctlg_lyrs, response_model=ResModel[list[ResLyrMapData]])
async def fetch_catalog_layers(req: ReqModel[ReqFetchCtlgLyrs]):
    response = await request_handling(
        req.request_body,
        ReqFetchCtlgLyrs,
        ResModel[list[ResLyrMapData]],
        fetch_ctlg_lyrs,
        wrap_output=True,
    )
    return response


@catalogs_router.post(
    CONF.save_draft_catalog,
    response_model=ResModel[str],
    dependencies=[Depends(JWTBearer())],
)
async def save_draft_catalog_endpoint(
    req: ReqModel[ReqSavePrdcerCtlg], request: Request
):
    response = await request_handling(
        req.request_body,
        ReqSavePrdcerCtlg,
        ResModel[str],
        save_draft_catalog,
        wrap_output=True,
    )
    return response

from datetime import timedelta, datetime, timezone
import logging
import random
from fuzzywuzzy import process, fuzz
import re
import asyncio
from urllib.parse import unquote, urlparse
import uuid
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import base64
from fastapi import HTTPException
from fastapi import status
import stripe
from all_types.internal_types import UserId
from backend_common.auth import (
    load_user_profile,
    update_user_profile,
    update_user_profile_settings,
    firebase_db,
)
from backend_common.background import get_background_tasks
from dataset_helper import excecute_dataset_plan
from backend_common.stripe_backend.customers import fetch_customer
from backend_common.utils.utils import convert_strings_to_ints
from backend_common.gbucket import (
    upload_file_to_google_cloud_bucket,
    delete_file_from_google_cloud_bucket,
)
from config_factory import CONF
from all_types.request_dtypes import *
from all_types.response_dtypes import ResLyrMapData, LayerInfo, ResUserCatalogInfo
from cost_calculator import calculate_cost
from geo_std_utils import fetch_lat_lng_bounding_box
from google_api_connector import (
    fetch_cat_google_maps_api,
    fetch_ggl_nearby,
    # text_fetch_from_google_maps_api,
    calculate_distance_traffic_route,
)
from logging_wrapper import (
    apply_decorator_to_module,
    preserve_validate_decorator,
)
from logging_wrapper import log_and_validate
from constants import load_country_city
from mapbox_connector import MapBoxConnector
from storage_methods import (
    GOOGLE_CATEGORIES,
    REAL_ESTATE_CATEGORIES,
    AREA_INTELLIGENCE_CATEGORIES,
    GRADIENT_COLORS,
    # load_real_estate_categories,
    # load_area_intelligence_categories,
    get_real_estate_dataset_from_storage,
    get_census_dataset_from_storage,
    get_commercial_properties_dataset_from_storage,
    fetch_dataset_id,
    load_dataset,
    update_dataset_layer_matching,
    update_user_layer_matching,
    delete_dataset_layer_matching,
    delete_user_layer_matching,
    fetch_user_catalogs,
    load_user_layer_matching,
    fetch_user_layers,
    load_store_catalogs,
    convert_to_serializable,
    generate_layer_id,
    # load_google_categories,
    get_full_load_geojson,
)
from boolean_query_processor import reduce_to_single_query
from popularity_algo import get_plan, transform_plan_items


logger = logging.getLogger(__name__)


async def fetch_census_realestate(
    req: ReqFetchDataset, data_type
) -> Tuple[Any, str, str, str]:
    next_page_token = req.page_token
    plan_name = ""
    action = req.action
    bknd_dataset_id = ""
    dataset = None

    req.included_types, req.excluded_types = reduce_to_single_query(
        req.boolean_query
    )

    req = fetch_lat_lng_bounding_box(req)
    # bknd_dataset_id = make_dataset_filename(req)
    # TODO remove redundent code
    # dataset = await load_dataset(bknd_dataset_id)

    if not dataset:
        if data_type == "real_estate" or (
            data_type == "commercial" and req.country_name == "Saudi Arabia"
        ):
            (dataset, bknd_dataset_id, next_page_token) = (
                await get_real_estate_dataset_from_storage(
                    bknd_dataset_id,
                    req=req,
                    next_page_token=next_page_token,
                    data_type=data_type,
                )
            )
            if dataset:
                dataset = convert_strings_to_ints(dataset)
                # bknd_dataset_id = await store_data_resp(
                #     req_dataset, dataset, bknd_dataset_id
                # )

    return dataset, bknd_dataset_id, next_page_token, plan_name


async def fetch_catlog_collection():
    """
    Generates and returns a collection of catalog metadata. This function creates
    a list of predefined catalog entries and then adds 20 more dummy entries.
    Each entry contains information such as ID, name, description, thumbnail URL,
    and access permissions. This is likely used for testing or as placeholder data.
    """

    metadata = [
        {
            "id": "2",
            "name": "Saudi Arabia - Real Estate Transactions",
            "description": "Database of real-estate transactions in Saudi Arabia",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/real_estate_ksa.png",
            "catalog_link": "https://example.com/catalog2.jpg",
            "records_number": 20,
            "can_access": True,
        },
        {
            "id": "55",
            "name": "Saudi Arabia - gas stations poi data",
            "description": "Database of all Saudi Arabia gas stations Points of Interests",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "records_number": 8517,
            "can_access": False,
        },
        {
            "id": "65",
            "name": "Saudi Arabia - Restaurants, Cafes and Bakeries",
            "description": "Focusing on the restaurants, cafes and bakeries in KSA",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sau_bak_res.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sau_bak_res.PNG",
            "records_number": 132383,
            "can_access": False,
        },
    ]

    # Add 20 more dummy entries
    for i in range(3, 4):
        metadata.append(
            {
                "id": str(i),
                "name": f"Saudi Arabia - Sample Data {i}",
                "description": f"Sample description for dataset {i}",
                "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/sample_image.png",
                "catalog_link": "https://example.com/sample_image.jpg",
                "records_number": i * 100,
                "can_access": True,
            }
        )

    return metadata


async def fetch_layer_collection():
    """
    Similar to fetch_catlog_collection, this function returns a collection of layer
    metadata. It provides a smaller, fixed set of layer entries. Each entry includes
    details like ID, name, description, and access permissions.
    """

    metadata = [
        {
            "id": "2",
            "name": "Saudi Arabia - Real Estate Transactions",
            "description": "Database of real-estate transactions in Saudi Arabia",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/real_estate_ksa.png",
            "catalog_link": "https://example.com/catalog2.jpg",
            "records_number": 20,
            "can_access": False,
        },
        {
            "id": "3",
            "name": "Saudi Arabia - 3",
            "description": "Database of all Saudi Arabia gas stations Points of Interests",
            "thumbnail_url": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "catalog_link": "https://catalog-assets.s3.ap-northeast-1.amazonaws.com/SAUgasStations.PNG",
            "records_number": 8517,
            "can_access": False,
        },
    ]

    return metadata


async def fetch_country_city_data() -> Dict[str, List[Dict[str, float]]]:
    """
    Returns a set of country and city data for United Arab Emirates, Saudi Arabia, and Canada.
    The data is structured as a dictionary where keys are country names and values are lists of cities.
    """

    data = load_country_city()
    return data


def determine_data_type(
    req: ReqFetchDataset, categories: Dict
) -> Optional[str]:
    """
    Determines the data type based on boolean query.
    Returns:
    - Special category if ALL terms belong to that category
    - "google_categories" if ANY terms are Google or custom terms
    - Raises HTTPException if any terms are not in approved categories (with fuzzy suggestions)
    - Raises HTTPException if mixing Google/custom with special categories
    """
    boolean_query = req.boolean_query

    if not boolean_query:
        return None

    # check if text search is in the boolean query. indicated by @ sign wrapping the search term like @auto parts@ OR @car repair@ OR قطع غيار السيارات NOT بنشر
    # if so remove it from the boolean query and add it to the text search text_search_terms
    text_search_terms = re.findall(r"@([^@]+)@", boolean_query)
    for term in text_search_terms:
        boolean_query = boolean_query.replace(f"@{term}@", f"{term}")

    # Extract just the terms
    terms = set(
        term.strip()
        for term in boolean_query.replace("(", " ")
        .replace(")", " ")
        .replace("AND", " ")
        .replace("OR", " ")
        .replace("NOT", " ")
        .split()
    )

    if not terms:
        return None

    if req.search_type == "keyword_search":
        # If the search type is text_search, we can assume it's a Google search
        # and return the google_categories directly
        return "google_categories"

    # Create a set of all approved terms from all categories and organize by category
    approved_terms = set()
    categories_with_terms = {}

    for category_name, category_terms in categories.items():
        if isinstance(category_terms, list):
            approved_terms.update(category_terms)
            categories_with_terms[category_name] = category_terms

    # Check if all terms are in the approved list
    invalid_terms = terms - approved_terms
    if invalid_terms:
        # Generate fuzzy suggestions for each invalid term
        suggestions = {}
        for invalid_term in invalid_terms:
            # Get top 1 closest match
            closest_match = process.extractOne(
                invalid_term, list(approved_terms), scorer=fuzz.ratio
            )

            # Only suggest if score > 60 to avoid poor suggestions
            if closest_match and closest_match[1] > 60:
                suggestions[invalid_term] = {"did_you_mean": closest_match[0]}
            else:
                suggestions[invalid_term] = {"message": "No close match found"}

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid terms found in boolean query",
                "invalid_terms": list(invalid_terms),
                "suggestions": suggestions,
                "help": "Use terms from the approved categories list below or try the suggested alternatives",
                "available_categories": categories_with_terms,
                "total_available_terms": len(approved_terms),
            },
        )

    # Check non-Google categories first
    for category, category_terms in categories.items():
        if category not in GOOGLE_CATEGORIES:
            matches = terms.intersection(set(category_terms))
            if matches:
                # If we found any special category terms, ALL terms must belong to this category
                if len(matches) != len(terms):
                    non_matching_terms = terms - matches

                    # Generate suggestions for non-matching terms within this category
                    category_suggestions = {}
                    for term in non_matching_terms:
                        closest_in_category = process.extractOne(
                            term, category_terms, scorer=fuzz.ratio
                        )

                        if closest_in_category and closest_in_category[1] > 60:
                            category_suggestions[term] = {
                                "did_you_mean": closest_in_category[0]
                            }
                        else:
                            category_suggestions[term] = {
                                "message": f"No close match in {category} category"
                            }

                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": f"Cannot mix {category} terms with other category terms",
                            "category": category,
                            "valid_category_terms": list(matches),
                            "invalid_mixed_terms": list(non_matching_terms),
                            "suggestions": category_suggestions,
                            "suggestion": f"Use only {category} terms or only general/Google category terms",
                            "available_categories": categories_with_terms,
                        },
                    )
                return category

    # If we get here, no special category matches were found
    # So we can safely return google_categories for either Google terms or custom terms
    return "google_categories"


async def check_purchase(req: ReqFetchDataset, plan_name: str):
    # Skip payment check in test mode
    if CONF.test_mode:
        logger.info("TEST_MODE: Bypassing payment check for full data request")
        return
        
    if req.action == "full data":
        contains_text_search = False
        if "@" in req.boolean_query:
            contains_text_search = True
            estimated_cost = 100
        else:
            estimated_cost, _ = await calculate_cost(
                req, text_search=contains_text_search
            )
            estimated_cost = int(round(estimated_cost[1], 2) * 100)
        user_data = await load_user_profile(req.user_id)
        admin_id = user_data["admin_id"]
        user_owns_this_dataset = False

        if plan_name in user_data["prdcer"]["prdcer_dataset"]:
            user_owns_this_dataset = True

        # if the user already has this dataset on his profile don't charge him
        # if the user already has this dataset on his profile don't charge him
        # if the first query of the full data was successful and returned results
        # deduct money from the user's wallet for the price of this dataset
        # if the user doesn't have funds return a specific error to the frontend to prompt the user to add funds
        if not user_owns_this_dataset:

            if not admin_id:
                customer = await fetch_customer(user_id=req.user_id)
            else:
                customer = await fetch_customer(user_id=admin_id)

            if not customer:
                raise HTTPException(
                    status_code=404, detail="Customer not found"
                )

            if customer["balance"] < estimated_cost:
                raise HTTPException(
                    status_code=400, detail="Insufficient balance in wallet"
                )

            # Deduct funds from the customer's balance in Stripe
            # Note: For deductions, we pass a negative amount
            stripe.Customer.create_balance_transaction(
                customer["id"],
                amount=-estimated_cost,  # Negative amount to decrease balance
                currency="usd",
                description="Deducted funds from wallet",
            )


async def bkgnd_full_load(
    req: ReqFetchDataset, plan_name: str, layer_id: str, next_page_token: str
):

    progress, progress_complete = await fetch_plan_progress(plan_name)

    if not progress_complete:
        get_background_tasks().add_task(
            excecute_dataset_plan, req, plan_name, layer_id, next_page_token
        )

    # if the first query of the full data was successful and returned results continue the fetch data plan in the background
    # when the user has made a purchase as a background task we should finish the plan, the background taks should execute calls within the same level at the same time in a batch of 5 at a time
    # when saving the dataset we should save what is the % availability of this dataset based on the plan , plan that is 50% executed means data available 50%
    # while we are at it we should add the dataset's next refresh date, and a flag saying whether to auto refresh or no
    # after the initiial api call api call, when we return to the frontend we need to add a new key in the return object saying delay before next call ,
    # and we should make this delay 3 seconds
    # in those 3 seconds we hope to allow to backend to advance in the query plan execution
    # the frontend should display the % as a bar with an indication that this bar is filling in those 3 seconds to reassure the user
    # we should return this % completetion to the user to display while the user is watiing for his data

    # TODO this is seperate, optimisation for foreground process of data retrival from db
    # then on subsequent calls using next page token the backend should execute calls within the same level at the same time in a batch of 5 at a time

    # TODO
    # we need to somehow deduplicate our data before we send it to the user, i'm not sure how
    user_data = await load_user_profile(req.user_id)
    user_data["prdcer"]["prdcer_dataset"][f"{plan_name}"] = plan_name
    await update_user_profile(req.user_id, user_data)

    return progress


async def fetch_plan_progress(plan_name):
    progress = 0
    progress_complete = False
    plan_progress_ref = (
        firebase_db.get_async_client()
        .collection("plan_progress")
        .document(plan_name)
    )
    plan_progress_doc = await plan_progress_ref.get()

    if plan_progress_doc.exists:
        plan_progress_data = plan_progress_doc.to_dict()
        progress = plan_progress_data.get("progress", 0)
        completed_at = plan_progress_data.get("completed_at", datetime.min)

        if progress >= 100 and completed_at.replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc) + timedelta(days=90):
            progress_complete = True

            # check if this plan is currently being fetched in the background by checking that last_updated is more than 30 seconds ago
            # last_updated was saved like this firestore.SERVER_TIMESTAMP
        last_updated = plan_progress_data.get("last_updated", datetime.min)
        if last_updated.replace(tzinfo=timezone.utc) > datetime.now(
            timezone.utc
        ) - timedelta(seconds=30):
            progress_complete = True
    return progress, progress_complete


async def fetch_dataset(req: ReqFetchDataset):
    """
    This function attempts to fetch an existing layer based on the provided
    request parameters. If the layer exists, it loads the data, transforms it,
    and returns it. If the layer doesn't exist, it creates a new layer
    """
    next_page_token = None
    progress = 0
    layer_id = req.prdcer_lyr_id
    if req.page_token == "" or req.prdcer_lyr_id == "":
        layer_id = generate_layer_id()

    geojson_dataset = []

    # Load all categories

    categories = await poi_categories(
        ReqCityCountry(country_name=req.country_name, city_name=req.city_name)
    )

    data_type = determine_data_type(req, categories)

    if (
        data_type == "real_estate"
        or data_type in list(AREA_INTELLIGENCE_CATEGORIES.keys())
        or (
            data_type == "commercial"
            and (req.country_name == "Saudi Arabia" or True)
        )
    ):
        geojson_dataset, bknd_dataset_id, next_page_token, plan_name = (
            await fetch_census_realestate(req=req, data_type=data_type)
        )
        progress = 100
    else:
        city_data = fetch_lat_lng_bounding_box(req)

        if city_data is None:
            raise HTTPException(
                status_code=404,
                detail="City not found in the specified country",
            )
        # Default to Google Maps API
        req.lat = city_data.lat
        req.lng = city_data.lng
        req.bounding_box = city_data.bounding_box
        (
            geojson_dataset,
            bknd_dataset_id,
            next_page_token,
            plan_name,
            next_plan_index,
        ) = await fetch_ggl_nearby(req)

        await check_purchase(req, plan_name)

        if req.action == "full data":
            if not req.full_load:
                await bkgnd_full_load(req, plan_name, layer_id, next_page_token)

            if req.full_load:
                # TODO at the moment we can't do full load unless progress is 100 following background task
                progress, progress_complete = await fetch_plan_progress(plan_name)
                progress_check_counts = 0
                while progress <= 100 and progress_check_counts < 1:
                    if progress == 100:
                        plan = await get_plan(plan_name)

                        # execute in db merge+deduplicate all datasets
                        output_filenames = await transform_plan_items(req, plan)
                        geojson_dataset = (
                            await get_full_load_geojson(output_filenames)
                        )
                        
                        break
                    else:
                        progress = await bkgnd_full_load(
                            req, plan_name, layer_id, next_page_token
                        )

                    progress_check_counts += 1

    geojson_dataset["bknd_dataset_id"] = bknd_dataset_id
    geojson_dataset["records_count"] = len(geojson_dataset.get("features", ""))
    geojson_dataset["prdcer_lyr_id"] = layer_id
    geojson_dataset["next_page_token"] = next_page_token
    geojson_dataset["delay_before_next_call"] = 3
    geojson_dataset["progress"] = progress

    return geojson_dataset


async def save_lyr(req: ReqSavePrdcerLyer) -> str:
    user_data = await load_user_profile(req.user_id)

    # Check for duplicate prdcer_layer_name
    new_layer_name = req.model_dump(exclude={"user_id"})["prdcer_layer_name"]
    for layer in user_data["prdcer"]["prdcer_lyrs"].values():
        if layer["prdcer_layer_name"] == new_layer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Layer name '{new_layer_name}' already exists. Layer names must be unique.",
            )

    # Add the new layer to user profile
    user_data["prdcer"]["prdcer_lyrs"][req.prdcer_lyr_id] = req.model_dump(
        exclude={"user_id"}
    )

    # Save updated user data
    await update_user_profile(req.user_id, user_data)
    if req.prdcer_lyr_id:
        await update_user_layer_matching(req.prdcer_lyr_id, req.user_id)
        if req.bknd_dataset_id:
            await update_dataset_layer_matching(
                req.prdcer_lyr_id, req.bknd_dataset_id
            )

    return "Producer layer created successfully"


async def delete_layer(req: ReqDeletePrdcerLayer) -> str:
    """
    Deletes a layer based on its id.
    Args:
        req (ReqDeletePrdcerLayer): The request data containing `user_id` and `prdcer_lyr_id`.

    Returns:
        str: Success message if the layer is deleted.
    """

    bknd_dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
    user_data = await load_user_profile(req.user_id)

    try:
        # Find the layer to delete based on its id
        layers = user_data["prdcer"]["prdcer_lyrs"]
        layer_to_delete = None

        for layer_id, layer in layers.items():
            if layer["prdcer_lyr_id"] == req.prdcer_lyr_id:
                layer_to_delete = layer_id
                break

        if not layer_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer id '{req.prdcer_lyr_id}' not found.",
            )

        # Delete the layer
        del user_data["prdcer"]["prdcer_lyrs"][layer_to_delete]

        # Save updated user data
        await update_user_profile(req.user_id, user_data)
        await delete_dataset_layer_matching(layer_to_delete, bknd_dataset_id)
        await delete_user_layer_matching(layer_to_delete)

    except KeyError as ke:
        logger.error(f"Invalid user data structure for user_id: {req.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data structure",
        ) from ke

    return f"Layer '{req.prdcer_lyr_id}' deleted successfully."


@preserve_validate_decorator
@log_and_validate(logger, validate_output=True, output_model=List[LayerInfo])
async def aquire_user_lyrs(req: UserId) -> List[LayerInfo]:
    """
    Retrieves all producer layers associated with a specific user. It reads the
    user's data file and the dataset-layer matching file to compile a list of
    all layers owned by the user, including metadata like layer name, color,
    and record count.
    """
    user_layers = await fetch_user_layers(req.user_id)

    user_layers_metadata = []
    for lyr_id, lyr_data in user_layers.items():
        try:
            dataset_id, dataset_info = await fetch_dataset_id(lyr_id)
            records_count = dataset_info["records_count"]

            user_layers_metadata.append(
                LayerInfo(
                    prdcer_lyr_id=lyr_id,
                    prdcer_layer_name=lyr_data["prdcer_layer_name"],
                    points_color=lyr_data["points_color"],
                    layer_legend=lyr_data["layer_legend"],
                    layer_description=lyr_data["layer_description"],
                    records_count=records_count,
                    city_name=lyr_data["city_name"],
                    bknd_dataset_id=lyr_data["bknd_dataset_id"],
                    is_zone_lyr="false",
                    progress=random.randint(0, 100),
                )
            )
        except KeyError as e:
            logger.error(f"Missing key in layer data: {str(e)}")
            # Continue to next layer instead of failing the entire request
            continue

    # if not user_layers_metadata:
    #     raise HTTPException(
    #         status_code=404, detail="No valid layers found for the user"
    #     )

    return user_layers_metadata


async def fetch_lyr_map_data(req: ReqPrdcerLyrMapData) -> ResLyrMapData:
    """
    Fetches detailed map data for a specific producer layer.
    """
    # Validate layer ID is not empty
    if not req.prdcer_lyr_id or not req.prdcer_lyr_id.strip():
        raise HTTPException(
            status_code=400, detail="Layer ID cannot be empty"
        )
    
    dataset = {}
    user_layer_matching = await load_user_layer_matching()
    layer_owner_id = user_layer_matching.get(req.prdcer_lyr_id)
    layer_owner_data = await load_user_profile(layer_owner_id)

    try:
        layer_metadata = layer_owner_data["prdcer"]["prdcer_lyrs"][
            req.prdcer_lyr_id
        ]
    except KeyError as ke:
        raise HTTPException(
            status_code=404, detail="Producer layer not found for this user"
        ) from ke

    dataset_id, dataset_info = await fetch_dataset_id(req.prdcer_lyr_id)
    dataset = await load_dataset(dataset_id, fetch_full_plan_datasets=True)

    # Check if dataset was found
    if dataset is None:
        raise HTTPException(
            status_code=404, detail=f"Dataset not found for layer {req.prdcer_lyr_id}"
        )

    # Extract properties from first feature if available
    properties = []
    if dataset.get("features") and len(dataset.get("features", [])) > 0:
        first_feature = dataset.get("features", [])[0]
        properties = list(first_feature.get("properties", {}).keys())

        num_records = len(dataset.get("features"))

    return ResLyrMapData(
        type="FeatureCollection",
        features=dataset.get("features", []),
        properties=properties,  # Add the properties list here
        prdcer_layer_name=layer_metadata.get("prdcer_layer_name"),
        prdcer_lyr_id=req.prdcer_lyr_id,
        bknd_dataset_id=dataset_id,
        points_color=layer_metadata.get("points_color"),
        layer_legend=layer_metadata.get("layer_legend"),
        layer_description=layer_metadata.get("layer_description"),
        city_name=layer_metadata.get("city_name"),
        records_count=num_records,
        is_zone_lyr="false",
        progress=random.randint(0, 100),
    )


async def save_prdcer_ctlg(req: ReqSavePrdcerCtlg) -> str:
    """
    Creates and saves a new producer catalog.
    """

    # add display elements key value pair display_elements:{"polygons":[]}
    # catalog should have "catlog_layer_options":{} extra configurations for the layers with their display options (point,grid:{"size":3, color:#FFFF45},heatmap:{"proeprty":rating})
    try:
        user_data = await load_user_profile(req.user_id)
        new_ctlg_id = str(uuid.uuid4())
        thumbnail_url = "No image uploaded"
        if req.image:
            try:
                thumbnail_url = upload_file_to_google_cloud_bucket(
                    req.image,
                    CONF.gcloud_slocator_bucket_name,
                    CONF.gcloud_images_bucket_path,
                    CONF.secrets_dir + CONF.gcloud_bucket_credentials_json_path,
                )
                # serialize url to be saved in firestore safely using base64
                thumbnail_url = base64.b64encode(
                    thumbnail_url.encode()
                ).decode()

            except Exception as e:
                logger.error(f"Error uploading image: {str(e)}")
                # Keep the original thumbnail_url if upload fails

        # Create new catalog using Pydantic model
        new_catalog = ResUserCatalogInfo(
            prdcer_ctlg_name=req.prdcer_ctlg_name,
            prdcer_ctlg_id=new_ctlg_id,
            subscription_price=req.subscription_price,
            ctlg_description=req.ctlg_description,
            total_records=req.total_records,
            lyrs=req.lyrs,
            thumbnail_url=thumbnail_url,
            ctlg_owner_user_id=req.user_id,
            display_elements=req.display_elements,
        )
        user_data["prdcer"]["prdcer_ctlgs"][
            new_ctlg_id
        ] = new_catalog.model_dump()
        # serializable_user_data = convert_to_serializable(user_data)
        await update_user_profile(req.user_id, user_data)
        return new_ctlg_id
    except Exception as e:
        raise e


async def delete_prdcer_ctlg(req: ReqDeletePrdcerCtlg) -> str:
    """
    Deletes an existing producer catalog.
    """
    try:
        # Load the user profile to get the catalog
        user_data = await load_user_profile(req.user_id)

        # Check if the catalog exists
        if req.prdcer_ctlg_id not in user_data["prdcer"]["prdcer_ctlgs"]:
            raise ValueError(f"Catalog ID {req.prdcer_ctlg_id} not found.")

        thumbnail_url = user_data["prdcer"]["prdcer_ctlgs"][req.prdcer_ctlg_id][
            "thumbnail_url"
        ]

        # Delete the catalog
        del user_data["prdcer"]["prdcer_ctlgs"][req.prdcer_ctlg_id]

        # Delete the thumbnail image from Google Cloud Storage if it exists
        if thumbnail_url:
            # Extract the file path from the URL (assuming the URL is like 'https://storage.googleapis.com/bucket_name/path/to/file.jpg')
            parsed_url = urlparse(thumbnail_url)
            blob_name = unquote(parsed_url.path.lstrip("/").split("/", 1)[-1])
            # file_path = thumbnail_url.split(CONF.gcloud_slocator_bucket_name+"/")[-1]  # Get the file path (e.g., "path/to/file.jpg")
            delete_file_from_google_cloud_bucket(
                blob_name,
                CONF.gcloud_slocator_bucket_name,
                CONF.secrets_dir + CONF.gcloud_bucket_credentials_json_path,
            )

        # Update the user profile after deleting the catalog
        await update_user_profile(req.user_id, user_data)

        return f"Catalog with ID {req.prdcer_ctlg_id} deleted successfully."

    except Exception as e:
        logger.error(f"Error deleting catalog: {str(e)}")
        raise e


async def fetch_prdcer_ctlgs(req: UserId) -> List[ResUserCatalogInfo]:
    """
    Retrieves all producer catalogs associated with a specific user.
    """
    try:
        user_catalogs = await fetch_user_catalogs(req.user_id)
        validated_catalogs = []

        for ctlg_id, ctlg_data in user_catalogs.items():
            validated_catalogs.append(
                ResUserCatalogInfo(
                    prdcer_ctlg_id=ctlg_id,
                    prdcer_ctlg_name=ctlg_data["prdcer_ctlg_name"],
                    ctlg_description=ctlg_data["ctlg_description"],
                    thumbnail_url=ctlg_data.get("thumbnail_url", ""),
                    subscription_price=ctlg_data["subscription_price"],
                    ctlg_owner_user_id=ctlg_data["ctlg_owner_user_id"],
                    total_records=ctlg_data.get("total_records", 0),
                )
            )
        return validated_catalogs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching catalogs: {str(e)}",
        ) from e


async def fetch_ctlg_lyrs(req: ReqFetchCtlgLyrs) -> List[ResLyrMapData]:
    """
    Fetches all layers associated with a specific catalog.
    """
    try:
        user_data = await load_user_profile(req.user_id)
        ctlg = (
            user_data.get("prdcer", {})
            .get("prdcer_ctlgs", {})
            .get(req.prdcer_ctlg_id, {})
        )
        if not ctlg:
            store_ctlgs = load_store_catalogs()
            ctlg = next(
                (
                    ctlg_info
                    for ctlg_key, ctlg_info in store_ctlgs.items()
                    if ctlg_key == req.prdcer_ctlg_id
                ),
                {},
            )
        if not ctlg:
            raise HTTPException(status_code=404, detail="Catalog not found")

        ctlg_owner_data = await load_user_profile(ctlg["ctlg_owner_user_id"])
        ctlg_lyrs_map_data = []

        for lyr_info in ctlg["lyrs"]:
            lyr_id = lyr_info["layer_id"]
            dataset_id, dataset_info = await fetch_dataset_id(lyr_id)
            trans_dataset = await load_dataset(
                dataset_id, fetch_full_plan_datasets=True
            )
            # trans_dataset = await MapBoxConnector.new_ggl_to_boxmap(trans_dataset)

            # Extract properties from first feature if available
            properties = []
            if (
                trans_dataset.get("features")
                and len(trans_dataset["features"]) > 0
            ):
                first_feature = trans_dataset["features"][0]
                properties = list(first_feature.get("properties", {}).keys())

            lyr_metadata = (
                ctlg_owner_data.get("prdcer", {})
                .get("prdcer_lyrs", {})
                .get(lyr_id, {})
            )

            ctlg_lyrs_map_data.append(
                ResLyrMapData(
                    type="FeatureCollection",
                    features=trans_dataset["features"],
                    properties=properties,  # Add the properties list here
                    prdcer_layer_name=lyr_metadata.get(
                        "prdcer_layer_name", f"Layer {lyr_id}"
                    ),
                    prdcer_lyr_id=lyr_id,
                    bknd_dataset_id=dataset_id,
                    points_color=lyr_metadata.get("points_color", "red"),
                    layer_legend=lyr_metadata.get("layer_legend", ""),
                    layer_description=lyr_metadata.get("layer_description", ""),
                    records_count=len(trans_dataset["features"]),
                    city_name=lyr_metadata["city_name"],
                    is_zone_lyr="false",
                    progress=None,
                )
            )
        return ctlg_lyrs_map_data
    except HTTPException:
        raise


async def load_area_intelligence_categories(req: ReqCityCountry = "") -> Dict:
    """
    Loads and returns a dictionary of area intelligence categories.
    """
    return AREA_INTELLIGENCE_CATEGORIES


async def poi_categories(req: ReqCityCountry = "") -> Dict:
    """
    Provides a comprehensive list of place categories, including Google places,
    real estate, and other custom categories.
    """

    # combine all category types
    categories = {
        **GOOGLE_CATEGORIES,
        **REAL_ESTATE_CATEGORIES,
        **AREA_INTELLIGENCE_CATEGORIES,
    }

    return categories


async def save_draft_catalog(req: ReqSavePrdcerLyer) -> str:
    try:
        user_data = await load_user_profile(req.user_id)
        if len(req.lyrs) > 0:

            new_ctlg_id = str(uuid.uuid4())
            new_catalog = {
                "prdcer_ctlg_name": req.prdcer_ctlg_name,
                "prdcer_ctlg_id": new_ctlg_id,
                "subscription_price": req.subscription_price,
                "ctlg_description": req.ctlg_description,
                "total_records": req.total_records,
                "lyrs": req.lyrs,
                "thumbnail_url": req.thumbnail_url,
                "ctlg_owner_user_id": req.user_id,
            }
            user_data["prdcer"]["draft_ctlgs"][new_ctlg_id] = new_catalog

            serializable_user_data = convert_to_serializable(user_data)
            await update_user_profile(req.user_id, serializable_user_data)

            return new_ctlg_id
        else:
            raise HTTPException(
                status_code=400,
                detail="No layers found in the request",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving draft catalog: {str(e)}",
        ) from e


async def fetch_gradient_colors() -> List[List]:
    """ """
    return GRADIENT_COLORS


async def given_layer_fetch_dataset(layer_id: str):
    # given layer id get dataset
    user_layer_matching = await load_user_layer_matching()
    layer_owner_id = user_layer_matching.get(layer_id)
    layer_owner_data = await load_user_profile(layer_owner_id)
    try:
        layer_metadata = layer_owner_data["prdcer"]["prdcer_lyrs"][layer_id]
    except KeyError as ke:
        raise HTTPException(
            status_code=404, detail="Producer layer not found for this user"
        ) from ke

    dataset_id, dataset_info = await fetch_dataset_id(layer_id)
    all_datasets = await load_dataset(dataset_id, fetch_full_plan_datasets=True)

    return all_datasets, layer_metadata


async def get_user_profile(req):
    return await load_user_profile(req.user_id)


async def load_distance_drive_time_polygon(req: ReqSrcDistination) -> dict:
    """
    Returns: {
        "distance in km": float,
        "duration in minutes": float,         # e.g. "1 hour 23 mins"
        "polyline": str          # Encoded route shape
    }
    """
    route_info = await calculate_distance_traffic_route(
        origin=f"{req.source.lat},{req.source.lng}",
        destination=f"{req.destination.lat},{req.destination.lng}",
    )
    if not route_info.route:
        raise HTTPException(status_code=400, detail="No route found")
    leg = route_info.route[0]
    # time from str to float and to minutes
    drive_time_seconds = (
        float(leg.duration.replace("s", ""))
        if isinstance(leg.duration, str)
        else float(leg.duration)
    )
    drive_time_minutes = drive_time_seconds / 60

    # Convert meters to kilometers
    distance_km = float(leg.distance) / 1000
    return {
        "distance_in_km": round(distance_km, 2),
        "drive_time_in_min": round(drive_time_minutes, 2),
        "drive_polygon": leg.polyline,
    }


async def update_profile(req):
    return await update_user_profile_settings(req)


# Apply the decorator to all functions in this module
apply_decorator_to_module(logger)(__name__)

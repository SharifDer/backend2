import logging
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, Tuple, Optional
import json
import os
from use_json import use_json
from naming_strings import TOKEN_SEPARATOR
from fastapi import HTTPException, status
from pydantic import BaseModel
from backend_common.auth import load_user_profile
from backend_common.database import Database
import pandas as pd
from sql_object import SqlObject
from all_types.request_dtypes import ReqFetchDataset, ReqIntelligenceData
from all_types.response_dtypes import PopulationViewportData
from logging_wrapper import apply_decorator_to_module
from backend_common.auth import firebase_db
import asyncpg
from backend_common.background import get_background_tasks
import orjson
from popularity_algo import get_plan
import geopandas as gpd
from shapely.geometry import box, Point
import geopandas as gpd
from shapely.geometry import box
from fastapi import HTTPException
import geopandas as gpd
from shapely.geometry import box
import json
import time
from fastapi import HTTPException
import math




logger = logging.getLogger(__name__)

BACKEND_DIR = "Backend/real_estate_storage"
USERS_PATH = "Backend/users"
STORE_CATALOGS_PATH = "Backend/store_catalogs.json"
DATASET_LAYER_MATCHING_PATH = "Backend/dataset_layer_matching.json"
DATASETS_PATH = "Backend/datasets"
USER_LAYER_MATCHING_PATH = "Backend/user_layer_matching.json"
METASTORE_PATH = "Backend/layer_category_country_city_matching"
STORAGE_DIR = "Backend/storage"
COLOR_PATH = "Backend/gradient_colors.json"
USERS_INFO_PATH = "Backend/users_info.json"
RIYADH_VILLA_ALLROOMS = "Backend/riyadh_villa_allrooms.json"  # to be change to real estate id needed
GOOGLE_CATEGORIES_PATH = "Backend/google_categories.json"
REAL_ESTATE_CATEGORIES_PATH = "Backend/real_estate_categories.json"
# Add a new constant for census categories path
area_intelligence_categories_PATH = "Backend/area_intelligence_categories.json"
# Map census types to their respective CSV files
CENSUS_FILE_MAPPING = {
    "household": "Backend/census_data/Final_household_all.csv",
    "population": "Backend/census_data/Final_population_all.csv",
    "housing": "Backend/census_data/Final_housing_all.csv",
    "economic": "Backend/census_data/Final_economic_all.csv",
}

DEFAULT_LIMIT = 20

os.makedirs(STORAGE_DIR, exist_ok=True)


with open(GOOGLE_CATEGORIES_PATH, "r") as f:
    GOOGLE_CATEGORIES = json.load(f)
with open(REAL_ESTATE_CATEGORIES_PATH, "r") as f:
    REAL_ESTATE_CATEGORIES = json.load(f)
with open(area_intelligence_categories_PATH, "r") as f:
    AREA_INTELLIGENCE_CATEGORIES = json.load(f)
with open(COLOR_PATH, "r") as f:
    GRADIENT_COLORS = json.load(f)


def to_serializable(obj: Any) -> Any:
    """
    Convert a Pydantic model or any other object to a JSON-serializable format.

    Args:
    obj (Any): The object to convert.

    Returns:
    Any: A JSON-serializable representation of the object.
    """
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(to_serializable(item) for item in obj)
    elif isinstance(obj, BaseModel):
        return to_serializable(obj.dict(by_alias=True))
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):
        return to_serializable(obj.__dict__)
    else:
        return obj


def convert_to_serializable(obj: Any) -> Any:
    """
    Convert an object to a JSON-serializable format and verify serializability.

    Args:
    obj (Any): The object to convert.

    Returns:
    Any: A JSON-serializable representation of the object.

    Raises:
    ValueError: If the object cannot be serialized to JSON.
    """
    try:
        serializable_obj = to_serializable(obj)
        json.dumps(serializable_obj)
        return serializable_obj
    except (TypeError, OverflowError, ValueError) as e:
        raise ValueError(f"Object is not JSON serializable: {str(e)}")


async def fetch_dataset_id(lyr_id: str) -> Tuple[str, Dict]:
    """
    Searches for the dataset ID associated with a given layer ID.
    """
    dataset_layer_matching = await load_dataset_layer_matching()

    for d_id, dataset_info in dataset_layer_matching.items():
        if lyr_id in dataset_info["prdcer_lyrs"]:
            return d_id, dataset_info
    # raise HTTPException(
    #     status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found for this layer"
    # )


def fetch_layer_owner(prdcer_lyr_id: str) -> str:
    """
    Fetches the owner of a layer based on the producer layer ID.
    """
    with open(USER_LAYER_MATCHING_PATH, "r") as f:
        user_layer_matching = json.load(f)
    layer_owner_id = user_layer_matching.get(prdcer_lyr_id)
    if not layer_owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer owner not found",
        )
    return layer_owner_id


async def load_dataset_layer_matching() -> Dict:
    """Load dataset layer matching from Firestore"""
    try:
        return await firebase_db.get_document(
            "layer_matchings", "dataset_matching"
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            return {}
        raise e


async def update_dataset_layer_matching(
    prdcer_lyr_id: str, bknd_dataset_id: str, records_count: int = 9191919
):
    collection_name = "layer_matchings"
    document_id = "dataset_matching"

    dataset_layer_matching = await firebase_db.get_document(
        collection_name, document_id
    )

    if bknd_dataset_id not in dataset_layer_matching:
        dataset_layer_matching[bknd_dataset_id] = {
            "records_count": records_count,
            "prdcer_lyrs": [],
        }

    if (
        prdcer_lyr_id
        not in dataset_layer_matching[bknd_dataset_id]["prdcer_lyrs"]
    ):
        dataset_layer_matching[bknd_dataset_id]["prdcer_lyrs"].append(
            prdcer_lyr_id
        )

    dataset_layer_matching[bknd_dataset_id]["records_count"] = records_count

    # Update cache immediately
    firebase_db._cache[collection_name][document_id] = dataset_layer_matching

    async def _background_update():
        doc_ref = (
            firebase_db.get_async_client()
            .collection(collection_name)
            .document(document_id)
        )
        await doc_ref.set(dataset_layer_matching)

    get_background_tasks().add_task(_background_update)
    return dataset_layer_matching


async def delete_dataset_layer_matching(
    prdcer_lyr_id: str, bknd_dataset_id: str, records_count: int = 9191919
):
    collection_name = "layer_matchings"
    document_id = "dataset_matching"

    try:
        dataset_layer_matching = await firebase_db.get_document(
            collection_name, document_id
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            dataset_layer_matching = {}
        else:
            raise e

    if bknd_dataset_id not in dataset_layer_matching:
        dataset_layer_matching[bknd_dataset_id] = {
            "records_count": records_count,
            "prdcer_lyrs": [],
        }

    # Check if the producer layer exists in the dataset
    if (
        prdcer_lyr_id
        not in dataset_layer_matching[bknd_dataset_id]["prdcer_lyrs"]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer {prdcer_lyr_id} not found in dataset {bknd_dataset_id}",
        )

    # Remove the layer ID from the dataset's 'prdcer_lyrs' list
    dataset_layer_matching[bknd_dataset_id]["prdcer_lyrs"].remove(prdcer_lyr_id)

    # Update cache immediately
    firebase_db._cache[collection_name][document_id] = dataset_layer_matching

    async def _background_update():
        # Update the dataset layer matching document in the database
        doc_ref = (
            firebase_db.get_async_client()
            .collection(collection_name)
            .document(document_id)
        )
        await doc_ref.set(dataset_layer_matching)

    # Run background task to persist the changes in the database
    get_background_tasks().add_task(_background_update)

    return {
        "message": f"Layer {prdcer_lyr_id} removed from dataset {bknd_dataset_id} successfully"
    }


async def load_user_layer_matching() -> Dict:
    """Load user layer matching from Firestore"""
    try:
        return await firebase_db.get_document(
            "layer_matchings", "user_matching"
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            return {}
        raise e


async def update_user_layer_matching(layer_id: str, layer_owner_id: str):
    collection_name = "layer_matchings"
    document_id = "user_matching"

    user_layer_matching = await firebase_db.get_document(
        collection_name, document_id
    )

    user_layer_matching[layer_id] = layer_owner_id

    # Update cache immediately
    firebase_db._cache[collection_name][document_id] = user_layer_matching

    async def _background_update():
        doc_ref = (
            firebase_db.get_async_client()
            .collection(collection_name)
            .document(document_id)
        )
        await doc_ref.set(user_layer_matching)

    get_background_tasks().add_task(_background_update)
    return user_layer_matching


async def delete_user_layer_matching(layer_id: str):
    collection_name = "layer_matchings"
    document_id = "user_matching"

    try:
        # Fetch the current layer matching data
        user_layer_matching = await firebase_db.get_document(
            collection_name, document_id
        )
    except HTTPException as e:
        # Handle cases where the document is not found
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User layer matching document not found",
            )
        else:
            raise e

    # Check if the layer_id exists in the mapping
    if layer_id not in user_layer_matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer {layer_id} not found in the user layer matching.",
        )

    # Remove the layer from the user_layer_matching
    del user_layer_matching[layer_id]

    # Update cache immediately
    firebase_db._cache[collection_name][document_id] = user_layer_matching

    # Background update to persist the change in the database
    async def _background_update():
        doc_ref = (
            firebase_db.get_async_client()
            .collection(collection_name)
            .document(document_id)
        )
        await doc_ref.set(user_layer_matching)

    get_background_tasks().add_task(_background_update)
    return {"message": f"Layer {layer_id} removed successfully."}


async def fetch_user_layers(user_id: str) -> Dict[str, Any]:
    try:
        user_data = await load_user_profile(user_id)
        user_layers = user_data.get("prdcer", {}).get("prdcer_lyrs", {})
        return user_layers
    except FileNotFoundError as fnfe:
        logger.error(f"User layers not found for user_id: {user_id}")
        raise HTTPException(
            status_code=404, detail="User layers not found"
        ) from fnfe


async def fetch_user_catalogs(user_id: str) -> Dict[str, Any]:

    user_data = await load_user_profile(user_id)
    user_catalogs = user_data.get("prdcer", {}).get("prdcer_ctlgs", {})
    return user_catalogs


# def create_new_user(user_id: str, username: str, email: str) -> None:
#     user_file_path = os.path.join(USERS_PATH, f"user_{user_id}.json")

#     if os.path.exists(user_file_path):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User profile already exists",
#         )

#     user_data = {
#         "user_id": user_id,
#         "username": username,
#         "email": email,
#         "prdcer": {"prdcer_lyrs": {}, "prdcer_ctlgs": {}},
#     }

#     try:
#         with open(user_file_path, "w") as f:
#             json.dump(user_data, f, indent=2)
#     except IOError:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Error creating new user profile",
#         )


def load_store_catalogs() -> Dict[str, Any]:
    try:
        with open(STORE_CATALOGS_PATH, "r") as f:
            store_ctlgs = json.load(f)
        return store_ctlgs
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store catalogs file not found",
        )


def update_metastore(ccc_filename: str, bknd_dataset_id: str):
    """Update the metastore with the new layer information"""
    if bknd_dataset_id is not None:
        metastore_data = {
            "bknd_dataset_id": bknd_dataset_id,
            "created_at": datetime.now().isoformat(),
        }
        with open(f"{METASTORE_PATH}/{ccc_filename}", "w") as f:
            json.dump(metastore_data, f)


def get_country_code(country_name: str) -> str:
    country_codes = {
        "United Arab Emirates": "AE",
        "Saudi Arabia": "SA",
        "Canada": "CA",
    }
    return country_codes.get(country_name, "")


def generate_layer_id() -> str:
    return "l" + str(uuid.uuid4())


def remove_exclusions_from_id(dataset_id: str) -> str:
    """Removes 'excluding_*' from the dataset ID to find a broader match."""
    parts = dataset_id.split("_")
    filtered_parts = [p for p in parts if not p.startswith("excluding")]
    return "_".join(filtered_parts)


async def store_place_details(filename_id: str, place_details: dict):
    if place_details:
        await Database.execute(
            SqlObject.store_dataset,
            filename_id,
            json.dumps(""),
            json.dumps(place_details),
            datetime.utcnow(),
        )


async def store_data_resp(
    req: ReqFetchDataset, dataset: Dict, file_name: str
) -> str:
    """
    Stores Google Maps data in the database, creating the table if needed.

    Args:
        req: Location request object
        dataset: Response data from Google Maps

    Returns:
        str: Filename/ID used as the primary key
    """
    try:
        filtered_features = []
        for feature in dataset.get("features", []):
            if feature["properties"]["id"] != "n/a":
                filtered_features.append(feature)
        dataset["features"] = filtered_features

        if dataset.get("features"):
            # Convert request object to dictionary using Pydantic's model_dump
            req_dict = req.model_dump()

            await Database.execute(
                SqlObject.store_dataset,
                file_name,
                json.dumps(req_dict),
                json.dumps(dataset),
                datetime.utcnow(),
            )

            return file_name

    except asyncpg.exceptions.UndefinedTableError:
        # If table doesn't exist, create it and retry
        await Database.execute(SqlObject.create_datasets_table)
        return await store_data_resp(req, dataset, file_name)


async def load_place_details(place_id: str) -> Optional[dict]:
    json_content = await Database.fetchrow(
        SqlObject.load_dataset_with_timestamp, place_id
    )
    if json_content:
        json_content = orjson.loads(json_content.get("response_data", "{}"))
    return json_content


async def load_dataset(dataset_id: str, fetch_full_plan_datasets=False) -> Dict:
    """
    Loads a dataset from file based on its ID.
    """

    #TODO temporary soultion this shouldn't be needed if we were removing the properties from the dataset before saving
    def select_sub_properties(dataset):
        fields = [
            "displayName", "rating", "user_ratings_total","formattedAddress", "internationalPhoneNumber",
            "types", "priceLevel", "primaryType", "userRatingCount", "location",
            "name", "id","popularity_score", "photos","types","googleMapsUri","phone"
        ]
    
        filtered_features = []
    
        for feature in dataset.get("features", []):
            # Create new filtered feature with proper GeoJSON structure
            filtered_feature = {
                "type": feature.get("type", "Feature"),
                "geometry": feature.get("geometry"),  # Keep the geometry
                "properties": {}  # Start with empty properties dict
            }
            
            # Only add the properties we want
            feature_properties = feature.get("properties", {})
            for field in fields:
                if field in feature_properties:
                    filtered_feature["properties"][field] = feature_properties[field]
            
            filtered_features.append(filtered_feature)
    
        # Update the dataset with filtered features
        dataset["features"] = filtered_features
        return dataset


    # if the dataset_id contains the word plan '21.57445341427591_39.1728_30000.0_mosque__plan_mosque_Saudi Arabia_Jeddah@#$9'
    # isolate the plan's name from the dataset_id = mosque__plan_mosque_Saudi Arabia_Jeddah
    # load the plan's json file
    # from the dataset_id isolate the page number which is after @#$ = 9
    # using the page number and the plan , load and concatenate all datasets from the plan that have page number equal to that number or less
    # each dataset is a list of dictionaries , so just extend the list  and save the big final list into dataset variable
    # else load dataset with dataset id
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

    if "plan" in dataset_id and fetch_full_plan_datasets:
        # Extract plan name and page number
        if f"{TOKEN_SEPARATOR}" in dataset_id:
            plan_name, page_number = dataset_id.split(f"{TOKEN_SEPARATOR}")
            dataset_prefix, plan_name = plan_name.split("page_token=")
            page_number = int(page_number)
        else:
            plan_name = dataset_id
            # TODO bad assumption below to say it's at max 100 different paginations but this is for perrformance now
            page_number = 100
        # Load the plan
        plan = await get_plan(plan_name)
        if not plan:
            return {}

        # TODO this is a temp fix because this whole thing needs to be redone
        new_plan = []
        for i, item in enumerate(plan):
            if item == "end of search plan":
                continue

            first_parts = item.split("_", 3)
            lat, lon, value, rest = first_parts
            category = rest.split("_circle=")[0].replace(" ", "_")

            if i == 0:
                new_item = f"{lat}_{lon}_{value}_{category}_token="
            else:
                new_item = f"{lat}_{lon}_{value}_{category}_token=page_token={plan_name}@#${i}"

            new_plan.append(new_item)

        # Initialize an empty list to store all datasets
        all_features = []
        feat_collec = {"type": "FeatureCollection", "features": []}
        properties_set = set()  # Initialize a set to store unique properties
        for i in range(page_number):
            dataset_id = new_plan[i]  # Get the formatted item for this page
            json_content = await Database.fetchrow(
                SqlObject.load_dataset_with_timestamp, dataset_id
            )
            if json_content:
                created_at = json_content.get("created_at")
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at and created_at < three_months_ago:
                    await Database.execute(SqlObject.delete_dataset, dataset_id)
                    json_content = None
            if json_content:
                dataset = orjson.loads(json_content.get("response_data", "{}"))
                all_features.extend(dataset.get("features", []))
                properties_set.update(dataset.get("properties", []))
        if all_features:
            # Create the final combined GeoJSON
            feat_collec["features"] = all_features
            feat_collec["properties"] = list(properties_set)
        #TODO temporary soultion this shouldn't be needed if we were removing the properties from the dataset before saving
        feat_collec = select_sub_properties(feat_collec)
    
    elif "real_estate" in dataset_id:
        # Parse the real estate dataset ID to extract bounding box and type
        # Format: saudi_real_estate_riyadh_box=46.082,24.172,47.268,25.255_type=warehouse_for_rent
        # Extract bounding box
        box_start = dataset_id.find("box=") + 4
        box_end = dataset_id.find("_type=")
        bbox_str = dataset_id[box_start:box_end]
        bbox_coords = [float(coord) for coord in bbox_str.split(",")]
        
        # Extract type
        type_start = dataset_id.find("type=") + 5
        type_str = dataset_id[type_start:]
        # Handle multiple types separated by commas
        property_types = [t.strip() for t in type_str.split(",")]
        
        # bbox_coords format: [min_lng, min_lat, max_lng, max_lat]
        min_lng = bbox_coords[0]
        min_lat = bbox_coords[1]
        max_lng = bbox_coords[2]
        max_lat = bbox_coords[3] 
        
        # Query the database using the correct parameter mapping
        city_data = await Database.fetch(
            SqlObject.real_estate_full_data,
            property_types,  # $1 - category array
            min_lng,
            min_lat,
            max_lng,
            max_lat
        )
        
        # Convert to DataFrame and then to GeoJSON format
        city_df = pd.DataFrame([dict(record) for record in city_data])
        
        # Convert to GeoJSON format
        features = []
        for _, row in city_df.iterrows():
            # Parse coordinates
            coordinates = [float(row["longitude"]), float(row["latitude"])]
            
            # Create properties dict excluding certain columns
            columns_to_drop = ["latitude", "longitude", "city"]
            if "country" in row:
                columns_to_drop.append("country")
            properties = row.drop(columns_to_drop).to_dict()
            
            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coordinates},
                "properties": properties,
            }
            features.append(feature)
        
        # Create GeoJSON structure
        feat_collec = {
            "type": "FeatureCollection", 
            "features": features,
            "properties": list(city_df.columns) if not city_df.empty else []
        }

            
    else:
        feat_collec = None
        json_content = await Database.fetchrow(
            SqlObject.load_dataset_with_timestamp, dataset_id
        )
        if json_content:
            created_at = json_content.get("created_at")
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at and created_at < three_months_ago:
                await Database.execute(SqlObject.delete_dataset, dataset_id)
                json_content = None

        if json_content:
            feat_collec = orjson.loads(json_content.get("response_data", "{}"))

        #TODO temporary soultion this shouldn't be needed if we were removing the properties from the dataset before saving
        if feat_collec:
            feat_collec = select_sub_properties(feat_collec)

    return feat_collec


async def get_census_dataset_from_storage(
    filename: str,
    action: str,
    request_location: ReqFetchDataset,
    next_page_token: str,
    data_type: str,
) -> tuple[dict, str, str]:
    """
    Retrieves census data from CSV files based on the data type requested.
    Returns data in GeoJSON format for consistency with other dataset types.
    """

    # Determine which CSV file to use based on included types
    # data_type = req.included_types[0]  # Using first type for now

    if data_type in ["Population Area Intelligence"]:
        query = SqlObject.census_w_bounding_box
    # elif data_type in ["Housing Area Intelligence"]:
    #     query = SqlObject.census_w_bounding_box
    # elif data_type in ["Income Area Intelligence"]:
    #     query = SqlObject.economic_w_bounding_box

    city_data = await Database.fetch(
        query, *request_location.bounding_box, request_location.zoom_level
    )
    city_df = pd.DataFrame([dict(record) for record in city_data], dtype=object)
    # city_df = pd.DataFrame(city_data, dtype=object)

    # Convert to GeoJSON format
    features = []
    for _, row in city_df.iterrows():
        # Parse coordinates from Degree column
        coordinates = [float(row["longitude"]), float(row["latitude"])]

        # Create properties dict excluding certain columns
        columns_to_drop = ["latitude", "longitude", "city"]
        if "country" in row:
            columns_to_drop.append("country")

        row = row.dropna()
        properties = row.drop(columns_to_drop).to_dict()

        if len(row) == 0:
            continue

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coordinates},
            "properties": properties,
        }
        features.append(feature)

    # Create GeoJSON structure similar to Google Maps API response
    geojson_data = {"type": "FeatureCollection", "features": features}

    # Generate a unique filename if one isn't provided
    if not filename:
        filename = f"census_{request_location.city_name.lower()}_{data_type}"

    return geojson_data, filename, next_page_token


async def get_commercial_properties_dataset_from_storage(
    filename: str,
    action: str,
    request_location: ReqFetchDataset,
    next_page_token: str,
    data_type: str,
) -> tuple[dict, str, str]:
    """
    Retrieves commercial properties data from database based on the data type requested.
    Returns data in GeoJSON format for consistency with other dataset types.
    """
    data_type = request_location.included_types[0]

    page_number = 0
    if next_page_token:
        page_number = int(next_page_token)

    offset = page_number * DEFAULT_LIMIT

    query = SqlObject.canada_commercial_w_bounding_box_and_property_type

    city_data = await Database.fetch(
        query,
        data_type.replace("_", " "),
        *request_location.bounding_box,
        DEFAULT_LIMIT,
        offset,
    )
    city_df = pd.DataFrame([dict(record) for record in city_data])

    # Convert to GeoJSON format
    features = []
    for _, row in city_df.iterrows():
        # Parse coordinates from Degree column
        coordinates = [float(row["longitude"]), float(row["latitude"])]

        # Create properties dict excluding certain columns
        columns_to_drop = ["latitude", "longitude", "city"]
        if "country" in row:
            columns_to_drop.append("country")
        properties = row.drop(columns_to_drop).to_dict()

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coordinates},
            "properties": properties,
        }
        features.append(feature)

    # Create GeoJSON structure similar to Google Maps API response
    geojson_data = {"type": "FeatureCollection", "features": features}

    # Generate a unique filename if one isn't provided
    if not filename:
        filename = f"commercial_canada_{request_location.city_name.lower()}_{data_type}"

    if len(features) < DEFAULT_LIMIT:
        next_page_token = ""
    else:
        next_page_token = str(page_number + 1)

    return geojson_data, filename, next_page_token


async def get_real_estate_dataset_from_storage(
    bknd_dataset_id: str,
    req: ReqFetchDataset,
    next_page_token: str,
    data_type: str,
) -> tuple[dict, str, str]:
    """
    Retrieves data from storage based on the location request.
    """
    data_type = req.included_types
    # TODO at moment the user will only give one category, in the future we should see how to implement this with more
    # realEstateData=(await load_real_estate_categories())
    # filtered_categories = [item for item in realEstateData if item in req.included_types]
    # final_categories = [item for item in filtered_categories if item not in req.excludedTypes]
    next_page_token = ""
    if req.action == "sample":
        page_number = 0
        offset = page_number * DEFAULT_LIMIT
        query = SqlObject.saudi_real_estate_w_bounding_box_and_category
        city_data = await Database.fetch(
            query, data_type, *req.bounding_box, DEFAULT_LIMIT, offset
        )
    if req.action == "full data":
        query = SqlObject.real_estate_full_data
        city_data = await Database.fetch(
            query, data_type, *req.bounding_box
        )
    city_df = pd.DataFrame([dict(record) for record in city_data])
    # Convert to GeoJSON format
    features = []
    for _, row in city_df.iterrows():
        # Parse coordinates from Degree column
        coordinates = [float(row["longitude"]), float(row["latitude"])]
        # Create properties dict excluding certain columns
        columns_to_drop = ["latitude", "longitude", "city"]
        if "country" in row:
            columns_to_drop.append("country")
        properties = row.drop(columns_to_drop).to_dict()
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coordinates},
            "properties": properties,
        }
        features.append(feature)
   
    geojson_data = {"type": "FeatureCollection", "features": features}
    
    # Format bounding box as min_lng,min_lat,max_lng,max_lat
    bbox_str = f"{req.bounding_box[0]},{req.bounding_box[1]},{req.bounding_box[2]},{req.bounding_box[3]}"
    
    # Format data type - handle both single string and list formats
    if isinstance(data_type, list):
        type_str = ",".join(data_type)
    else:
        type_str = str(data_type)
    
    # Create the new filename format with explicit prefixes
    bknd_dataset_id = f"saudi_real_estate_{req.city_name.lower()}_box={bbox_str}_type={type_str}"
    
    return geojson_data, bknd_dataset_id, next_page_token


async def fetch_db_categories_by_lat_lng(bounding_box: list[float]) -> Dict:
    # call db with bounding box
    pass


def combine_income_and_population_data(population_data, income_data):
    # Create a lookup dictionary from income data using Main_ID as key
    income_lookup = {}
    for feature in income_data["features"]:
        main_id = feature["properties"]["Main_ID"]
        income_lookup[main_id] = feature["properties"][
            "income"
        ]  # Only store the income value

    # Create a copy of population data to avoid modifying the original
    combined_data = population_data.copy()
    combined_data["features"] = []
    combined_data["properties"].append("Income")

    # Loop through population features and add income data
    for pop_feature in population_data["features"]:
        # Create a copy of the population feature
        combined_feature = pop_feature.copy()
        combined_feature["properties"] = pop_feature["properties"].copy()

        # Get the Main_ID
        main_id = pop_feature["properties"]["Main_ID"]

        # Add income property if matching Main_ID exists
        if main_id in income_lookup:
            combined_feature["properties"]["income"] = income_lookup[main_id]
        else:
            combined_feature["properties"]["income"] = None

        combined_data["features"].append(combined_feature)

    return combined_data



async def fetch_intelligence_by_viewport(req: ReqIntelligenceData) -> Dict:
    """
    Fetches population data from local GeoJSON files based on viewport and zoom level.
    """
    # TODO first check if the user has purchased intelligence

    population_centers = None  # Initialize population centers

    if req.population and not req.income:
        base_path = f"Backend/population_json_files/v{req.zoom_level}/" 
        file_path =  base_path + "all_features.geojson"
        intelligence_geojson_data = await use_json(file_path, "r")
        layer_type = "population"
        if not intelligence_geojson_data:
            raise Exception(
                f"could not find geojson data for zoom level {req.zoom_level}, in folder {file_path}"
            )
        
        # Load population centers when population is requested
        centers_file_path =  base_path + "population_centers.geojson"
        population_centers = await use_json(centers_file_path, "r")

        # Filter population centers based on viewport
        if population_centers and population_centers.get("features"):
            filtered_centers = []
            for center in population_centers["features"]:
                coords = center.get("geometry", {}).get("coordinates", [])
                lng, lat = coords[1], coords[0]
                # Check if point is within viewport bounds
                if (req.min_lng <= lng <= req.max_lng and 
                    req.min_lat <= lat <= req.max_lat):
                    filtered_centers.append(center)
            
            # Update population_centers with filtered results
            population_centers = {
                **population_centers,
                "features": filtered_centers
            } if filtered_centers else None

    # if income is also true load income
    if req.income:
        file_path = f"Backend/area_income_geojson/v{req.zoom_level}/all_features.geojson"
        intelligence_geojson_data = await use_json(file_path, "r")
        layer_type = "income"

    if not intelligence_geojson_data:
        raise Exception(
            f"could not find geojson data for zoom level {req.zoom_level}, in folder {file_path}"
        )

    # Load only the required portion from the GeoJSON
    filtered_features = []
    
    # Only collect density values for income normalization
    density_values = [] if req.income else None

    for feature in intelligence_geojson_data.get("features", []):
        # For polygon features, do a basic bounds check (faster than full intersection)
        geom_type = feature.get("geometry", {}).get("type")
        coords = feature.get("geometry", {}).get("coordinates", [])

        # Simple bounding box check (this is much faster than full geometric operations)
        if geom_type == "Polygon":
            # Extract the bounds of the polygon (min/max lng/lat)
            flat_coords = [point for ring in coords for point in ring]
            lngs = [p[0] for p in flat_coords]
            lats = [p[1] for p in flat_coords]

            # Check if polygon bbox overlaps viewport
            poly_min_lng = min(lngs)
            poly_max_lng = max(lngs)
            poly_min_lat = min(lats)
            poly_max_lat = max(lats)

            # If polygon bounding box overlaps viewport, include it
            if (
                poly_min_lng <= req.max_lng
                and poly_max_lng >= req.min_lng
                and poly_min_lat <= req.max_lat
                and poly_max_lat >= req.min_lat
            ):

                properties = feature.get("properties", {})

                if layer_type == "population":
                    # Density is already pre-calculated in the JSON files
                    filtered_features.append(feature)
                    
                elif layer_type == "income":
                    # For income, calculate and collect for normalization
                    income = properties.get("income", 0)  # Update field name as needed
                    area_km2 = calculate_polygon_area_km2(coords)  # Keep this function for income
                    raw_density = income / area_km2 if area_km2 > 0 else 0
                    density_values.append(raw_density)
                    filtered_features.append((feature, raw_density))

    # Only normalize for income
    if req.income and density_values:
        min_density = min(density_values)
        max_density = max(density_values)
        density_range = max_density - min_density if max_density > min_density else 1
        
        # Process income features with normalization
        processed_features = []
        for feature, raw_density in filtered_features:
            normalized_density = ((raw_density - min_density) / density_range) * 100
            feature["properties"]["density"] = round(normalized_density, 6)
            processed_features.append(feature)
        
        filtered_features = processed_features

    # Extract properties from first feature if available
    properties = []
    if filtered_features and len(filtered_features) > 0:
        properties = list(filtered_features[0].get("properties", {}).keys())

    # Return raw dictionary
    intelligence_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features,
        "metadata": {
            "color": "#e74c3c" if layer_type == "population" else "#3498db",
            "name": f"{layer_type.title()} Density Layer",
            "layer_type": layer_type,
            "zoom_level": req.zoom_level,
            "population_centers": population_centers,
        },
        "properties": properties,
        "records_count": len(filtered_features),
    }

    return intelligence_geojson


async def get_full_load_geojson(filenames: list[str]) -> str:

    formatted_filenames_list = []
    for fname in filenames:
        escaped_fname = fname.replace("'", "''")  # Escape single quotes for SQL
        formatted_filenames_list.append(f"'{escaped_fname}'")

    sql_query = """
WITH FileList AS (
    SELECT unnest($1::text[]) AS filename
),
DistinctFeatureIds AS (
    SELECT
        jsonb_extract_path_text(features.feature -> 'properties', 'id') as feature_id,
        FIRST_VALUE(features.feature) OVER (
            PARTITION BY jsonb_extract_path_text(features.feature -> 'properties', 'id')
            ORDER BY d.created_at DESC, (d.filename NOT LIKE '%_text_search=true_') DESC, d.filename DESC
        ) as geojson_feature_obj
    FROM
        schema_marketplace.datasets d
        JOIN FileList fl ON d.filename = fl.filename,
        LATERAL jsonb_array_elements(d.response_data -> 'features') AS features(feature)
    WHERE
        d.response_data IS NOT NULL
        AND jsonb_typeof(d.response_data) = 'object'
        AND jsonb_typeof(d.response_data -> 'features') = 'array'
        AND jsonb_array_length(d.response_data -> 'features') > 0
        AND jsonb_typeof(features.feature) = 'object'
        AND jsonb_typeof(features.feature -> 'properties') = 'object'
        AND (features.feature -> 'properties' ->> 'id') IS NOT NULL
),
AggregatedUniqueFeatures AS (
    SELECT DISTINCT geojson_feature_obj
    FROM DistinctFeatureIds
)
SELECT
    jsonb_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(jsonb_agg(auf.geojson_feature_obj), '[]'::jsonb),
        'properties', (
            SELECT response_data -> 'properties'
            FROM schema_marketplace.datasets d
            JOIN FileList fl ON d.filename = fl.filename
            ORDER BY (d.filename NOT LIKE '%_text_search=true_') DESC, d.created_at DESC, d.filename DESC
            LIMIT 1
        )
    ) AS merged_geojson
FROM
    AggregatedUniqueFeatures auf;
"""

    merged_deduplicated_data = await Database.fetchrow(sql_query, filenames)
    if merged_deduplicated_data:
        merged_geojson = orjson.loads(
            merged_deduplicated_data.get("merged_geojson", "{}")
        )
    return merged_geojson


# Apply the decorator to all functions in this module
apply_decorator_to_module(logger)(__name__)



def calculate_polygon_area_km2(coordinates):
    """
    Calculate approximate area of polygon in square kilometers.
    Uses simple lat/lng to approximate area (good enough for density calculations).
    """
    if not coordinates or not coordinates[0]:
        return 1  # Default to avoid division by zero

    # Get the outer ring (first array in coordinates)
    ring = coordinates[0]
    if len(ring) < 3:
        return 1

    # Simple area calculation in square degrees, then convert to km2
    area_sq_degrees = 0
    n = len(ring) - 1  # Last point same as first, so exclude it

    for i in range(n):
        j = (i + 1) % n
        area_sq_degrees += ring[i][0] * ring[j][1]
        area_sq_degrees -= ring[j][0] * ring[i][1]

    area_sq_degrees = abs(area_sq_degrees) / 2

    # Rough conversion from square degrees to square kilometers
    lat_avg = sum(point[1] for point in ring[:n]) / n
    km_per_degree_lat = 111.0
    km_per_degree_lng = 111.0 * math.cos(math.radians(lat_avg))
    area_km2 = area_sq_degrees * km_per_degree_lat * km_per_degree_lng

    return max(area_km2, 0.01)  # Minimum area to avoid division by zero


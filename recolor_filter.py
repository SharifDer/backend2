from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException
from all_types.response_dtypes import (
    ResRecolorBasedon,
    NearestPointRouteResponse,
)
from google_api_connector import calculate_distance_traffic_route
from geo_std_utils import calculate_distance
from all_types.request_dtypes import *
from data_fetcher import given_layer_fetch_dataset, fetch_user_layers
from geopy.distance import geodesic
import numpy as np
import uuid
import asyncio
from agents import *

# Type definitions
FilterResult = Dict[str, List[Dict[str, Any]]]
LayerConfig = Dict[str, Any]


# ============================================================================
# CORE UTILITY FUNCTIONS
# ============================================================================

def extract_coordinates(dataset: Dict[str, Any]) -> List[Dict[str, float]]:
    """Extract latitude/longitude coordinates from a dataset."""
    if dataset is None or "features" not in dataset:
        return []
    return [
        {
            "latitude": point["geometry"]["coordinates"][1],
            "longitude": point["geometry"]["coordinates"][0],
        }
        for point in dataset["features"]
    ]


def create_feature(point: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized feature from a point."""
    return {
        "type": "Feature",
        "geometry": point["geometry"],
        "properties": point.get("properties", {}),
    }


def find_matching_feature(
    dataset: Dict[str, Any], target_coord: Dict[str, float]
) -> Optional[Dict[str, Any]]:
    """Find feature matching target coordinates."""
    for feature in dataset["features"]:
        if (
            feature["geometry"]["coordinates"][1] == target_coord["latitude"]
            and feature["geometry"]["coordinates"][0] == target_coord["longitude"]
        ):
            return feature
    return None


def apply_comparison(value: Any, threshold: Any, comparison_operator: str) -> bool:
    """
    Apply comparison operation based on comparison_operator.
    
    Args:
        value: The value to compare
        threshold: The threshold to compare against
        comparison_operator: "less" or "more"
    
    Returns:
        bool: Result of the comparison
    """
    if comparison_operator == "less":
        return value <= threshold
    else:  # "more"
        return value >= threshold


def calculate_nearby_average(
    property_name: str,
    point: Dict[str, Any],
    reference_dataset: Dict[str, Any],
    radius: float,
) -> Optional[float]:
    """Calculate average metric value of points within radius."""
    lat, lon = (
        point["geometry"]["coordinates"][1],
        point["geometry"]["coordinates"][0],
    )
    nearby_values = []

    for ref_point in reference_dataset["features"]:
        if property_name not in ref_point["properties"]:
            continue

        distance = geodesic(
            (lat, lon),
            (
                ref_point["geometry"]["coordinates"][1],
                ref_point["geometry"]["coordinates"][0],
            ),
        ).meters

        if distance <= radius:
            nearby_values.append(ref_point["properties"][property_name])

    if nearby_values:
        cleaned_values = [
            float(x)
            for x in nearby_values
            if str(x).strip() and not isinstance(x, bool)
        ]
        return np.mean(cleaned_values) if cleaned_values else None
    return None


# ============================================================================
# CARDINAL POINTS AND DRIVE TIME CALCULATION
# ============================================================================

def find_cardinal_extreme_points(
    coordinates: List[Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    """Find the furthest points in each cardinal direction (N, S, E, W)."""
    if not coordinates:
        return {}

    extremes = {
        "north": coordinates[0],
        "south": coordinates[0],
        "east": coordinates[0],
        "west": coordinates[0],
    }

    for coord in coordinates:
        if coord["latitude"] > extremes["north"]["latitude"]:
            extremes["north"] = coord
        if coord["latitude"] < extremes["south"]["latitude"]:
            extremes["south"] = coord
        if coord["longitude"] > extremes["east"]["longitude"]:
            extremes["east"] = coord
        if coord["longitude"] < extremes["west"]["longitude"]:
            extremes["west"] = coord

    return extremes


async def calculate_regional_driving_speed(
    cardinal_extremes: Dict[str, Dict[str, float]],
) -> float:
    """Calculate average driving speed from cardinal extreme points."""
    total_speed = 0
    speed_count = 0

    pairs = [
        ("north", "south"),
        ("east", "west"),
        ("north", "east"),
        ("south", "west"),
    ]

    tasks = []
    call_info = []

    for point1_dir, point2_dir in pairs:
        if point1_dir in cardinal_extremes and point2_dir in cardinal_extremes:
            point1 = cardinal_extremes[point1_dir]
            point2 = cardinal_extremes[point2_dir]

            origin = f"{point1['latitude']},{point1['longitude']}"
            destination = f"{point2['latitude']},{point2['longitude']}"

            task = calculate_distance_traffic_route(origin, destination)
            tasks.append(task)
            call_info.append((point1, point2))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            point1, point2 = call_info[i]

            try:
                if (
                    not isinstance(result, Exception)
                    and result.route
                    and result.route[0].static_duration
                ):
                    drive_time_seconds = int(
                        result.route[0].static_duration.replace("s", "")
                    )
                    distance_meters = calculate_distance(point1, point2)

                    if drive_time_seconds > 0:
                        speed_mps = distance_meters / drive_time_seconds
                        total_speed += speed_mps
                        speed_count += 1
            except:
                continue

    return total_speed / speed_count if speed_count > 0 else 11.11


def estimate_drive_time_by_distance(
    target_coord: Dict[str, float],
    reference_coord: Dict[str, float],
    avg_speed_mps: float,
) -> float:
    """Estimate drive time based on straight-line distance and regional average speed."""
    distance_meters = calculate_distance(target_coord, reference_coord)
    road_distance_factor = 1.3
    estimated_road_distance = distance_meters * road_distance_factor
    estimated_time_minutes = (estimated_road_distance / avg_speed_mps) / 60
    return estimated_time_minutes


# ============================================================================
# FILTERING FUNCTIONS
# ============================================================================

def filter_by_name(dataset: Dict[str, Any], names: List[str]) -> FilterResult:
    """Filter features by name matching."""
    names_lower = [name.strip().lower() for name in names]
    matched, unmatched = [], []

    for feature in dataset["features"]:
        feature_name = feature["properties"].get("name", "").strip().lower()
        target_list = (
            matched
            if any(name in feature_name for name in names_lower)
            else unmatched
        )
        target_list.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}


def filter_by_property(
    dataset: Dict[str, Any], 
    property_name: str, 
    property_value: Any,
    comparison_operator: str
) -> FilterResult:
    """Filter features by property value with comparison."""
    matched, unmatched = [], []

    for feature in dataset["features"]:
        props = feature["properties"]
        feature_value = props.get(property_name)

        if feature_value is None:
            unmatched.append(create_feature(feature))
            continue

        try:
            if property_name == "types":
                is_match = property_value in feature_value
            elif property_name in ["rating", "popularity_score", "user_ratings_total", "heatmap_weight"]:
                is_match = apply_comparison(float(feature_value), property_value, comparison_operator)
            else:
                is_match = apply_comparison(feature_value, property_value, comparison_operator)

            target_list = matched if is_match else unmatched
            target_list.append(create_feature(feature))
        except (ValueError, TypeError):
            unmatched.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}


def filter_by_distance(
    target_coords: List[Dict[str, float]],
    reference_coords: List[Dict[str, float]],
    threshold: float,
    comparison_operator: str,
    distance_unit: str = "meters"
) -> List[Dict[str, float]]:
    """Filter coordinates by distance threshold."""
    valid_coords = []
    threshold_meters = threshold * 1000 if distance_unit == "km" else threshold

    for target in target_coords:
        for ref in reference_coords:
            if target != ref:
                distance = calculate_distance(ref, target)
                if apply_comparison(distance, threshold_meters, comparison_operator):
                    valid_coords.append(target)
                    break

    return valid_coords


async def filter_by_drive_time(
    target_coords: List[Dict[str, float]],
    reference_coords: List[Dict[str, float]],
    threshold_minutes: float,
    comparison_operator: str
) -> Tuple[List[Dict[str, float]], List[Dict[str, float]]]:
    """Filter coordinates by drive time using cardinal points method."""
    cardinal_extremes = find_cardinal_extreme_points(reference_coords)
    
    if len(cardinal_extremes) < 2:
        return [], target_coords  # No valid routing possible

    avg_speed_mps = await calculate_regional_driving_speed(cardinal_extremes)
    
    within_time = []
    outside_time = []

    for target_coord in target_coords:
        min_estimated_time = float("inf")

        for ref_coord in reference_coords:
            estimated_time = estimate_drive_time_by_distance(
                target_coord, ref_coord, avg_speed_mps
            )
            min_estimated_time = min(min_estimated_time, estimated_time)

        if apply_comparison(min_estimated_time, threshold_minutes, comparison_operator):
            within_time.append(target_coord)
        else:
            outside_time.append(target_coord)

    return within_time, outside_time


def create_filter_result_from_coords(
    dataset: Dict[str, Any],
    valid_coords: List[Dict[str, float]],
    all_coords: List[Dict[str, float]]
) -> FilterResult:
    """Create FilterResult from coordinate lists."""
    matched, unmatched = [], []
    
    for feature in dataset["features"]:
        feature_coord = {
            "latitude": feature["geometry"]["coordinates"][1],
            "longitude": feature["geometry"]["coordinates"][0],
        }
        
        target_list = matched if feature_coord in valid_coords else unmatched
        target_list.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}


async def create_drive_time_filter_result(
    dataset: Dict[str, Any],
    target_coords: List[Dict[str, float]],
    reference_coords: List[Dict[str, float]],
    threshold_minutes: float,
    comparison_operator: str
) -> FilterResult:
    """Create FilterResult for drive time filtering."""
    within_time_coords, outside_time_coords = await filter_by_drive_time(
        target_coords, reference_coords, threshold_minutes, comparison_operator
    )
    
    within_time, outside_time, unallocated = [], [], []
    
    for feature in dataset["features"]:
        feature_coord = {
            "latitude": feature["geometry"]["coordinates"][1],
            "longitude": feature["geometry"]["coordinates"][0],
        }
        
        feature_obj = create_feature(feature)
        
        if feature_coord in within_time_coords:
            within_time.append(feature_obj)
        elif feature_coord in outside_time_coords:
            outside_time.append(feature_obj)
        else:
            unallocated.append(feature_obj)

    return {
        "within_time": within_time,
        "outside_time": outside_time,
        "unallocated": unallocated,
    }


# ============================================================================
# LAYER CONFIGURATION AND CREATION
# ============================================================================

def create_layer_configs(
    filter_type: str,
    comparison_operator: str,
    threshold: float,
    req: ReqRecolorBasedon,
    unit: str = ""
) -> List[LayerConfig]:
    """Create layer configurations based on filter type and comparison."""
    
    if filter_type == "name":
        return [
            {
                "feature_key": "matched",
                "category": "matched",
                "name_suffix": "Matched Names",
                "color": req.change_lyr_new_color,
                "legend": f"Contains: {', '.join(req.list_names)}",
                "description": f"Features matching names: {', '.join(req.list_names)}",
            },
            {
                "feature_key": "unmatched",
                "category": "unmatched",
                "name_suffix": "Unmatched Names",
                "color": req.change_lyr_current_color,
                "legend": "No name match",
                "description": "Features without matching names",
            },
        ]
    
    elif filter_type == "drive_time":
        symbol = "≤" if comparison_operator == "less" else "≥"
        primary_desc = f"{comparison_operator} than {threshold} minutes"
        opposite_desc = f"{'more' if comparison_operator == 'less' else 'less'} than {threshold} minutes"
        
        return [
            {
                "feature_key": "within_time",
                "category": "primary_condition",
                "name_suffix": f"Drive Time {symbol} {threshold}m",
                "color": req.change_lyr_new_color,
                "legend": f"Drive Time {symbol} {threshold} min",
                "description": f"Points {primary_desc} drive time",
            },
            {
                "feature_key": "outside_time",
                "category": "opposite_condition",
                "name_suffix": f"Drive Time {'>' if comparison_operator == 'less' else '<'} {threshold}m",
                "color": req.change_lyr_current_color,
                "legend": f"Drive Time {'>' if comparison_operator == 'less' else '<'} {threshold} min",
                "description": f"Points {opposite_desc} drive time",
            },
            {
                "feature_key": "unallocated",
                "category": "unallocated",
                "name_suffix": "No Route Available",
                "color": "#FFFFFF",
                "legend": "No route available",
                "description": "Points with no available route information",
            },
        ]
    
    elif filter_type == "radius":
        symbol = "≤" if comparison_operator == "less" else "≥"
        primary_desc = f"{comparison_operator} than {threshold} {unit}"
        opposite_desc = f"{'more' if comparison_operator == 'less' else 'less'} than {threshold} {unit}"
        
        return [
            {
                "feature_key": "matched",
                "category": "primary_condition",
                "name_suffix": f"Radius {symbol} {threshold}{unit}",
                "color": req.change_lyr_new_color,
                "legend": f"{symbol} {threshold} {unit} from {req.based_on_lyr_name}",
                "description": f"Points {primary_desc}",
            },
            {
                "feature_key": "unmatched",
                "category": "opposite_condition",
                "name_suffix": f"Radius {'>' if comparison_operator == 'less' else '<'} {threshold}{unit}",
                "color": req.change_lyr_current_color,
                "legend": f"{'>' if comparison_operator == 'less' else '<'} {threshold} {unit} from {req.based_on_lyr_name}",
                "description": f"Points {opposite_desc}",
            },
        ]
    
    else:  # property-based filtering
        symbol = "≤" if comparison_operator == "less" else "≥"
        return [
            {
                "feature_key": "matched",
                "category": "primary_condition", 
                "name_suffix": f"{filter_type.title()} {symbol} {threshold}",
                "color": req.change_lyr_new_color,
                "legend": f"{filter_type} {symbol} {threshold}",
                "description": f"Points with {filter_type} {comparison_operator} than {threshold}",
            },
            {
                "feature_key": "unmatched",
                "category": "opposite_condition",
                "name_suffix": f"{filter_type.title()} {'>' if comparison_operator == 'less' else '<'} {threshold}",
                "color": req.change_lyr_current_color,
                "legend": f"{filter_type} {'>' if comparison_operator == 'less' else '<'} {threshold}",
                "description": f"Points with {filter_type} {'more' if comparison_operator == 'less' else 'less'} than {threshold}",
            },
        ]


def create_layers_from_config(
    filtered_features: FilterResult,
    base_name: str,
    layer_configs: List[LayerConfig],
    change_layer_id: str,
    city_name: str = "",
) -> List[ResRecolorBasedon]:
    """Create layers from filtered features using configuration."""
    layers = []

    for config in layer_configs:
        features = filtered_features.get(config["feature_key"], [])
        if not features:
            continue

        layers.append(
            ResRecolorBasedon(
                type="FeatureCollection",
                features=features,
                properties=(
                    list(features[0].get("properties", {}).keys())
                    if features
                    else []
                ),
                prdcer_layer_name=f"{base_name} - {config['name_suffix']}",
                prdcer_lyr_id=str(uuid.uuid4()),
                sub_lyr_id=f"{change_layer_id}_{config['category']}",
                bknd_dataset_id="",
                points_color=config["color"],
                layer_legend=config["legend"],
                layer_description=config["description"],
                records_count=len(features),
                city_name=city_name,
                is_zone_lyr="true",
                progress=0,
            )
        )

    return layers


# ============================================================================
# GRADIENT PROCESSING
# ============================================================================

async def process_gradient_coloring(
    req: ReqRecolorBasedon,
) -> List[ResRecolorBasedon]:
    """Process gradient coloring based on surrounding point influence."""
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)

    influence_scores = []
    point_influence_map = {}

    for point in change_dataset["features"]:
        point_id = str(uuid.uuid4())
        point["id"] = point_id

        avg_influence = calculate_nearby_average(
            req.property_name, point, reference_dataset, req.coverage_value
        )

        if avg_influence is not None:
            influence_scores.append(avg_influence)
            point_influence_map[point_id] = avg_influence

    if not influence_scores:
        unallocated_features = [create_feature(point) for point in change_dataset["features"]]
        return [create_unallocated_layer(unallocated_features, req, change_metadata)]

    percentiles = [16.67, 33.33, 50, 66.67, 83.33]
    thresholds = np.percentile(influence_scores, percentiles)
    layer_groups = [[] for _ in range(len(thresholds) + 2)]

    for point in change_dataset["features"]:
        feature = create_feature(point)
        influence = point_influence_map.get(point["id"])

        if influence is None:
            layer_index = -1
            feature["properties"]["influence_score"] = None
        else:
            layer_index = next(
                (i for i, threshold in enumerate(thresholds) if influence <= threshold),
                len(thresholds),
            )
            feature["properties"]["influence_score"] = influence

        layer_groups[layer_index].append(feature)

    layers = []
    for i, features in enumerate(layer_groups):
        if features:
            layers.append(create_gradient_layer(features, i, thresholds, req, change_metadata))

    return layers


def create_unallocated_layer(
    features: List[Dict[str, Any]],
    req: ReqRecolorBasedon,
    metadata: Dict[str, Any],
) -> ResRecolorBasedon:
    """Create layer for unallocated points."""
    return ResRecolorBasedon(
        type="FeatureCollection",
        features=features,
        properties=(list(features[0].get("properties", {}).keys()) if features else []),
        prdcer_layer_name="Unallocated Points",
        prdcer_lyr_id=req.change_lyr_id,
        sub_lyr_id=f"{req.change_lyr_id}_unallocated",
        bknd_dataset_id="",
        points_color="#FFFFFF",
        layer_legend="No nearby points",
        layer_description="Points with no nearby reference points",
        records_count=len(features),
        city_name=metadata.get("city_name", ""),
        is_zone_lyr="true",
        progress=0,
    )


def create_gradient_layer(
    features: List[Dict[str, Any]],
    layer_index: int,
    thresholds: List[float],
    req: ReqRecolorBasedon,
    metadata: Dict[str, Any],
) -> ResRecolorBasedon:
    """Create a single gradient layer."""
    color = (
        req.color_grid_choice[layer_index]
        if layer_index < len(req.color_grid_choice)
        else "#FFFFFF"
    )

    if layer_index == len(thresholds) + 1:
        legend = "No nearby points"
    elif layer_index == 0:
        legend = f"Influence Score < {thresholds[0]:.2f}"
    elif layer_index == len(thresholds):
        legend = f"Influence Score > {thresholds[-1]:.2f}"
    else:
        legend = f"Influence Score {thresholds[layer_index-1]:.2f} - {thresholds[layer_index]:.2f}"

    return ResRecolorBasedon(
        type="FeatureCollection",
        features=features,
        properties=(list(features[0].get("properties", {}).keys()) if features else []),
        prdcer_layer_name=f"Gradient Layer {layer_index + 1}",
        prdcer_lyr_id=req.change_lyr_id,
        sub_lyr_id=f"{req.change_lyr_id}_gradient_{layer_index + 1}",
        bknd_dataset_id="",
        points_color=color,
        layer_legend=legend,
        layer_description=f"Gradient layer based on nearby {req.property_name} influence",
        records_count=len(features),
        city_name=metadata.get("city_name", ""),
        is_zone_lyr="true",
        progress=0,
    )


# ============================================================================
# MAIN API FUNCTIONS
# ============================================================================

async def recolor_based_on(req: ReqRecolorBasedon) -> List[ResRecolorBasedon]:
    """Main function to process color-based filtering requests."""
    
    # Fetch datasets
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    city_name = change_metadata.get("city_name", "")
    
    # Handle name-based filtering
    if req.property_name == "name":
        if not req.list_names:
            raise ValueError("list_names must be provided when property_name is 'name'.")
        if req.based_on_lyr_id == req.change_lyr_id:
            raise ValueError("based_on_lyr_id and change_lyr_id must be different.")

        filtered_features = filter_by_name(change_dataset, req.list_names)
        filter_type = "name"
        base_name = req.change_lyr_name
        
    # Handle coverage-based filtering
    elif hasattr(req, "area_coverage_property") and req.area_coverage_property:
        reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)
        reference_coords = extract_coordinates(reference_dataset)
        target_coords = extract_coordinates(change_dataset)
        
        if req.area_coverage_property == "drive_time":
            filtered_features = await create_drive_time_filter_result(
                change_dataset, target_coords, reference_coords,
                req.coverage_value, req.comparison_operator
            )
            filter_type = "drive_time"
            base_name = f"{req.change_lyr_name} based on {req.based_on_lyr_name}"
        else:  # radius
            valid_coords = filter_by_distance(
                target_coords, reference_coords, req.coverage_value, 
                req.comparison_operator, "km"
            )
            filtered_features = create_filter_result_from_coords(
                change_dataset, valid_coords, target_coords
            )
            filter_type = "radius"
            base_name = req.change_lyr_name
        
    # Handle gradient coloring
    else:
        return await process_gradient_coloring(req)
    
    # Common layer creation logic
    layer_configs = create_layer_configs(filter_type, req.comparison_operator, 
                                       getattr(req, 'coverage_value', 0), req)
    layer = create_layers_from_config(
        filtered_features, base_name, layer_configs, req.change_lyr_id, city_name
    )
    return layer


async def filter_based_on(req: ReqFilter) -> List[ResRecolorBasedon]:
    """Filter features based on coverage and property criteria."""
    
    # Fetch datasets
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)
    
    # Check if datasets are valid
    if change_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found for change layer")
    if reference_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found for reference layer")
    
    # Extract coordinates
    reference_coords = extract_coordinates(reference_dataset)
    target_coords = extract_coordinates(change_dataset)
    
    # Apply coverage filter
    if req.area_coverage_property == "drive_time":
        valid_coords, _ = await filter_by_drive_time(
            target_coords, reference_coords, req.coverage_value, req.comparison_operator
        )
    elif req.area_coverage_property == "radius":
        valid_coords = filter_by_distance(
            target_coords, reference_coords, req.coverage_value, 
            req.comparison_operator, "km"
        )
    else:
        valid_coords = target_coords
    
    # Create initial filtered dataset
    temp_features = []
    if change_dataset and "features" in change_dataset:
        for feature in change_dataset["features"]:
            feature_coord = {
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0],
            }
            if feature_coord in valid_coords:
                temp_features.append(feature)
    
    temp_dataset = {"features": temp_features}
    
    # Apply property filter if specified
    if req.property_name:
        if req.property_name == "name":
            property_result = filter_by_name(temp_dataset, req.list_names)
            final_features = property_result["matched"]
        else:
            property_result = filter_by_property(
                temp_dataset, req.property_name, req.property_threshold, req.comparison_operator
            )
            final_features = property_result["matched"]
    else:
        final_features = [create_feature(f) for f in temp_features]
    
    # Create result layers
    if not final_features:
        raise ValueError("No features found based on the given criteria.")
    
    # Create individual layers for each feature
    layers = []
    symbol = "≤" if req.comparison_operator == "less" else "≥"
    
    for feature in final_features:
        layer = ResRecolorBasedon(
            prdcer_layer_name=(
                f"{req.change_lyr_name} - Drive Time Filter" 
                if req.area_coverage_property == "drive_time"
                else f"{req.change_lyr_name} - Radius Filter"
            ),
            prdcer_lyr_id=str(uuid.uuid4()),
            bknd_dataset_id="",
            points_color=req.change_lyr_current_color,
            layer_legend=(
                f"Drive Time {symbol} {req.coverage_value} min" 
                if req.area_coverage_property == "drive_time"
                else f"Radius {symbol} {req.coverage_value} km"
            ),
            is_zone_lyr="true",
            type="FeatureCollection",
            features=[feature],
            properties=list(feature.get("properties", {}).keys()),
            sub_lyr_id=(
                f"{req.change_lyr_id}_drive_time_filter" 
                if req.area_coverage_property == "drive_time"
                else f"{req.change_lyr_id}_radius_filter"
            ),
            layer_description="Filtered based on coverage and property criteria",
            records_count=1,
            city_name=change_metadata.get("city_name", ""),
            progress=0,
        )
        layers.append(layer)
    
    return layers


async def recolor_based_on_agent(req: ReqPrompt) -> ValidationResult:
    """Process agent-based color filtering requests."""
    user_layers = req.layers or await fetch_user_layers(req.user_id)

    # Validate prompt
    prompt_validator = PromptValidationAgent()
    validation_result = prompt_validator(req.prompt, user_layers)

    if not validation_result.is_valid:
        return validation_result

    # Generate request object
    recolor_agent = ReqGradientColorBasedOnZoneAgent()
    recolor_object = recolor_agent(req.prompt, user_layers)

    # Validate output
    output_validator = OutputValidationAgent()
    final_validation = output_validator(req.prompt, recolor_object, user_layers)

    if final_validation.is_valid:
        final_validation.endpoint = "gradient_color_based_on_zone"
        final_validation.body = recolor_object

    return final_validation
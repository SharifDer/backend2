from typing import List, Dict, Any, Tuple
from all_types.response_dtypes import (
    ResGradientColorBasedOnZone,
    NearestPointRouteResponse,
)

from google_api_connector import calculate_distance_traffic_route
from geo_std_utils import calculate_distance
from all_types.request_dtypes import *
from data_fetcher import given_layer_fetch_dataset

from geopy.distance import geodesic
import numpy as np
import uuid


from all_types.response_dtypes import (
    ResGradientColorBasedOnZone,
    NearestPointRouteResponse,
)
from agents import *
from data_fetcher import given_layer_fetch_dataset, fetch_user_layers

# Core utility functions
def extract_coordinates(dataset: Dict[str, Any]) -> List[Dict[str, float]]:
    """Extract latitude/longitude coordinates from a dataset."""
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

def calculate_nearby_average(
    color_based_on: str, 
    point: Dict[str, Any], 
    reference_dataset: Dict[str, Any], 
    radius: float
) -> Optional[float]:
    """Calculate average metric value of points within radius."""
    lat, lon = point["geometry"]["coordinates"][1], point["geometry"]["coordinates"][0]
    nearby_values = []

    for ref_point in reference_dataset["features"]:
        if color_based_on not in ref_point["properties"]:
            continue

        distance = geodesic(
            (lat, lon),
            (ref_point["geometry"]["coordinates"][1], ref_point["geometry"]["coordinates"][0])
        ).meters

        if distance <= radius:
            nearby_values.append(ref_point["properties"][color_based_on])

    if nearby_values:
        cleaned_values = [
            float(x) for x in nearby_values 
            if str(x).strip() and not isinstance(x, bool)
        ]
        return np.mean(cleaned_values) if cleaned_values else None
    return None

# Generic filtering functions
FilterResult = Dict[str, List[Dict[str, Any]]]

def filter_by_name(dataset: Dict[str, Any], names: List[str]) -> FilterResult:
    """Filter features by name matching."""
    names_lower = [name.strip().lower() for name in names]
    matched, unmatched = [], []

    for feature in dataset["features"]:
        feature_name = feature["properties"].get("name", "").strip().lower()
        target_list = matched if any(name in feature_name for name in names_lower) else unmatched
        target_list.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}

def filter_by_property(
    dataset: Dict[str, Any], 
    property_name: str, 
    property_value: Any
) -> FilterResult:
    """Filter features by property value."""
    matched, unmatched = [], []

    for feature in dataset["features"]:
        props = feature["properties"]
        feature_value = props.get(property_name)
        
        is_match = False
        if property_name in ["rating", "popularity_score", "user_ratings_total", "heatmap_weight"]:
            is_match = float(feature_value) <= property_value
        elif property_name == "types":
            is_match = property_value in feature_value
        else:
            is_match = feature_value == property_value

        target_list = matched if is_match else unmatched
        target_list.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}

def filter_by_radius(
    dataset: Dict[str, Any],
    reference_coords: List[Dict[str, float]],
    target_coords: List[Dict[str, float]],
    radius: float
) -> FilterResult:
    """Filter features by distance radius."""
    valid_coords = []
    
    for target in target_coords:
        for ref in reference_coords:
            if target != ref and calculate_distance(ref, target) <= radius:
                valid_coords.append(target)
                break

    matched, unmatched = [], []
    for feature in dataset["features"]:
        feature_coord = {
            "latitude": feature["geometry"]["coordinates"][1],
            "longitude": feature["geometry"]["coordinates"][0],
        }
        target_list = matched if feature_coord in valid_coords else unmatched
        target_list.append(create_feature(feature))

    return {"matched": matched, "unmatched": unmatched}

async def filter_by_drive_time(
    dataset: Dict[str, Any],
    reference_coords: List[Dict[str, float]],
    target_coords: List[Dict[str, float]],
    max_minutes: float,
    points_per_target: int = 2
) -> FilterResult:
    """Filter features by drive time."""
    # Get nearest points and estimate by distance first
    nearest_locations = await _find_nearest_points(
        reference_coords, target_coords, points_per_target
    )
    
    # Filter by estimated drive time
    filtered_locations = _filter_by_estimated_drive_time(nearest_locations, max_minutes)
    
    # Get actual routes
    route_results = await _calculate_drive_times(filtered_locations)
    
    # Categorize features
    within_time, outside_time, unallocated = [], [], []
    
    for target_routes in route_results:
        min_time = _get_minimum_drive_time(target_routes.routes)
        feature = _find_matching_feature(dataset, target_routes.target)
        
        if feature:
            if min_time != float("inf"):
                target_list = within_time if min_time / 60 <= max_minutes else outside_time
            else:
                target_list = unallocated
            target_list.append(create_feature(feature))

    return {"within_time": within_time, "outside_time": outside_time, "unallocated": unallocated}

# Helper functions for drive time filtering
async def _find_nearest_points(
    reference_coords: List[Dict[str, float]],
    target_coords: List[Dict[str, float]],
    points_per_target: int
) -> List[Dict[str, Any]]:
    """Find nearest reference points for each target."""
    nearest_locations = []
    
    for target in target_coords:
        distances = [
            {
                "latitude": ref["latitude"],
                "longitude": ref["longitude"],
                "distance": calculate_distance(target, ref) / 1000,
            }
            for ref in reference_coords
        ]
        
        nearest = sorted(distances, key=lambda x: x["distance"])[:points_per_target]
        nearest_locations.append({
            "target": target,
            "nearest_coordinates": [(loc["latitude"], loc["longitude"]) for loc in nearest],
        })
    
    return nearest_locations

def _filter_by_estimated_drive_time(
    nearest_locations: List[Dict[str, Any]], 
    max_minutes: float
) -> List[Dict[str, Any]]:
    """Filter by estimated drive time using average speed."""
    AVERAGE_SPEED_MPS = 11.11  # 40 km/h
    max_distance = AVERAGE_SPEED_MPS * max_minutes * 60
    
    filtered_locations = []
    for location in nearest_locations:
        target = location["target"]
        filtered_coords = [
            coord for coord in location["nearest_coordinates"]
            if geodesic((target["latitude"], target["longitude"]), coord).meters <= max_distance
        ]
        filtered_locations.append({
            "target": target,
            "nearest_coordinates": filtered_coords,
        })
    
    return filtered_locations

async def _calculate_drive_times(
    filtered_locations: List[Dict[str, Any]]
) -> List[NearestPointRouteResponse]:
    """Calculate actual drive times using Google API."""
    results = []
    
    for item in filtered_locations:
        target = item["target"]
        target_routes = NearestPointRouteResponse(target=target, routes=[])

        for nearest in item["nearest_coordinates"]:
            origin = f"{target['latitude']},{target['longitude']}"
            destination = f"{nearest[0]},{nearest[1]}"

            if origin != destination:
                route_info = await calculate_distance_traffic_route(origin, destination)
                target_routes.routes.append(route_info)

        results.append(target_routes)
    
    return results

def _get_minimum_drive_time(routes: List[Any]) -> float:
    """Extract minimum drive time from routes."""
    min_time = float("inf")
    
    for route in routes:
        try:
            if route.route and route.route[0].static_duration:
                time_seconds = int(route.route[0].static_duration.replace("s", ""))
                min_time = min(min_time, time_seconds)
        except:
            continue
    
    return min_time

def _find_matching_feature(dataset: Dict[str, Any], target_coord: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """Find feature matching target coordinates."""
    for feature in dataset["features"]:
        if (feature["geometry"]["coordinates"][1] == target_coord["latitude"] and
            feature["geometry"]["coordinates"][0] == target_coord["longitude"]):
            return feature
    return None

# Generic layer creation
LayerConfig = Dict[str, Any]

def create_layers(
    filtered_features: FilterResult,
    base_name: str,
    layer_configs: List[LayerConfig],
    change_layer_id: str,
    city_name: str = ""
) -> List[ResGradientColorBasedOnZone]:
    """Create layers from filtered features using configuration."""
    layers = []
    
    for config in layer_configs:
        features = filtered_features.get(config["feature_key"], [])
        if not features:
            continue
            
        layers.append(ResGradientColorBasedOnZone(
            type="FeatureCollection",
            features=features,
            properties=list(features[0].get("properties", {}).keys()) if features else [],
            prdcer_layer_name=f"{base_name} ({config['name_suffix']})",
            prdcer_lyr_id=str(uuid.uuid4()),
            sub_lyr_id=f"{change_layer_id}_{config['category']}",
            bknd_dataset_id=change_layer_id,
            points_color=config["color"],
            layer_legend=config["legend"],
            layer_description=config["description"],
            records_count=len(features),
            city_name=city_name,
            is_zone_lyr="true",
            progress=0,
        ))
    
    return layers

# Layer configuration factories
def get_name_filter_config(names: List[str], req: Any) -> List[LayerConfig]:
    """Get configuration for name-based filtering layers."""
    return [
        {
            "feature_key": "matched",
            "category": "matched",
            "name_suffix": "Matched",
            "color": req.change_lyr_new_color,
            "legend": f"Contains: {', '.join(names)}",
            "description": f"Features matching names: {', '.join(names)}",
        },
        {
            "feature_key": "unmatched",
            "category": "unmatched", 
            "name_suffix": "Unmatched",
            "color": req.change_lyr_orginal_color,
            "legend": "No name match",
            "description": "Features without matching names",
        }
    ]

def get_drive_time_config(coverage_minutes: float, req: Any) -> List[LayerConfig]:
    """Get configuration for drive time filtering layers."""
    return [
        {
            "feature_key": "within_time",
            "category": "within_drivetime",
            "name_suffix": "Within Drive Time",
            "color": req.color_grid_choice[0],
            "legend": f"Drive Time ≤ {coverage_minutes} m",
            "description": f"Points within {coverage_minutes} minutes drive time",
        },
        {
            "feature_key": "outside_time",
            "category": "outside_drivetime",
            "name_suffix": "Outside Drive Time", 
            "color": req.color_grid_choice[-1],
            "legend": f"Drive Time > {coverage_minutes} m",
            "description": f"Points outside {coverage_minutes} minutes drive time",
        },
        {
            "feature_key": "unallocated",
            "category": "unallocated_drivetime",
            "name_suffix": "Unallocated Drive Time",
            "color": "#FFFFFF",
            "legend": "No route available",
            "description": "Points with no available route information",
        }
    ]

def get_radius_config(radius: float, req: Any) -> List[LayerConfig]:
    """Get configuration for radius filtering layers."""
    return [
        {
            "feature_key": "matched",
            "category": "within_radius",
            "name_suffix": "Within Radius",
            "color": req.change_lyr_new_color,
            "legend": f"Radius ≤ {radius} m",
            "description": f"Points within {radius} meters",
        },
        {
            "feature_key": "unmatched", 
            "category": "outside_radius",
            "name_suffix": "Outside Radius",
            "color": req.change_lyr_orginal_color,
            "legend": f"Radius > {radius} m", 
            "description": f"Points outside {radius} meters",
        }
    ]

# Main processing functions
async def process_coverage_filter(req: ReqGradientColorBasedOnZone) -> List[ResGradientColorBasedOnZone]:
    """Process coverage-based filtering (drive time or radius)."""
    # Fetch datasets
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)
    
    # Extract coordinates
    reference_coords = extract_coordinates(reference_dataset)
    target_coords = extract_coordinates(change_dataset)
    
    # Apply filter based on coverage type
    if req.coverage_property == "drive_time":
        filtered_features = await filter_by_drive_time(
            change_dataset, reference_coords, target_coords, req.coverage_value
        )
        layer_configs = get_drive_time_config(req.coverage_value, req)
        base_name = f"{req.change_lyr_name} based on {req.based_on_lyr_name}"
    else:  # radius
        filtered_features = filter_by_radius(
            change_dataset, reference_coords, target_coords, req.coverage_value
        )
        layer_configs = get_radius_config(req.coverage_value, req)
        base_name = f"{req.change_lyr_name} - Radius Match"
    
    return create_layers(
        filtered_features, base_name, layer_configs, 
        req.change_lyr_id, change_metadata.get("city_name", "")
    )

async def process_gradient_coloring(req: ReqGradientColorBasedOnZone) -> List[ResGradientColorBasedOnZone]:
    """Process gradient coloring based on surrounding point influence."""
    # Fetch datasets
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)
    
    # Calculate influence scores
    influence_scores = []
    point_influence_map = {}
    
    for point in change_dataset["features"]:
        point_id = str(uuid.uuid4())
        point["id"] = point_id
        
        avg_influence = calculate_nearby_average(
            req.color_based_on, point, reference_dataset, req.coverage_value
        )
        
        if avg_influence is not None:
            influence_scores.append(avg_influence)
            point_influence_map[point_id] = avg_influence
    
    # Create gradient layers
    if not influence_scores:
        # No scores - create unallocated layer
        unallocated_features = [create_feature(point) for point in change_dataset["features"]]
        return [_create_unallocated_layer(unallocated_features, req, change_metadata)]
    
    # Calculate percentile thresholds
    percentiles = [16.67, 33.33, 50, 66.67, 83.33]
    thresholds = np.percentile(influence_scores, percentiles)
    
    # Group points by threshold
    layer_groups = [[] for _ in range(len(thresholds) + 2)]
    
    for point in change_dataset["features"]:
        feature = create_feature(point)
        influence = point_influence_map.get(point["id"])
        
        if influence is None:
            layer_index = -1  # Unallocated
            feature["properties"]["influence_score"] = None
        else:
            layer_index = next(
                (i for i, threshold in enumerate(thresholds) if influence <= threshold),
                len(thresholds)
            )
            feature["properties"]["influence_score"] = influence
        
        layer_groups[layer_index].append(feature)
    
    # Create layers
    layers = []
    for i, features in enumerate(layer_groups):
        if features:
            layers.append(_create_gradient_layer(
                features, i, thresholds, req, change_metadata
            ))
    
    return layers

def _create_unallocated_layer(
    features: List[Dict[str, Any]], 
    req: ReqGradientColorBasedOnZone, 
    metadata: Dict[str, Any]
) -> ResGradientColorBasedOnZone:
    """Create layer for unallocated points."""
    return ResGradientColorBasedOnZone(
        type="FeatureCollection",
        features=features,
        properties=list(features[0].get("properties", {}).keys()) if features else [],
        prdcer_layer_name="Unallocated Points",
        prdcer_lyr_id=req.change_lyr_id,
        sub_lyr_id=f"{req.change_lyr_id}_unallocated",
        bknd_dataset_id=req.change_lyr_id,
        points_color="#FFFFFF",
        layer_legend="No nearby points",
        layer_description="Points with no nearby reference points",
        records_count=len(features),
        city_name=metadata.get("city_name", ""),
        is_zone_lyr="true",
        progress=0,
    )

def _create_gradient_layer(
    features: List[Dict[str, Any]], 
    layer_index: int, 
    thresholds: List[float], 
    req: ReqGradientColorBasedOnZone, 
    metadata: Dict[str, Any]
) -> ResGradientColorBasedOnZone:
    """Create a single gradient layer."""
    color = req.color_grid_choice[layer_index] if layer_index < len(req.color_grid_choice) else "#FFFFFF"
    
    # Determine legend based on layer position
    if layer_index == len(thresholds) + 1:  # Unallocated
        legend = "No nearby points"
    elif layer_index == 0:
        legend = f"Influence Score < {thresholds[0]:.2f}"
    elif layer_index == len(thresholds):
        legend = f"Influence Score > {thresholds[-1]:.2f}"
    else:
        legend = f"Influence Score {thresholds[layer_index-1]:.2f} - {thresholds[layer_index]:.2f}"
    
    return ResGradientColorBasedOnZone(
        type="FeatureCollection",
        features=features,
        properties=list(features[0].get("properties", {}).keys()) if features else [],
        prdcer_layer_name=f"Gradient Layer {layer_index + 1}",
        prdcer_lyr_id=req.change_lyr_id,
        sub_lyr_id=f"{req.change_lyr_id}_gradient_{layer_index + 1}",
        bknd_dataset_id=req.change_lyr_id,
        points_color=color,
        layer_legend=legend,
        layer_description=f"Gradient layer based on nearby {req.color_based_on} influence",
        records_count=len(features),
        city_name=metadata.get("city_name", ""),
        is_zone_lyr="true",
        progress=0,
    )

# Main API functions
async def recolor_based_on(req: ReqGradientColorBasedOnZone) -> List[ResGradientColorBasedOnZone]:
    """Main function to process color-based filtering requests."""
    if req.color_based_on == "name":
        # Validate inputs
        if not req.list_names:
            raise ValueError("list_names must be provided when color_based_on is 'name'.")
        if req.based_on_lyr_id == req.change_lyr_id:
            raise ValueError("based_on_lyr_id and change_lyr_id must be different.")
        
        # Process name filtering
        change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
        filtered_features = filter_by_name(change_dataset, req.list_names)
        layer_configs = get_name_filter_config(req.list_names, req)
        
        return create_layers(
            filtered_features, f"{req.change_lyr_name} - Name Match", 
            layer_configs, req.change_lyr_id, change_metadata.get("city_name", "")
        )
    
    elif hasattr(req, 'coverage_property') and req.coverage_property:
        # Coverage-based filtering
        return await process_coverage_filter(req)
    
    else:
        # Gradient coloring based on influence
        return await process_gradient_coloring(req)

async def filter_based_on(req: ReqFilter) -> List[ResGradientColorBasedOnZone]:
    """Filter features based on coverage and property criteria."""
    # Fetch datasets
    change_dataset, change_metadata = await given_layer_fetch_dataset(req.change_lyr_id)
    reference_dataset, _ = await given_layer_fetch_dataset(req.based_on_lyr_id)
    
    # Extract coordinates
    reference_coords = extract_coordinates(reference_dataset)
    target_coords = extract_coordinates(change_dataset)
    
    # Apply coverage filter
    if req.coverage_property == "drive_time":
        coverage_result = await filter_by_drive_time(
            change_dataset, reference_coords, target_coords, req.coverage_value
        )
        filtered_features = coverage_result["within_time"]
    elif req.coverage_property == "radius":
        coverage_result = filter_by_radius(
            change_dataset, reference_coords, target_coords, req.coverage_value
        )
        filtered_features = coverage_result["matched"]
    else:
        filtered_features = [create_feature(f) for f in change_dataset["features"]]
    
    # Apply property filter if specified
    if req.color_based_on:
        if req.color_based_on == "name":
            temp_dataset = {"features": [f for f in change_dataset["features"] 
                                       if create_feature(f) in filtered_features]}
            property_result = filter_by_name(temp_dataset, req.list_names)
            final_features = property_result["matched"]
        else:
            temp_dataset = {"features": [f for f in change_dataset["features"] 
                                       if create_feature(f) in filtered_features]}
            property_result = filter_by_property(temp_dataset, req.color_based_on, req.threshold)
            final_features = property_result["matched"]
    else:
        final_features = filtered_features
    
    # Create result layers
    if not final_features:
        raise ValueError("No features found based on the given criteria.")
    
    layers = []
    for feature in final_features:
        layer = ResGradientColorBasedOnZone(
            prdcer_layer_name=(
                f"{req.change_lyr_name} - Drive Time Match" if req.coverage_property == "drive_time"
                else f"{req.change_lyr_name} - Radius Match"
            ),
            prdcer_lyr_id=str(uuid.uuid4()),
            bknd_dataset_id=req.change_lyr_id,
            points_color=req.change_lyr_new_color,
            layer_legend=(
                f"Drive Time ≤ {req.coverage_value} m" if req.coverage_property == "drive_time"
                else f"Radius ≤ {req.coverage_value} m"
            ),
            is_zone_lyr="true",
            type="FeatureCollection",
            features=[feature],
            properties=list(feature.get("properties", {}).keys()),
            sub_lyr_id=(
                f"{req.change_lyr_id}_drive_time_match" if req.coverage_property == "drive_time"
                else f"{req.change_lyr_id}_radius_match"
            ),
            layer_description="",
            records_count=1,
            city_name=change_metadata.get("city_name", ""),
            progress=0,
        )
        layers.append(layer)
    
    return layers

async def color_based_on_agent(req: ReqPrompt) -> ValidationResult:
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
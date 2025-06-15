from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import math
from pydantic import BaseModel, Field

from all_types.request_dtypes import (
    ReqFetchDataset,
    ReqIntelligenceData,
    ReqHubExpansion,
)
from all_types.response_dtypes import ResHubExpansion
from storage_methods import fetch_intelligence_by_viewport
from data_fetcher import fetch_dataset
from geo_std_utils import calculate_distance, fetch_lat_lng_bounding_box
import pandas as pd


def estimate_travel_time_minutes(
    distance_km: float, traffic_factor: float = 1.2
) -> float:
    """Estimate travel time in minutes based on distance and traffic"""
    average_speed_kmh = 40.0 / traffic_factor
    time_hours = distance_km / average_speed_kmh
    time_minutes = time_hours * 60.0
    return time_minutes


def calculate_population_density(population: int, area_km2: float) -> float:
    """Calculate population density per km2"""
    if area_km2 <= 0:
        density = 0.0
    else:
        density = population / area_km2
    return density


def get_density_classification(
    density: float, thresholds: Dict[str, Dict[str, float]]
) -> str:
    """Classify density based on thresholds"""
    classification = "low_density"

    if density >= thresholds.get("very_high_density", {}).get(
        "threshold", 8000
    ):
        classification = "very_high_density"
    elif density >= thresholds.get("high_density", {}).get("threshold", 4000):
        classification = "high_density"
    elif density >= thresholds.get("medium_density", {}).get("threshold", 2000):
        classification = "medium_density"

    return classification


def normalize_score(
    value: float,
    min_val: float,
    max_val: float,
    threshold_config: Dict[str, float],
) -> float:
    """Normalize a value using configurable thresholds"""
    min_score = threshold_config.get("min_score", 0.0)
    max_score = threshold_config.get("max_score", 10.0)

    if max_val == min_val:
        score = (min_score + max_score) / 2.0
    else:
        normalized = (value - min_val) / (max_val - min_val)
        score = min_score + (normalized * (max_score - min_score))

    final_score = max(min_score, min(max_score, score))
    return final_score


async def fetch_population_centers(
    req: ReqHubExpansion,
) -> List[Dict[str, Any]]:
    """Fetch population center data using the intelligence viewport system"""

    # Create a temporary request to get city bounding box
    temp_req = ReqFetchDataset(
        city_name=req.city_name,
        country_name=req.country_name,
        user_id=req.user_id,
    )
    temp_req = fetch_lat_lng_bounding_box(temp_req)
    bbox_coords = temp_req._bounding_box
    min_lng = bbox_coords[0]
    min_lat = bbox_coords[1]
    max_lng = bbox_coords[2]
    max_lat = bbox_coords[3]

    # Create intelligence data request for population
    intel_req = ReqIntelligenceData(
        min_lng=min_lng,
        min_lat=min_lat,
        max_lng=max_lng,
        max_lat=max_lat,
        zoom_level=10,  # Appropriate zoom level for city analysis
        user_id=req.user_id,
        population=True,
        income=False,
    )

    # Fetch population data using the intelligence system
    population_data = await fetch_intelligence_by_viewport(intel_req)

    # Process population centers from the intelligence data
    population_centers = []

    features = population_data.get("features", [])
    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Handle both Point and Polygon geometries
        if geometry.get("type") == "Point":
            coordinates = geometry.get("coordinates", [])
            if len(coordinates) >= 2:
                lng, lat = coordinates[0], coordinates[1]
            else:
                continue
        elif geometry.get("type") == "Polygon":
            # For polygons, calculate centroid
            coords = geometry.get("coordinates", [[]])
            if coords and coords[0]:
                # Simple centroid calculation
                points = coords[0][:-1]  # Remove last point (same as first)
                lng = sum(p[0] for p in points) / len(points)
                lat = sum(p[1] for p in points) / len(points)
            else:
                continue
        else:
            continue

        population = properties.get(
            "population", properties.get("TotalPopulation", 0)
        )
        density = properties.get(
            "density", properties.get("PopulationDensity", 0)
        )

        # Only include centers above minimum population threshold
        if population > req.min_population_threshold:
            center_data = {
                "coordinates": {
                    "lat": lat,
                    "lng": lng,
                },
                "population": population,
                "density": density,
                "properties": properties,
            }
            population_centers.append(center_data)

    # Sort by population and take top centers
    sorted_centers = sorted(
        population_centers, key=lambda x: x.get("population", 0), reverse=True
    )
    top_centers = sorted_centers[:8]  # Limit to top 8 population centers

    return top_centers


async def analyze_hub_expansion(req: ReqHubExpansion) -> ResHubExpansion:
    """Main function to analyze hub expansion opportunities"""

    # Fetch hub locations
    hub_req = ReqFetchDataset(
        city_name=req.city_name,
        country_name=req.country_name,
        user_id=req.user_id,
        boolean_query=req.hub_type,
        action="full data",
        analysis_bounds=req.analysis_bounds,
        search_type="category_search",
        full_load=True,
    )
    hub_data = await fetch_dataset(hub_req)

    # Fetch target locations
    target_req = ReqFetchDataset(
        city_name=req.city_name,
        country_name=req.country_name,
        user_id=req.user_id,
        boolean_query=f"@{req.target_search}@",
        action="full data",
        analysis_bounds=req.analysis_bounds,
        search_type="keyword_search",
        full_load=True,
    )
    target_data = await fetch_dataset(target_req)

    # Fetch competitor locations
    competitor_req = ReqFetchDataset(
        city_name=req.city_name,
        country_name=req.country_name,
        user_id=req.user_id,
        boolean_query=f"@{req.competitor_name}@",
        action="full data",
        analysis_bounds=req.analysis_bounds,
        search_type="keyword_search",
        full_load=True,
    )
    competitor_data = await fetch_dataset(competitor_req)

    # Fetch population centers
    population_centers = await fetch_population_centers(req)

    # Extract features from datasets
    hub_features = hub_data.get("features", [])
    target_features = target_data.get("features", [])
    competitor_features = competitor_data.get("features", [])

    # Filter hubs by requirements
    qualified_hubs = []
    all_rents = []

    for hub in hub_features:
        properties = hub.get("properties", {})
        geometry = hub.get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        if len(coordinates) >= 2:
            # Check size requirement
            size_m2 = properties.get("area_sqm", properties.get("size_m2", 0))
            rent_per_m2 = properties.get(
                "rent_per_sqm", properties.get("price_per_sqm", 0)
            )

            size_ok = True
            if req.min_facility_size_m2 and size_m2 < req.min_facility_size_m2:
                size_ok = False

            rent_ok = True
            if req.max_rent_per_m2 and rent_per_m2 > req.max_rent_per_m2:
                rent_ok = False

            if size_ok and rent_ok:
                qualified_hubs.append(hub)
                if rent_per_m2 > 0:
                    all_rents.append(rent_per_m2)

    # Score each qualified hub using existing scoring functions
    scored_hubs = []

    for hub in qualified_hubs:
        coordinates = hub.get("geometry", {}).get("coordinates", [])
        properties = hub.get("properties", {})

        hub_location = {"lat": coordinates[1], "lng": coordinates[0]}

        # Calculate individual scores using your existing functions
        target_score, target_details = calculate_target_proximity_score(
            hub_location,
            target_features,
            req.max_target_distance_km,
            req.scoring_thresholds.get("target_proximity", {}),
        )

        population_score, population_details = (
            calculate_population_access_score(
                hub_location,
                population_centers,
                req.max_population_center_time_minutes,
                req.scoring_thresholds.get("population_access", {}),
            )
        )

        rent_score, rent_details = calculate_rent_efficiency_score(
            properties,
            all_rents,
            req.scoring_thresholds.get("rent_efficiency", {}),
        )

        competitive_score, competitive_details = (
            calculate_competitive_advantage_score(
                hub_location,
                competitor_features,
                req.competitor_analysis_radius_km,
                req.scoring_thresholds.get("competitive_advantage", {}),
            )
        )

        coverage_score, coverage_details = calculate_population_coverage_score(
            hub_location,
            population_centers,
            req.density_thresholds,
            req.scoring_thresholds.get("population_coverage", {}),
        )

        # Calculate weighted total score
        weights = req.scoring_weights
        total_score = (
            target_score * weights.get("target_proximity", 0.35)
            + population_score * weights.get("population_access", 0.30)
            + rent_score * weights.get("rent_efficiency", 0.10)
            + competitive_score * weights.get("competitive_advantage", 0.15)
            + coverage_score * weights.get("population_coverage", 0.10)
        )

        # Compile hub analysis
        hub_analysis = {
            "hub_id": properties.get("id", f"hub_{len(scored_hubs)}"),
            "location": {
                "coordinates": {"lat": coordinates[1], "lng": coordinates[0]},
                "address": properties.get(
                    "address", properties.get("formattedAddress", "")
                ),
                "district": properties.get("district", ""),
            },
            "specifications": {
                "size_m2": properties.get(
                    "area_sqm", properties.get("size_m2", 0)
                ),
                "monthly_rent": properties.get("monthly_rent", 0),
                "rent_per_m2": properties.get(
                    "rent_per_sqm", properties.get("price_per_sqm", 0)
                ),
            },
            "performance_metrics": {
                "total_score": round(total_score, 1),
                "component_scores": {
                    "target_proximity_score": round(target_score, 1),
                    "population_access_score": round(population_score, 1),
                    "rent_efficiency_score": round(rent_score, 1),
                    "competitive_advantage_score": round(competitive_score, 1),
                    "population_coverage_score": round(coverage_score, 1),
                },
                "target_access": target_details,
                "population_access": population_details,
                "rent_details": rent_details,
                "competitive_positioning": competitive_details,
                "coverage_analysis": coverage_details,
            },
        }

        scored_hubs.append(hub_analysis)

    # Sort by total score and take top results
    sorted_hubs = sorted(
        scored_hubs,
        key=lambda x: x.get("performance_metrics", {}).get("total_score", 0),
        reverse=True,
    )
    top_hubs = sorted_hubs[: req.top_results_count]
    alternative_hubs = top_hubs[1:] if len(top_hubs) > 1 else []

    # Build analysis summary
    analysis_summary = {
        "scope": f"{len(qualified_hubs)} {req.hub_type}s analyzed",
        "methodology": "Multi-criteria weighted scoring with density-adjusted coverage zones",
        "qualification_criteria": f"≤{req.max_target_distance_km}km {req.target_search} + ≤{req.max_population_center_time_minutes}min population centers",
        "target_type": req.target_search,
        "competitor_analyzed": req.competitor_name,
        "total_qualified_locations": len(qualified_hubs),
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "client_project": f"{req.city_name.upper()}-LOG-2025-001",
    }

    # Build scoring methodology
    scoring_methodology = {
        "weights_applied": req.scoring_weights,
        "scoring_thresholds": req.scoring_thresholds,
        "normalization_method": "Configurable min-max scaling",
        "distance_calculations": "Standard geospatial methods with traffic pattern adjustments",
        "coverage_zones": "Density-adjusted radii based on population density thresholds",
    }

    # Build market analysis
    market_analysis = {
        "total_population_centers": len(population_centers),
        "total_target_locations": len(target_features),
        "total_competitor_locations": len(competitor_features),
        "coverage_methodology": req.density_thresholds,
        "min_population_threshold": req.min_population_threshold,
    }

    # Build primary recommendation
    primary_recommendation = {}
    if top_hubs:
        primary_recommendation = {"hub_details": top_hubs[0]}

    # Build response
    response = ResHubExpansion(
        analysis_summary=analysis_summary,
        scoring_methodology=scoring_methodology,
        primary_recommendation=primary_recommendation,
        alternative_locations=alternative_hubs,
        market_competitive_analysis=market_analysis,
    )

    return response


def calculate_target_proximity_score(
    hub_location: Dict[str, float],
    target_locations: List[Dict[str, Any]],
    max_distance_km: float,
    threshold_config: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """Calculate target proximity score for a hub location"""

    hub_lat = hub_location.get("lat", 0.0)
    hub_lng = hub_location.get("lng", 0.0)

    if not target_locations:
        score = threshold_config.get("min_score", 0.0)
        details = {
            "nearest_target": None,
            "distance_km": None,
            "time_minutes": None,
        }
        return score, details

    # Find closest target using standard distance calculation
    min_distance_m = float("inf")
    closest_target = None

    for target in target_locations:
        target_coords = target.get("geometry", {}).get("coordinates", [])

        if len(target_coords) >= 2:
            target_lng = target_coords[0]
            target_lat = target_coords[1]

            # Use standard distance calculation method
            coord1 = {"latitude": hub_lat, "longitude": hub_lng}
            coord2 = {"latitude": target_lat, "longitude": target_lng}
            distance_m = calculate_distance(coord1, coord2)

            if distance_m < min_distance_m:
                min_distance_m = distance_m
                closest_target = target

    min_distance_km = min_distance_m / 1000.0

    # Calculate score based on distance using configurable thresholds
    max_score = threshold_config.get("max_score", 10.0)
    min_score = threshold_config.get("min_score", 0.0)
    penalty_multiplier = threshold_config.get("penalty_multiplier", 1.0)

    if min_distance_km <= max_distance_km:
        score = max_score - (min_distance_km / max_distance_km) * (
            max_score - 6.0
        )
    else:
        excess_distance = min_distance_km - max_distance_km
        score = max(min_score, 6.0 - (excess_distance * penalty_multiplier))

    # Calculate travel time
    travel_time = estimate_travel_time_minutes(min_distance_km)

    details = {
        "nearest_target": (
            closest_target.get("properties", {}).get("name", "Unknown")
            if closest_target
            else None
        ),
        "distance_km": round(min_distance_km, 2),
        "time_minutes": round(travel_time, 1),
    }

    final_score = max(min_score, min(max_score, score))
    return final_score, details


def calculate_population_access_score(
    hub_location: Dict[str, float],
    population_centers: List[Dict[str, Any]],
    max_time_minutes: int,
    threshold_config: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """Calculate population access score for a hub location"""

    hub_lat = hub_location.get("lat", 0.0)
    hub_lng = hub_location.get("lng", 0.0)

    min_score = threshold_config.get("min_score", 0.0)
    max_score = threshold_config.get("max_score", 10.0)
    accessibility_bonus_max = threshold_config.get(
        "accessibility_bonus_max", 3.0
    )

    if not population_centers:
        score = (min_score + max_score) / 2.0
        details = {"avg_time_to_centers": None, "accessible_population": 0}
        return score, details

    # Calculate distances and times to all centers using standard methods
    total_weighted_time = 0.0
    total_population = 0
    accessible_population = 0

    for center in population_centers:
        center_coords = center.get("coordinates", {})
        center_lat = center_coords.get("lat", 0.0)
        center_lng = center_coords.get("lng", 0.0)
        center_population = center.get("population", 0)

        # Use standard distance calculation
        coord1 = {"latitude": hub_lat, "longitude": hub_lng}
        coord2 = {"latitude": center_lat, "longitude": center_lng}
        distance_m = calculate_distance(coord1, coord2)
        distance_km = distance_m / 1000.0

        travel_time = estimate_travel_time_minutes(distance_km)

        if travel_time <= max_time_minutes:
            accessible_population += center_population

        # Weight by population for average calculation
        total_weighted_time += travel_time * center_population
        total_population += center_population

    # Calculate weighted average time
    if total_population > 0:
        avg_time = total_weighted_time / total_population
    else:
        avg_time = (
            max_time_minutes * 2
        )  # Default to double the max time if no population data

    # Score based on average time and accessible population using configurable thresholds
    if avg_time <= max_time_minutes:
        time_score = max_score - (avg_time / max_time_minutes) * 5.0
    else:
        time_score = max(
            min_score, 5.0 - (avg_time - max_time_minutes) / max_time_minutes
        )

    # Bonus for high accessible population
    if total_population > 0:
        accessibility_ratio = accessible_population / total_population
        accessibility_bonus = accessibility_ratio * accessibility_bonus_max
    else:
        accessibility_bonus = 0.0

    score = time_score + accessibility_bonus

    details = {
        "avg_time_to_centers": round(avg_time, 1),
        "accessible_population": accessible_population,
    }

    final_score = max(min_score, min(max_score, score))
    return final_score, details


def calculate_rent_efficiency_score(
    hub_properties: Dict[str, Any],
    all_hub_rents: List[float],
    threshold_config: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """Calculate rent efficiency score for a hub"""

    rent_per_m2 = hub_properties.get(
        "rent_per_sqm", hub_properties.get("price_per_sqm", 0)
    )

    min_score = threshold_config.get("min_score", 0.0)
    max_score = threshold_config.get("max_score", 10.0)

    if not all_hub_rents or rent_per_m2 <= 0:
        score = (min_score + max_score) / 2.0
        details = {"rent_per_m2": rent_per_m2, "percentile": None}
        return score, details

    # Calculate percentile (lower rent = higher score)
    sorted_rents = sorted(all_hub_rents)
    total_hubs = len(sorted_rents)

    # Find position in sorted list
    position = 0
    for i, rent in enumerate(sorted_rents):
        if rent_per_m2 <= rent:
            position = i
            break
        position = i + 1

    # Calculate percentile (0-100, where 0 = cheapest)
    if total_hubs > 1:
        percentile = (position / (total_hubs - 1)) * 100
    else:
        percentile = 50.0

    # Score: lower percentile = higher score using configurable thresholds
    score = max_score - (percentile / 100.0) * (max_score - min_score)

    details = {"rent_per_m2": rent_per_m2, "percentile": round(percentile, 1)}

    final_score = max(min_score, min(max_score, score))
    return final_score, details


def calculate_competitive_advantage_score(
    hub_location: Dict[str, float],
    competitor_locations: List[Dict[str, Any]],
    analysis_radius_km: float,
    threshold_config: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """Calculate competitive advantage score for a hub location"""

    hub_lat = hub_location.get("lat", 0.0)
    hub_lng = hub_location.get("lng", 0.0)

    min_score = threshold_config.get("min_score", 2.0)
    max_score = threshold_config.get("max_score", 10.0)
    density_penalty_max = threshold_config.get("density_penalty_max", 5.0)

    if not competitor_locations:
        score = max_score
        details = {
            "nearest_competitor": None,
            "distance_km": None,
            "competitors_in_radius": 0,
        }
        return score, details

    # Find closest competitor and count competitors in radius using standard methods
    min_distance_m = float("inf")
    closest_competitor = None
    competitors_in_radius = 0

    for competitor in competitor_locations:
        comp_coords = competitor.get("geometry", {}).get("coordinates", [])

        if len(comp_coords) >= 2:
            comp_lng = comp_coords[0]
            comp_lat = comp_coords[1]

            # Use standard distance calculation
            coord1 = {"latitude": hub_lat, "longitude": hub_lng}
            coord2 = {"latitude": comp_lat, "longitude": comp_lng}
            distance_m = calculate_distance(coord1, coord2)
            distance_km = distance_m / 1000.0

            if distance_m < min_distance_m:
                min_distance_m = distance_m
                closest_competitor = competitor

            if distance_km <= analysis_radius_km:
                competitors_in_radius += 1

    min_distance_km = min_distance_m / 1000.0

    # Score based on distance to nearest competitor and density using configurable thresholds
    if min_distance_m == float("inf"):
        distance_score = max_score
    else:
        distance_score = min(
            max_score,
            min_score
            + (min_distance_km / analysis_radius_km) * (max_score - min_score),
        )

    # Penalty for high competitor density
    density_penalty = min(density_penalty_max, competitors_in_radius * 1.0)
    score = distance_score - density_penalty

    details = {
        "nearest_competitor": (
            closest_competitor.get("properties", {}).get("name", "Unknown")
            if closest_competitor
            else None
        ),
        "distance_km": (
            round(min_distance_km, 2)
            if min_distance_m != float("inf")
            else None
        ),
        "competitors_in_radius": competitors_in_radius,
    }

    final_score = max(min_score, min(max_score, score))
    return final_score, details


def calculate_population_coverage_score(
    hub_location: Dict[str, float],
    population_centers: List[Dict[str, Any]],
    density_thresholds: Dict[str, Dict[str, float]],
    threshold_config: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """Calculate population coverage score based on density-adjusted coverage zones"""

    hub_lat = hub_location.get("lat", 0.0)
    hub_lng = hub_location.get("lng", 0.0)

    min_score = threshold_config.get("min_score", 0.0)
    max_score = threshold_config.get("max_score", 10.0)

    if not population_centers:
        score = (min_score + max_score) / 2.0
        details = {"total_coverage": 0, "coverage_breakdown": {}}
        return score, details

    total_covered_population = 0
    total_population = 0
    coverage_breakdown = {}

    for center in population_centers:
        center_coords = center.get("coordinates", {})
        center_lat = center_coords.get("lat", 0.0)
        center_lng = center_coords.get("lng", 0.0)
        center_population = center.get("population", 0)
        center_density = center.get("density", 0)

        # Determine coverage radius based on density
        density_class = get_density_classification(
            center_density, density_thresholds
        )
        coverage_radius = density_thresholds.get(density_class, {}).get(
            "radius_km", 5.0
        )

        # Use standard distance calculation
        coord1 = {"latitude": hub_lat, "longitude": hub_lng}
        coord2 = {"latitude": center_lat, "longitude": center_lng}
        distance_m = calculate_distance(coord1, coord2)
        distance_km = distance_m / 1000.0

        total_population += center_population

        if distance_km <= coverage_radius:
            total_covered_population += center_population

            if density_class not in coverage_breakdown:
                coverage_breakdown[density_class] = {
                    "population": 0,
                    "centers": 0,
                }

            coverage_breakdown[density_class]["population"] += center_population
            coverage_breakdown[density_class]["centers"] += 1

    # Calculate coverage percentage
    if total_population > 0:
        coverage_percentage = (
            total_covered_population / total_population
        ) * 100
    else:
        coverage_percentage = 0.0

    # Score based on coverage percentage using configurable thresholds
    score = min_score + (coverage_percentage / 100.0) * (max_score - min_score)

    details = {
        "total_coverage": total_covered_population,
        "coverage_percentage": round(coverage_percentage, 1),
        "coverage_breakdown": coverage_breakdown,
    }

    final_score = max(min_score, min(max_score, score))
    return final_score, details


# ===== HELPER FUNCTIONS =====


def calculate_market_saturation_index(
    competitor_count: int, population_total: int, area_km2: float
) -> float:
    """Calculate market saturation index for competitive analysis"""

    if area_km2 <= 0 or population_total <= 0:
        saturation_index = 0.0
        return saturation_index

    # Calculate competitors per 100k population per km2
    population_density = population_total / area_km2
    population_100k = population_total / 100000.0

    if population_100k <= 0:
        saturation_index = 0.0
    else:
        competitors_per_100k = competitor_count / population_100k
        # Normalize by area to account for geographic spread
        saturation_index = competitors_per_100k / area_km2

    return saturation_index


def generate_expansion_priority_matrix(
    scored_locations: List[Dict[str, Any]],
    investment_budget: Optional[float] = None,
    priority_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Generate priority matrix for expansion decisions"""

    if not scored_locations:
        priority_matrix = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
        }
        return priority_matrix

    # Use configurable thresholds or defaults
    if priority_thresholds:
        high_threshold = priority_thresholds.get("high_threshold", 7.5)
        medium_threshold = priority_thresholds.get("medium_threshold", 5.0)
    else:
        high_threshold = 7.5
        medium_threshold = 5.0

    # Sort locations by score
    sorted_locations = sorted(
        scored_locations,
        key=lambda x: x.get("performance_metrics", {}).get("total_score", 0),
        reverse=True,
    )

    total_locations = len(sorted_locations)

    high_priority = []
    medium_priority = []
    low_priority = []

    for location in sorted_locations:
        score = location.get("performance_metrics", {}).get("total_score", 0)

        if score >= high_threshold:
            high_priority.append(location)
        elif score >= medium_threshold:
            medium_priority.append(location)
        else:
            low_priority.append(location)

    # If budget constraint provided, prioritize by ROI
    if investment_budget:
        # Calculate basic ROI indicators (simplified)
        for priority_list in [high_priority, medium_priority, low_priority]:
            for location in priority_list:
                rent_monthly = location.get("specifications", {}).get(
                    "monthly_rent", 0
                )
                score = location.get("performance_metrics", {}).get(
                    "total_score", 0
                )

                if rent_monthly > 0:
                    roi_indicator = score / (
                        rent_monthly / 1000.0
                    )  # Score per 1k rent
                else:
                    roi_indicator = score

                location["roi_indicator"] = roi_indicator

    priority_matrix = {
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "total_analyzed": total_locations,
    }

    return priority_matrix


def calculate_coverage_overlap_analysis(
    hub_locations: List[Dict[str, Any]],
    density_thresholds: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """Calculate overlap analysis between potential hub coverage areas"""

    if len(hub_locations) < 2:
        overlap_analysis = {
            "overlapping_pairs": [],
            "total_overlap_percentage": 0.0,
        }
        return overlap_analysis

    overlapping_pairs = []
    total_pairs = 0
    overlapping_count = 0

    # Use configurable average coverage radius
    avg_coverage_radius = sum(
        config.get("radius_km", 5.0) for config in density_thresholds.values()
    ) / len(density_thresholds)

    overlap_threshold = avg_coverage_radius * 2.0

    # Compare each pair of hubs using standard distance calculation
    for i in range(len(hub_locations)):
        for j in range(i + 1, len(hub_locations)):
            hub1 = hub_locations[i]
            hub2 = hub_locations[j]

            coords1 = hub1.get("location", {}).get("coordinates", {})
            coords2 = hub2.get("location", {}).get("coordinates", {})

            lat1 = coords1.get("lat", 0.0)
            lng1 = coords1.get("lng", 0.0)
            lat2 = coords2.get("lat", 0.0)
            lng2 = coords2.get("lng", 0.0)

            # Use standard distance calculation
            coord1 = {"latitude": lat1, "longitude": lng1}
            coord2 = {"latitude": lat2, "longitude": lng2}
            distance_m = calculate_distance(coord1, coord2)
            distance_km = distance_m / 1000.0

            total_pairs += 1

            if distance_km < overlap_threshold:
                overlapping_count += 1
                overlap_percentage = max(
                    0.0,
                    ((overlap_threshold - distance_km) / overlap_threshold)
                    * 100.0,
                )

                overlap_info = {
                    "hub1_id": hub1.get("hub_id"),
                    "hub2_id": hub2.get("hub_id"),
                    "distance_km": round(distance_km, 2),
                    "overlap_percentage": round(overlap_percentage, 1),
                }
                overlapping_pairs.append(overlap_info)

    # Calculate total overlap percentage
    if total_pairs > 0:
        total_overlap_percentage = (overlapping_count / total_pairs) * 100.0
    else:
        total_overlap_percentage = 0.0

    overlap_analysis = {
        "overlapping_pairs": overlapping_pairs,
        "total_overlap_percentage": round(total_overlap_percentage, 1),
        "total_pairs_analyzed": total_pairs,
    }

    return overlap_analysis


# ===== PERFORMANCE METRICS =====


def calculate_network_efficiency_metrics(
    selected_hubs: List[Dict[str, Any]],
    population_centers: List[Dict[str, Any]],
    target_locations: List[Dict[str, Any]],
    coverage_config: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate network efficiency metrics for selected hubs"""

    if not selected_hubs:
        efficiency_metrics = {
            "network_coverage": 0.0,
            "average_delivery_time": None,
            "network_redundancy": 0.0,
            "cost_efficiency": 0.0,
        }
        return efficiency_metrics

    # Use configurable coverage radius or default
    if coverage_config:
        coverage_radius = coverage_config.get("radius_km", 5.0)
        redundancy_multiplier = coverage_config.get(
            "redundancy_multiplier", 25.0
        )
        cost_normalization_factor = coverage_config.get(
            "cost_normalization_factor", 10000.0
        )
    else:
        coverage_radius = 5.0
        redundancy_multiplier = 25.0
        cost_normalization_factor = 10000.0

    # Calculate total network coverage using standard distance methods
    total_population = sum(
        center.get("population", 0) for center in population_centers
    )
    covered_population = 0

    for center in population_centers:
        center_coords = center.get("coordinates", {})
        center_lat = center_coords.get("lat", 0.0)
        center_lng = center_coords.get("lng", 0.0)
        center_population = center.get("population", 0)

        # Check if any hub covers this population center
        is_covered = False
        for hub in selected_hubs:
            hub_coords = hub.get("location", {}).get("coordinates", {})
            hub_lat = hub_coords.get("lat", 0.0)
            hub_lng = hub_coords.get("lng", 0.0)

            # Use standard distance calculation
            coord1 = {"latitude": center_lat, "longitude": center_lng}
            coord2 = {"latitude": hub_lat, "longitude": hub_lng}
            distance_m = calculate_distance(coord1, coord2)
            distance_km = distance_m / 1000.0

            if distance_km <= coverage_radius:
                is_covered = True
                break

        if is_covered:
            covered_population += center_population

    # Calculate network coverage percentage
    if total_population > 0:
        network_coverage = (covered_population / total_population) * 100.0
    else:
        network_coverage = 0.0

    # Calculate average delivery time to targets using standard methods
    total_time = 0.0
    target_count = 0

    for target in target_locations:
        target_coords = target.get("geometry", {}).get("coordinates", [])

        if len(target_coords) >= 2:
            target_lat = target_coords[1]
            target_lng = target_coords[0]

            # Find nearest hub to this target
            min_time = float("inf")

            for hub in selected_hubs:
                hub_coords = hub.get("location", {}).get("coordinates", {})
                hub_lat = hub_coords.get("lat", 0.0)
                hub_lng = hub_coords.get("lng", 0.0)

                # Use standard distance calculation
                coord1 = {"latitude": target_lat, "longitude": target_lng}
                coord2 = {"latitude": hub_lat, "longitude": hub_lng}
                distance_m = calculate_distance(coord1, coord2)
                distance_km = distance_m / 1000.0

                travel_time = estimate_travel_time_minutes(distance_km)

                if travel_time < min_time:
                    min_time = travel_time

            if min_time != float("inf"):
                total_time += min_time
                target_count += 1

    # Calculate average delivery time
    if target_count > 0:
        average_delivery_time = total_time / target_count
    else:
        average_delivery_time = None

    # Calculate network redundancy using configurable multiplier
    hub_count = len(selected_hubs)
    if hub_count > 1:
        network_redundancy = min(100.0, (hub_count - 1) * redundancy_multiplier)
    else:
        network_redundancy = 0.0

    # Calculate cost efficiency using configurable normalization
    total_monthly_cost = sum(
        hub.get("specifications", {}).get("monthly_rent", 0)
        for hub in selected_hubs
    )

    if total_monthly_cost > 0 and covered_population > 0:
        cost_per_person_per_month = total_monthly_cost / covered_population
        # Normalize to 0-100 scale (lower cost = higher efficiency)
        cost_efficiency = max(
            0.0, 100.0 - (cost_per_person_per_month * cost_normalization_factor)
        )
    else:
        cost_efficiency = 0.0

    efficiency_metrics = {
        "network_coverage": round(network_coverage, 1),
        "average_delivery_time": (
            round(average_delivery_time, 1) if average_delivery_time else None
        ),
        "network_redundancy": round(network_redundancy, 1),
        "cost_efficiency": round(cost_efficiency, 1),
        "total_monthly_cost": total_monthly_cost,
        "covered_population": covered_population,
    }

    return efficiency_metrics


# ===== EXPORT FUNCTIONS =====


async def export_analysis_results(
    analysis_result: ResHubExpansion, export_format: str = "json"
) -> str:
    """Export analysis results in specified format"""

    if export_format.lower() == "json":
        # Convert to JSON
        result_dict = analysis_result.model_dump()
        json_output = json.dumps(result_dict, indent=2, ensure_ascii=False)
        return json_output

    elif export_format.lower() == "summary":
        # Create summary text
        summary_lines = []

        summary_lines.append("=== HUB EXPANSION ANALYSIS SUMMARY ===")
        summary_lines.append("")

        # Analysis overview
        summary_data = analysis_result.analysis_summary
        summary_lines.append(
            f"Analysis Scope: {summary_data.get('scope', 'N/A')}"
        )
        summary_lines.append(
            f"Methodology: {summary_data.get('methodology', 'N/A')}"
        )
        summary_lines.append(
            f"Total Qualified Locations: {summary_data.get('total_qualified_locations', 0)}"
        )
        summary_lines.append("")

        # Primary recommendation
        primary = analysis_result.primary_recommendation
        if primary:
            hub_details = primary.get("hub_details", {})
            location_info = hub_details.get("location", {})
            metrics = hub_details.get("performance_metrics", {})

            summary_lines.append("=== PRIMARY RECOMMENDATION ===")
            summary_lines.append(f"Hub ID: {hub_details.get('hub_id', 'N/A')}")
            summary_lines.append(
                f"Address: {location_info.get('address', 'N/A')}"
            )
            summary_lines.append(
                f"Total Score: {metrics.get('total_score', 0)}/10"
            )
            summary_lines.append("")

        # Alternative locations
        alternatives = analysis_result.alternative_locations
        if alternatives:
            summary_lines.append("=== ALTERNATIVE LOCATIONS ===")
            for i, alt in enumerate(alternatives[:3], 1):  # Top 3 alternatives
                alt_location = alt.get("location", {})
                alt_metrics = alt.get("performance_metrics", {})
                summary_lines.append(
                    f"{i}. {alt.get('hub_id', 'N/A')} - Score: {alt_metrics.get('total_score', 0)}/10"
                )
            summary_lines.append("")

        summary_text = "\n".join(summary_lines)
        return summary_text

    else:
        # Default to JSON
        result_dict = analysis_result.model_dump()
        json_output = json.dumps(result_dict, indent=2, ensure_ascii=False)
        return json_output

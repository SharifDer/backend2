import os
import json
import asyncio
import logging
import math
import unicodedata
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

from data_fetcher import fetch_dataset, poi_categories
from storage_methods import fetch_intelligence_by_viewport
from traffic_data import fetch_here_traffic_flow, calculate_traffic_score, get_traffic_bbox_for_candidates
from screenshot_utils import setup_webdriver, capture_map_screenshot, cleanup_webdriver
from report_generator import create_property_map, create_overview_map, generate_complete_html_report
from all_types.request_dtypes import ReqFetchDataset, ReqIntelligenceData, ReqDineInSuitabilityAnalysis
from all_types.internal_types import UserId

logger = logging.getLogger(__name__)

async def analyze_dine_in_sites(request: ReqDineInSuitabilityAnalysis) -> Dict[str, Any]:
    """Main function to analyze dine-in suitability for properties"""
    
    logger.info(f"Starting dine-in suitability analysis for {request.dine_in_type}")
    
    # 1. Fetch candidate properties
    candidates_data = await fetch_candidates(request)
    candidates = process_candidates(candidates_data)
    
    if not candidates:
        raise ValueError("No candidate properties found")
    
    logger.info(f"Processing {len(candidates)} candidate properties")
    
    # 2. Fetch demographics data for all candidates
    demographics_data = await fetch_demographics_for_candidates(request, candidates)
    
    # 3. Fetch competitors and businesses for all candidates
    competitors_data = await fetch_competitors_and_businesses(request, candidates)
    
    # 4. Fetch traffic data
    traffic_bbox = get_traffic_bbox_for_candidates(candidates)
    traffic_data = await fetch_here_traffic_flow(traffic_bbox)
    
    # 5. Setup screenshot capability
    driver = setup_webdriver()
    
    # 6. Analyze each property
    analysis_results = []
    
    for i, candidate in enumerate(candidates):
        logger.info(f"Analyzing property {i+1}/{len(candidates)}: {candidate['id']}")
        
        # Get demographics for this property
        demographics = get_property_demographics(candidate, demographics_data)
        
        # Get businesses for this property
        property_data = competitors_data.get(f"{candidate['lat']},{candidate['lng']}", {'competitors': [], 'businesses': []})
        property_competitors = property_data['competitors']
        property_businesses = property_data['businesses']
        
        # Calculate all scores
        traffic_analysis = calculate_traffic_score(
            candidate['lat'], candidate['lng'], traffic_data, 
            request.target_max_speed_kmh
        )
        
        business_count = len(property_businesses)
        business_score = calculate_business_score(business_count, request.optimal_nearby_businesses, request.business_penalty_per_missing)
        
        demographics_analysis = calculate_demographics_score(
            demographics['median_age'], demographics['income'], 
            request.target_age, request.age_penalty_per_year
        )
        
        competitor_count = len(property_competitors)  # Direct count since they're already filtered
        competition_score = calculate_competition_score(
            competitor_count, request.max_competitors, request.competitor_penalty_per_excess
        )
        
        # Calculate final weighted score
        final_score = (
            traffic_analysis['score'] * request.traffic_weight +
            business_score * request.business_density_weight +
            demographics_analysis['total'] * request.demographics_weight +
            competition_score * request.competition_weight
        )
        
        # Store comprehensive results
        result = {
            'rank': 0,  # Will be set after sorting
            'property_id': candidate['id'],
            'name': f'Property {i+1:03d}',
            'url': candidate.get('url', ''),
            'price': candidate.get('price', 0),
            'category': candidate.get('category', 'shop_for_rent'),
            'lat': candidate['lat'],
            'lng': candidate['lng'],
            
            # Demographics
            'median_age': demographics['median_age'],
            'income': demographics['income'],
            'demographics_score': demographics_analysis['total'],
            'age_score': demographics_analysis['age_score'],
            'income_score': demographics_analysis['income_score'],
            'age_difference': demographics_analysis['age_diff'],
            
            # Traffic
            'traffic_score': traffic_analysis['score'],
            'avg_road_speed': traffic_analysis['avg_speed'],
            'traffic_segments': traffic_analysis['segments_count'],
            'traffic_details': traffic_analysis['details'],
            
            # Business environment
            'business_count': business_count,
            'business_score': business_score,
            'businesses': property_businesses,
            
            # Competition
            'competitor_count': competitor_count,
            'competition_score': competition_score,
            
            # Final results
            'final_score': final_score,
            'screenshot_path': None,
            'screenshot_base64': None,
        }
        
        analysis_results.append(result)
    
    # Sort by final score and assign ranks
    analysis_results.sort(key=lambda x: x['final_score'], reverse=True)
    for i, result in enumerate(analysis_results):
        result['rank'] = i + 1
    
    # 7. Generate maps and screenshots for top 10 properties
    for i, result in enumerate(analysis_results[:10]):
        property_data = {
            'lat': result['lat'],
            'lng': result['lng'],
            'rank': result['rank'],
            'final_score': result['final_score'],
            'price': result['price'],
            'median_age': result['median_age'],
            'income': result['income'],
            'name': f"Property {result['rank']}"
        }
        
        property_map = create_property_map(
            property_data, result['businesses'], result['traffic_details'], request.analysis_radius
        )
        screenshot_path, screenshot_base64 = capture_map_screenshot(
            property_map, f"property_{result['rank']:02d}_map", driver
        )
        
        result['screenshot_path'] = screenshot_path
        result['screenshot_base64'] = screenshot_base64
    
    # 8. Create overview map
    overview_map = create_overview_map(analysis_results)
    overview_screenshot_path, overview_screenshot_base64 = capture_map_screenshot(
        overview_map, "overview_map", driver
    )
    
    # 9. Cleanup webdriver
    cleanup_webdriver(driver)
    
    # 10. Generate complete HTML report
    report_filename = await generate_complete_html_report(
        analysis_results, overview_screenshot_base64, {
            'dine_in_type': request.dine_in_type,
            'target_age': request.target_age,
            'target_max_speed_kmh': request.target_max_speed_kmh,
            'optimal_nearby_businesses': request.optimal_nearby_businesses,
            'max_competitors': request.max_competitors
        }
    )
    
    # 11. Calculate summary statistics
    avg_score = np.mean([r['final_score'] for r in analysis_results])
    total_businesses = sum(r['business_count'] for r in analysis_results)
    total_competitors = sum(r['competitor_count'] for r in analysis_results)
    avg_price = np.mean([r['price'] for r in analysis_results])
    
    logger.info(f"Analysis complete for {len(analysis_results)} properties")
    
    return {
        'report_url': f"/static/reports/{report_filename}",
        'analysis_summary': {
            'total_properties': len(analysis_results),
            'avg_score': avg_score,
            'top_score': analysis_results[0]['final_score'] if analysis_results else 0,
            'avg_price': avg_price,
            'total_businesses': total_businesses,
            'total_competitors': total_competitors,
        },
        'top_properties': [
            {
                'rank': r['rank'],
                'property_id': r['property_id'],
                'final_score': r['final_score'],
                'price': r['price'],
                'url': r['url'],
                'traffic_score': r['traffic_score'],
                'business_score': r['business_score'],
                'demographics_score': r['demographics_score'],
                'competition_score': r['competition_score']
            } for r in analysis_results[:10]
        ],
        'total_properties_analyzed': len(analysis_results),
        'report_filename': report_filename
    }

async def fetch_candidates(request: ReqDineInSuitabilityAnalysis) -> Dict[str, Any]:
    """Fetch candidate properties using existing fetch_dataset function"""
    
    fetch_request = ReqFetchDataset(
        country_name=request.country_name,
        city_name=request.city_name,
        boolean_query="shop_for_rent",
        user_id=request.user_id,
        search_type="category_search",
        action="full data",  # Use full data instead of sample
        layer_name=f"{request.country_name} {request.city_name} shop_for_rent",
        page_token="",
        layerId="",
        text_search="",
        zoom_level=6,
        full_load=True  # Enable full load
    )
    
    logger.info("Fetching candidate properties...")
    return await fetch_dataset(fetch_request)

def process_candidates(candidates_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process candidates data from GeoJSON format"""
    
    candidates = []
    features = candidates_data.get('features', [])
    
    logger.info(f"Processing {len(features)} candidate features")
    
    for i, feature in enumerate(features):
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [0, 0])
        
        candidates.append({
            'id': f'PROP_{i:03d}',
            'lat': coordinates[1],
            'lng': coordinates[0],
            'url': properties.get('url', ''),
            'price': properties.get('price', 0),
            'category': properties.get('category', 'shop_for_rent'),
        })
    
    return candidates

async def fetch_demographics_for_candidates(request: ReqDineInSuitabilityAnalysis, 
                                          candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fetch demographics data for candidate properties using viewport"""
    
    if not candidates:
        return {'features': []}
    
    # Calculate bounding box for all candidates
    lats = [c['lat'] for c in candidates]
    lngs = [c['lng'] for c in candidates]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    # Add buffer
    buffer = 0.02
    top_lat = max_lat + buffer
    bottom_lat = min_lat - buffer
    top_lng = max_lng + buffer
    bottom_lng = min_lng - buffer
    
    demographics_request = ReqIntelligenceData(
        top_lng=top_lng,
        top_lat=top_lat,
        bottom_lng=bottom_lng,
        bottom_lat=bottom_lat,
        zoom_level=10,  # Appropriate zoom level for city analysis
        user_id=request.user_id,
        population=True,
        income=True
    )
    
    logger.info("Fetching demographics data...")
    return await fetch_intelligence_by_viewport(demographics_request)

def get_property_demographics(candidate: Dict[str, Any], 
                            demographics_data: Dict[str, Any]) -> Dict[str, float]:
    """Get demographics for a specific property using spatial join"""
    
    features = demographics_data.get('features', [])
    candidate_point = Point(candidate['lng'], candidate['lat'])
    
    for feature in features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        if geometry.get('type') == 'Polygon':
            try:
                coords = geometry.get('coordinates', [[]])[0]
                polygon = Polygon(coords)
                
                if polygon.contains(candidate_point):
                    return {
                        'median_age': properties.get('Median_Age_Total', 30),
                        'income': properties.get('income', 15000)
                    }
            except Exception as e:
                logger.warning(f"Error processing polygon: {e}")
                continue
    
    # Default values if no match found
    return {'median_age': 30, 'income': 15000}

async def fetch_competitors_and_businesses(request: ReqDineInSuitabilityAnalysis, 
                                         candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Fetch competitors and general businesses for each candidate using real data"""
    
    competitors_and_businesses_data = {}
    
    # For each candidate, fetch both competitors and general businesses
    for candidate in candidates:
        key = f"{candidate['lat']},{candidate['lng']}"
        
        # Create bounding box around this candidate for analysis_bounds
        lat_offset = 0.018  # ~2km in degrees
        lng_offset = 0.018
        analysis_bounds = {
            "north": candidate['lat'] + lat_offset,
            "south": candidate['lat'] - lat_offset,
            "east": candidate['lng'] + lng_offset,
            "west": candidate['lng'] - lng_offset
        }
        
        try:
            # 1. FETCH COMPETITORS (same category as analysis)
            competitor_request = ReqFetchDataset(
                country_name=request.country_name,
                city_name=request.city_name,
                boolean_query=request.dine_in_type,  # Specific competitors
                user_id=request.user_id,
                search_type="category_search",
                action="full data",
                layer_name=f"Competitors near {candidate['id']}",
                page_token="",
                layerId="",
                text_search="",
                zoom_level=16,
                full_load=True,
                analysis_bounds=analysis_bounds
            )
            
            competitor_data = await fetch_dataset(competitor_request)
            competitors = process_businesses_for_candidate(
                competitor_data, candidate, request.analysis_radius
            )
            
            # 2. FETCH GENERAL BUSINESSES (all types for business density)
            business_request = ReqFetchDataset(
                country_name=request.country_name,
                city_name=request.city_name,
                boolean_query="restaurant OR cafe OR bank OR shopping_mall OR hotel OR pharmacy OR gas_station OR grocery_store OR fitness_center OR beauty_salon OR real_estate_agency",
                user_id=request.user_id,
                search_type="category_search",
                action="full data",
                layer_name=f"Businesses near {candidate['id']}",
                page_token="",
                layerId="",
                text_search="",
                zoom_level=16,
                full_load=True,
                analysis_bounds=analysis_bounds
            )
            
            business_data = await fetch_dataset(business_request)
            general_businesses = process_businesses_for_candidate(
                business_data, candidate, request.analysis_radius
            )
            
            # Store both competitors and general businesses
            competitors_and_businesses_data[key] = {
                'competitors': competitors,
                'businesses': general_businesses
            }
            
        except Exception as e:
            logger.warning(f"Error fetching data for {candidate['id']}: {e}")
            competitors_and_businesses_data[key] = {
                'competitors': [],
                'businesses': []
            }
    
    return competitors_and_businesses_data

def process_businesses_for_candidate(business_data: Dict[str, Any], 
                                   candidate: Dict[str, Any], 
                                   analysis_radius: int) -> List[Dict[str, Any]]:
    """Process business data and filter by distance from candidate"""
    
    businesses = []
    features = business_data.get('features', [])
    
    for feature in features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [0, 0])
        
        # Calculate distance from candidate
        distance = calculate_distance_meters(
            candidate['lat'], candidate['lng'],
            coordinates[1], coordinates[0]
        )
        
        if distance <= analysis_radius:
            # Convert to format expected by analysis
            businesses.append({
                "position": {
                    "lat": coordinates[1],
                    "lon": coordinates[0]
                },
                "poi": {
                    "name": properties.get('name', 'Business'),
                    "categories": [properties.get('category', 'restaurant')]
                },
                "dist": distance
            })
    
    return businesses

def calculate_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def calculate_business_score(business_count: int, optimal_count: int, penalty_per_missing: int) -> float:
    """Calculate business density score"""
    if business_count >= optimal_count:
        return 100.0
    else:
        missing = optimal_count - business_count
        penalty = missing * penalty_per_missing
        return max(0.0, 100.0 - penalty)

def calculate_demographics_score(median_age: float, income: float, 
                               target_age: int, age_penalty_per_year: int) -> Dict[str, float]:
    """Calculate demographics score based on age and income"""
    
    # Age score calculation
    age_diff = abs(median_age - target_age)
    age_penalty = age_diff * age_penalty_per_year
    age_score = max(0.0, 100.0 - age_penalty)
    
    # Income score calculation (normalized)
    min_income, max_income = 497.69, 27954.77
    
    if income <= min_income:
        income_score = 0.0
    elif income >= max_income:
        income_score = 100.0
    else:
        income_score = ((income - min_income) / (max_income - min_income)) * 100.0
    
    # Combine age and income scores (60% age, 40% income)
    total_score = (age_score * 0.6) + (income_score * 0.4)
    
    return {
        'total': total_score,
        'age_score': age_score,
        'income_score': income_score,
        'age_diff': age_diff
    }

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    text = text.lower()
    return "".join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

def calculate_competition_score(competitor_count: int, max_competitors: int, 
                              penalty_per_excess: int) -> float:
    """Calculate competition score"""
    if competitor_count <= max_competitors:
        return 100.0
    else:
        excess = competitor_count - max_competitors
        penalty = excess * penalty_per_excess
        return max(0.0, 100.0 - penalty)
import requests
import math
import logging
from typing import List, Dict, Any, Optional
from config_factory import CONF

logger = logging.getLogger(__name__)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

async def fetch_here_traffic_flow(bbox: str) -> List[Dict[str, Any]]:
    """Fetch traffic flow data from HERE API"""
    if not hasattr(CONF, 'here_api_key') or not CONF.here_api_key or CONF.here_api_key == "Put your api key":
        logger.error("HERE API key not configured.")
        raise ValueError("Failed to get traffic data from API, generate request again")
    
    params = {
        'in': f'bbox:{bbox}',
        'locationReferencing': 'shape',
        'apikey': CONF.here_api_key
    }
    
    logger.info("Fetching traffic flow data from HERE API...")
    
    try:
        response = requests.get(CONF.here_traffic_flow_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' in data and data['results']:
            logger.info(f"Successfully fetched {len(data['results'])} traffic flow segments")
            return data['results']
        else:
            logger.error("No results in HERE API response")
            raise ValueError("Failed to get traffic data from API, generate request again")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching HERE traffic data: {e}")
        raise ValueError("Failed to get traffic data from API, generate request again")

def calculate_distance_score(min_distance: float) -> float:
    """Calculate distance score based on proximity to nearest road"""
    if min_distance <= 50:
        return 100.0
    elif min_distance <= 100:
        return 75.0
    elif min_distance <= 150:
        return 25.0
    else:
        return 0.0

def calculate_speed_score(avg_speed: float, target_max_speed: int, speed_penalty_per_2kmh: int = 5) -> float:
    """Calculate speed score based on traffic speed relative to target"""
    if avg_speed <= target_max_speed:
        return 100.0
    else:
        excess_speed = avg_speed - target_max_speed
        penalty = (excess_speed / 2) * speed_penalty_per_2kmh
        return max(0.0, 100.0 - penalty)

def calculate_traffic_score(property_lat: float, property_lng: float, 
                          traffic_data: List[Dict[str, Any]], 
                          target_max_speed: int) -> Dict[str, Any]:
    """Calculate traffic score based on distance to roads and traffic speed"""
    nearby_speeds = []
    nearby_segments = []
    road_distances = []
    
    for segment in traffic_data:
        try:
            flow = segment.get('currentFlow', {})
            location = segment.get('location', {})
            shape = location.get('shape', {}).get('links', [])
            
            speed = flow.get('speed', None)
            if speed is None:
                continue
            
            # Calculate distance to each road segment
            for link in shape:
                points = link.get('points', [])
                if points:
                    segment_lat = points[0]['lat']
                    segment_lng = points[0]['lng']
                    
                    distance = calculate_distance(
                        property_lat, property_lng, 
                        segment_lat, segment_lng
                    )
                    
                    # Consider segments within reasonable distance for analysis
                    if distance <= 500:  # Within 500m
                        nearby_speeds.append(speed)
                        road_distances.append(distance)
                        nearby_segments.append({
                            'speed': speed,
                            'jam_factor': flow.get('jamFactor', 0),
                            'distance': distance,
                            'description': location.get('description', 'Road')
                        })
                        
        except Exception as e:
            logger.warning(f"Error processing traffic segment: {e}")
            continue
    
    if not nearby_speeds or not road_distances:
        # No traffic data available within reasonable distance
        return {
            'score': 0, 
            'avg_speed': 0,
            'min_distance': 999,
            'distance_score': 0,
            'speed_score': 0, 
            'segments_count': 0, 
            'details': []
        }
    
    # Calculate component scores
    avg_speed = sum(nearby_speeds) / len(nearby_speeds)
    min_distance = min(road_distances)
    
    distance_score = calculate_distance_score(min_distance)
    speed_score = calculate_speed_score(avg_speed, target_max_speed)
    
    # Final combined score: distance × speed ÷ 100
    final_score = (distance_score * speed_score) / 100
    
    return {
        'score': final_score,
        'avg_speed': avg_speed,
        'min_distance': min_distance,
        'distance_score': distance_score,
        'speed_score': speed_score,
        'segments_count': len(nearby_segments),
        'details': nearby_segments[:3]
    }

def get_traffic_bbox_for_candidates(candidates: List[Dict[str, Any]]) -> str:
    """Generate bounding box for traffic data based on candidates"""
    if not candidates:
        # Default Riyadh bbox
        return "46.5000,24.6000,46.8000,24.8000"
    
    lats = [c['lat'] for c in candidates]
    lngs = [c['lng'] for c in candidates]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    # Add buffer
    buffer = 0.02
    min_lng -= buffer
    max_lng += buffer
    min_lat -= buffer
    max_lat += buffer
    
    return f"{min_lng},{min_lat},{max_lng},{max_lat}"
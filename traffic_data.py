import requests
import random
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
        logger.warning("HERE API key not configured. Using simulated traffic data.")
        return create_simulated_traffic()
    
    url = "https://data.traffic.hereapi.com/v7/flow"
    params = {
        'in': f'bbox:{bbox}',
        'locationReferencing': 'shape',
        'apikey': CONF.HERE_API_KEY
    }
    
    logger.info("Fetching traffic flow data from HERE API...")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' in data:
            logger.info(f"Successfully fetched {len(data['results'])} traffic flow segments")
            return data['results']
        else:
            logger.warning("No results in HERE API response")
            return create_simulated_traffic()
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching HERE traffic data: {e}")
        return create_simulated_traffic()

def create_simulated_traffic() -> List[Dict[str, Any]]:
    """Create simulated traffic data for testing"""
    logger.info("Creating simulated traffic data...")
    
    traffic_segments = []
    
    # Major roads in Riyadh with typical speeds
    major_roads = [
        {'lat': 24.7300, 'lng': 46.6800, 'speed': 25, 'name': 'King Fahd Road'},
        {'lat': 24.7100, 'lng': 46.6900, 'speed': 15, 'name': 'Tahlia Street'},
        {'lat': 24.7450, 'lng': 46.6300, 'speed': 30, 'name': 'Prince Mohammed Rd'},
        {'lat': 24.6900, 'lng': 46.7200, 'speed': 18, 'name': 'King Abdullah Road'},
        {'lat': 24.6500, 'lng': 46.6200, 'speed': 22, 'name': 'Riyadh Front Road'},
        {'lat': 24.6800, 'lng': 46.6100, 'speed': 20, 'name': 'Diplomatic Quarter'},
        {'lat': 24.7600, 'lng': 46.6500, 'speed': 28, 'name': 'Al-Nakheel Area'},
        {'lat': 24.7800, 'lng': 46.7000, 'speed': 35, 'name': 'Airport Road'},
    ]
    
    for road in major_roads:
        # Create multiple segments for each major road
        for offset in [0.001, -0.001, 0.002, -0.002, 0.003, -0.003]:
            traffic_segments.append({
                'currentFlow': {
                    'speed': road['speed'] + random.randint(-5, 5),
                    'jamFactor': random.random() * 0.5
                },
                'location': {
                    'description': road['name'],
                    'shape': {
                        'links': [{
                            'points': [{
                                'lat': road['lat'] + offset,
                                'lng': road['lng'] + offset
                            }]
                        }]
                    }
                }
            })
    
    return traffic_segments

def calculate_traffic_score(property_lat: float, property_lng: float, 
                          traffic_data: List[Dict[str, Any]], 
                          target_max_speed: int) -> Dict[str, Any]:
    """Calculate traffic score based on nearby road speeds"""
    nearby_speeds = []
    nearby_segments = []
    
    for segment in traffic_data:
        try:
            flow = segment.get('currentFlow', {})
            location = segment.get('location', {})
            shape = location.get('shape', {}).get('links', [])
            
            speed = flow.get('speed', None)
            if speed is None:
                continue
            
            # Check if traffic segment is near property
            for link in shape:
                points = link.get('points', [])
                if points:
                    segment_lat = points[0]['lat']
                    segment_lng = points[0]['lng']
                    
                    distance = calculate_distance(
                        property_lat, property_lng, 
                        segment_lat, segment_lng
                    )
                    
                    if distance <= 500:  # Within 500m
                        nearby_speeds.append(speed)
                        nearby_segments.append({
                            'speed': speed,
                            'jam_factor': flow.get('jamFactor', 0),
                            'distance': distance,
                            'description': location.get('description', 'Road')
                        })
                        
        except Exception as e:
            continue
    
    if not nearby_speeds:
        # No traffic data available, use neutral score
        return {
            'score': 50, 
            'avg_speed': target_max_speed, 
            'segments_count': 0, 
            'details': []
        }
    
    avg_speed = sum(nearby_speeds) / len(nearby_speeds)
    
    # Calculate score based on speed relative to target
    if avg_speed <= target_max_speed:
        score = 100
    else:
        # Reduce score by penalty for every 2 km/h above target
        excess_speed = avg_speed - target_max_speed
        penalty = (excess_speed / 2) * 5  # Default penalty from config
        score = max(0, 100 - penalty)
    
    return {
        'score': score,
        'avg_speed': avg_speed,
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
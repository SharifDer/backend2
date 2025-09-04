import requests
import math
from typing import List, Dict, Any
from config_factory import CONF
from app_logger import get_logger

logger = get_logger(__name__)

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

def chunk_bounding_box(min_lng: float, min_lat: float, max_lng: float, max_lat: float, max_size: float = 0.95) -> List[Dict[str, float]]:
    """Split a large bounding box into smaller chunks that fit HERE API limits"""
    chunks = []
    
    # Calculate how many chunks we need in each direction
    width = max_lng - min_lng
    height = max_lat - min_lat
    
    lng_chunks = math.ceil(width / max_size)
    lat_chunks = math.ceil(height / max_size)
    
    # Calculate actual chunk sizes
    lng_step = width / lng_chunks
    lat_step = height / lat_chunks
    
    logger.info(f"Splitting bounding box into {lng_chunks}x{lat_chunks} = {lng_chunks * lat_chunks} chunks")
    logger.info(f"Original size: {width:.3f}° x {height:.3f}°, Chunk size: {lng_step:.3f}° x {lat_step:.3f}°")
    
    # Create chunks
    for i in range(lng_chunks):
        for j in range(lat_chunks):
            chunk_min_lng = min_lng + i * lng_step
            chunk_max_lng = min(min_lng + (i + 1) * lng_step, max_lng)
            chunk_min_lat = min_lat + j * lat_step
            chunk_max_lat = min(min_lat + (j + 1) * lat_step, max_lat)
            
            chunks.append({
                'min_lng': chunk_min_lng,
                'min_lat': chunk_min_lat,
                'max_lng': chunk_max_lng,
                'max_lat': chunk_max_lat,
                'bbox_string': f"{chunk_min_lng},{chunk_min_lat},{chunk_max_lng},{chunk_max_lat}"
            })
    
    return chunks

async def fetch_here_traffic_flow_chunked(bbox: str) -> List[Dict[str, Any]]:
    """Fetch traffic flow data with automatic chunking for large bounding boxes"""
    if not hasattr(CONF, 'here_api_key') or not CONF.here_api_key or CONF.here_api_key == "Put your api key":
        logger.error("HERE API key not configured.")
        raise ValueError("Failed to get traffic data from API, generate request again")
    
    # Parse bounding box
    coords = list(map(float, bbox.split(',')))
    min_lng, min_lat, max_lng, max_lat = coords
    
    # Check if chunking is needed
    width = max_lng - min_lng
    height = max_lat - min_lat
    max_dimension = max(width, height)
    
    if max_dimension <= 1.0:
        # Single request - no chunking needed
        logger.info(f"Bounding box size {width:.3f}° x {height:.3f}° - making single API call")
        return await fetch_here_traffic_flow_single(bbox)
    else:
        # Multiple requests - chunking needed
        logger.info(f"Bounding box size {width:.3f}° x {height:.3f}° - chunking required")
        chunks = chunk_bounding_box(min_lng, min_lat, max_lng, max_lat)
        
        all_results = []
        successful_chunks = 0
        
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Fetching chunk {i+1}/{len(chunks)}: {chunk['bbox_string']}")
                chunk_results = await fetch_here_traffic_flow_single(chunk['bbox_string'])
                all_results.extend(chunk_results)
                successful_chunks += 1
                
                # Small delay between requests to be respectful to the API
                if i < len(chunks) - 1:  # Don't delay after the last request
                    import asyncio
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch chunk {i+1}: {e}")
                continue
        
        logger.info(f"Successfully fetched {successful_chunks}/{len(chunks)} chunks, total segments: {len(all_results)}")
        
        if successful_chunks == 0:
            raise ValueError("Failed to get traffic data from API, generate request again")
        
        return all_results

async def fetch_here_traffic_flow_single(bbox: str) -> List[Dict[str, Any]]:
    """Fetch traffic flow data from HERE API for a single bounding box"""
    params = {
        'in': f'bbox:{bbox}',
        'locationReferencing': 'shape',
        'apikey': CONF.here_api_key
    }
    
    try:
        response = requests.get(CONF.here_traffic_flow_url, params=params, timeout=30)
        
        # Check for specific bounding box error
        if response.status_code == 400:
            error_data = response.json()
            if 'cause' in error_data and 'maximum width and height' in error_data['cause']:
                logger.error(f"HERE API bounding box error: {error_data}")
                raise ValueError("Bounding box too large - this should not happen with chunking")
        
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data and data['results']:
            return data['results']
        else:
            logger.warning("No results in HERE API response for this chunk")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching HERE traffic data: {e}")
        raise ValueError("Failed to get traffic data from API, generate request again")

# Update the main function to use the new chunked version
async def fetch_here_traffic_flow(bbox: str) -> List[Dict[str, Any]]:
    """Main entry point - automatically handles chunking if needed"""
    return await fetch_here_traffic_flow_chunked(bbox)

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
    """Generate bounding box for traffic data based on candidates with optimized buffer"""
    if not candidates:
        # Default Riyadh bbox
        return "46.5000,24.6000,46.8000,24.8000"
    
    lats = [c['lat'] for c in candidates]
    lngs = [c['lng'] for c in candidates]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    # Use smaller buffer to avoid exceeding limits
    # Calculate current dimensions
    current_width = max_lng - min_lng
    current_height = max_lat - min_lat
    
    # Use adaptive buffer - smaller for larger areas
    if max(current_width, current_height) > 0.8:
        buffer = 0.005  # Very small buffer for large areas
    elif max(current_width, current_height) > 0.5:
        buffer = 0.01   # Small buffer for medium areas  
    else:
        buffer = 0.02   # Normal buffer for small areas
    
    min_lng -= buffer
    max_lng += buffer
    min_lat -= buffer
    max_lat += buffer
    
    bbox = f"{min_lng},{min_lat},{max_lng},{max_lat}"
    
    # Log the final bounding box size for debugging
    final_width = max_lng - min_lng
    final_height = max_lat - min_lat
    logger.info(f"Generated traffic bounding box: {final_width:.3f}° x {final_height:.3f}° (buffer: {buffer:.3f}°)")
    
    return bbox
import random
import math
import logging

logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def create_simulated_traffic():
    traffic_segments = []
    
    major_roads = [
        {'lat': 24.7300, 'lng': 46.6800, 'speed': 25, 'name': 'King Fahd Road'},
        {'lat': 24.7100, 'lng': 46.6900, 'speed': 15, 'name': 'Tahlia Street'},
        {'lat': 24.7450, 'lng': 46.6300, 'speed': 30, 'name': 'Prince Mohammed Rd'},
        {'lat': 24.6900, 'lng': 46.7200, 'speed': 18, 'name': 'King Abdullah Road'},
        {'lat': 24.6500, 'lng': 46.6200, 'speed': 22, 'name': 'Riyadh Front Road'},
    ]
    
    for road in major_roads:
        for offset in [0.001, -0.001, 0.002, -0.002]:
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

def calculate_traffic_score(property_lat, property_lng, traffic_data, target_max_speed):
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
            
            for link in shape:
                points = link.get('points', [])
                if points:
                    segment_lat = points[0]['lat']
                    segment_lng = points[0]['lng']
                    
                    distance = calculate_distance(
                        property_lat, property_lng, 
                        segment_lat, segment_lng
                    )
                    
                    if distance <= 500:
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
        return {
            'score': 50, 
            'avg_speed': target_max_speed, 
            'segments_count': 0, 
            'details': []
        }
    
    avg_speed = sum(nearby_speeds) / len(nearby_speeds)
    
    if avg_speed <= target_max_speed:
        score = 100
    else:
        excess_speed = avg_speed - target_max_speed
        penalty = (excess_speed / 2) * 5
        score = max(0, 100 - penalty)
    
    return {
        'score': score,
        'avg_speed': avg_speed,
        'segments_count': len(nearby_segments),
        'details': nearby_segments[:3]
    }


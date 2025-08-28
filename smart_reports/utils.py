from shapely.geometry import box
from geopy.distance import geodesic

from shapely.geometry import box

def generate_bbox(center_lat , center_lng , radius_km=1):
    delta = radius_km / 111
    return {
        "min_lng": center_lng - delta,
        "max_lng": center_lng + delta,
        "min_lat" : center_lat - delta,
        "max_lat" : center_lat + delta
    }

def bbox_to_polygon(bbox):
    return box(bbox["min_lng"], bbox["min_lat"], bbox["max_lng"], bbox["max_lat"])


def calculate_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict:
    origin = (origin_lat, origin_lng)  # Latitude, Longitude of the origin
    destination = (dest_lat, dest_lng)
    distance = geodesic(origin , destination).meters
    return {
        "est_driving_distance_meters" : int(distance)
    }
# fetchers/complementary_businesses.py
from smart_reports.utils import calculate_distance
from shapely.geometry import Point

def process_category_data(area_polygon : dict , lat : float , lng : float , typ : str, category_data : dict):
    """
    Process category 'data' (already loaded). Returns {'nearby_{typ}': [...]}
    distance_key controls output field name so we don't change existing saved structures.
    """

    results = {f"nearby_{typ}": []}
    for feature in category_data:
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2:
            continue
        place_lng, place_lat = coords[0], coords[1]
        point = Point(place_lng, place_lat)
        if area_polygon.contains(point):
            dist_data = calculate_distance(lat, lng ,  place_lat, place_lng)
            results[f"nearby_{typ}"].append({
                "name": feature.get("properties", {}).get("name", ""),
                "coordinates": [place_lng, place_lat],
                'est_distance_meters': dist_data["est_driving_distance_meters"]
            })
    return results

async def get_other_businesses_data(area_polygon : dict , lat : float, lng : float , grocery_store_data, supermarket_data,
                              restaurant_data, bank_data, atm_data):
    def top_n_closest(category_results, key, n=5):
        items = category_results.get(key, [])
        items_sorted = sorted(items, key=lambda x: x["est_distance_meters"])
        return items_sorted[:n]

    categories = [
        "grocery_store",
        "supermarket",
        "restaurant",
        "atm",
        "bank"
    ]

    input_map = {
        "grocery_store": grocery_store_data,
        "supermarket": supermarket_data,
        "restaurant": restaurant_data,
        "atm": atm_data,
        "bank": bank_data
    }

    amenities = {}
    num_of_businesses_around = 0
    for category in categories:
        data = input_map.get(category, {})
        key = f"nearby_{category}"
        # Keep the same key name used previously for amenities: 'est_distance_meters'
        results = process_category_data(area_polygon , lat , lng , typ=category, category_data=data)
        num_of_businesses_around += len(results[key])
        results[key] = top_n_closest(results, key, 5)
        amenities[category] = {**results}

    return {
        "num of business around" : num_of_businesses_around,
        "nearest_businessess": amenities
   
    }

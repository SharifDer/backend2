
from smart_reports.utils import calculate_distance
from shapely.geometry import Point


def process_category_data(area_polygon : dict, lat : float , lng : float , typ , category_data):
    
    """
    Extract places of a given category inside the polygon and compute their driving distance.
    """
    results = {f"nearby_{typ}": []}

    # features = category_data["features"]
    for feature in category_data:
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2:
            continue

        place_lng, place_lat = coords[0], coords[1]  # GeoJSON = [place_lng, place_lat]

        # Check if point is inside polygon
        point = Point(place_lng, place_lat)
        if area_polygon.contains(point):
            # Calculate distance
            dist_data = calculate_distance(lat, lng, place_lat, place_lng)

            results[f"nearby_{typ}"].append({
                "name": feature.get("properties", {}).get("name", ""),
                "coordinates": [place_lng, place_lat],
                "est_driving_distance_meters": dist_data["est_driving_distance_meters"]
            })

    return results

async def get_healthcare_data(area_polygon : dict , lat : float , lng : float ,  hospital_data , dentist_data , pharmacies_data):
    """
    Collect healthcare data (hospitals, dentists, pharmacies), count them, and return top closest results.
    """
    types = ["hospital", "dentist"]
    hospitals = process_category_data(area_polygon, lat , lng , types[0] , hospital_data)
    dentists = process_category_data(area_polygon, lat , lng , types[1] , dentist_data )
    pharmacies = process_category_data(area_polygon, lat , lng , typ="pharmacy" , category_data=pharmacies_data)
    num_pharmacies = len(pharmacies.get("nearby_pharmacy", []))
    num_hospitals = len(hospitals.get("nearby_hospital" , []))
    num_dentists = len(dentists.get("nearby_dentist", []))
    def top_n_closest(category_results, key, n=5):
        items = category_results.get(key, [])
        items_sorted = sorted(items, key=lambda x: x["est_driving_distance_meters"])
        return items_sorted[:n]

    hospitals["nearby_hospital"] = top_n_closest(hospitals, "nearby_hospital", 5)
    dentists["nearby_dentist"] = top_n_closest(dentists, "nearby_dentist", 5)
    pharmacies["nearby_pharmacy"] = top_n_closest(pharmacies, "nearby_pharmacy", 5)


    return {
        "healthcare": {
             "pharmacy": {
                "num_of_pharmacies": num_pharmacies,
               
                **pharmacies
            },
            "num_of_hospitals" : num_hospitals,
            "num_of_dentists" : num_dentists,
            **hospitals,
            **dentists,
           
        }
    }

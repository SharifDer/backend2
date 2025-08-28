from all_types.request_dtypes import Reqsmartreport, ReqFetchDataset
from smart_reports.utils import generate_bbox,bbox_to_polygon
from data_fetcher import fetch_dataset
from smart_reports.traffic import fetch_traffic_data
from smart_reports.population import fetch_demographics, fetch_household_sizes
from smart_reports.healthcare_system import get_healthcare_data
from smart_reports.complementary_businesses import get_other_businesses_data
from smart_reports.scoring import *
from smart_reports.report_generation.pharmacy_report_final import generate_report_from_data

async def generate_pharmacy_report(req : Reqsmartreport):
    req_dataset = ReqFetchDataset(user_id=req.user_id , city_name=req.city_name,
                                  country_name=req.country_name,
                                boolean_query="shop_for_rent",
                                action="full data",
                                full_load=True)
    """
    Generate a pharmacy site report with multi-criteria scoring.

    Loads datasets, computes scores for traffic, demographics, healthcare,
    competition, and nearby amenities, then returns top-ranked sites.

    Args:
        req (Reqsmartreport): Request with user info and evaluation metrics.

    Returns:
        dict: Pharmacy report with scores and insights.
    """
    shops_for_rent = await loading_category_dataset(req_dataset)
    req_dataset.boolean_query = "pharmacy"
    pharmacies = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "hospital"
    hospitals = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "dentist"
    dentists = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "grocery_store"
    grocery_store = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "supermarket"
    supermarket = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "restaurant"
    restaurant = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "atm"
    atm = await loading_category_dataset(req_dataset)

    req_dataset.boolean_query = "bank"
    bank = await loading_category_dataset(req_dataset)
   

    ## in this part For Each location (shop for rent), 
    # we fetch all the details of that specific locations
    all_shops_data = []
    for shop in shops_for_rent:
        price = shop["properties"]['price'] or 0
        geometry = shop['geometry']
        coordinates = geometry['coordinates']
        lng = coordinates[0]
        lat = coordinates[1]
        place_url = shop["properties"]["url"]
        last_segment = place_url.split('/')[-1]
        extracted_part = last_segment.rsplit('-', 1)[0]
        shop_data = await fetch_all_criterions_data(
            lat=lat,
            lng=lng,
            Userid=req.user_id,
            hospital=hospitals,
            pharmacies=pharmacies,
            dentists=dentists,
            grocery_store=grocery_store,
            supermarket=supermarket,
            restaurant=restaurant,
            atm=atm,
            bank=bank,
            place_url=extracted_part,
            place_price=price
        )

        all_shops_data.append(shop_data)
   
    # in this part we process all candidates locations data
    results = {}
    for shop in all_shops_data:
        lat = shop.get("lat")
        lng = shop.get("lng")
        place_name = shop.get("place name")
        place_price = shop.get("price")
        # Compose key
        loc_key = f"{lat},{lng}"
        location_data = shop.get("location_data", {})
        num_of_businesses_around = location_data["num of business around"]
        traffic_data = location_data.get("traffic", {})
        healthcare_data = location_data.get("healthcare", {})
        amenities_data = location_data.get("nearest_businessess", {})
        pop_data = location_data.get("pop_data", {})
        traffic_score_weight = req.evaluation_metrics.traffic
        #here we score each location
        if traffic_data:
            traffic_score = score_traffic_for_retail(
                average_speed=traffic_data.get("Average Vehicle Speed in km", 0),
                ## Functional Road Class is how much of highway this street is
                frc=traffic_data.get("Functional Road Class", ""),
                traffic_score=traffic_score_weight
            )
        
        demographics_score = score_demographics(pop_data, req.evaluation_metrics.demographics)
        healthcare_score = score_healthcare_ecosystem(healthcare_data, req.evaluation_metrics.healthcare)
        competitive_score = score_competitive(healthcare_data, req.evaluation_metrics.competition)
        complementary_score = score_complementary_businesses(amenities_data, req.evaluation_metrics.complementary)


        results[loc_key] = {
            "place name" : place_name,
            "lat": lat,
            "lng": lng,
            "price" : place_price,
            "scores": {
                "overall_score" : (traffic_score["overall_score"] + demographics_score["overall_score"] + 
                                   healthcare_score["overall_score"] + competitive_score["overall_score"] + complementary_score["overall_score"]),
                "traffic": traffic_score,
                "demographics": demographics_score,
                "competition": competitive_score,
                "healthcare": healthcare_score,
                "complementary": complementary_score,
            },
            "data" : {
                'nearby Businesses within 500 meters' : num_of_businesses_around,
               **(traffic_data or {}),
                **(pop_data or {}),
                'competing_pharmacies' : healthcare_data.get("pharmacy" , 0).get("num_of_pharmacies" , 0),
                "pharmacies_per_10k_population" : healthcare_data.get("pharmacy").get("pharmacies_per_10k_population" ),
                "number of hospitals around" : healthcare_data.get("num_of_hospitals"),
                "number of dentists around" : healthcare_data.get("num_of_dentists") 
            }
        }

    criterion_weights = req.evaluation_metrics.dict()
    max_total = sum(criterion_weights.values())
    report_data = await generate_report_from_data(results , criterion_weights , max_total) 
    return report_data


async def fetch_all_criterions_data(
    lat: float,
    lng: float,
    Userid: str,
    hospital: dict,
    pharmacies: dict,
    dentists: dict,
    grocery_store: dict,
    supermarket: dict,
    restaurant: dict,
    atm: dict,
    bank: dict,
    place_url : str,
    place_price 
):
    """
    Fetch all relevant criterion data for evaluating a shop location.
    Combines traffic, households, demographics, healthcare, and other businesses.
    """
    bbox = generate_bbox(lat , lng)
    area_polygon = bbox_to_polygon(bbox=bbox)
    traffic = await fetch_traffic_data(lat, lng)
    households = await fetch_household_sizes(bbox)
    demographics = await fetch_demographics(bbox, Userid)
    healthcare = await get_healthcare_data(area_polygon, lat, lng, hospital, dentists, pharmacies)
    other_businesses = await get_other_businesses_data(
        area_polygon,
        lat,
        lng,
        grocery_store_data=grocery_store,
        supermarket_data=supermarket,
        restaurant_data=restaurant,
        bank_data=bank,
        atm_data=atm)
    total_population = demographics.get("total_population") if demographics else None
    num_pharmacies = (
            healthcare.get("healthcare", {})
                            .get("pharmacy", {})
                            .get("num_of_pharmacies")
            if healthcare else None
        )
    # Calculate pharmacies per 10k population
    pharmacies_per_10k = (num_pharmacies / total_population * 10000) if total_population and total_population > 0 else 0

    # Add the new key right under num_of_pharmacies
    healthcare["healthcare"]["pharmacy"]["pharmacies_per_10k_population"] = pharmacies_per_10k
    return {
        "place name" : place_url ,
        "lat": lat,
        "lng": lng ,
        "price" : place_price,
        "location_data": {
            "traffic": traffic,
            "pop_data" : {
                **households,
                **demographics
            },
        **healthcare,
        **other_businesses
        }
    }


    
async def loading_category_dataset(req: ReqFetchDataset):

    data = await fetch_dataset(req)   
    try:
        features = data.get("features", []) 
        return features
    except Exception as e:
        print("Error fetching features:", e)
        return []


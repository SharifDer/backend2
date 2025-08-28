
def score_traffic_for_retail(average_speed : float, frc : str,traffic_score):
    """
    Scores traffic conditions for retail based on average vehicle speed and functional road class (FRC).
    
    Returns a dict with weighted overall score and details of sub-scores.
    """
   #highway evaluation
    frc_weights = {
        "FRC" : {
        "FRC0": 0.0,  
        "FRC1": 0.0,
        "FRC2": 0.3,
        "FRC3": 0.6,
        "FRC4": 1,  
        "FRC5": 1,
        "FRC6": 0.9,
        "FRC7": 0.7,
        "FRC8" : 0.6
        }
        }
     # Speed normalization: in retail, moderate speed (~40–60 km/h) is ideal
    if average_speed < 20:
        speed_score = 0.6
    elif 20 <= average_speed <= 30 :
        speed_score = 1.0
    elif 30 < average_speed <= 50:
        speed_score = 0.8
    elif 50 < average_speed <= 70:
        speed_score = 0.7
    else:
        speed_score = 0.3  # highway speeds

    frc_score = frc_weights.get("FRC").get(frc , 0.5)

    combined_score = 0.5 * speed_score + 0.5 * frc_score
    # overall_score = traffic_score * combined_score

    return {
        "overall_score": (combined_score * traffic_score) ,
        "details": {
            "Average Viechle Speed": speed_score * 100,
            "highway score": frc_score * 100,
        }
    }

def score_demographics(pop_data: dict, weight_score: float) -> dict:
    """
    Scores demographics by combining:
    - Residential density (avg_density)
    - Age 35+ (%)
    - Income (avg_income)
    - Household size (median or average size)
    
    Returns dict with weighted overall score and detailed scores.
    """

    MAX_DENSITY = 6000    # people per sq km (adjust as max observed)
    MAX_INCOME = 11000     # SAR monthly (approximate upper bound)
    MAX_HOUSEHOLD_SIZE = 4 # large families in area
 
    density_score = min(pop_data.get("avg_density", 0) / MAX_DENSITY, 1.0)
    age_score = min(pop_data.get("percentage_age_above_35", 0) / 60, 1.0)
    income_score = min(pop_data.get("avg_income", 0) / MAX_INCOME, 1.0)
    
    household_size = pop_data.get("Household_Median_Size", pop_data.get("Household_Average_Size", 1))
    household_score = min(household_size / MAX_HOUSEHOLD_SIZE, 1.0)

    average_score = (density_score + age_score + income_score + household_score) / 4

    return {
        "overall_score": (average_score  * weight_score) ,
        "details": {
            " Residential density within 3km driving radius": (density_score * 100),
            "Age distribution above 35": age_score * 100,
            "Income levels": income_score * 100,
            "Household composition": household_score * 100
        }
    }

def score_competitive(healthcare_data, weight_score):
    nearby_pharmacies = healthcare_data['pharmacy'].get('nearby_pharmacy', [])
    pharmacies_per_10k = healthcare_data['pharmacy'].get('pharmacies_per_10k_population', 0) / 100

    if nearby_pharmacies:
        nearest_distance = min(p['est_driving_distance_meters'] for p in nearby_pharmacies)
    else:
        nearest_distance = 3000  # large distance, underserved
    # Normalize distance score: farther is better, capped at 5 km
    distance_score = min(nearest_distance / 1000, 1.0)

    # Normalize saturation: assume 0 to 20 pharmacies per 10k population
    saturation_score = max(0, (1 - pharmacies_per_10k)) if pharmacies_per_10k > 0 else 0

    # Average of the two criteria (0..1)
    average_score = (distance_score + saturation_score) / 2

    return {
        "overall_score": (average_score * weight_score) ,
        "details": {
            "Distance to nearest pharmacy": distance_score * 100,
            "Market saturation": saturation_score * 100,
            # "Underserved population pockets" : "N/A",
            "competeing pharmacies around" : healthcare_data["pharmacy"]["num_of_pharmacies"]
        }
    }


def score_healthcare_ecosystem(healthcare_data, weight_score):
    def score_proximity(places):
        if not places:
            return 0.0
        max_distance = 1500  # meters
        within_3km = [p for p in places if p['est_driving_distance_meters'] <= max_distance]
        if not within_3km:
            return 0.0

        avg_distance = sum(p['est_driving_distance_meters'] for p in within_3km) / len(within_3km)
        avg_distance_score = 1 - min(1, avg_distance / max_distance)
        count_score = min(len(within_3km), 5) / 5
        return avg_distance_score * count_score

    hospitals_score = score_proximity(healthcare_data.get('nearby_hospital', []))
    dentists_score = score_proximity(healthcare_data.get('nearby_dentist', []))

    average_score = (hospitals_score + dentists_score) / 2
    return {
        "overall_score": (average_score * weight_score) ,
        "details": {
            "Proximity to hospitals": hospitals_score * 100,
            " Proximity to dentists": dentists_score * 100
        }
    }


def score_complementary_businesses(amenities_data, weight_score):
    MAX_DISTANCE = 1000  # meters, max cutoff for proximity scoring

    def proximity_score(places):
        if not places:
            return 0.0
        # Score for each place: 1 - (distance / MAX_DISTANCE), clipped to [0,1]
        scores = [max(0, 1 - (p['est_distance_meters'] / (MAX_DISTANCE * 2))) for p in places]
        # Average score for all places of this type
        return min(1, (sum(scores) / len(scores)) + (len(places) * 0.05))

    grocery_score = proximity_score(amenities_data.get('grocery_store', {}).get('nearby_grocery_store', []))
    supermarket_score = proximity_score(amenities_data.get('supermarket', {}).get('nearby_supermarket', []))
    restaurant_score = proximity_score(amenities_data.get('restaurant', {}).get('nearby_restaurant', []))
    atm_score = proximity_score(amenities_data.get('atm', {}).get('nearby_atm', []))
    bank_score = proximity_score(amenities_data.get('bank', {}).get('nearby_bank', []))

    # Equal weight average of all five types
    average_score = (grocery_score + supermarket_score + restaurant_score + atm_score + bank_score) / 5

    return {
        "overall_score": (average_score * weight_score) ,
        "details": {
            "grocery_store": grocery_score * 100,
            "supermarkets": supermarket_score * 100,
            "restaurants": restaurant_score * 100,
            "ATMs": atm_score * 100,
            "Banks": bank_score * 100
        }
    }
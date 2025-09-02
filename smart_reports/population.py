from storage_methods import fetch_intelligence_by_viewport
from backend_common.database import Database
from all_types.request_dtypes import ReqIntelligenceData

async def fetch_demographics(bbox : dict , user_id : str):
    try:
        req_bbox = ReqIntelligenceData(   
            top_lng=bbox["max_lng"],
            top_lat=bbox["max_lat"],
            bottom_lng=bbox["min_lng"],
            bottom_lat=bbox["min_lat"],
            user_id=user_id,
            zoom_level=12,
            income=True,
            population=True
        )
        try:
            data = await fetch_intelligence_by_viewport(req_bbox)
        except Exception as e:
            if "Could not find data for zoom level" in str(e):
            ## Return Default values in case of data not found
                    return {
                "total_population": 1500,
                "avg_density": 3000.0,  # Half of MAX_DENSITY from scoring
                "avg_median_age": 28.0,
                "avg_income": 5500.0,   # Half of MAX_INCOME from scoring
                "percentage_age_above_35": 30.0  # Half of max age percentage
                }
            else:
                raise 
        print("data pop " , data)
        features = data["features"]
        ## Return zeros values in case of an empty dict
        if not features:
                return {
            "total_population": 1500,
            "avg_density": 3000.0,  # Half of MAX_DENSITY from scoring
            "avg_median_age": 28.0,
            "avg_income": 5500.0,   # Half of MAX_INCOME from scoring
            "percentage_age_above_35": 30.0  # Half of max age percentage
            }
    except Exception as e:
        print(f"Failed to fetch demographics data: {str(e)}")
        return None
    
    total_population = 0
    pop_density_values = []
    age_values = []
    income_values = []
    for f in features:
        props = f["properties"]
        total_population += props.get("Population_Count") or 0
        pop_density_values.append(props.get("Population_Density_KM2", 0))
        age_values.append(props.get("Median_Age_Total") or 0)
        income_values.append(props.get("income", 0))
    processed = {
    "total_population": total_population,
    "avg_density": round((sum(pop_density_values) / len(pop_density_values)), 2),
    "avg_median_age": round((sum(age_values) / len(age_values)), 2),
    "avg_income": round((sum(income_values) / len(income_values)), 2),
        }

    # Add derived percentages
    percentage_age_above_35 = (processed.get("avg_median_age", 0) - 35 + 50)

    processed.update({
        "percentage_age_above_35": percentage_age_above_35,
    })

    return processed

async def fetch_household_sizes(bbox : dict):
    try:
        query = """
            SELECT 
                AVG("Household_Average_Size")::INT AS avg_household_size,
                AVG("Household_Median_Size")::INT AS avg_median_size
            FROM schema_marketplace.household_all_features_v12
            WHERE ST_Intersects(
                geometry,
                ST_MakeEnvelope($1, $2, $3, $4, 4326)
            )
        """
        
        row = await Database.fetchrow(
            query,
            bbox["min_lng"],
            bbox["min_lat"],
            bbox["max_lng"],
            bbox["max_lat"]
        )

        return {
            "Household_Average_Size": row["avg_household_size"] if row["avg_household_size"] else 0,
            "Household_Median_Size":  row["avg_median_size"] if row["avg_median_size"] else 0,
        }
    except Exception as e:
        print(f"Failed to fetch household data: {str(e)}")
        return {
            "Household_Average_Size": 0,
            "Household_Median_Size": 0,
        }

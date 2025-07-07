# tests/integration/test_fetch_dataset.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint

# Dataset fetch test configurations
FETCH_DATASET_TESTS = [
    ConfigDrivenTest(
        name="test_fetch_dataset_supermarket",
        description="Test fetching dataset sample for supermarket search",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_dataset"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch dataset sample",
            "request_info": {"request_id": "test-fetch-sample-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 0,
                "lng": 0,
                "radius": 30000.0,
                "boolean_query": "supermarket",
                "page_token": "",
                "action": "sample",
                "search_type": "category_search",
                "country_name": "Saudi Arabia",
                "city_name": "Riyadh",
                "prdcer_lyr_id": "",
                "text_search": "",
                "zoom_level": 0,
                "bounding_box": [],
                "included_types": [],
                "excluded_types": [],
                "ids_and_location_only": False,
                "include_rating_info": False,
                "include_only_sub_properties": True,
                "full_load": False
            }
        },
        # ✅ Remove expected_output and use JSON instead
        expected_output_file="test_fetch_dataset.json",
        expected_output_key="supermarket_cat_response"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_cafe_restaurant",
        description="Test fetching dataset sample for cafe and restaurant search in Jeddah",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            ggl_raw_seeds=["restaurant_jeddah_cat_response", "cafe_jeddah_cat_response"],
            dataset_seeds=["cafe_restaurant_dataset"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch dataset sample",
            "request_info": {"request_id": "test-fetch-cafe-restaurant-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 0,
                "lng": 0,
                "radius": 30000.0,
                "boolean_query": "cafe OR restaurant",
                "page_token": "",
                "action": "sample",
                "search_type": "category_search",
                "country_name": "Saudi Arabia",
                "city_name": "Jeddah",
                "prdcer_lyr_id": "",
                "text_search": "",
                "zoom_level": 0,
                "bounding_box": [],
                "included_types": [],
                "excluded_types": [],
                "ids_and_location_only": False,
                "include_rating_info": False,
                "include_only_sub_properties": True,
                "full_load": False
            }
        },
        expected_output_file="test_fetch_dataset.json",
        expected_output_key="cafe_restaurant_cat_response"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_supermarket_full_data_riyadh",
        description="Test fetching full dataset for supermarket search in Riyadh with complete details",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            ggl_raw_seeds=["supermarket_full_data_riyadh_response"],
            dataset_seeds=["supermarket_full_data_riyadh_response"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch full dataset for supermarkets in Riyadh",
            "request_info": {"request_id": "test-fetch-full-data-supermarket-riyadh-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 0,
                "lng": 0,
                "radius": 30000.0,
                "boolean_query": "supermarket",
                "page_token": "",
                "action": "full data",
                "search_type": "category_search",
                "country_name": "Saudi Arabia",
                "city_name": "Riyadh",
                "prdcer_lyr_id": "",
                "text_search": "",
                "zoom_level": 0,
                "bounding_box": [],
                "included_types": [],
                "excluded_types": [],
                "ids_and_location_only": False,
                "include_rating_info": False,
                "include_only_sub_properties": True,
                "full_load": False
            }
        },
        expected_output_file="test_fetch_dataset.json",
        expected_output_key="supermarket_full_data_riyadh_response"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_supermarket_full_data_with_token",
        description="Test fetching full dataset for supermarket search in Riyadh with page token continuation",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            ggl_raw_seeds=["supermarket_full_data_riyadh_token_response"],
            dataset_seeds=["supermarket_full_data_riyadh_token_response"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch dataset with token",
            "request_info": {"request_id": "test-fetch-token-supermarket-riyadh-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 0,
                "lng": 0,
                "radius": 15000.0,
                "boolean_query": "supermarket",
                "page_token": "page_token=plan_supermarket_Saudi Arabia_Riyadh@#$1",
                "action": "full data",
                "search_type": "category_search",
                "country_name": "Saudi Arabia",
                "city_name": "Riyadh",
                "prdcer_lyr_id": "",
                "text_search": "",
                "zoom_level": 0,
                "bounding_box": [],
                "included_types": [],
                "excluded_types": [],
                "ids_and_location_only": False,
                "include_rating_info": False,
                "include_only_sub_properties": True,
                "full_load": False
            }
        },
        expected_output_file="test_fetch_dataset.json",
        expected_output_key="supermarket_full_data_riyadh_token_response"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_arabic_keyword_search",
        description="Test fetching dataset sample for Arabic keyword search '@الحلقه@' in Riyadh",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            ggl_raw_seeds=["arabic_keyword_al_halaqa_response"],
            dataset_seeds=["arabic_keyword_al_halaqa_dataset"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch dataset sample for Arabic keyword",
            "request_info": {"request_id": "test-fetch-arabic-keyword-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 0,
                "lng": 0,
                "radius": 30000.0,
                "boolean_query": "@الحلقه@",
                "page_token": "",
                "action": "sample",
                "search_type": "keyword_search",
                "country_name": "Saudi Arabia",
                "city_name": "Riyadh",
                "prdcer_lyr_id": "",
                "text_search": "",
                "zoom_level": 0,
                "bounding_box": [],
                "included_types": [],
                "excluded_types": [],
                "ids_and_location_only": False,
                "include_rating_info": False,
                "include_only_sub_properties": True,
                "full_load": False
            }
        },
        expected_output_file="test_fetch_dataset.json",
        expected_output_key="arabic_keyword_al_halaqa_response"
    )
]


# Create the parametrized test function
test_fetch_dataset_endpoints = create_parametrized_test(FETCH_DATASET_TESTS)

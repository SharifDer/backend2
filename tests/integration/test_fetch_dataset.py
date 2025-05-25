# tests/integration/test_fetch_dataset.py
import pytest
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
            ggl_raw_seeds=["supermarket"],
            dataset_seeds=["supermarket_dataset"]
        ),
        endpoint=Endpoint(method="POST", path="/fetch_dataset"),
        input_data={
            "message": "Fetch dataset sample",
            "request_info": {"request_id": "test-fetch-sample-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "lat": 24.7136,
                "lng": 46.6753,
                "radius": 2000.0,
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
        expected_output={
            "status_code": 200,
            "response_body": {
                "data": {
                    "features": "non_empty_list",
                    "type": "FeatureCollection"
                }
            }
        },
        print_response_on_failure=True  # ✅ Enable detailed response printing
    ),
    
    # ConfigDrivenTest(
    #     name="test_fetch_dataset_text_search_coffee",
    #     prerequisites=Prerequisites(
    #         requires_user=True,
    #         requires_auth=True,
    #         requires_database_seed=True,
    #         ggl_raw_seeds=["coffee_shop_search"]  # ✅ Make sure this matches your JSON key
    #     ),
    #     endpoint=Endpoint(method="POST", path="/fetch_dataset"),
    #     input_data={
    #         "message": "Fetch dataset text search",
    #         "request_info": {"request_id": "test-fetch-text-002"},
    #         "request_body": {
    #             "user_id": "${user.user_id}",
    #             "lat": 24.7136,
    #             "lng": 46.6753,
    #             "radius": 2000.0,
    #             "boolean_query": "@coffee shop@",
    #             "page_token": "",
    #             "action": "sample",
    #             "search_type": "keyword_search",  # ✅ Changed to string
    #             "country_name": "Saudi Arabia",
    #             "city_name": "Riyadh",
    #             "prdcer_lyr_id": "",
    #             "text_search": "true",  # ✅ Set for text search
    #             "zoom_level": 0,
    #             "bounding_box": [],
    #             "included_types": [],
    #             "excluded_types": [],
    #             "ids_and_location_only": False,
    #             "include_rating_info": False,
    #             "include_only_sub_properties": True,
    #             "full_load": False
    #         }
    #     },
    #     expected_output={
    #         "status_code": 200,
    #         "response_body": {
    #             "data": {
    #                 "bknd_dataset_id": "contains:text_search=true"
    #             }
    #         }
    #     }
    # ),
    
    # ConfigDrivenTest(
    #     name="test_fetch_dataset_full_data",
    #     prerequisites=Prerequisites(
    #         requires_user=True,
    #         requires_auth=True,
    #         requires_database_seed=True,
    #         ggl_raw_seeds=["supermarket"],
    #         dataset_seeds=["supermarket_dataset"]
    #     ),
    #     endpoint=Endpoint(method="POST", path="/fetch_dataset"),
    #     input_data={
    #         "message": "Fetch dataset full data",
    #         "request_info": {"request_id": "test-fetch-full-003"},
    #         "request_body": {
    #             "user_id": "${user.user_id}",
    #             "lat": 24.7136,
    #             "lng": 46.6753,
    #             "radius": 2000.0,
    #             "boolean_query": "supermarket",
    #             "page_token": "",
    #             "action": "full data",  # ✅ Note the space in "full data"
    #             "search_type": "category_search",  # ✅ Changed to string
    #             "country_name": "Saudi Arabia",
    #             "city_name": "Riyadh",
    #             "prdcer_lyr_id": "",
    #             "text_search": "",
    #             "zoom_level": 0,
    #             "bounding_box": [],
    #             "included_types": [],
    #             "excluded_types": [],
    #             "ids_and_location_only": False,
    #             "include_rating_info": False,
    #             "include_only_sub_properties": True,
    #             "full_load": False
    #         }
    #     },
    #     expected_output={
    #         "status_code": 200,
    #         "response_body": {
    #             "data": {
    #                 "next_page_token": "exists",
    #                 "progress": "exists"
    #             }
    #         }
    #     }
    # )
]


# Create the parametrized test function
test_fetch_dataset_endpoints = create_parametrized_test(FETCH_DATASET_TESTS)
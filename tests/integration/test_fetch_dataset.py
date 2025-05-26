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
            ggl_raw_seeds=["supermarket_cat_response"],
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
        expected_output_key="supermarket_cat_response",
        print_response_on_failure=True
    )
]


# Create the parametrized test function
test_fetch_dataset_endpoints = create_parametrized_test(FETCH_DATASET_TESTS)

# tests/integration/test_filter_based_on.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint

# Filter based on test configurations
FILTER_BASED_ON_TESTS = [
    ConfigDrivenTest(
        name="test_filter_based_on_radius_rating",
        description="Test filtering features based on radius and rating criteria",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/filter_based_on"),
        input_data={
            "message": "Filter features based on radius and rating",
            "request_info": {"request_id": "test-filter-radius-rating-001"},
            "request_body": {
                "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
                "change_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "change_lyr_name": "SA-RIY-supermarket",
                "change_lyr_current_color": "#28A745",
                "change_lyr_new_color": "#FF0000",
                "based_on_lyr_id": "l116e3196-e721-4434-bad6-46291ba2aa0a",
                "based_on_lyr_name": "SA-RIY-pharmacy",
                "coverage_value": 2.0,
                "coverage_property": "radius",
                "color_based_on": "rating",
                "list_names": [],
                "comparison_type": "greater",
                "threshold": 4.0
            }
        },
        expected_output_file="expected_responses/test_filter_based_on_radius_rating.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_drive_time_name",
        description="Test filtering features based on drive time and specific names",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/filter_based_on"),
        input_data={
            "message": "Filter features based on drive time and specific names",
            "request_info": {"request_id": "test-filter-drive-time-name-001"},
            "request_body": {
                "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
                "change_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "change_lyr_name": "SA-RIY-supermarket",
                "change_lyr_current_color": "#28A745",
                "change_lyr_new_color": "#FF0000",
                "based_on_lyr_id": "l116e3196-e721-4434-bad6-46291ba2aa0a",
                "based_on_lyr_name": "SA-RIY-pharmacy",
                "coverage_value": 10.0,
                "coverage_property": "drive_time",
                "color_based_on": "name",
                "list_names": ["Test Supermarket Riyadh", "Test Hypermarket Riyadh"],
                "comparison_type": "less",
                "threshold": ""
            }
        },
        expected_output_file="expected_responses/test_filter_based_on_drive_time_name.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_user_ratings_total",
        description="Test filtering features based on user ratings total",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["cafe_restaurant_dataset"],
            dataset_seeds=["cafe_restaurant_dataset"],
            firebase_profile_seeds=["admin_profile_with_cafe_restaurant"]
        ),
        endpoint=Endpoint(method="POST", path="/filter_based_on"),
        input_data={
            "message": "Filter features based on user ratings total",
            "request_info": {"request_id": "test-filter-user-ratings-001"},
            "request_body": {
                "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
                "change_lyr_id": "l217d4297-f832-5545-cbd7-57392ca3bb1b",
                "change_lyr_name": "SA-JED-cafe-restaurant",
                "change_lyr_current_color": "#17A2B8",
                "change_lyr_new_color": "#FF0000",
                "based_on_lyr_id": "l217d4297-f832-5545-cbd7-57392ca3bb1b",
                "based_on_lyr_name": "SA-JED-cafe-restaurant",
                "coverage_value": 1.5,
                "coverage_property": "radius",
                "color_based_on": "user_ratings_total",
                "list_names": [],
                "comparison_type": "greater",
                "threshold": 50
            }
        },
        expected_output_file="expected_responses/test_filter_based_on_user_ratings_total.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_no_coverage",
        description="Test filtering features with no coverage property (property filter only)",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/filter_based_on"),
        input_data={
            "message": "Filter features with property filter only",
            "request_info": {"request_id": "test-filter-property-only-001"},
            "request_body": {
                "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
                "change_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "change_lyr_name": "SA-RIY-supermarket",
                "change_lyr_current_color": "#28A745",
                "change_lyr_new_color": "#FF0000",
                "based_on_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "based_on_lyr_name": "SA-RIY-supermarket",
                "coverage_value": 0.0,
                "coverage_property": "",
                "color_based_on": "rating",
                "list_names": [],
                "comparison_type": "greater",
                "threshold": 4.0
            }
        },
        expected_output_file="expected_responses/test_filter_based_on_no_coverage.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_no_results",
        description="Test filtering with criteria that return no results",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/filter_based_on"),
        input_data={
            "message": "Filter features with impossible criteria",
            "request_info": {"request_id": "test-filter-no-results-001"},
            "request_body": {
                "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
                "change_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "change_lyr_name": "SA-RIY-supermarket",
                "change_lyr_current_color": "#28A745",
                "change_lyr_new_color": "#FF0000",
                "based_on_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                "based_on_lyr_name": "SA-RIY-supermarket",
                "coverage_value": 1.0,
                "coverage_property": "radius",
                "color_based_on": "rating",
                "list_names": [],
                "comparison_type": "greater",
                "threshold": 5.0  # Impossible rating threshold
            }
        },
        expected_output_file="expected_responses/test_filter_based_on_no_results.json"
    )
]

# Create parametrized tests
test_filter_based_on = create_parametrized_test(FILTER_BASED_ON_TESTS)

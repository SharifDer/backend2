# tests/integration/test_filter_based_on.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint
from all_types.request_dtypes import ReqFilterBasedon

# Filter based on test configurations
FILTER_BASED_ON_TESTS = [
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_radius_rating",
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
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=2.0,
                area_coverage_measure="radius",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=4.0
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_radius_rating.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_drive_time_name",
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
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=10.0,
                area_coverage_measure="drive_time",
                evaluation_property_name="name",
                evaluation_name_list=["Test Supermarket Riyadh", "Test Hypermarket Riyadh"],
                evaluation_comparison_operator="less",
                property_threshold=""
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_drive_time_name.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_self_filter_user_ratings_total",
        description="Test self-filtering features based on user ratings total",
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
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l217d4297-f832-5545-cbd7-57392ca3bb1b",
                change_lyr_name="SA-JED-cafe-restaurant",
                change_lyr_current_color="#17A2B8",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l217d4297-f832-5545-cbd7-57392ca3bb1b",
                based_on_lyr_name="SA-JED-cafe-restaurant",
                area_coverage_value=1.5,
                area_coverage_measure="radius",
                evaluation_property_name="user_ratings_total",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=50
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_user_ratings_total.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_self_filter_no_coverage",
        description="Test self-filtering features with no coverage property (property filter only)",
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
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                based_on_lyr_name="SA-RIY-supermarket",
                area_coverage_value=0.0,
                area_coverage_measure="",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=4.0
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_self_filter_no_coverage.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_self_filter_no_results",
        description="Test self-filtering with criteria that return no results",
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
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                based_on_lyr_name="SA-RIY-supermarket",
                area_coverage_value=1.0,
                area_coverage_measure="radius",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=5.0  # Impossible rating threshold
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_no_results.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_proximity_rating",
        description="Test filtering supermarket features based on proximity to pharmacies with high ratings",
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
            "message": "Filter supermarkets based on proximity to high-rated pharmacies",
            "request_info": {"request_id": "test-filter-cross-layer-proximity-001"},
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF6B35",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=1.5,
                area_coverage_measure="radius",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=4.2
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_cross_layer_proximity_rating.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_drive_time_reviews",
        description="Test filtering pharmacies based on drive time to supermarkets with many reviews",
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
            "message": "Filter pharmacies within drive time of popular supermarkets",
            "request_info": {"request_id": "test-filter-cross-layer-drive-time-001"},
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                change_lyr_name="SA-RIY-pharmacy",
                change_lyr_current_color="#DC3545",
                change_lyr_new_color="#17A2B8",
                based_on_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                based_on_lyr_name="SA-RIY-supermarket",
                area_coverage_value=8.0,
                area_coverage_measure="drive_time",
                evaluation_property_name="user_ratings_total",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=10
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_cross_layer_drive_time_reviews.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_name_match",
        description="Test filtering supermarkets based on specific pharmacy names within radius",
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
            "message": "Filter supermarkets near pharmacies with rating filter",
            "request_info": {"request_id": "test-filter-cross-layer-name-001"},
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#6F42C1",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=2.5,
                area_coverage_measure="radius",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=3.5
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_cross_layer_name_match.json"
    ),
    
    ConfigDrivenTest(
        name="test_filter_based_on_cross_layer_no_coverage",
        description="Test cross-layer filtering with no coverage property (property filter only)",
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
            "message": "Filter pharmacies based on supermarket property values only",
            "request_info": {"request_id": "test-filter-cross-layer-no-coverage-001"},
            "request_body": ReqFilterBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                change_lyr_name="SA-RIY-pharmacy",
                change_lyr_current_color="#DC3545",
                change_lyr_new_color="#FFC107",
                based_on_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                based_on_lyr_name="SA-RIY-supermarket",
                area_coverage_value=0.0,
                area_coverage_measure="",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater",
                property_threshold=3.8
            ).model_dump()
        },
        expected_output_file="expected_responses/test_filter_based_on_cross_layer_no_coverage.json"
    )
]

# Create parametrized tests
test_filter_based_on = create_parametrized_test(FILTER_BASED_ON_TESTS)

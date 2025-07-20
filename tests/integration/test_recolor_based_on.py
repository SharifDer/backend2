# tests/integration/test_recolor_based_on.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint
from all_types.request_dtypes import ReqColorBasedon

# Recolor based on test configurations
RECOLOR_BASED_ON_TESTS = [
    ConfigDrivenTest(
        name="test_recolor_based_on_property_rating",
        description="Test recoloring features based on their rating property",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features based on rating property",
            "request_info": {"request_id": "test-recolor-property-rating-001"},
            "request_body": ReqColorBasedon(
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
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_property_rating.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_cross_layer_radius",
        description="Test recoloring features based on another layer's radius property",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features based on cross-layer radius",
            "request_info": {"request_id": "test-recolor-cross-layer-radius-001"},
            "request_body": ReqColorBasedon(
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
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_cross_layer_radius.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_cross_layer_drive_time",
        description="Test recoloring features based on drive time proximity to another layer",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features based on drive time proximity",
            "request_info": {"request_id": "test-recolor-drive-time-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=10.0,
                area_coverage_measure="drive_time",
                evaluation_property_name="user_ratings_total",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_cross_layer_drive_time.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_gradient_coloring",
        description="Test gradient coloring based on nearby influence scores",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Apply gradient coloring based on nearby pharmacy influence",
            "request_info": {"request_id": "test-recolor-gradient-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#00FF00", "#33CC00", "#669900", "#996600", "#CC3300", "#FF0000"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=1.5,
                area_coverage_measure="",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_gradient_coloring.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_name_filtering",
        description="Test recoloring features based on specific names",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor specific named features",
            "request_info": {"request_id": "test-recolor-name-filtering-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=0.0,
                area_coverage_measure="",
                evaluation_property_name="name",
                evaluation_name_list=["Test Supermarket Riyadh", "Test Hypermarket Riyadh"],
                evaluation_comparison_operator="equal"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_name_filtering.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_user_ratings_coverage",
        description="Test recoloring features based on user ratings with coverage area",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features based on user ratings within coverage area",
            "request_info": {"request_id": "test-recolor-user-ratings-coverage-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                change_lyr_name="SA-RIY-pharmacy",
                change_lyr_current_color="#DC3545",
                change_lyr_new_color="#17A2B8",
                based_on_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                based_on_lyr_name="SA-RIY-supermarket",
                area_coverage_value=3.0,
                area_coverage_measure="radius",
                evaluation_property_name="user_ratings_total",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_user_ratings_coverage.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_self_layer_property",
        description="Test recoloring features within the same layer based on property",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features within same layer based on property",
            "request_info": {"request_id": "test-recolor-self-layer-001"},
            "request_body": ReqColorBasedon(
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
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_self_layer_property.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_multiple_colors_gradient",
        description="Test recoloring with multiple color gradient based on influence",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Apply multi-color gradient based on influence scores",
            "request_info": {"request_id": "test-recolor-multi-gradient-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333", "#000000"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#000000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=2.5,
                area_coverage_measure="",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_multiple_colors_gradient.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_no_coverage_property_only",
        description="Test recoloring based only on property without coverage constraints",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Recolor features based on property only without coverage",
            "request_info": {"request_id": "test-recolor-no-coverage-001"},
            "request_body": ReqColorBasedon(
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
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_no_coverage_property_only.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_edge_case_empty_names",
        description="Test recoloring with empty evaluation_name_list when evaluation_property_name is name",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response"],
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Test edge case with empty names list",
            "request_info": {"request_id": "test-recolor-edge-empty-names-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=0.0,
                area_coverage_measure="",
                evaluation_property_name="name",
                evaluation_name_list=[],
                evaluation_comparison_operator="equal"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_edge_case_empty_names.json"
    ),
    
    ConfigDrivenTest(
        name="test_recolor_based_on_high_coverage_value",
        description="Test recoloring with high coverage value to test boundary conditions",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
            dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/recolor_based"),
        input_data={
            "message": "Test recoloring with high coverage value",
            "request_info": {"request_id": "test-recolor-high-coverage-001"},
            "request_body": ReqColorBasedon(
                color_grid_choice=["#FF0000", "#00FF00", "#0000FF"],
                change_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                change_lyr_name="SA-RIY-supermarket",
                change_lyr_current_color="#28A745",
                change_lyr_new_color="#FF0000",
                based_on_lyr_id="l116e3196-e721-4434-bad6-46291ba2aa0a",
                based_on_lyr_name="SA-RIY-pharmacy",
                area_coverage_value=50.0,
                area_coverage_measure="radius",
                evaluation_property_name="rating",
                evaluation_name_list=[],
                evaluation_comparison_operator="greater"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_recolor_based_on_high_coverage_value.json"
    )
]

# Create parametrized tests
test_recolor_based_on = create_parametrized_test(RECOLOR_BASED_ON_TESTS)

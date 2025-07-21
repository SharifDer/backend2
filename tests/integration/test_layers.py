# tests/integration/test_layers.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint
from all_types.request_dtypes import ReqSavePrdcerLyer, ReqDeletePrdcerLayer, ReqPrdcerLyrMapData
from all_types.internal_types import UserId


# You can add more test configurations here
LAYER_MANAGEMENT_TESTS = [
    ConfigDrivenTest(
        name="test_save_layer_with_auth",
        description="Test creating a layer with authenticated user",
        prerequisites=Prerequisites(
            requires_user=True, requires_auth=True, user_type="admin"
        ),
        endpoint=Endpoint(method="POST", path="/save_layer"),
        input_data={
            "message": "save layer",
            "request_info": {"request_id": "test-layer-001"},
            "request_body": ReqSavePrdcerLyer(
                user_id="${user.user_id}",
                prdcer_layer_name="Test Layer",
                bknd_dataset_id="test-dataset-123",
                points_color="#FF0000",
                layer_legend="Test Legend",
                layer_description="Test layer description",
                city_name="Test City",
                prdcer_lyr_id=""
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "Producer layer created successfully"
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_delete_layer_with_seeded_profile",
        description="Test deleting a layer from a user profile that has been seeded with layers",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Seed Firebase profile with pre-existing layers
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="DELETE", path="/delete_layer"),
        input_data={
            "message": "delete layer",
            "request_info": {"request_id": "test-delete-001"},
            "request_body": ReqDeletePrdcerLayer(
                user_id="${user.user_id}",
                # Delete one of the seeded layers (supermarket layer)
                prdcer_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "contains:deleted successfully"
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_verify_layer_deletion_via_profile",
        description="Verify layer was deleted by first deleting it, then checking user profile",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Use seeded profile with multiple layers to delete one
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="DELETE", path="/delete_layer"),
        input_data={
            "message": "delete layer then verify profile",
            "request_info": {"request_id": "test-delete-then-verify"},
            "request_body": ReqDeletePrdcerLayer(
                user_id="${user.user_id}",
                # Delete the supermarket layer
                prdcer_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "contains:deleted successfully"
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_complete_layer_deletion_workflow",
        description="Complete test: seed profile with layers, delete layer, and verify via user profile",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Seed Firebase profile with layers to delete
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="DELETE", path="/delete_layer"),
        input_data={
            "message": "delete layer and verify",
            "request_info": {"request_id": "test-complete-workflow"},
            "request_body": ReqDeletePrdcerLayer(
                user_id="${user.user_id}",
                # Delete the supermarket layer (first one in the seeded profile)
                prdcer_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "contains:deleted"  # Should contain "deleted" in the response message
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_delete_nonexistent_layer",
        description="Test deleting a layer that doesn't exist",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Use basic profile without layers
            firebase_profile_seeds=["admin_profile_basic"]
        ),
        endpoint=Endpoint(method="DELETE", path="/delete_layer"),
        input_data={
            "message": "delete nonexistent layer",
            "request_info": {"request_id": "test-nonexistent"},
            "request_body": ReqDeletePrdcerLayer(
                user_id="${user.user_id}",
                prdcer_lyr_id="nonexistent-layer-id-12345"
            ).model_dump()
        },
        expected_output={
            "status_code": 404,  # Should return not found or similar error
        },
    ),
    
    ConfigDrivenTest(
        name="test_layer_count_after_deletion",
        description="Test that user_layers endpoint returns the correct layers",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Seed profile with 2 layers
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/user_layers"),
        input_data={
            "message": "get user layers",
            "request_info": {"request_id": "test-layer-count"},
            "request_body": UserId(
                user_id="${user.user_id}"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "length:2"  # Should have exactly 2 layers from the seeded profile
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_layer_count_after_deletion_reduced",
        description="Test that user_layers endpoint returns list format correctly",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Use seeded profile to test list response format
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/user_layers"),
        input_data={
            "message": "get user layers as list",
            "request_info": {"request_id": "test-layer-list-format"},
            "request_body": UserId(
                user_id="${user.user_id}"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "min_length:1"  # Should have at least 1 layer (it's a list)
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_prdcer_lyr_map_data_with_seeded_supermarket_data",
        description="Test retrieving map data for supermarket layer with complete data flow: seed dataset -> seed profile -> verify response",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            # Seed both the transformed dataset and Firebase profile
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/prdcer_lyr_map_data"),
        input_data={
            "message": "get supermarket layer map data",
            "request_info": {"request_id": "test-supermarket-map-data"},
            "request_body": ReqPrdcerLyrMapData(
                user_id="${user.user_id}",
                # This layer ID corresponds to the supermarket layer in admin_profile_with_datasets
                prdcer_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548"
            ).model_dump()
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": {
                    # Verify layer metadata matches the seeded profile
                    "prdcer_layer_name": "SA-RIY-supermarket",
                    "prdcer_lyr_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                    "bknd_dataset_id": "contains:supermarket",
                    "points_color": "#28A745",
                    "layer_legend": "SA-RIY-supermarket",
                    "layer_description": "",
                    "city_name": "Riyadh",
                    "is_zone_lyr": "false",
                    "progress": "type:int",  # Accept any integer (0-100 range)
                    # Verify GeoJSON structure matches the seeded dataset
                    "type": "FeatureCollection",
                    "features": "length:2",  # Should have exactly 2 features from supermarket_cat_response
                    "properties": "length:4"  # Should have 4 property types: id, displayName, rating, formattedAddress
                }
            },
        },
    ),
    
    ConfigDrivenTest(
        name="test_prdcer_lyr_map_data_verify_feature_data",
        description="Test that the returned features contain the exact data from seeded dataset",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            dataset_seeds=["supermarket_cat_response"],
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/prdcer_lyr_map_data"),
        input_data={
            "message": "verify feature data consistency",
            "request_info": {"request_id": "test-feature-data-verification"},
            "request_body": ReqPrdcerLyrMapData(
                user_id="${user.user_id}",
                prdcer_lyr_id="l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548"
            ).model_dump()
        },
        expected_output_file="expected_responses/test_prdcer_lyr_map_data_verify_feature_data.json"
    ),
    
    ConfigDrivenTest(
        name="test_prdcer_lyr_map_data_nonexistent_layer",
        description="Test retrieving map data for a nonexistent layer ID",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            firebase_profile_seeds=["admin_profile_basic"]
        ),
        endpoint=Endpoint(method="POST", path="/prdcer_lyr_map_data"),
        input_data={
            "message": "get nonexistent layer map data",
            "request_info": {"request_id": "test-map-data-404"},
            "request_body": ReqPrdcerLyrMapData(
                user_id="${user.user_id}",
                prdcer_lyr_id="nonexistent-layer-id-12345"
            ).model_dump()
        },
        expected_output={
            "status_code": 404,  # Should return not found for nonexistent layer
        },
    ),
    
    ConfigDrivenTest(
        name="test_prdcer_lyr_map_data_empty_layer_id",
        description="Test retrieving map data with empty layer ID",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            user_type="admin"
        ),
        endpoint=Endpoint(method="POST", path="/prdcer_lyr_map_data"),
        input_data={
            "message": "get map data with empty layer ID",
            "request_info": {"request_id": "test-empty-layer-id"},
            "request_body": ReqPrdcerLyrMapData(
                user_id="${user.user_id}",
                prdcer_lyr_id=""
            ).model_dump()
        },
        expected_output={
            "status_code": 400,  # Should return bad request for empty layer ID
        },
    )
]

# Layer Management API Endpoints:
# - POST /save_layer      - Create/save a new layer
# - DELETE /delete_layer  - Delete an existing layer  
# - POST /user_layers     - Get all layers for a user
# - POST /prdcer_lyr_map_data - Get map data for a layer


test_user_profile_endpoints = create_parametrized_test(
    LAYER_MANAGEMENT_TESTS
)

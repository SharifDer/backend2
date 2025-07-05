# tests/integration/test_user.py
from .fixtures.test_utils import create_parametrized_test

# tests/integration/test_configs/user_configs.py
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint


# You can add more test configurations here
LAYER_MANAGEMENT_TESTS = [
    ConfigDrivenTest(
        name="test_create_layer_with_auth",
        description="Test creating a layer with authenticated user",
        prerequisites=Prerequisites(
            requires_user=True, requires_auth=True, user_type="admin"
        ),
        endpoint=Endpoint(method="POST", path="/save_layer"),
        input_data={
            "message": "Create layer",
            "request_info": {"request_id": "test-layer-001"},
            "request_body": {
                "user_id": "${user.user_id}",
                "prdcer_layer_name": "Test Layer",
                "bknd_dataset_id": "test-dataset-123",
                "points_color": "#FF0000",
                "layer_legend": "Test Legend",
                "layer_description": "Test layer description",
                "city_name": "Test City",
            },
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "${dynamic}",
                "data": "Producer layer created successfully"
            },
        },
    )
]


test_user_profile_endpoints = create_parametrized_test(
    LAYER_MANAGEMENT_TESTS
)

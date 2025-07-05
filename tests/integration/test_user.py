# tests/integration/test_user.py
import pytest
from .fixtures.test_utils import create_parametrized_test
import uuid

# tests/integration/test_configs/user_configs.py
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint


# Define your tests as dictionaries/configurations
USER_PROFILE_TESTS = [
    ConfigDrivenTest(
        name="test_create_new_user_profile",
        description="Test creating a completely new user profile",
        prerequisites=Prerequisites(
            requires_user=False,  # No user needed!
            requires_auth=False,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/create_user_profile"),
        input_data={
            "message": "Create user profile",
            "request_info": {"request_id": "test-create-new-profile-001"},
            "request_body": {
                "email": "brand_new_user_123@test.com",
                "password": "BrandNewPass123!",
                "username": "Brand New User 123",
                "account_type": "admin",
                "admin_id": None,
                "show_price_on_purchase": True,
            },
        },
        expected_output={
            "status_code": 200,
            "response_body": [
                # ✅ First response: Firebase user creation
                {
                    "message": "Request received.",
                    "request_id": "req-6b83c0dd-de27-48a7-9ac6-a89f3fdb1b8b",  # Will be auto-validated as min_length:1
                    "data": {
                        "user_id": "min_length:1",  # ✅ Validate user ID exists
                        "message": "User profile created successfully",
                    },
                },
                # ✅ Second response: Stripe customer creation
                {
                    "message": "Request received.",
                    "request_id": "req-61675310-1e7d-4655-a860-d9d8e31528e5",  # Will be auto-validated
                    "data": {
                        "id": "starts_with:cus_",  # ✅ Stripe customer ID format
                        "object": "customer",
                        "email": "brand_new_user_123@test.com",
                        "name": "Brand New User 123",
                        "user_id": "min_length:1",  # ✅ Same user ID as first response
                        # ✅ Ignore other Stripe fields - they're not important for the test
                    },
                },
                # ✅ Third response: User profile creation
                {
                    "message": "Request received.",
                    "request_id": "req-3e731e4d-7ad0-44e3-a1d7-57af6dd5b0c7",  # Will be auto-validated
                    "data": {
                        "user_id": "min_length:1",  # ✅ Same user ID
                        "email": "brand_new_user_123@test.com",
                        "username": "Brand New User 123",
                        "account_type": "admin",
                        "admin_id": None,
                        "settings": {
                            "show_price_on_purchase": False  # ✅ API overwrites to false
                        },
                        "prdcer": {
                            "prdcer_ctlgs": {},
                            "draft_ctlgs": {},
                            "prdcer_lyrs": {},
                            "prdcer_dataset": {
                                "dataset_plan": "",
                                "auto_refresh": True,
                                # ✅ Ignore dynamic fields: progress, dataset_next_refresh_date
                            },
                        },
                    },
                },
            ],
        },
    ),
    ConfigDrivenTest(
        name="test_get_user_profile_success",
        description="Test getting user profile with valid authentication",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            user_type="regular",
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/user_profile"),
        input_data={
            "message": "Get user profile",
            "request_info": {"request_id": "test-profile-001"},
            "request_body": {"user_id": "${user.user_id}"},
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "test-profile-001",
                "data": {
                    "user_id": "${user.user_id}",
                    "email": "${user.email}",
                    "username": "${user.username}",
                    "account_type": "admin",  # Backend sets this to admin
                    "admin_id": None,
                    "settings": {
                        "show_price_on_purchase": False  # Default value
                    },
                    "prdcer": {
                        "prdcer_ctlgs": {},
                        "draft_ctlgs": {},
                        "prdcer_lyrs": {},
                        "prdcer_dataset": {
                            "dataset_plan": "",
                            "auto_refresh": True,
                        },
                    },
                },
            },
        },
    ),
    ConfigDrivenTest(
        name="test_get_user_profile_unauthorized",
        description="Test getting user profile without authentication",
        prerequisites=Prerequisites(
            requires_user=True,  # Create user but...
            requires_auth=False,  # Don't add auth headers
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/user_profile"),
        input_data={
            "message": "Get user profile",
            "request_info": {"request_id": "test-profile-unauth-001"},
            "request_body": {"user_id": "${user.user_id}"},
        },
        expected_output={
            "status_code": 403,  # or whatever your API returns for unauthorized
            "response_body": {"detail": "Not authenticated"},
        },
    ),
]


test_user_profile_endpoints = create_parametrized_test(USER_PROFILE_TESTS)

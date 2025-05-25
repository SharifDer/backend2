# # tests/integration/test_my_feature.py
# import pytest
# from .fixtures.test_utils import create_parametrized_test
# # tests/integration/test_configs/my_feature_configs.py
# from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint

# # Test a REAL endpoint that exists on your server
# MY_FEATURE_TESTS = [
#     ConfigDrivenTest(
#         name="test_user_profile_endpoint",
#         description="Test getting user profile with authentication",
#         prerequisites=Prerequisites(requires_user=True, requires_auth=True),
#         endpoint=Endpoint(method="POST", path="/user_profile"),
#         input_data={
#             "message": "Get user profile",
#             "request_info": {"request_id": "test-profile-001"},
#             "request_body": {
#                 "user_id": "${user.user_id}"
#             }
#         },
#         expected_output={
#             "status_code": 200,
#             "response_body": {
#                 "data": {
#                     "user_id": "${user.user_id}",
#                     "email": "${user.email}",
#                     "username": "${user.username}"
#                 }
#             }
#         }
#     ),
    
#     ConfigDrivenTest(
#         name="test_create_user_profile_config",
#         description="Test creating a user profile via config",
#         prerequisites=Prerequisites(requires_user=False, requires_auth=False),
#         endpoint=Endpoint(method="POST", path="/create_user_profile"),
#         input_data={
#             "message": "Create user profile",
#             "request_info": {"request_id": "test-create-config-001"},
#             "request_body": {
#                 "email": "config_test_user@test.com",
#                 "password": "ConfigTest123!",
#                 "username": "Config Test User",
#                 "account_type": "individual",
#                 "admin_id": None,
#                 "show_price_on_purchase": False
#             }
#         },
#         expected_output={
#             "status_code": 200
#             # Note: Not checking exact response body since user_id is generated
#         }
#     )
# ]

# pytestmark = [pytest.mark.integration]

# # One line to create all your tests!
# test_my_feature_endpoints = create_parametrized_test(MY_FEATURE_TESTS)
# # tests/integration/test_user.py
# import pytest
# from .fixtures.test_utils import create_parametrized_test
# import uuid

# # tests/integration/test_configs/user_configs.py
# from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint


# # Define your tests as dictionaries/configurations
# USER_PROFILE_TESTS = [
#     ConfigDrivenTest(
#         name="test_create_new_user_profile",
#         description="Test creating a completely new user profile",
#         prerequisites=Prerequisites(
#             requires_user=False,  # ⭐ NO user needed!
#             requires_auth=False,
#         ),
#         endpoint=Endpoint(method="POST", path="/create_user_profile"),
#         input_data={
#             "message": "Create user profile",
#             "request_info": {"request_id": f"test-create-{uuid.uuid4()}"},
#             "request_body": {
#                 # ⭐ Use static values, not templates
#                 "email": f"brand_new_user_{uuid.uuid4()}@test.com",
#                 "password": "BrandNewPass123!",
#                 "username": f"Brand New User {uuid.uuid4()}",
#                 "account_type": "admin",
#                 "admin_id": None,
#                 "show_price_on_purchase": True,
#             },
#         },
#         expected_output={
#             "status_code": 200,
#             # ⭐ Can't template the response user_id since it's generated
#             # Just check for successful creation
#         },
#     ),
#     ConfigDrivenTest(
#         name="test_get_user_profile_success",
#         description="Test getting user profile with valid authentication",
#         prerequisites=Prerequisites(
#             requires_user=True, requires_auth=True, user_type="regular"
#         ),
#         endpoint=Endpoint(method="POST", path="/user_profile"),
#         input_data={
#             "message": "Get user profile",
#             "request_info": {"request_id": "test-profile-001"},
#             "request_body": {"user_id": "${user.user_id}"},
#         },
#         expected_output={
#             "status_code": 200,
#             "response_body": {
#                 "message": "Request received.",
#                 "data": {
#                     "user_id": "${user.user_id}",
#                     "email": "${user.email}",
#                     "username": "${user.username}",
#                     "account_type": "admin",  # Backend sets this to admin
#                     "admin_id": None,
#                     "settings": {
#                         "show_price_on_purchase": False  # Default value
#                     },
#                     "prdcer": {
#                         "prdcer_ctlgs": {},  # Should be empty dict
#                         "draft_ctlgs": {},  # Should be empty dict
#                         "prdcer_lyrs": {},  # Should be empty dict
#                         "prdcer_dataset": {
#                             "dataset_plan": "",  # Should be empty string
#                             "auto_refresh": True,  # Should be true
#                         },
#                     },
#                 },
#             },
#         },
#     ),
# ]


# # Two one-liners - that's it!
# test_user_profile_endpoints = create_parametrized_test(USER_PROFILE_TESTS)

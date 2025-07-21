# # tests/integration/test_filter_based_on.py
# from .fixtures.test_utils import create_parametrized_test
# from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint
# from all_types.request_dtypes import ReqLLMEditBasedon

# # Filter based on test configurations
# FILTER_BASED_ON_TESTS = [
#     ConfigDrivenTest(
#         name="test_filter_based_on_cross_layer_radius_rating",
#         description="Test filtering features based on radius and rating criteria",
#         prerequisites=Prerequisites(
#             requires_user=True,
#             requires_auth=True,
#             requires_database_seed=True,
#             user_type="admin",
#             ggl_raw_seeds=["supermarket_cat_response", "pharmacy_cat_response"],
#             dataset_seeds=["supermarket_cat_response", "pharmacy_dataset"],
#             firebase_profile_seeds=["admin_profile_with_datasets"]
#         ),
#         endpoint=Endpoint(method="POST", path="/filter_based_on"),
#         input_data={
#             "message": "Filter features based on radius and rating",
#             "request_info": {"request_id": "test-filter-radius-rating-001"},
#             "request_body": ReqLLMEditBasedon(
#                 user_id="${user.user_id}",
#                 layers=["l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548","l116e3196-e721-4434-bad6-46291ba2aa0a"],
#                 property_threshold=4.0
#             ).model_dump()
#         },
#         expected_output_file="expected_responses/test_filter_based_on_radius_rating.json"
#     ),
# ]

# # Create parametrized tests
# test_filter_based_on = create_parametrized_test(FILTER_BASED_ON_TESTS)

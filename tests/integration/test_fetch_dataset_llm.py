# tests/integration/test_fetch_dataset_llm.py
from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint

# LLM Dataset fetch test configurations
FETCH_DATASET_LLM_TESTS = [
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_valid_query",
        description="Test LLM processing of valid query for supermarket search in Riyadh",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,  # LLM endpoint doesn't need database seeds
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process LLM query for supermarket search",
            "request_info": {"request_id": "test-llm-valid-001"},
            "request_body": {
                "query": "Find supermarkets in Riyadh"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="valid_supermarket_query"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_invalid_query_no_city",
        description="Test LLM processing of invalid query without approved city",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process LLM query without approved city",
            "request_info": {"request_id": "test-llm-invalid-001"},
            "request_body": {
                "query": "Find supermarkets"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="invalid_query_no_city"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_invalid_query_multiple_cities",
        description="Test LLM processing of invalid query with multiple cities",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process LLM query with multiple cities",
            "request_info": {"request_id": "test-llm-invalid-002"},
            "request_body": {
                "query": "Find restaurants in Riyadh and Jeddah"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="invalid_query_multiple_cities"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_complex_boolean_query",
        description="Test LLM processing of complex query with boolean operators",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process complex LLM query with boolean operators",
            "request_info": {"request_id": "test-llm-complex-001"},
            "request_body": {
                "query": "Find restaurants or cafes in Riyadh"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="complex_boolean_query"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_invalid_category",
        description="Test LLM processing of query with unapproved category",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process LLM query with invalid category",
            "request_info": {"request_id": "test-llm-invalid-003"},
            "request_body": {
                "query": "Find alien spaceship landing sites in Riyadh"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="invalid_category_query"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_non_location_query",
        description="Test LLM processing of non-location based query",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process non-location LLM query",
            "request_info": {"request_id": "test-llm-non-location-001"},
            "request_body": {
                "query": "What is the weather like in Riyadh?"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="non_location_query"
    ),
    ConfigDrivenTest(
        name="test_fetch_dataset_llm_conversational_query",
        description="Test LLM processing of conversational sentence to extract restaurant search in Jeddah",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=False,
        ),
        endpoint=Endpoint(method="POST", path="/process_llm_query"),
        input_data={
            "message": "Process conversational LLM query to extract location and business type",
            "request_info": {"request_id": "test-llm-conversational-001"},
            "request_body": {
                "query": "I have an idea to open a fancy restaurant with my sister with my sister and where do you think I should open it in the city of Jeddah where people love dogs"
            }
        },
        expected_output_file="test_fetch_dataset_llm.json",
        expected_output_key="conversational_restaurant_query"
    )

]


# Create the parametrized test function
test_fetch_dataset_llm_endpoints = create_parametrized_test(FETCH_DATASET_LLM_TESTS)

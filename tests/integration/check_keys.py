import json
import sys

try:
    with open('test_fetch_dataset_llm.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Keys found:")
    for key in data.keys():
        print(f"  {key}")
        
    # Based on expected_output_key values from the test file
    expected_keys = [
        "valid_supermarket_query",
        "invalid_query_no_city", 
        "invalid_query_multiple_cities",
        "complex_boolean_query",
        "invalid_category_query", 
        "non_location_query",
        "conversational_restaurant_query"
    ]
    
    print("\nChecking expected keys:")
    for key in expected_keys:
        if key in data:
            print(f"  ✅ {key}")
        else:
            print(f"  ❌ {key} (MISSING)")
            
except Exception as e:
    print(f"Error: {e}")

"""
Test script for fetch_dataset_llm functionality.
Tests various query scenarios and validates LLM responses.
Run this to verify the LLM processing is working correctly.
"""

import asyncio
import time
from fetch_dataset_llm import process_llm_query, extract_countries_and_cities
from all_types.request_dtypes import ReqLLMFetchDataset
from data_fetcher import fetch_country_city_data, poi_categories
from config_factory import CONF

# Global cache for dependencies
_cached_data = None

async def load_dependencies_once():
    """Load and cache the dependencies once"""
    global _cached_data
    if _cached_data is None:
        print("Loading dependencies for the first time...")
        start = time.time()
        
        country_city_data = await fetch_country_city_data()
        approved_countries, approved_cities = extract_countries_and_cities(country_city_data)
        category_data = await poi_categories()
        
        _cached_data = {
            'countries': approved_countries,
            'cities': approved_cities,
            'categories': category_data
        }
        
        load_time = time.time() - start
        print(f"Dependencies loaded in {load_time:.2f} seconds")
        print(f"Cities count: {len(approved_cities)}")
        print(f"Categories count: {len(category_data)}")
    
    return _cached_data

async def test_single_query(query_text, description):
    """Test a single query with detailed timing"""
    print(f"\n--- {description} ---")
    
    # Time the LLM call specifically
    req = ReqLLMFetchDataset(query=query_text)
    
    start_time = time.time()
    try:
        result = await process_llm_query(req)
        total_time = time.time() - start_time
        
        print(f"Query: '{req.query}'")
        print(f"Total processing time: {total_time:.2f} seconds")
        print(f"is_valid: '{result.is_valid}'")
        print(f"reason: '{result.reason}'")
        
        # Check if reason field is meaningful
        if not result.reason or len(result.reason.strip()) == 0:
            print("⚠️  WARNING: Empty or no reason provided!")
        
        # Check if is_valid is properly set
        if result.is_valid not in ["Valid", "Invalid"]:
            print(f"⚠️  WARNING: is_valid should be 'Valid' or 'Invalid', got: '{result.is_valid}'")
            
        print(f"body: {result.body is not None}")
        print(f"cost: {result.cost}")
        
        return result
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ Error after {total_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("=== LLM Functionality Test ===")
    print(f"Using Gemini API Key: {CONF.gemini_api_key[:10]}...")
    
    # Load dependencies once
    start_total = time.time()
    await load_dependencies_once()
    
    # Test various query scenarios
    test_cases = [
        ("help", "Ambiguous query test"),
        ("Find restaurants in InvalidCity", "Invalid city test"),  
        ("Find restaurants in Riyadh", "Valid query test"),
        ("Find cafes in Dubai", "Another valid query"),
        ("Find hotels and restaurants in Jeddah", "Complex boolean query"),
    ]
    
    results = []
    for query, desc in test_cases:
        result = await test_single_query(query, desc)
        results.append((query, result))
    
    total_time = time.time() - start_total
    print(f"\n=== Summary ===")
    print(f"Total script time: {total_time:.2f} seconds")
    
    # Analyze results
    for query, result in results:
        if result:
            status = "✅ Valid" if result.is_valid == "Valid" else "❌ Invalid" if result.is_valid == "Invalid" else "⚠️  Unknown"
            print(f"'{query}' → {status}")
        else:
            print(f"'{query}' → 💥 Error")

if __name__ == "__main__":
    asyncio.run(main())

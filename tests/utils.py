import aiohttp
import logging
from typing import List, Dict, Any, Tuple, Optional
import json
from all_types.request_dtypes import ReqStreeViewCheck
import hashlib
import os
from backend_common.database import Database
from sql_object import SqlObject
from logging_wrapper import apply_decorator_to_module


logger = logging.getLogger(__name__)


async def _get_test_data_for_get_call(ggl_api_url: str, headers: dict) -> dict:
    """Get test data for GET API calls (place details)"""
    logger.info(f"🔍 Looking for test data for GET call: {ggl_api_url}")
    
    # Extract place_id from URL for place details calls
    if "/places/" in ggl_api_url:
        place_id = ggl_api_url.split("/places/")[-1].split("?")[0]
        filename = f"test_place_details_{place_id}"
        logger.info(f"📋 Generated filename for place details: {filename}")
    else:
        # Generate filename based on URL hash for other GET calls
        url_hash = hashlib.md5(ggl_api_url.encode()).hexdigest()[:12]
        filename = f"test_get_call_{url_hash}"
        logger.info(f"📋 Generated filename for GET call: {filename}")

    try:
        # Query the correct test data table
        query = """
            SELECT filename, response_data 
            FROM schema_marketplace.google_maps_test_raw 
            WHERE filename = $1
        """
        logger.debug(f"🗄️ Executing query: {query} with filename: {filename}")
        
        result = await Database.fetchrow(query, filename)
        
        if result and result["response_data"]:
            logger.info(f"✅ Found test data for GET call: {filename}")
            logger.debug(f"📦 Raw response data: {result['response_data'][:200]}...")
            response_data = json.loads(result["response_data"])
            logger.info(f"🎯 Returning test data with keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'non-dict response'}")
            return response_data
        else:
            logger.warning(f"❌ No test data found for GET call: {filename}")
            logger.info("🔍 Available test files in database:")
            
            # List available files for debugging
            available_query = "SELECT filename FROM schema_marketplace.google_maps_test_raw LIMIT 10"
            available_results = await Database.fetch(available_query)
            for row in available_results:
                logger.info(f"  📁 {row['filename']}")
            
            return {}
            
    except Exception as e:
        logger.error(f"💥 Error loading test data for GET call: {e}")
        logger.exception("Full exception details:")
        return {}


async def _get_test_data_for_post_call(
    ggl_api_url: str, headers: dict, data: dict
) -> list:
    """Get test data for POST API calls (nearby search, text search)"""
    logger.info(f"🔍 Looking for test data for POST call: {ggl_api_url}")
    logger.debug(f"📦 Request data: {json.dumps(data, indent=2)}")
    
    # Check if we're in test mode
    is_test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
    logger.info(f"🧪 Test mode: {is_test_mode}")
    
    filename = None
    
    if "textQuery" in data:
        # Text search
        text_query = data.get("textQuery", "").replace(" ", "_")
        location = data.get("locationRestriction", {}).get("circle", {}).get("center", {})
        radius = data.get("locationRestriction", {}).get("circle", {}).get("radius", 1500)
        lat = location.get("latitude", 0)
        lng = location.get("longitude", 0)

        # Generate filename pattern that matches test seeding
        filename_pattern = f"test_text_search_{lat}_{lng}_{radius}_{text_query}"
        logger.info(f"📋 Text search filename pattern: {filename_pattern}")

    elif "includedTypes" in data or "excludedTypes" in data:
        # Category search - this should match your test data!
        included_types = data.get("includedTypes", [])
        excluded_types = data.get("excludedTypes", [])
        location = data.get("locationRestriction", {}).get("circle", {}).get("center", {})
        radius = data.get("locationRestriction", {}).get("circle", {}).get("radius", 1500)
        lat = location.get("latitude", 0)
        lng = location.get("longitude", 0)

        included_str = "_".join(sorted(included_types))
        excluded_str = "_".join(sorted(excluded_types))
        
        # Generate filename pattern that matches test seeding format
        filename_pattern = f"test_category_search_{lat}_{lng}_{radius}_inc_{included_str}_exc_{excluded_str}"
        logger.info(f"📋 Category search filename pattern: {filename_pattern}")
        logger.info(f"🎯 Looking for files matching: {filename_pattern}*")

    else:
        # Fallback: generate filename based on data hash
        data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
        filename_pattern = f"test_post_call_{data_hash}"
        logger.info(f"📋 Fallback filename pattern: {filename_pattern}")

    try:
        # First, try to find exact match
        if filename_pattern:
            query = """
                SELECT filename, response_data 
                FROM schema_marketplace.google_maps_test_raw 
                WHERE filename = $1
            """
            logger.debug(f"🗄️ Trying exact match query: {query} with pattern: {filename_pattern}")
            result = await Database.fetchrow(query, filename_pattern)
            
            if result:
                filename = result["filename"]
                logger.info(f"✅ Found exact match: {filename}")
            else:
                # Try pattern matching for test files with test_run_id
                pattern_query = """
                    SELECT filename, response_data 
                    FROM schema_marketplace.google_maps_test_raw 
                    WHERE filename LIKE $1
                    ORDER BY filename DESC
                    LIMIT 1
                """
                like_pattern = f"{filename_pattern}%"
                logger.debug(f"🗄️ Trying pattern match query: {pattern_query} with pattern: {like_pattern}")
                result = await Database.fetchrow(pattern_query, like_pattern)
                
                if result:
                    filename = result["filename"]
                    logger.info(f"✅ Found pattern match: {filename}")

        if result and result["response_data"]:
            logger.info(f"✅ Found test data for POST call: {filename}")
            logger.debug(f"📦 Raw response data: {result['response_data'][:200]}...")
            
            response_data = json.loads(result["response_data"])
            logger.info(f"🎯 Parsed response data type: {type(response_data)}")
            
            if isinstance(response_data, dict):
                logger.info(f"📊 Response data keys: {list(response_data.keys())}")
                
                # Return the places array for consistency with Google API response
                places = response_data.get("places", [])
                logger.info(f"🏢 Found {len(places)} places in test data")
                
                # Log first place for debugging
                if places:
                    first_place = places[0]
                    logger.debug(f"🏪 First place: {json.dumps(first_place, indent=2)[:300]}...")
                
                return places
            else:
                logger.warning(f"⚠️ Expected dict response, got {type(response_data)}")
                return response_data if isinstance(response_data, list) else []
        else:
            logger.warning(f"❌ No test data found for POST call pattern: {filename_pattern}")
            
            # List available files for debugging
            logger.info("🔍 Available test files in database:")
            available_query = "SELECT filename FROM schema_marketplace.google_maps_test_raw ORDER BY filename"
            available_results = await Database.fetch(available_query)
            
            for row in available_results:
                logger.info(f"  📁 {row['filename']}")
                
            return []
            
    except Exception as e:
        logger.error(f"💥 Error loading test data for POST call: {e}")
        logger.exception("Full exception details:")
        return []


async def _get_test_data_for_street_view(req: ReqStreeViewCheck) -> dict:
    """Get test data for Street View API calls"""
    logger.info(f"🔍 Looking for Street View test data for coordinates: {req.lat}, {req.lng}")
    
    # Generate filename based on coordinates
    filename = f"test_street_view_{req.lat}_{req.lng}".replace(".", "_")
    logger.info(f"📋 Street View filename: {filename}")

    try:
        query = """
            SELECT filename, response_data 
            FROM schema_marketplace.google_maps_test_raw 
            WHERE filename = $1
        """
        logger.debug(f"🗄️ Executing Street View query: {query} with filename: {filename}")
        
        result = await Database.fetchrow(query, filename)
        
        if result and result["response_data"]:
            logger.info(f"✅ Found test data for Street View: {filename}")
            response_data = json.loads(result["response_data"])
            logger.info(f"🎯 Street View response: {response_data}")
            return response_data
        else:
            logger.warning(f"❌ No test data found for Street View: {filename}")
            logger.info("🔍 Available Street View test files:")
            
            # List available street view files
            available_query = """
                SELECT filename FROM schema_marketplace.google_maps_test_raw 
                WHERE filename LIKE 'test_street_view%'
            """
            available_results = await Database.fetch(available_query)
            for row in available_results:
                logger.info(f"  📁 {row['filename']}")
            
            # Return default response indicating street view is available
            default_response = {"has_street_view": True}
            logger.info(f"🎯 Returning default Street View response: {default_response}")
            return default_response
            
    except Exception as e:
        logger.error(f"💥 Error loading test data for Street View: {e}")
        logger.exception("Full exception details:")
        return {"has_street_view": False}


# Apply the decorator to all functions in this module
apply_decorator_to_module(logger)(__name__)
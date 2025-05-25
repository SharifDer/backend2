# tests/integration/fixtures/test_generator.py
import pytest
import httpx
import logging
import asyncio
import json
import re
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .user_fixtures import UserSeeder, UserData
from .auth_fixtures import AuthHelper
from .cleanup_fixtures import CleanupManager
from .database_fixtures import DatabaseSeeder, DatabaseCleanupManager

logger = logging.getLogger(__name__)

@dataclass
class Prerequisites:
    """Defines what needs to be set up before a test"""
    requires_user: bool = False
    requires_auth: bool = False
    requires_database_seed: bool = False
    user_type: str = "regular"  # "regular", "admin", "custom"
    ggl_raw_seeds: List[str] = None  # ["supermarket", "coffee_shop_search"]
    dataset_seeds: List[str] = None  # ["supermarket_dataset", "coffee_dataset"]
    real_estate_seeds: List[str] = None  # ["residential_properties", "commercial_properties"]
    custom_user_config: Optional[Dict[str, Any]] = None

@dataclass
class Endpoint:
    """Defines the API endpoint to test"""
    method: str  # "GET", "POST", "PUT", "DELETE"
    path: str    # "/user_profile"
    headers: Optional[Dict[str, str]] = None

# tests/integration/fixtures/test_generator.py - Update the ConfigDrivenTest class
@dataclass
class ConfigDrivenTest:
    """Complete test configuration"""
    name: str
    description: str
    prerequisites: Prerequisites
    endpoint: Endpoint
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    pydantic_model: Optional[str] = None  # Optional Pydantic model class name
    timeout: int = 30  # Request timeout in seconds
    print_response_on_failure: bool = True  # ✅ New field for debugging

class RuntimeContext:
    """Holds runtime test data"""
    def __init__(self):
        self.user_data: Optional[UserData] = None
        self.auth_headers: Optional[Dict[str, str]] = None
        self.variables: Dict[str, Any] = {}
        self.database_vars: Dict[str, Any] = {}

class ConfigTestGenerator:
    """Generates and executes tests from configuration"""
    
    def __init__(self, 
                 http_client: httpx.Client,
                 user_seeder: UserSeeder,
                 auth_helper: AuthHelper,
                 cleanup_manager: CleanupManager,
                 database_seeder: DatabaseSeeder = None,
                 database_cleanup_manager: DatabaseCleanupManager = None):
        self.http_client = http_client
        self.user_seeder = user_seeder
        self.auth_helper = auth_helper
        self.cleanup_manager = cleanup_manager
        self.database_seeder = database_seeder
        self.database_cleanup_manager = database_cleanup_manager
    
    def setup_prerequisites(self, config: ConfigDrivenTest) -> RuntimeContext:
        """Set up prerequisites for a test"""
        context = RuntimeContext()
        
        # ======================
        # 1. USER SEEDING
        # ======================
        if config.prerequisites.requires_user:
            logger.info(f"🔧 Setting up user for test: {config.name}")
            
            # Create user based on type
            if config.prerequisites.user_type == "admin":
                user_data = self.user_seeder.seed_admin_user()
            elif config.prerequisites.user_type == "regular":
                user_data = self.user_seeder.seed_regular_user()
            elif config.prerequisites.user_type == "custom":
                # Use custom user configuration
                custom_config = config.prerequisites.custom_user_config or {}
                user_data = self.user_seeder.create_user(
                    email_prefix=custom_config.get("email_prefix", "custom_user"),
                    password=custom_config.get("password", "CustomPass123!"),
                    username_prefix=custom_config.get("username_prefix", "Custom User"),
                    account_type=custom_config.get("account_type", "individual")
                )
            else:
                # Default to regular user
                user_data = self.user_seeder.seed_regular_user()
            
            context.user_data = user_data
            self.cleanup_manager.register_user_for_cleanup(user_data)
            
            # Set up variables for substitution
            context.variables.update({
                "user.user_id": user_data.user_id,
                "user.email": user_data.email,
                "user.username": user_data.username,
                "user.account_type": user_data.account_type,
                "user.password": user_data.password
            })
            
            logger.info(f"✅ Seeded user for test: {user_data.user_id} ({user_data.email})")
        
        # ======================
        # 2. AUTHENTICATION
        # ======================
        if config.prerequisites.requires_auth and context.user_data:
            logger.info(f"🔐 Setting up authentication for test: {config.name}")
            
            auth_headers = self.auth_helper.get_auth_headers(context.user_data)
            context.auth_headers = auth_headers
            
            logger.info(f"✅ Authentication headers prepared for user: {context.user_data.user_id}")
        
        # ======================
        # 3. DATABASE SEEDING
        # ======================
        if config.prerequisites.requires_database_seed and self.database_seeder:
            logger.info(f"🗃️ Setting up database seeding for test: {config.name}")
            
            # Seed Google Maps raw data if specified
            if config.prerequisites.ggl_raw_seeds:
                logger.info(f"🌱 Seeding Google Maps raw data: {config.prerequisites.ggl_raw_seeds}")
                google_maps_vars = self.database_seeder.seed_db_ggl_maps_data(config.prerequisites.ggl_raw_seeds)
                context.variables.update({f"db.{k}": v for k, v in google_maps_vars.items()})
                context.database_vars.update(google_maps_vars)
                logger.info(f"✅ Google Maps data seeded with variables: {list(google_maps_vars.keys())}")
            
            # Seed transformed datasets if specified and user exists
            if config.prerequisites.dataset_seeds and context.user_data:
                logger.info(f"🌱 Seeding transformed datasets: {config.prerequisites.dataset_seeds}")
                dataset_vars = self.database_seeder.seed_transformed_datasets(context.user_data, config.prerequisites.dataset_seeds)
                context.variables.update({f"db.{k}": v for k, v in dataset_vars.items()})
                context.database_vars.update(dataset_vars)
                logger.info(f"✅ Transformed datasets seeded with variables: {list(dataset_vars.keys())}")
            
            # Seed real estate data if specified
            if config.prerequisites.real_estate_seeds:
                logger.info(f"🌱 Seeding real estate data: {config.prerequisites.real_estate_seeds}")
                real_estate_vars = self.database_seeder.seed_real_estate_data(config.prerequisites.real_estate_seeds)
                context.variables.update({f"db.{k}": v for k, v in real_estate_vars.items()})
                context.database_vars.update(real_estate_vars)
                logger.info(f"✅ Real estate data seeded with variables: {list(real_estate_vars.keys())}")
            
            # Register tables for cleanup
            if self.database_cleanup_manager:
                for table in self.database_seeder.created_tables:
                    self.database_cleanup_manager.register_table_for_cleanup(table)
                    logger.info(f"📝 Registered table for cleanup: {table}")
            
            # Log all seeded data types
            seeded_types = []
            if config.prerequisites.ggl_raw_seeds:
                seeded_types.append("google_maps_raw")
            if config.prerequisites.dataset_seeds:
                seeded_types.append("transformed_datasets")
            if config.prerequisites.real_estate_seeds:
                seeded_types.append("real_estate_data")
            
            logger.info(f"✅ Database seeding completed for types: {seeded_types}")
        
        # ======================
        # 4. FINAL SETUP
        # ======================
        logger.info(f"🎯 Prerequisites setup complete for test: {config.name}")
        logger.info(f"📊 Available variables: {list(context.variables.keys())}")
        
        return context
    
    def substitute_variables(self, data: Any, context: RuntimeContext) -> Any:
        """Replace ${variable} placeholders with actual values"""
        if isinstance(data, dict):
            return {k: self.substitute_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.substitute_variables(item, context) for item in data]
        elif isinstance(data, str):
            # Replace ${variable} patterns
            pattern = r'\$\{([^}]+)\}'
            def replace_var(match):
                var_name = match.group(1)
                if var_name in context.variables:
                    replacement = str(context.variables[var_name])
                    logger.debug(f"🔄 Substituting ${{{var_name}}} -> {replacement}")
                    return replacement
                else:
                    logger.warning(f"⚠️ Variable ${{{var_name}}} not found in context")
                    return match.group(0)  # Return original if not found
            return re.sub(pattern, replace_var, data)
        else:
            return data
    
    def execute_test(self, config: ConfigDrivenTest) -> bool:
        """Execute a single test based on configuration"""
        logger.info(f"🧪 Executing test: {config.name}")
        
        try:
            # ======================
            # 1. SEEDING - Set up prerequisites
            # ======================
            logger.info("🌱 Setting up prerequisites...")
            context = self.setup_prerequisites(config)
            
            # Small delay after seeding to let any background processes complete
            if config.prerequisites.requires_database_seed or config.prerequisites.requires_user:
                logger.info("⏳ Waiting for seeding to stabilize...")
                time.sleep(2)
            
            # ======================
            # 2. TESTING - Prepare request
            # ======================
            logger.info("🔧 Preparing request...")
            input_data = self.substitute_variables(config.input_data, context)
            headers = config.endpoint.headers or {}
            
            # Add auth headers if needed
            if context.auth_headers:
                headers.update(context.auth_headers)
                logger.info("🔐 Added authentication headers to request")
            
            # Make the request
            method = config.endpoint.method.lower()
            url = config.endpoint.path
            
            logger.info(f"🌐 Making {method.upper()} request to {url}")
            logger.debug(f"📋 Request headers: {headers}")
            logger.debug(f"📦 Request data: {json.dumps(input_data, indent=2)}")
            
            start_time = time.time()
            
            if method == "get":
                response = self.http_client.get(
                    url, 
                    headers=headers, 
                    params=input_data, 
                    timeout=config.timeout
                )
            elif method == "post":
                response = self.http_client.post(
                    url, 
                    headers=headers, 
                    json=input_data, 
                    timeout=config.timeout
                )
            elif method == "put":
                response = self.http_client.put(
                    url, 
                    headers=headers, 
                    json=input_data, 
                    timeout=config.timeout
                )
            elif method == "delete":
                response = self.http_client.delete(
                    url, 
                    headers=headers, 
                    json=input_data, 
                    timeout=config.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            request_time = time.time() - start_time
            logger.info(f"⏱️ Request completed in {request_time:.2f}s")
            

            # ======================
            # 3. VALIDATION - Check results
            # ======================
            logger.info("✅ Validating response...")
            expected = config.expected_output
            
            # Check status code
            expected_status = expected.get("status_code", 200)
            actual_status = response.status_code
            
            logger.info(f"📊 Response status: {actual_status}")
            
            if actual_status != expected_status:
                logger.error(f"❌ Status code mismatch: expected {expected_status}, got {actual_status}")
                if config.print_response_on_failure:
                    logger.error(f"📄 Full response body: {response.text}")
                else:
                    logger.error(f"📄 Response body: {response.text}")
                return False
            
            # Check response body if expected
            if "response_body" in expected:
                try:
                    actual_body = response.json()
                    if config.print_response_on_failure:
                        logger.info(f"📦 Full actual response body: {json.dumps(actual_body, indent=2)}")
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to parse response as JSON: {response.text}")
                    return False
                
                expected_body = self.substitute_variables(expected["response_body"], context)
                if config.print_response_on_failure:
                    logger.info(f"🎯 Full expected body: {json.dumps(expected_body, indent=2)}")
                
                if not self.compare_json_objects(actual_body, expected_body):
                    logger.error(f"❌ Response body validation failed")
                    if config.print_response_on_failure:
                        logger.error("=" * 80)
                        logger.error("🔍 DETAILED COMPARISON:")
                        logger.error(f"📦 ACTUAL RESPONSE:")
                        logger.error(json.dumps(actual_body, indent=2))
                        logger.error(f"🎯 EXPECTED RESPONSE:")
                        logger.error(json.dumps(expected_body, indent=2))
                        logger.error("=" * 80)
                    return False
            
            logger.info(f"✅ Test passed: {config.name}")
            
            # Delay between tests for cache updates and system stabilization
            time.sleep(1)
            return True
            
        except httpx.TimeoutException:
            logger.error(f"❌ Test failed due to timeout: {config.name}")
            return False
        except httpx.RequestError as e:
            logger.error(f"❌ Test failed due to request error: {config.name} - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {config.name} - {e}")
            logger.exception("Full exception details:")
            return False
    
    def compare_json_objects(self, actual: Any, expected: Any, path: str = "root") -> bool:
        """
        Deep compare JSON objects with flexible field matching and special validators
        
        Args:
            actual: The actual response data
            expected: The expected response data (can contain special validators)
            path: Current path in the object tree (for error reporting)
        
        Returns:
            bool: True if objects match according to validation rules
        """
        
        # If expected is None, skip validation
        if expected is None:
            logger.debug(f"🔄 Skipping validation at {path} (expected is None)")
            return True
        
        # ======================
        # SPECIAL STRING VALIDATORS
        # ======================
        if isinstance(expected, str):
            # Special validator: non_empty_list
            if expected == "non_empty_list":
                is_valid = isinstance(actual, list) and len(actual) > 0
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected non-empty list, got {type(actual)} with length {len(actual) if isinstance(actual, list) else 'N/A'}")
                else:
                    logger.debug(f"✅ non_empty_list validation passed at {path}")
                return is_valid
            
            # Special validator: non_empty_dict
            elif expected == "non_empty_dict":
                is_valid = isinstance(actual, dict) and len(actual) > 0
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected non-empty dict, got {type(actual)} with length {len(actual) if isinstance(actual, dict) else 'N/A'}")
                else:
                    logger.debug(f"✅ non_empty_dict validation passed at {path}")
                return is_valid
            
            # Special validator: exists
            elif expected == "exists":
                is_valid = actual is not None
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected value to exist, got None")
                else:
                    logger.debug(f"✅ exists validation passed at {path}")
                return is_valid
            
            # Special validator: not_exists
            elif expected == "not_exists":
                is_valid = actual is None
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected None, got {actual}")
                else:
                    logger.debug(f"✅ not_exists validation passed at {path}")
                return is_valid
            
            # Special validator: contains:something
            elif expected.startswith("contains:"):
                search_term = expected.replace("contains:", "", 1)
                is_valid = isinstance(actual, str) and search_term in actual
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected string containing '{search_term}', got '{actual}'")
                else:
                    logger.debug(f"✅ contains validation passed at {path}: '{search_term}' found in '{actual}'")
                return is_valid
            
            # Special validator: not_contains:something
            elif expected.startswith("not_contains:"):
                search_term = expected.replace("not_contains:", "", 1)
                is_valid = isinstance(actual, str) and search_term not in actual
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected string NOT containing '{search_term}', got '{actual}'")
                else:
                    logger.debug(f"✅ not_contains validation passed at {path}: '{search_term}' not found in '{actual}'")
                return is_valid
            
            # Special validator: starts_with:something
            elif expected.startswith("starts_with:"):
                prefix = expected.replace("starts_with:", "", 1)
                is_valid = isinstance(actual, str) and actual.startswith(prefix)
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected string starting with '{prefix}', got '{actual}'")
                else:
                    logger.debug(f"✅ starts_with validation passed at {path}")
                return is_valid
            
            # Special validator: ends_with:something
            elif expected.startswith("ends_with:"):
                suffix = expected.replace("ends_with:", "", 1)
                is_valid = isinstance(actual, str) and actual.endswith(suffix)
                if not is_valid:
                    logger.error(f"❌ Validation failed at {path}: expected string ending with '{suffix}', got '{actual}'")
                else:
                    logger.debug(f"✅ ends_with validation passed at {path}")
                return is_valid
            
            # Special validator: type:int, type:str, etc.
            elif expected.startswith("type:"):
                expected_type = expected.replace("type:", "", 1)
                type_mapping = {
                    "str": str, "string": str,
                    "int": int, "integer": int,
                    "float": float,
                    "bool": bool, "boolean": bool,
                    "list": list,
                    "dict": dict,
                    "none": type(None)
                }
                
                if expected_type not in type_mapping:
                    logger.error(f"❌ Unknown type validator: {expected_type}")
                    return False
                
                expected_python_type = type_mapping[expected_type]
                is_valid = isinstance(actual, expected_python_type)
                if not is_valid:
                    logger.error(f"❌ Type validation failed at {path}: expected {expected_type}, got {type(actual).__name__}")
                else:
                    logger.debug(f"✅ type validation passed at {path}: {expected_type}")
                return is_valid
            
            # Special validator: regex:pattern
            elif expected.startswith("regex:"):
                pattern = expected.replace("regex:", "", 1)
                try:
                    is_valid = isinstance(actual, str) and re.match(pattern, actual) is not None
                    if not is_valid:
                        logger.error(f"❌ Regex validation failed at {path}: pattern '{pattern}' did not match '{actual}'")
                    else:
                        logger.debug(f"✅ regex validation passed at {path}")
                    return is_valid
                except re.error as e:
                    logger.error(f"❌ Invalid regex pattern at {path}: {pattern} - {e}")
                    return False
            
            # Special validator: length:number
            elif expected.startswith("length:"):
                try:
                    expected_length = int(expected.replace("length:", "", 1))
                    if hasattr(actual, '__len__'):
                        actual_length = len(actual)
                        is_valid = actual_length == expected_length
                        if not is_valid:
                            logger.error(f"❌ Length validation failed at {path}: expected length {expected_length}, got {actual_length}")
                        else:
                            logger.debug(f"✅ length validation passed at {path}")
                        return is_valid
                    else:
                        logger.error(f"❌ Length validation failed at {path}: object has no length")
                        return False
                except ValueError:
                    logger.error(f"❌ Invalid length validator: {expected}")
                    return False
            
            # Special validator: min_length:number
            elif expected.startswith("min_length:"):
                try:
                    min_length = int(expected.replace("min_length:", "", 1))
                    if hasattr(actual, '__len__'):
                        actual_length = len(actual)
                        is_valid = actual_length >= min_length
                        if not is_valid:
                            logger.error(f"❌ Min length validation failed at {path}: expected min length {min_length}, got {actual_length}")
                        else:
                            logger.debug(f"✅ min_length validation passed at {path}")
                        return is_valid
                    else:
                        logger.error(f"❌ Min length validation failed at {path}: object has no length")
                        return False
                except ValueError:
                    logger.error(f"❌ Invalid min_length validator: {expected}")
                    return False
            
            # Special validator: max_length:number
            elif expected.startswith("max_length:"):
                try:
                    max_length = int(expected.replace("max_length:", "", 1))
                    if hasattr(actual, '__len__'):
                        actual_length = len(actual)
                        is_valid = actual_length <= max_length
                        if not is_valid:
                            logger.error(f"❌ Max length validation failed at {path}: expected max length {max_length}, got {actual_length}")
                        else:
                            logger.debug(f"✅ max_length validation passed at {path}")
                        return is_valid
                    else:
                        logger.error(f"❌ Max length validation failed at {path}: object has no length")
                        return False
                except ValueError:
                    logger.error(f"❌ Invalid max_length validator: {expected}")
                    return False
        
        # ======================
        # TYPE CHECKING
        # ======================
        if type(actual) is not type(expected):
            logger.error(f"❌ Type mismatch at {path}: expected {type(expected).__name__}, got {type(actual).__name__}")
            return False
        
        # ======================
        # DICTIONARY COMPARISON
        # ======================
        if isinstance(expected, dict):
            logger.debug(f"🔍 Comparing dict at {path} with {len(expected)} expected keys")
            
            # Check that all EXPECTED keys exist and match
            # Allow actual to have additional keys (partial matching)
            for key, expected_value in expected.items():
                current_path = f"{path}.{key}"
                
                if key not in actual:
                    logger.error(f"❌ Missing expected key '{key}' at {path}")
                    logger.error(f"   Available keys: {list(actual.keys())}")
                    return False
                
                if not self.compare_json_objects(actual[key], expected_value, current_path):
                    logger.error(f"❌ Value mismatch for key '{key}' at {current_path}")
                    return False
            
            logger.debug(f"✅ Dict comparison passed at {path}")
            return True
        
        # ======================
        # LIST COMPARISON
        # ======================
        elif isinstance(expected, list):
            logger.debug(f"🔍 Comparing list at {path} with {len(expected)} expected items")
            
            if len(actual) != len(expected):
                logger.error(f"❌ List length mismatch at {path}: expected {len(expected)}, got {len(actual)}")
                return False
            
            for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
                current_path = f"{path}[{i}]"
                if not self.compare_json_objects(actual_item, expected_item, current_path):
                    logger.error(f"❌ List item mismatch at {current_path}")
                    return False
            
            logger.debug(f"✅ List comparison passed at {path}")
            return True
        
        # ======================
        # PRIMITIVE VALUE COMPARISON
        # ======================
        else:
            is_valid = actual == expected
            if not is_valid:
                logger.error(f"❌ Value mismatch at {path}: expected {expected}, got {actual}")
            else:
                logger.debug(f"✅ Value comparison passed at {path}")
            return is_valid
    
    def validate_config(self, config: ConfigDrivenTest) -> bool:
        """Validate test configuration before execution"""
        errors = []
        
        # Validate required fields
        if not config.name:
            errors.append("Test name is required")
        
        if not config.endpoint.method:
            errors.append("HTTP method is required")
        
        if not config.endpoint.path:
            errors.append("Endpoint path is required")
        
        if config.endpoint.method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            errors.append(f"Unsupported HTTP method: {config.endpoint.method}")
        
        # Validate prerequisites
        if config.prerequisites.requires_auth and not config.prerequisites.requires_user:
            errors.append("Authentication requires a user to be created")
        
        if config.prerequisites.requires_database_seed and not self.database_seeder:
            errors.append("Database seeding required but no database seeder provided")
        
        # Check if database seeding is requested but no seed lists are provided
        if config.prerequisites.requires_database_seed:
            has_seeds = any([
                config.prerequisites.ggl_raw_seeds,
                config.prerequisites.dataset_seeds,
                config.prerequisites.real_estate_seeds
            ])
            if not has_seeds:
                errors.append("Database seeding requested but no seed lists provided")
        
        if errors:
            logger.error(f"❌ Configuration validation failed for {config.name}:")
            for error in errors:
                logger.error(f"   - {error}")
            return False
        
        return True
    
    def get_available_validators(self) -> List[str]:
        """Get list of available special validators"""
        return [
            "non_empty_list",
            "non_empty_dict", 
            "exists",
            "not_exists",
            "contains:search_term",
            "not_contains:search_term",
            "starts_with:prefix",
            "ends_with:suffix",
            "type:str|int|float|bool|list|dict|none",
            "regex:pattern",
            "length:number",
            "min_length:number",
            "max_length:number"
        ]
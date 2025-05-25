# tests/integration/fixtures/test_utils.py
import pytest
from .test_generator import ConfigTestGenerator

def execute_config_driven_test(test_config, http_client, user_seeder, auth_helper, cleanup_manager, database_seeder=None, database_cleanup_manager=None):
    """Reusable function to execute any config-driven test"""
    generator = ConfigTestGenerator(
        http_client, 
        user_seeder, 
        auth_helper, 
        cleanup_manager,
        database_seeder,  # ✅ Add database seeder
        database_cleanup_manager  # ✅ Add database cleanup
    )
    success = generator.execute_test(test_config)
    assert success, f"Configuration-driven test failed: {test_config.name}"

def create_parametrized_test(test_configs, pytest_marks=None):
    """Factory function to create a parametrized test function"""
    pytest_marks = pytest_marks or []
    
    # Apply marks to the test function
    @pytest.mark.parametrize("test_config", test_configs, ids=lambda config: config.name)
    def test_function(test_config, http_client, user_seeder, auth_helper, cleanup_manager, database_seeder, database_cleanup_manager):
        execute_config_driven_test(
            test_config, 
            http_client, 
            user_seeder, 
            auth_helper, 
            cleanup_manager,
            database_seeder,      # ✅ Pass database seeder
            database_cleanup_manager  # ✅ Pass database cleanup
        )
    
    # Apply additional marks
    for mark in pytest_marks:
        test_function = mark(test_function)
    
    return test_function
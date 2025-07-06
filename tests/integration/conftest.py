# tests/integration/conftest.py
import pytest
import httpx
import logging
import time
import os
from datetime import datetime
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import auth
from backend_common.auth import firebase_db
from .fixtures import (
    UserSeeder,
    AuthHelper,
    CleanupManager,
    DatabaseSeeder,
    DatabaseCleanupManager,
)

logger = logging.getLogger(__name__)

# Generate unique test identifiers for each test run
TEST_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


@pytest.fixture(scope="session")
def test_run_id():
    """Unique test run identifier"""
    return TEST_RUN_ID


@pytest.fixture(scope="session")
def api_base_url():
    """API base URL for tests - dynamically determined from environment"""
    # Check if a custom port was set by the test runner
    test_port = os.environ.get("TEST_SERVER_PORT", "8080")
    base_url = f"http://localhost:{test_port}/fastapi"
    logger.info(f"🌐 Using API base URL: {base_url}")
    return base_url


@pytest.fixture(scope="function")
def http_client(api_base_url):
    """HTTP client for API calls"""
    return httpx.Client(base_url=api_base_url, timeout=60.0)


@pytest.fixture(scope="function")
def user_seeder(http_client, test_run_id):
    """User seeder for creating test users"""
    return UserSeeder(http_client, test_run_id)


@pytest.fixture(scope="function")
def auth_helper(http_client):
    """Authentication helper for login operations"""
    return AuthHelper(http_client)


@pytest.fixture(scope="function")
def cleanup_manager():
    """Cleanup manager for test resources"""
    manager = CleanupManager()
    yield manager
    # Automatic cleanup at end of test
    manager.cleanup_all_registered()


# tests/integration/conftest.py - Add database fixtures
@pytest.fixture(scope="function")
def database_seeder(test_run_id):
    """Database seeder for creating test data"""
    
    return DatabaseSeeder(test_run_id)

@pytest.fixture(scope="function")
def database_cleanup_manager():
    """Database cleanup manager for test data"""
    
    manager = DatabaseCleanupManager()
    yield manager
    # Synchronous cleanup at end of test
    manager.cleanup_all_registered()


@pytest.fixture(scope="session", autouse=True)
def cleanup_existing_test_users():
    """Clean up any existing test users before and after test session"""
    _cleanup_test_users_by_pattern()
    yield
    _cleanup_test_users_by_pattern()


def _cleanup_test_users_by_pattern():
    """Clean up users with test email patterns"""
    try:
        page = auth.list_users()

        test_user_patterns = [
            "integration_user_",
            "login_test_user_",
            "update_test_user_",
            "multi_user_",
            "admin_user_",
            "regular_user_",
            "@test.com",
        ]

        users_to_delete = []
        for user in page.users:
            if user.email and any(
                pattern in user.email for pattern in test_user_patterns
            ):
                users_to_delete.append(user.uid)

        for user_id in users_to_delete:
            try:
                auth.delete_user(user_id)
                firebase_db.get_sync_client().collection(
                    "all_user_profiles"
                ).document(user_id).delete()
                firebase_db.get_sync_client().collection(
                    "firebase_stripe_mappings"
                ).document(user_id).delete()
            except Exception as e:
                logger.warning(
                    f"Error during pre-cleanup of user {user_id}: {e}"
                )

        if users_to_delete:
            logger.info(
                f"Pre-cleanup: Removed {len(users_to_delete)} test users"
            )

    except Exception as e:
        logger.warning(f"Error during test user cleanup: {e}")

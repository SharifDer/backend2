# tests/integration/fixtures/user_fixtures.py
import httpx
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UserData:
    """Container for user data"""
    user_id: str
    email: str
    password: str
    username: str
    account_type: str = "individual"
    
class UserSeeder:
    """Handles user creation and seeding for tests"""
    
    def __init__(self, http_client: httpx.Client, test_run_id: str):
        self.http_client = http_client
        self.test_run_id = test_run_id
        self.created_users: List[UserData] = []
    
    def create_user(self, 
                   email_prefix: str, 
                   password: str, 
                   username_prefix: str,
                   account_type: str = "individual") -> UserData:
        """Create a single user and return UserData"""
        
        email = f"{email_prefix}_{self.test_run_id}@test.com"
        username = f"{username_prefix} - {self.test_run_id}"
        
        req_data = {
            "message": "Create user profile",
            "request_info": {"request_id": f"test-create-{email}"},
            "request_body": {
                "email": email,
                "password": password,
                "username": username,
                "account_type": account_type,
                "admin_id": None,
                "show_price_on_purchase": False
            }
        }
        
        response = self.http_client.post("/create_user_profile", json=req_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data[0]["data"]["user_id"]
            
            user_data = UserData(
                user_id=user_id,
                email=email,
                password=password,
                username=username,
                account_type=account_type
            )
            
            self.created_users.append(user_data)
            logger.info(f"✅ Seeded user: {user_id} ({email})")
            
            # Small delay to let background tasks complete
            time.sleep(3)
            
            return user_data
        
        else:
            logger.error(f"❌ Failed to seed user {email}: {response.text}")
            raise Exception(f"Failed to seed user {email}: {response.text}")
    
    def create_multiple_users(self, count: int, base_prefix: str) -> List[UserData]:
        """Create multiple users with sequential naming"""
        users = []
        for i in range(count):
            user_data = self.create_user(
                email_prefix=f"{base_prefix}_{i}",
                password=f"Test{base_prefix.title()}{i}!",
                username_prefix=f"Test {base_prefix.title()} User {i}"
            )
            users.append(user_data)
            # Small delay between creations
            time.sleep(0.5)
        
        logger.info(f"✅ Seeded {count} {base_prefix} users")
        return users
    
    def seed_admin_user(self) -> UserData:
        """Seed a pre-configured admin user"""
        return self.create_user(
            email_prefix="admin_user",
            password="AdminPass123!",
            username_prefix="Admin Test User",
            account_type="admin"
        )
    
    def seed_regular_user(self) -> UserData:
        """Seed a pre-configured regular user"""
        return self.create_user(
            email_prefix="regular_user",
            password="RegularPass123!",
            username_prefix="Regular Test User"
        )
    
    def get_created_users(self) -> List[UserData]:
        """Get all users created by this seeder"""
        return self.created_users.copy()
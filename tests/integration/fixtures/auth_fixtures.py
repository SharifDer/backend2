# tests/integration/fixtures/auth_fixtures.py
import httpx
import logging
from typing import Optional, Dict, Any
from .user_fixtures import UserData

logger = logging.getLogger(__name__)

class AuthHelper:
    """Handles authentication operations for tests"""
    
    def __init__(self, http_client: httpx.Client):
        self.http_client = http_client
    
    # tests/integration/fixtures/auth_fixtures.py
    def get_auth_headers(self, user_data: UserData) -> Dict[str, str]:
        """
        Get authorization headers for a user
        In test mode, just return a simple token without trying to login
        """
        # In test mode, skip login entirely and just return a mock token
        mock_token = f"test_token_{user_data.user_id}"
        logger.info(f"Using test mode bypass token for {user_data.email}")
        return {"Authorization": f"Bearer {mock_token}"}

    def login_user(self, user_data: UserData) -> Optional[str]:
        """
        In test mode, skip login entirely since backend has auth bypass
        """
        logger.info(f"Skipping login in test mode for {user_data.email}")
        return f"test_token_{user_data.user_id}"

    def verify_user_profile_exists(self, user_data: UserData) -> bool:
        """Verify user profile exists in Firestore"""
        from backend_common.auth import firebase_db
        
        try:
            user_doc = firebase_db.get_sync_client().collection(
                "all_user_profiles"
            ).document(user_data.user_id).get()
            
            if user_doc.exists:
                doc_data = user_doc.to_dict()
                return (doc_data["email"] == user_data.email and 
                       doc_data["username"] == user_data.username)
            return False
        except Exception as e:
            logger.error(f"Error verifying user profile for {user_data.user_id}: {e}")
            return False
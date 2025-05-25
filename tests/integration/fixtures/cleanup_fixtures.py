# tests/integration/fixtures/cleanup_fixtures.py
import logging
import time
from typing import List, Set
from firebase_admin import auth
from backend_common.auth import firebase_db
from .user_fixtures import UserData

logger = logging.getLogger(__name__)

class CleanupManager:
    """Handles cleanup of test resources"""
    
    def __init__(self):
        self.cleanup_registry: Set[str] = set()
    
    def register_user_for_cleanup(self, user_data: UserData):
        """Register a user for cleanup"""
        self.cleanup_registry.add(user_data.user_id)
    
    def register_users_for_cleanup(self, users: List[UserData]):
        """Register multiple users for cleanup"""
        for user in users:
            self.register_user_for_cleanup(user)
    
    def cleanup_user(self, user_data: UserData):
        """Clean up a single user"""
        try:
            # Delete from Firebase Auth
            auth.delete_user(user_data.user_id)
            logger.info(f"🗑️ Deleted Firebase user: {user_data.user_id}")
            
            # Delete from Firestore
            firebase_db.get_sync_client().collection("all_user_profiles").document(user_data.user_id).delete()
            firebase_db.get_sync_client().collection("firebase_stripe_mappings").document(user_data.user_id).delete()
            
            # Remove from registry
            self.cleanup_registry.discard(user_data.user_id)
            
            # Small delay
            time.sleep(0.1)
            
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up user {user_data.user_id}: {e}")
    
    def cleanup_users(self, users: List[UserData]):
        """Clean up multiple users"""
        cleanup_count = 0
        for user in users:
            try:
                self.cleanup_user(user)
                cleanup_count += 1
                time.sleep(0.2)  # Delay between cleanups
            except Exception as e:
                logger.warning(f"Failed to cleanup user {user.user_id}: {e}")
        
        logger.info(f"🧹 Cleaned up {cleanup_count}/{len(users)} users")
    
    def cleanup_all_registered(self):
        """Clean up all registered users"""
        if not self.cleanup_registry:
            logger.info("No users registered for cleanup")
            return
        
        user_ids = list(self.cleanup_registry)
        cleanup_count = 0
        
        for user_id in user_ids:
            try:
                # Delete from Firebase Auth
                auth.delete_user(user_id)
                logger.info(f"🗑️ Deleted Firebase user: {user_id}")
                
                # Delete from Firestore
                firebase_db.get_sync_client().collection("all_user_profiles").document(user_id).delete()
                firebase_db.get_sync_client().collection("firebase_stripe_mappings").document(user_id).delete()
                
                cleanup_count += 1
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up registered user {user_id}: {e}")
        
        self.cleanup_registry.clear()
        logger.info(f"🧹 Cleaned up {cleanup_count}/{len(user_ids)} registered users")
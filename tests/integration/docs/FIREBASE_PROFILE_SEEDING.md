# Firebase Profile Seeding for Integration Tests

## Overview

The Firebase profile seeding functionality allows you to automatically create and manage Firestore user profile documents during integration tests. This is useful for testing endpoints that depend on user profile data being present in Firebase.

## How It Works

1. **User Profile Creation**: After seeding user data and database records, the system can now also seed Firebase user profiles
2. **Template-Based**: Uses JSON templates from `firebase_profiles.json` with variable substitution
3. **Automatic Cleanup**: Profiles are automatically deleted after tests complete
4. **Integration**: Works seamlessly with existing database seeding and user authentication

## Firebase Profile Templates

The system uses predefined profile templates in `tests/integration/db_seed_data/firebase_profiles.json`:

### Available Templates

- `admin_profile_basic`: Basic admin profile with empty datasets
- `admin_profile_with_datasets`: Admin profile with pre-populated dataset and layer data
- `member_profile_basic`: Basic member profile linked to an admin
- `admin_profile_with_real_estate`: Admin profile with real estate layer data

### Template Structure

```json
{
  "admin_profile_basic": {
    "user_id": "{user_id}",
    "email": "{email}",
    "username": "{username}",
    "account_type": "admin",
    "admin_id": null,
    "settings": {
      "show_price_on_purchase": true
    },
    "prdcer": {
      "prdcer_dataset": {},
      "prdcer_lyrs": {},
      "prdcer_ctlgs": {},
      "draft_ctlgs": {}
    }
  }
}
```

## Usage in Test Configuration

### 1. Enable Firebase Profile Seeding

Add `firebase_profile_seeds` to your test prerequisites:

```python
from tests.integration.fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint

test_config = ConfigDrivenTest(
    name="test_with_firebase_profiles",
    description="Test with Firebase profile seeding",
    
    prerequisites=Prerequisites(
        requires_user=True,
        requires_auth=True,
        requires_database_seed=True,
        user_type="admin",
        
        # Enable Firebase profile seeding
        firebase_profile_seeds=["admin_profile_with_datasets", "member_profile_basic"]
    ),
    
    endpoint=Endpoint(method="GET", path="/user_profile"),
    input_data={"user_id": "${user.user_id}"},
    expected_output={"status_code": 200}
)
```

### 2. Access Seeded Profile Data

The seeding process creates variables you can use in your tests:

```python
# Variables created for each profile:
# - {profile_name}_user_id
# - {profile_name}_email  
# - {profile_name}_username
# - {profile_name}_account_type

# Example usage in test input:
input_data = {
    "admin_user_id": "${firebase.admin_profile_with_datasets_user_id}",
    "member_user_id": "${firebase.member_profile_basic_user_id}"
}
```

## Sequence of Operations

When a test runs with Firebase profile seeding enabled:

1. **User Seeding**: Create test user accounts (if `requires_user=True`)
2. **Database Seeding**: Seed Google Maps, datasets, real estate data (if specified)
3. **Firebase Profile Seeding**: Create Firestore profile documents using templates
4. **Authentication**: Set up auth headers (if `requires_auth=True`)
5. **Test Execution**: Run the actual API test
6. **Cleanup**: Delete Firebase profiles and database records

## Implementation Details

### DatabaseSeeder.seed_firebase_profiles()

```python
def seed_firebase_profiles(
    self, 
    profile_configs: List[str], 
    user_data: UserData = None, 
    admin_user_data: UserData = None
) -> Dict[str, Any]:
    """
    Seed Firebase user profiles for testing
    
    Args:
        profile_configs: List of profile template names from firebase_profiles.json
        user_data: User data for substitution in profiles  
        admin_user_data: Admin user data for member profiles that need admin_id
        
    Returns:
        Dict with seeded profile information and variables
    """
```

### Firebase Client Setup

The seeder uses the same Firebase configuration as your main application:

```python
def _get_firebase_client(self):
    """Get Firebase Firestore client using service account"""
    from backend_common.common_config import CONF
    
    if os.path.exists(CONF.firebase_sp_path):
        self._firebase_client = firestore.Client.from_service_account_json(
            CONF.firebase_sp_path
        )
    else:
        raise Exception(f"Firebase service account file not found: {CONF.firebase_sp_path}")
```

### Automatic Cleanup

Profiles are automatically deleted when the test completes:

```python
def close_connection(self):
    """Close the database connection and clean up Firebase profiles"""
    if self.seeded_firebase_profiles and self._firebase_client:
        collection_ref = self._firebase_client.collection("all_user_profiles")
        for doc_id in self.seeded_firebase_profiles:
            collection_ref.document(doc_id).delete()
```

## Best Practices

### 1. Profile Template Selection

- Use `admin_profile_basic` for simple admin profile tests
- Use `admin_profile_with_datasets` when testing features that require existing datasets
- Use `member_profile_basic` for testing member account functionality
- Use `admin_profile_with_real_estate` for real estate related tests

### 2. Variable Substitution

Templates support these substitutions:
- `{user_id}`: From user seeding or auto-generated
- `{email}`: From user seeding or auto-generated  
- `{username}`: From user seeding or auto-generated
- `{admin_id}`: For member profiles, from admin user data
- `{test_run_id}`: Unique test run identifier

### 3. Combining with Database Seeding

Firebase profiles work best when combined with database seeding:

```python
prerequisites=Prerequisites(
    requires_user=True,
    requires_auth=True, 
    requires_database_seed=True,
    
    # Seed the data pipeline: raw -> transformed -> firebase profiles
    ggl_raw_seeds=["supermarket"],
    dataset_seeds=["supermarket_dataset"], 
    firebase_profile_seeds=["admin_profile_with_datasets"]
)
```

### 4. Error Handling

The seeding process includes comprehensive error handling and logging:
- Missing template files are logged as warnings
- Firebase connection errors are raised as exceptions
- Individual profile creation failures are logged and re-raised
- Cleanup failures are logged as warnings but don't fail the test

## Example Test Scenarios

### 1. Basic Profile Test

```python
# Test user profile retrieval with basic admin profile
prerequisites=Prerequisites(
    requires_user=True,
    requires_auth=True,
    requires_database_seed=True,
    firebase_profile_seeds=["admin_profile_basic"]
)
```

### 2. Dataset Integration Test

```python
# Test dataset functionality with pre-populated profile
prerequisites=Prerequisites(
    requires_user=True,
    requires_auth=True,
    requires_database_seed=True,
    ggl_raw_seeds=["supermarket"],
    dataset_seeds=["supermarket_dataset"],
    firebase_profile_seeds=["admin_profile_with_datasets"]
)
```

### 3. Multi-User Test

```python
# Test admin-member relationship
prerequisites=Prerequisites(
    requires_user=True,
    requires_auth=True,
    requires_database_seed=True,
    firebase_profile_seeds=["admin_profile_basic", "member_profile_basic"]
)
```

This Firebase profile seeding functionality integrates seamlessly with the existing test infrastructure and provides a comprehensive way to test features that depend on Firestore user profile data.

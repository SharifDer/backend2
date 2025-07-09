# Example usage of Firebase profile seeding in integration tests

# This example shows how to configure Firebase profile seeding
# Run this from the project root: python -m tests.integration.examples.firebase_profile_seeding_example

print("Firebase Profile Seeding Example")
print("=================================")
print()

print("1. Prerequisites Configuration:")
print("   - requires_user: True")
print("   - requires_auth: True") 
print("   - requires_database_seed: True")
print("   - firebase_profile_seeds: ['admin_profile_with_datasets', 'member_profile_basic']")
print()

print("2. Available Firebase Profile Templates:")
profiles = [
    "admin_profile_basic - Basic admin profile with empty datasets",
    "admin_profile_with_datasets - Admin profile with pre-populated dataset and layer data", 
    "member_profile_basic - Basic member profile linked to an admin",
    "admin_profile_with_real_estate - Admin profile with real estate layer data"
]

for profile in profiles:
    print(f"   - {profile}")
print()

print("3. Template Variables Available:")
variables = [
    "firebase.{profile_name}_user_id",
    "firebase.{profile_name}_email", 
    "firebase.{profile_name}_username",
    "firebase.{profile_name}_account_type"
]

for var in variables:
    print(f"   - ${{{var}}}")
print()

print("4. Seeding Process Order:")
steps = [
    "User seeding (create test user accounts)",
    "Database seeding (Google Maps raw data, transformed datasets, real estate)",
    "Firebase profile seeding (create Firestore profile documents)", 
    "Authentication setup (prepare auth headers)",
    "Test execution",
    "Automatic cleanup (delete profiles and database records)"
]

for i, step in enumerate(steps, 1):
    print(f"   {i}. {step}")
print()

print("5. Example Test Configuration Structure:")
print("""
ConfigDrivenTest(
    name="test_user_profile_with_datasets",
    prerequisites=Prerequisites(
        requires_user=True,
        requires_auth=True,
        requires_database_seed=True,
        user_type="admin",
        ggl_raw_seeds=["supermarket", "pharmacy"],
        dataset_seeds=["supermarket_dataset", "pharmacy_dataset"],
        firebase_profile_seeds=["admin_profile_with_datasets"]
    ),
    endpoint=Endpoint(method="GET", path="/user_profile"),
    input_data={"user_id": "${user.user_id}"},
    expected_output={
        "status_code": 200,
        "prdcer": {
            "prdcer_dataset": "non_empty_dict",
            "prdcer_lyrs": "non_empty_dict"
        }
    }
)
""")

print("✅ Firebase profile seeding is now available for integration tests!")
print("📖 See tests/integration/docs/FIREBASE_PROFILE_SEEDING.md for full documentation")

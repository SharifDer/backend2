# Filter Based On Endpoint - Integration Tests

This directory contains comprehensive integration tests for the `/filter_based_on` endpoint using our config-driven testing framework.

## 🎯 Quick Start

### 1. Validate Setup
```bash
cd tests/integration
python validate_filter_setup.py
```

### 2. Run Tests
```bash
python run_filter_tests.py
```

## 📁 File Structure

```
tests/integration/
├── test_filter_based_on.py           # Main test configurations
├── run_filter_tests.py               # Custom test runner
├── validate_filter_setup.py          # Setup validation script
├── expected_responses/
│   └── filter_based_on_responses.json # Expected API responses
├── db_seed_data/
│   ├── transformed_datasets.json      # Test datasets (updated)
│   ├── firebase_profiles.json        # User profiles (updated)
│   └── google_maps_raw.json          # Raw API responses
├── docs/
│   └── filter_based_on_tests.md      # Detailed documentation
└── fixtures/
    ├── test_generator.py              # Config-driven test framework
    ├── database_fixtures.py           # Database seeding (updated)
    └── ...                           # Other test fixtures
```

## 🧪 Test Scenarios

| Test | Purpose | Coverage | Property Filter |
|------|---------|----------|----------------|
| **radius_rating** | Radius + Rating filter | 2km from pharmacies | Rating > 4.0 |
| **drive_time_name** | Drive time + Name filter | 10min drive time | Specific names |
| **user_ratings_total** | Radius + User ratings | 1.5km radius | >50 ratings |
| **no_coverage** | Property only | None | Rating > 4.0 |
| **no_results** | Error handling | 1km radius | Rating > 5.0 (impossible) |

## 🔧 What Was Created/Updated

### New Files
- ✅ `test_filter_based_on.py` - Complete test suite with 5 scenarios
- ✅ `expected_responses/filter_based_on_responses.json` - Expected API responses
- ✅ `run_filter_tests.py` - Custom test runner with detailed logging
- ✅ `validate_filter_setup.py` - Setup validation script
- ✅ `docs/filter_based_on_tests.md` - Comprehensive documentation

### Updated Files
- ✅ `db_seed_data/transformed_datasets.json` - Added `pharmacy_dataset`
- ✅ `db_seed_data/firebase_profiles.json` - Added `admin_profile_with_cafe_restaurant`
- ✅ `fixtures/database_fixtures.py` - Enhanced layer ID extraction

## 🛠 Key Features

### Config-Driven Testing
- **Declarative**: Tests defined as configuration objects
- **Reusable**: Common test patterns abstracted into framework
- **Maintainable**: Easy to add new test scenarios

### Comprehensive Seeding
- **Google Maps Data**: Raw API responses for realistic testing
- **Transformed Datasets**: Processed data for layer operations
- **Firebase Profiles**: User profiles with layer configurations
- **Auto Layer ID Extraction**: Automatic mapping of layer IDs for tests

### Advanced Validation
- **Flexible Assertions**: `min_length`, `contains`, `type` validators
- **JSON Structure Validation**: Deep object comparison
- **Error Response Testing**: Proper error handling verification
- **Performance Monitoring**: Response time tracking

### Test Data Management
- **Unique Test Run IDs**: Prevents test interference
- **Automatic Cleanup**: Removes test data after completion
- **Database Isolation**: Each test run uses isolated data
- **Firebase Integration**: Real Firestore operations for authenticity

## 📊 Database Schema

The tests seed the following data:

### PostgreSQL Tables
```sql
-- Google Maps raw responses
schema_marketplace.google_maps_test_raw (
    filename TEXT PRIMARY KEY,
    request_data TEXT,
    response_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE
)

-- Transformed datasets  
schema_marketplace.datasets (
    filename TEXT PRIMARY KEY,
    request_data TEXT,
    response_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE
)
```

### Firestore Collections
```
all_user_profiles/
├── {user_id}/
│   ├── account_type: "admin"
│   ├── prdcer/
│   │   ├── prdcer_dataset: {...}
│   │   └── prdcer_lyrs: {
│   │       "l09a5e6ed-...": {supermarket layer},
│   │       "l116e3196-...": {pharmacy layer},
│   │       "l217d4297-...": {cafe/restaurant layer}
│   │   }
│   └── ...
```

## 🎪 Test Execution Flow

1. **Validation**: Check all required files and data exist
2. **User Creation**: Create test user with Firebase authentication  
3. **Database Seeding**: Seed all required test data
4. **Layer ID Extraction**: Map layer IDs to test variables
5. **Request Execution**: Send API requests with substituted variables
6. **Response Validation**: Validate against expected responses
7. **Cleanup**: Remove all test data

## 🔍 Variable Substitution

Tests use dynamic variable substitution:

```json
{
  "change_lyr_id": "${database.supermarket_layer_id}",
  "based_on_lyr_id": "${database.pharmacy_layer_id}",
  "user_id": "${user.user_id}"
}
```

Available variables:
- `${user.user_id}`, `${user.email}`, `${user.username}`
- `${database.supermarket_layer_id}`, `${database.pharmacy_layer_id}`
- `${database.cafe_restaurant_layer_id}`

## 🚨 Prerequisites

### Environment
- PostgreSQL database with `schema_marketplace` 
- Firebase/Firestore with test collections enabled
- FastAPI server running on `localhost:8000`
- Python dependencies installed

### Configuration
- Database connection configured in `backend_common/common_config.py`
- Firebase credentials in `secrets/firebase_service_account.json`
- Proper CORS and authentication settings

## 🎯 Usage Examples

### Run All Tests
```bash
python run_filter_tests.py
```

### Run Specific Test
```bash
pytest test_filter_based_on.py::test_filter_based_on[test_filter_based_on_radius_rating] -v
```

### Validate Setup Only
```bash
python validate_filter_setup.py
```

### Debug Mode
```bash
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from tests.integration.run_filter_tests import run_filter_tests
import asyncio
asyncio.run(run_filter_tests())
"
```

## 🤝 Contributing

To add new filter test scenarios:

1. Add configuration to `FILTER_BASED_ON_TESTS` in `test_filter_based_on.py`
2. Add expected response to `expected_responses/filter_based_on_responses.json`
3. Add any new seed data to `db_seed_data/` files if needed
4. Run validation: `python validate_filter_setup.py`
5. Test your changes: `python run_filter_tests.py`

## 📝 Notes

- Tests run sequentially to avoid database conflicts
- Each test includes comprehensive cleanup
- Layer IDs are automatically extracted from Firebase profiles
- Drive time tests may take longer due to Google Maps API calls
- All test data uses unique identifiers to prevent conflicts

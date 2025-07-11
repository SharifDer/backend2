# Filter Based On Endpoint - Integration Tests

This document explains the comprehensive integration tests for the `/filter_based_on` endpoint using our config-driven testing framework.

## Overview

The `filter_based_on` endpoint filters features from a source layer based on:
1. **Coverage criteria** (radius or drive time from reference points)
2. **Property criteria** (rating, user_ratings_total, or specific names)

## Test Suite Structure

### Test Configurations

The test suite includes 5 comprehensive test scenarios:

#### 1. `test_filter_based_on_radius_rating`
- **Purpose**: Tests radius-based filtering combined with rating criteria
- **Setup**: Supermarket and pharmacy layers in Riyadh
- **Filter**: Features within 2km radius of pharmacies with rating > 4.0
- **Expected**: Returns supermarkets meeting both criteria

#### 2. `test_filter_based_on_drive_time_name`
- **Purpose**: Tests drive time filtering with specific name matching
- **Setup**: Supermarket and pharmacy layers in Riyadh  
- **Filter**: Features within 10min drive time, matching specific names
- **Expected**: Returns named supermarkets within drive time

#### 3. `test_filter_based_on_user_ratings_total`
- **Purpose**: Tests filtering by user ratings count
- **Setup**: Cafe/restaurant layer in Jeddah
- **Filter**: Features within 1.5km radius with >50 user ratings
- **Expected**: Returns highly-rated establishments

#### 4. `test_filter_based_on_no_coverage`
- **Purpose**: Tests property-only filtering (no spatial constraints)
- **Setup**: Supermarket layer in Riyadh
- **Filter**: Rating > 4.0 only
- **Expected**: Returns all supermarkets with high ratings

#### 5. `test_filter_based_on_no_results`
- **Purpose**: Tests error handling for impossible criteria
- **Setup**: Supermarket layer in Riyadh
- **Filter**: Rating > 5.0 (impossible)
- **Expected**: Returns 500 error with appropriate message

## Database Seeding

### Required Data Seeds

Each test requires specific data to be seeded:

1. **Google Maps Raw Data** (`ggl_raw_seeds`)
   - `supermarket_cat_response`
   - `pharmacy_cat_response` 
   - `cafe_restaurant_dataset`

2. **Transformed Datasets** (`dataset_seeds`)
   - `supermarket_dataset`
   - `pharmacy_dataset`
   - `cafe_restaurant_dataset`

3. **Firebase Profiles** (`firebase_profile_seeds`)
   - `admin_profile_with_datasets` (supermarket + pharmacy)
   - `admin_profile_with_cafe_restaurant` (cafe/restaurant data)

### Layer ID Mapping

The seeding automatically extracts layer IDs for test use:

```python
variables = {
    "supermarket_layer_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
    "pharmacy_layer_id": "l116e3196-e721-4434-bad6-46291ba2aa0a", 
    "cafe_restaurant_layer_id": "l217d4297-f832-5545-cbd7-57392ca3bb1b"
}
```

## Request Structure

Each test sends a request with this structure:

```json
{
  "message": "Filter features based on criteria",
  "request_info": {"request_id": "test-filter-001"},
  "request_body": {
    "color_grid_choice": ["#FF0000", "#00FF00", "#0000FF"],
    "change_lyr_id": "${database.supermarket_layer_id}",
    "change_lyr_name": "SA-RIY-supermarket", 
    "change_lyr_current_color": "#28A745",
    "change_lyr_new_color": "#FF0000",
    "based_on_lyr_id": "${database.pharmacy_layer_id}",
    "based_on_lyr_name": "SA-RIY-pharmacy",
    "coverage_value": 2.0,
    "coverage_property": "radius", // or "drive_time"
    "color_based_on": "rating", // or "user_ratings_total", "name" 
    "list_names": [], // for name-based filtering
    "comparison_type": "greater", // or "less"
    "threshold": 4.0
  }
}
```

## Expected Response

Successful responses return an array of filtered layers:

```json
{
  "message": "Request received.",
  "request_id": "...",
  "data": [
    {
      "prdcer_layer_name": "SA-RIY-supermarket - Radius Filter",
      "prdcer_lyr_id": "generated-uuid",
      "bknd_dataset_id": "supermarket-dataset-id",
      "points_color": "#28A745",
      "layer_legend": "Radius ≥ 2.0 km",
      "layer_description": "Filtered based on coverage and property criteria",
      "records_count": 1,
      "city_name": "Riyadh",
      "is_zone_lyr": "true",
      "progress": 0,
      "sub_lyr_id": "supermarket_radius_filter",
      "type": "FeatureCollection",
      "features": [...],
      "properties": [...]
    }
  ]
}
```

## Running the Tests

### Option 1: Using the Custom Test Runner

```bash
cd tests/integration
python run_filter_tests.py
```

### Option 2: Using pytest

```bash
pytest tests/integration/test_filter_based_on.py -v
```

### Option 3: Individual Test

```python
from tests.integration.test_filter_based_on import FILTER_BASED_ON_TESTS
from tests.integration.fixtures.test_generator import ConfigTestGenerator

# Run specific test
test_config = FILTER_BASED_ON_TESTS[0]  # radius_rating test
generator = ConfigTestGenerator(...)
success = generator.execute_test(test_config)
```

## Prerequisites

### Environment Setup

1. **Database**: PostgreSQL with required schemas
2. **Firebase**: Firestore with test collections  
3. **Server**: FastAPI application running on localhost:8000
4. **Dependencies**: All required Python packages installed

### Configuration

The tests automatically:
- Create unique test run IDs to avoid conflicts
- Seed all required test data
- Set up user authentication
- Clean up after completion

## Validation Features

The tests use advanced validation including:

- **Flexible Assertions**: `min_length`, `contains`, `type` validators
- **JSON Structure Validation**: Deep object comparison
- **Error Response Testing**: Proper error handling verification
- **Performance Monitoring**: Response time tracking
- **Detailed Logging**: Comprehensive test execution logs

## Troubleshooting

### Common Issues

1. **Layer ID Not Found**: Check that Firebase profiles are properly seeded
2. **Database Connection**: Verify PostgreSQL is running and accessible
3. **Authentication Failure**: Ensure Firebase credentials are configured
4. **Timeout Errors**: Increase test timeout for complex filtering operations

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Data Inspection

Check seeded data:
```python
# View seeded datasets
from tests.integration.fixtures.database_fixtures import DatabaseSeeder
seeder = DatabaseSeeder("debug_run")
variables = seeder.seed_transformed_datasets(...)
print(variables)
```

## Contributing

When adding new filter tests:

1. Add test configuration to `FILTER_BASED_ON_TESTS`
2. Update expected responses in `filter_based_on_responses.json`
3. Add required seed data if needed
4. Update this documentation

## Performance Considerations

- Tests run sequentially to avoid database conflicts
- Each test includes cleanup to prevent data pollution
- Timeouts are set appropriately for drive time calculations
- Database connections are properly managed

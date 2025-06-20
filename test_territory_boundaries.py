#!/usr/bin/env python3
"""
Simple test script to verify the territory boundaries functionality works correctly.
"""

import sys
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from all_types.request_dtypes import ReqClustersForSalesManData

# Test the create_territory_boundaries function
from sales_man_problem import create_territory_boundaries

def create_test_data():
    """Create synthetic test data for testing"""
    # Create synthetic grid data with clusters
    np.random.seed(42)
    
    # Create some test points and polygons
    test_polygons = []
    test_data = []
    
    for i in range(20):
        # Create small square polygons
        x = (i % 5) * 0.01  # 5 columns
        y = (i // 5) * 0.01  # 4 rows
        polygon = Polygon([
            (x, y), (x + 0.008, y), 
            (x + 0.008, y + 0.008), (x, y + 0.008)
        ])
        
        test_polygons.append(polygon)
        test_data.append({
            'geometry': polygon,
            'group': i % 3,  # 3 groups (0, 1, 2)
            'number_of_persons': np.random.randint(100, 1000),
            'population_purchasing_power': np.random.uniform(50000, 200000),
            'number_of_supermarkets': np.random.randint(0, 5),
            'population_purchasing_potential': np.random.uniform(10000, 80000)
        })
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(test_data)
    
    return gdf

def create_test_request():
    """Create a test request object"""
    return ReqClustersForSalesManData(
        num_sales_man=3,
        city_name="Test City",
        country_name="Test Country",
        distance_limit=5.0,
        boolean_query="supermarket",
        user_id="test_user",
        include_raw_data=False
    )

def create_test_groups():
    """Create test groups dictionary"""
    return {
        0: [0, 1, 2, 5, 6, 7],       # Group 0: indices 0,1,2,5,6,7
        1: [3, 4, 8, 9, 10, 13],     # Group 1: indices 3,4,8,9,10,13  
        2: [11, 12, 14, 15, 16, 17, 18, 19]  # Group 2: remaining indices
    }

def test_territory_boundaries():
    """Test the territory boundaries creation function"""
    print("🧪 Testing territory boundaries functionality...")
    
    # Create test data
    print("📊 Creating test data...")
    test_gdf = create_test_data()
    test_req = create_test_request()
    test_groups = create_test_groups()
    
    print(f"   ✅ Created {len(test_gdf)} test grid cells")
    print(f"   ✅ Created {len(test_groups)} test groups")
    
    # Test the function
    print("🔧 Testing create_territory_boundaries function...")
    boundaries_gdf, boundaries_geojson = create_territory_boundaries(
        test_gdf, test_req, test_groups
    )
    
    # Verify results
    print("✅ Function executed successfully!")
    print(f"   📍 Created {len(boundaries_gdf)} territory boundaries")
    print(f"   🗺️  GeoJSON contains {len(boundaries_geojson['features'])} features")
    
    # Check GeoDataFrame structure
    print("📋 Boundary GeoDataFrame columns:", list(boundaries_gdf.columns))
    
    # Check that all groups are represented
    boundary_groups = set(boundaries_gdf['group'].values)
    expected_groups = set(test_groups.keys())
    
    assert boundary_groups == expected_groups, f"Group mismatch! Expected: {expected_groups}, Got: {boundary_groups}"
    print(f"   ✅ All {len(expected_groups)} groups represented in boundaries")
    
    # Check GeoJSON structure
    print("🔍 Verifying GeoJSON structure...")
    assert boundaries_geojson['type'] == 'FeatureCollection', "Invalid GeoJSON type"
    print("   ✅ Valid GeoJSON FeatureCollection")
    
    # Check individual features
    for i, feature in enumerate(boundaries_geojson['features']):
        assert all(key in feature for key in ['type', 'properties', 'geometry']), f"Feature {i} missing required keys"
        
    print("   ✅ All GeoJSON features have required structure")
    
    # Test aggregated data
    print("📊 Verifying aggregated data...")
    required_properties = ['group', 'number_of_persons', 'population_purchasing_power', 
                         'number_of_supermarkets', 'population_purchasing_potential']
    
    for prop in required_properties:
        assert prop in boundaries_gdf.columns, f"Missing property: {prop}"
        print(f"   ✅ {prop}: {boundaries_gdf[prop].sum():.0f} (total)")
    
    print("\n🎉 All tests passed! Territory boundaries functionality is working correctly.")

if __name__ == "__main__":
    try:
        test_territory_boundaries()
        print("✅ Test completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

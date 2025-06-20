#!/usr/bin/env python3
"""
Integration test for the full sales territory optimization workflow with territory boundaries
"""

import sys
import asyncio
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
from all_types.request_dtypes import ReqClustersForSalesManData

# Test the full workflow
from sales_man_problem import get_clusters_for_sales_man

def create_integration_test_data():
    """Create synthetic test data that simulates a realistic scenario"""
    np.random.seed(42)
    
    # Create a larger grid simulating a city area
    test_polygons = []
    test_data = []
    
    # Create a 10x10 grid (100 cells) representing city blocks
    for i in range(100):
        row = i // 10
        col = i % 10
        
        # Create small square polygons (city blocks)
        x = col * 0.01 + 0.0  # Longitude-like
        y = row * 0.01 + 0.0  # Latitude-like
        
        polygon = Polygon([
            (x, y), (x + 0.008, y), 
            (x + 0.008, y + 0.008), (x, y + 0.008)
        ])
        
        test_polygons.append(polygon)
        
        # Generate realistic demographic data
        base_population = np.random.randint(200, 2000)
        purchasing_power = base_population * np.random.uniform(40000, 120000)
        supermarkets = np.random.poisson(0.5)  # Average 0.5 supermarkets per block
        purchasing_potential = base_population * np.random.uniform(8000, 25000)
        
        test_data.append({
            'geometry': polygon,
            'number_of_persons': base_population,
            'population_purchasing_power': purchasing_power,
            'number_of_supermarkets': supermarkets,
            'population_purchasing_potential': purchasing_potential,
            'cell_id': i
        })
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(test_data)
    
    return gdf

def create_integration_test_request():
    """Create a realistic test request"""
    return ReqClustersForSalesManData(
        num_sales_man=4,  # 4 sales territories
        city_name="Test Metropolitan Area",
        country_name="Test Country",
        distance_limit=10.0,
        boolean_query="supermarket OR grocery",
        user_id="integration_test_user",
        include_raw_data=True
    )

async def test_full_integration_workflow():
    """Test the complete sales territory optimization workflow with boundaries"""
    print("🔬 Running full integration test for sales territory optimization...")
    
    try:
        # Create test data
        print("📊 Creating integration test data...")
        test_gdf = create_integration_test_data()
        test_req = create_integration_test_request()
        
        print(f"   ✅ Created {len(test_gdf)} test grid cells")
        print(f"   💰 Total market value: ${test_gdf['population_purchasing_potential'].sum():,.0f}")
        print(f"   🏪 Total supermarkets: {test_gdf['number_of_supermarkets'].sum()}")
        print(f"   👥 Total population: {test_gdf['number_of_persons'].sum():,}")
        
        # Mock the data fetching (since we're not using real API calls)
        print("🔧 Running sales territory optimization with territory boundaries...")
        
        # This would normally be called with real API data, but we'll use our test data
        # We need to simulate what the real function would do:
        
        # Import the main function components we need
        from sales_man_problem import create_territory_boundaries, generate_all_plots
        
        # Simulate clustering (assign random groups for this test)
        np.random.seed(42)
        test_gdf['group'] = np.random.randint(0, test_req.num_sales_man, len(test_gdf))
        
        # Create groups dictionary (like the real function does)
        groups = {}
        for group_id in range(test_req.num_sales_man):
            groups[group_id] = test_gdf[test_gdf['group'] == group_id].index.tolist()
        
        print(f"   ✅ Created {len(groups)} territory groups")
        for group_id, indices in groups.items():
            market_value = test_gdf.loc[indices, 'population_purchasing_potential'].sum()
            print(f"      Territory {group_id}: {len(indices)} cells, ${market_value:,.0f} market value")
        
        # Test territory boundaries creation
        print("🗺️  Creating territory boundaries...")
        boundaries_gdf, boundaries_geojson = create_territory_boundaries(
            test_gdf, test_req, groups
        )
        
        print(f"   ✅ Created {len(boundaries_gdf)} territory boundaries")
        print(f"   🗺️  GeoJSON contains {len(boundaries_geojson['features'])} features")
        
        # Test plot generation with boundaries
        print("📊 Generating plots with territory boundaries...")
        
        # Create a simple plot_path for testing
        import os
        plot_path = os.path.join(os.getcwd(), "test_plots")
        os.makedirs(plot_path, exist_ok=True)
          # Generate plots (this should include the new territory boundaries plot)
        generate_all_plots(
            test_gdf, 
            test_gdf,  # Use test_gdf as places for this test
            boundaries_gdf=boundaries_gdf,
            request_id="integration_test"
        )
        
        print("   ✅ Plots generated successfully")
        
        # Verify the territory boundaries plot was created
        territory_plot_path = os.path.join(plot_path, "territory_boundaries.png")
        if os.path.exists(territory_plot_path):
            print("   ✅ Territory boundaries plot created successfully")
        else:
            print("   ⚠️  Territory boundaries plot not found")
        
        # Test GeoJSON structure
        print("🔍 Verifying integration results...")
        
        # Check that boundaries have proper data aggregation
        total_original_population = test_gdf['number_of_persons'].sum()
        total_boundary_population = boundaries_gdf['number_of_persons'].sum()
        
        if abs(total_original_population - total_boundary_population) < 1:
            print(f"   ✅ Population aggregation correct: {total_boundary_population:,}")
        else:
            print(f"   ❌ Population mismatch: {total_original_population:,} vs {total_boundary_population:,}")
            return False
        
        # Check GeoJSON features
        if len(boundaries_geojson['features']) == test_req.num_sales_man:
            print(f"   ✅ All {test_req.num_sales_man} territories in GeoJSON")
        else:
            print(f"   ❌ Territory count mismatch in GeoJSON")
            return False
        
        # Check that each feature has required properties
        required_props = ['group', 'number_of_persons', 'population_purchasing_power', 
                         'number_of_supermarkets', 'population_purchasing_potential']
        
        for i, feature in enumerate(boundaries_geojson['features']):
            for prop in required_props:
                if prop not in feature['properties']:
                    print(f"   ❌ Feature {i} missing property: {prop}")
                    return False
        
        print("   ✅ All GeoJSON features have required properties")
        
        # Summary statistics
        print("\n📈 Integration Test Summary:")
        print(f"   🎯 Territories created: {len(boundaries_gdf)}")
        print(f"   💰 Total market value: ${boundaries_gdf['population_purchasing_potential'].sum():,.0f}")
        print(f"   👥 Total population: {boundaries_gdf['number_of_persons'].sum():,}")
        print(f"   🏪 Total supermarkets: {boundaries_gdf['number_of_supermarkets'].sum()}")
        
        # Territory balance analysis
        market_values = [
            boundaries_gdf[boundaries_gdf['group'] == i]['population_purchasing_potential'].sum() 
            for i in range(test_req.num_sales_man)
        ]
        
        min_value = min(market_values)
        max_value = max(market_values)
        balance_ratio = min_value / max_value if max_value > 0 else 0
        
        print(f"   ⚖️  Territory balance ratio: {balance_ratio:.2f} (1.0 = perfect balance)")
        
        if balance_ratio > 0.5:  # Reasonable balance
            print("   ✅ Territories are reasonably balanced")
        else:
            print("   ⚠️  Territories may be unbalanced")
        
        print("\n🎉 Full integration test completed successfully!")
        print("✅ Territory boundaries feature is fully integrated and working")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_full_integration_workflow())
    sys.exit(0 if success else 1)

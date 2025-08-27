"""
Interactive plotting module for territory optimization data visualization.
Creates dynamic Plotly visualizations from GeoJSON data files.
"""

import json
import pandas as pd
import plotly.express as px
from typing import Dict, Optional, Tuple
from pathlib import Path


class InteractivePlotter:
    """Handle interactive plotting for territory optimization data"""
    
    def __init__(self):
        self.grid_df = pd.DataFrame()
        self.supermarkets_df = pd.DataFrame()
        self.grid_geojson = None
        self.places_geojson = None
        self.data_loaded = False
        
    def load_data_files(self, data_files: Dict[str, str]) -> bool:
        """
        Load GeoJSON data files into DataFrames for plotting
        
        Args:
            data_files: Dictionary with file paths for grid_data, places_data, boundaries
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            print(f"[DEBUG] Loading data files for interactive plotting...")
            
            # Load grid data GeoJSON
            grid_path = data_files.get('grid_data')
            if grid_path and Path(grid_path).exists():
                with open(grid_path) as f:
                    self.grid_geojson = json.load(f)
                    
                # Extract feature properties into DataFrame
                self.grid_df = pd.DataFrame([
                    feature['properties'] for feature in self.grid_geojson['features']
                ])
                # Add unique ID for choropleth mapping
                self.grid_df['id'] = [
                    feature['id'] for feature in self.grid_geojson['features']
                ]
                print(f"✅ Grid data loaded: {len(self.grid_df)} features")
            else:
                print(f"❌ Grid data file not found: {grid_path}")
                return False
            
            # Load places data GeoJSON
            places_path = data_files.get('places_data')
            if places_path and Path(places_path).exists():
                with open(places_path) as f:
                    self.places_geojson = json.load(f)
                    
                # Extract feature properties and coordinates
                places_df = pd.DataFrame([
                    feature['properties'] for feature in self.places_geojson['features']
                ])
                places_df['lon'] = [
                    feature['geometry']['coordinates'][0] 
                    for feature in self.places_geojson['features']
                ]
                places_df['lat'] = [
                    feature['geometry']['coordinates'][1] 
                    for feature in self.places_geojson['features']
                ]
                
                # Filter for supermarkets
                self.supermarkets_df = places_df[
                    places_df['primaryType'] == 'supermarket'
                ].reset_index(drop=True)
                print(f"✅ Places data loaded: {len(self.supermarkets_df)} supermarkets")
            else:
                print(f"❌ Places data file not found: {places_path}")
                return False
            
            self.data_loaded = True
            print(f"✅ All data files loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data files: {str(e)}")
            return False
    
    def get_available_variables(self) -> Dict[str, str]:
        """
        Get available variables for plotting based on loaded data
        
        Returns:
            Dictionary mapping variable keys to display names
        """
        if not self.data_loaded or self.grid_df.empty:
            return {}
            
        available_vars = {}
        
        # Check which columns are available in the grid data
        column_mappings = {
            'number_of_persons': 'Number of Persons',
            'population_purchasing_power': 'Population Purchasing Power',
            'number_of_supermarkets': 'Number of Supermarkets',
            'population_purchasing_potential': 'Population Purchasing Potential'
        }
        
        for col_key, display_name in column_mappings.items():
            if col_key in self.grid_df.columns:
                available_vars[col_key] = display_name
                
        return available_vars
    
    def create_choropleth_map(self, selected_variable: str) -> Optional[dict]:
        """
        Create interactive choropleth map for selected variable
        
        Args:
            selected_variable: Variable to visualize (e.g., 'population_purchasing_power')
            
        Returns:
            Plotly figure dictionary or None if error
        """
        if not self.data_loaded or self.grid_df.empty or self.grid_geojson is None:
            print("❌ Cannot create choropleth: data not loaded")
            return None
            
        if selected_variable not in self.grid_df.columns:
            print(f"❌ Variable '{selected_variable}' not found in data")
            return None
            
        try:
            # Create the choropleth map
            fig = px.choropleth_mapbox(
                self.grid_df,
                geojson=self.grid_geojson,
                locations='id',
                featureidkey='id',
                color=selected_variable,
                color_continuous_scale="Plasma",
                mapbox_style="carto-positron",
                zoom=9,
                center={"lat": 24.7, "lon": 46.7},  # Default to Riyadh
                opacity=0.6,
                labels={selected_variable: selected_variable.replace('_', ' ').title()},
                hover_data={
                    'id': False,
                    **{col: ':.2s' if 'power' in col or 'potential' in col else True 
                       for col in self.grid_df.columns if col != 'id'}
                }
            )
            
            fig.update_layout(
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=500
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creating choropleth map: {str(e)}")
            return None
    
    def create_supermarket_scatter_map(self) -> Optional[dict]:
        """
        Create interactive scatter map of supermarket locations
        
        Returns:
            Plotly figure dictionary or None if error
        """
        if not self.data_loaded or self.supermarkets_df.empty:
            print("❌ Cannot create scatter map: supermarket data not loaded")
            return None
            
        try:
            fig = px.scatter_mapbox(
                self.supermarkets_df,
                lat="lat",
                lon="lon",
                hover_name="name",
                hover_data={
                    "name": True, 
                    "phone": True, 
                    "lon": False, 
                    "lat": False
                },
                color_discrete_sequence=["#1f77b4"],
                mapbox_style="carto-positron",
                zoom=9,
                center={"lat": 24.7, "lon": 46.7},
                title="Supermarket Locations"
            )
            
            fig.update_layout(
                margin={"r": 0, "t": 40, "l": 0, "b": 0},
                height=500
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Error creating scatter map: {str(e)}")
            return None
    
    def get_data_summary(self) -> Dict[str, any]:
        """
        Get summary statistics about loaded data
        
        Returns:
            Dictionary with data summary information
        """
        if not self.data_loaded:
            return {"status": "No data loaded"}
            
        return {
            "status": "Data loaded successfully",
            "grid_features": len(self.grid_df),
            "supermarkets": len(self.supermarkets_df),
            "available_variables": list(self.get_available_variables().keys()),
            "data_columns": list(self.grid_df.columns)
        }


# Global plotter instance for use across the app
plotter = InteractivePlotter()


def load_and_create_plots(data_files: Dict[str, str]) -> Tuple[bool, Dict[str, any]]:
    """
    Convenience function to load data and get basic plot information
    
    Args:
        data_files: Dictionary with GeoJSON file paths
        
    Returns:
        Tuple of (success, plot_info)
    """
    global plotter
    
    success = plotter.load_data_files(data_files)
    if success:
        plot_info = {
            "variables": plotter.get_available_variables(),
            "summary": plotter.get_data_summary(),
            "default_variable": list(plotter.get_available_variables().keys())[0] if plotter.get_available_variables() else None
        }
        return True, plot_info
    else:
        return False, {"error": "Failed to load data files"}
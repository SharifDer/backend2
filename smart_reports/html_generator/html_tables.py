"""
HTML Tables Module for Pharmacy Report Generation
Contains all table generation functions for pharmacy reports
"""

from typing import Dict, Any, List


def generate_rankings_table(rankings: List[Dict[str, Any]]) -> str:
    """Generate rankings table HTML"""
    table_rows = ""
    for i, property_data in enumerate(rankings, 1):
        rank_class = "top3" if i <= 3 else ""
        
        # Extract data with proper field mapping - ONLY use data that exists in JSON
        site_name = property_data.get('site_name', 'Property')  # Use site_name from JSON
        price = property_data.get('price_sar', 0)  # Use price_sar from JSON
        # Handle None price values
        if price is None:
            price = 0
        
        # Extract scores from comparison objects in JSON using display_text with icons
        final_score = _get_display_text_with_icon(property_data.get('final_score_comparison', {}))
        traffic_score = _get_display_text_with_icon(property_data.get('traffic_score_comparison', {}))
        demographics_score = _get_display_text_with_icon(property_data.get('demographics_score_comparison', {}))
        competition_score = _get_display_text_with_icon(property_data.get('competition_score_comparison', {}))
        healthcare_score = _get_display_text_with_icon(property_data.get('healthcare_ecosystem_score_comparison', {}))
        complementary_score = _get_display_text_with_icon(property_data.get('complementary_businesses_score_comparison', {}))
        
        # Generate Google Maps URL if coordinates are available
        google_maps_url = property_data.get('url', '#')  # Use url from JSON instead of google_maps_url
        if not google_maps_url or google_maps_url == '#':
            # Try to get coordinates from location object if available
            location = property_data.get('location', {})
            lat = location.get('latitude')
            lng = location.get('longitude')
            if lat and lng:
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        
        # Format price display
        price_display = "N/A" if price == 0 and property_data.get('price_sar') is None else f"{price:,.0f}"
        
        table_rows += f"""
      <tr>
        <td><span class="rank-badge {rank_class}">#{i}</span></td>
        <td><code>{site_name}</code></td>
        <td>{price_display}</td>
        <td><strong>{final_score}</strong></td>
        <td>{traffic_score}</td>
        <td>{demographics_score}</td>
        <td>{competition_score}</td>
        <td>{healthcare_score}</td>
        <td>{complementary_score}</td>
        <td><a href="{google_maps_url}" target="_blank">View</a></td>
      </tr>"""
    return table_rows

def generate_current_location_table(processed_report_data: Dict[str, Any]) -> str:
    """Generate Current Location Scores table if current location data exists"""
    current_location = processed_report_data.get('current_location', [])
    
    if not current_location:
        return ""
    
    # Generate table rows for current location
    table_rows = ""
    for location_data in current_location:
        site_name = location_data.get('site_name', 'Your current location')
        price = location_data.get('price_sar', 0)
        rank = location_data.get('rank', 0)
        
        # Handle None price values
        if price is None:
            price = 0
        
        # Use direct score values from JSON (no comparison objects for current/custom locations)
        final_score = f"{location_data.get('final_score', 0):.1f}"
        traffic_score = f"{location_data.get('traffic_score', 0):.1f}"
        demographics_score = f"{location_data.get('demographics_score', 0):.1f}"
        competition_score = f"{location_data.get('competition_score', 0):.1f}"
        healthcare_score = f"{location_data.get('healthcare_ecosystem_score', 0):.1f}"
        complementary_score = f"{location_data.get('complementary_businesses_score', 0):.1f}"
        
        # Generate Google Maps URL if coordinates are available
        google_maps_url = location_data.get('url', '#')
        if not google_maps_url or google_maps_url == '#':
            # Try to get coordinates from location object if available
            location = location_data.get('location', {})
            lat = location.get('latitude')
            lng = location.get('longitude')
            if lat and lng:
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        
        # Format price display
        price_display = "N/A" if price == 0 and location_data.get('price_sar') is None else f"{price:,.0f}"
        
        table_rows += f"""
      <tr>
        <td><span class="rank-badge">#{rank}</span></td>
        <td><code>{site_name}</code></td>
        <td>{price_display}</td>
        <td><strong>{final_score}</strong></td>
        <td>{traffic_score}</td>
        <td>{demographics_score}</td>
        <td>{competition_score}</td>
        <td>{healthcare_score}</td>
        <td>{complementary_score}</td>
        <td><a href="{google_maps_url}" target="_blank">View</a></td>
      </tr>"""
    
    return f"""
  <h2 class="section-title">📍 Current Location Scores</h2>

  <table class="rankings-table">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Site Name</th>
        <th>Rent Price (SAR)</th>
        <th>Final Score</th>
        <th>Traffic</th>
        <th>Demographics</th>
        <th>Competition</th>
        <th>Healthcare Environment</th>
        <th>Complementary Businesses</th>
        <th>View</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>"""

def generate_custom_locations_table(processed_report_data: Dict[str, Any]) -> str:
    """Generate Custom Location Analysis table if custom locations data exists"""
    custom_locations = processed_report_data.get('custom_locations', [])
    
    if not custom_locations:
        return ""
    
    # Generate table rows for custom locations
    table_rows = ""
    for location_data in custom_locations:
        site_name = location_data.get('site_name', 'Custom location')
        price = location_data.get('price_sar', 0)
        rank = location_data.get('rank', 0)
        
        # Handle None price values
        if price is None:
            price = 0
        
        # Use direct score values from JSON (no comparison objects for current/custom locations)
        final_score = f"{location_data.get('final_score', 0):.1f}"
        traffic_score = f"{location_data.get('traffic_score', 0):.1f}"
        demographics_score = f"{location_data.get('demographics_score', 0):.1f}"
        competition_score = f"{location_data.get('competition_score', 0):.1f}"
        healthcare_score = f"{location_data.get('healthcare_ecosystem_score', 0):.1f}"
        complementary_score = f"{location_data.get('complementary_businesses_score', 0):.1f}"
        
        # Generate Google Maps URL if coordinates are available
        google_maps_url = location_data.get('url', '#')
        if not google_maps_url or google_maps_url == '#':
            # Try to get coordinates from location object if available
            location = location_data.get('location', {})
            lat = location.get('latitude')
            lng = location.get('longitude')
            if lat and lng:
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        
        # Format price display
        price_display = "N/A" if price == 0 and location_data.get('price_sar') is None else f"{price:,.0f}"
        
        table_rows += f"""
      <tr>
        <td><span class="rank-badge">#{rank}</span></td>
        <td><code>{site_name}</code></td>
        <td>{price_display}</td>
        <td><strong>{final_score}</strong></td>
        <td>{traffic_score}</td>
        <td>{demographics_score}</td>
        <td>{competition_score}</td>
        <td>{healthcare_score}</td>
        <td>{complementary_score}</td>
        <td><a href="{google_maps_url}" target="_blank">View</a></td>
      </tr>"""
    
    return f"""
  <h2 class="section-title">📍 Custom Location Analysis</h2>

  <table class="rankings-table">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Site Name</th>
        <th>Rent Price (SAR)</th>
        <th>Final Score</th>
        <th>Traffic</th>
        <th>Demographics</th>
        <th>Competition</th>
        <th>Healthcare Environment</th>
        <th>Complementary Businesses</th>
        <th>View</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>"""

def _get_display_text_with_icon(comparison_data: Dict[str, Any]) -> str:
    """Extract display text with appropriate icon based on comparison type"""
    if not comparison_data:
        return "N/A"
    
    display_text = comparison_data.get('display_text', '')
    comparison_type = comparison_data.get('comparison_type', '')
    
    # Add appropriate icon based on comparison type
    if comparison_type == 'improvement':
        return f"{display_text} 📈"
    elif comparison_type == 'disadvantage':
        return f"{display_text} 📉"
    elif comparison_type == 'difference':
        # For 'difference' (like 0% difference), just return the display text with no icon
        return display_text
    else:
        # For other types, just return the display text
        return display_text

"""
HTML Property Cards Module for Pharmacy Report Generation
Contains property card generation functions for pharmacy reports
"""

from typing import Dict, Any, List


def generate_property_cards(detailed_analysis: List[Dict[str, Any]], visual_analysis: Dict[str, Any] = None, processed_report_data: Dict[str, Any] = None) -> str:
    """Generate property cards HTML"""
    # Interactive maps mapping removed - not used in current implementation
    
    property_cards_html = ""
    for i, property_data in enumerate(detailed_analysis, 1):
        site_name = property_data.get('site_name', 'Property')
        final_score = property_data.get('final_score', 0)
        price_sar = property_data.get('price_sar', 0)
        # Handle None price values
        if price_sar is None:
            price_sar = 0
        category = property_data.get('category', 'Pharmacy')
        google_maps_url = property_data.get('google_maps_url', '#')
        
        # Extract coordinates from nested location object
        location = property_data.get('location', {})
        latitude = location.get('latitude', 0)
        longitude = location.get('longitude', 0)
        
        # Extract from detailed_insights nested structure
        detailed_insights = property_data.get('detailed_insights', {})
        traffic_performance = detailed_insights.get('traffic_performance', {})
        business_environment = detailed_insights.get('business_environment', {})
        demographics_match = detailed_insights.get('demographics_match', {})
        competitive_position = detailed_insights.get('competitive_position', {})
        
        # Get the actual values from the nested structure
        current_speed = traffic_performance.get('current_speed_kmh', 0)
        nearby_businesses = business_environment.get('nearby_businesses_500m', 0)
        population_age_35_plus = demographics_match.get('population_age_35_plus_percent', 0)
        average_income = demographics_match.get('average_income_sar', 0)
        competing_pharmacies = competitive_position.get('competing_pharmacies', 0)
        
        # Get scores from rankings data using display_text with icons
        rankings = processed_report_data.get('rankings', []) if processed_report_data else []
        matching_ranking = {}
        if rankings:
            # Find the matching ranking by site_name
            matching_ranking = next((prop for prop in rankings if prop.get('site_name') == site_name), {})
        
        # Get display text with icons for each score
        traffic_score_display = _get_display_text_with_icon(matching_ranking.get('traffic_score_comparison', {}))
        demographics_score_display = _get_display_text_with_icon(matching_ranking.get('demographics_score_comparison', {}))
        competition_score_display = _get_display_text_with_icon(matching_ranking.get('competition_score_comparison', {}))
        
        # Scoring breakdown calculation removed - not used in current implementation
        
        property_cards_html += f"""
      <div class="property-card">
        <div class="property-header">
          <div class="property-title">#{i} {site_name}</div>
          <div class="score-badge">{final_score:.1f}/100</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px">
          <div>
            <h4 style="color: #2c3e50; margin-bottom: 10px">📍 Property Details</h4>
            <p><strong>Price:</strong> {"N/A" if price_sar == 0 and property_data.get('price_sar') is None else f"{price_sar:,.0f} SAR"}</p>
            <p><strong>Coordinates:</strong> {latitude:.6f}, {longitude:.6f}</p>
            <p><strong>Category:</strong> {category}</p>
            <p>
              <strong>Listing:</strong>
              <a href="{google_maps_url}" target="_blank" style="color: #3498db">View Property</a>
            </p>
          </div>

          <div>
            <h4 style="color: #2c3e50; margin-bottom: 10px">🎯 Performance Metrics</h4>
            <div class="score-breakdown">
              <div class="score-item">
                <div class="value">{traffic_score_display}</div>
                <div class="label">Traffic<br />({current_speed:.1f} km/h)</div>
              </div>
              <div class="score-item">
                <div class="value">{nearby_businesses}</div>
                <div class="label">Business<br />({nearby_businesses} nearby)</div>
              </div>
              <div class="score-item">
                <div class="value">{demographics_score_display}</div>
                <div class="label">Demographics<br />(Age: {population_age_35_plus:.0f})</div>
              </div>
              <div class="score-item">
                <div class="value">{competition_score_display}</div>
                <div class="label">Competition<br />({competing_pharmacies} pharmacies)</div>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top: 20px">
          <h4 style="color: #2c3e50; margin-bottom: 10px">📊 Detailed Analysis</h4>
          <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
              ">
            <div>
              <strong>🚗 Traffic Performance:</strong><br />
              <small>Current: {current_speed:.1f} km/h vs Target: 20–30 km/h<br />Assessment: ℹ️ Light traffic — smooth access but potentially less exposure to passersby.</small>
            </div>
            <div>
              <strong>🏪 Business Environment:</strong><br />
              <small>{nearby_businesses} businesses within 500m<br />Assessment: ❌ Weak ecosystem — limited complementary activity may reduce visibility.</small>
            </div>
            <div>
              <strong>👥 Demographics Match:</strong><br />
              <small>Population Aged 35+: {population_age_35_plus:.1f}%<br />Average Income: {average_income:,.2f} SAR<br />Assessment: ✅ Strong alignment with demand.</small>
            </div>
            <div>
              <strong>☕ Competitive Position:</strong><br />
              <small>{competing_pharmacies} pharmacies in area (2 per 10k population)<br />🟢 Underserved market<br />Strategy: Strong opportunity for entry and growth.</small>
            </div>
          </div>
        </div>

        <div class="map-container">
          <h4 style="color: #2c3e50; margin-bottom: 15px">📍 Site Location Map</h4>
          <iframe src="maps/site_{latitude},{longitude}_map.html" width="100%" height="400" style="border:0; border-radius: 12px;"></iframe>
          <p style="margin-top: 15px; color: #7f8c8d; font-size: 0.9em">
            <strong>Map shows:</strong> Property location, nearby businesses, analysis radius, and traffic patterns.
          </p>
        </div>
      </div>"""
    return property_cards_html

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

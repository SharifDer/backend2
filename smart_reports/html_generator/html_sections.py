"""
HTML Sections Module for Pharmacy Report Generation
Contains main section generation functions for pharmacy reports
"""

from typing import Dict, Any, List
from datetime import datetime

# Import functional modules
from .html_tables import generate_rankings_table, generate_current_location_table, generate_custom_locations_table
from .html_property_cards import generate_property_cards
from .html_charts_visuals import generate_chart_grid, generate_investment_insights_list


def generate_executive_summary_section(report_data, processed_report_data: Dict[str, Any]) -> str:
    """Generate Executive Summary Section with rankings and top recommendations"""
    # Extract data
    city_name = report_data.city_name if report_data else "Unknown City"
    title = processed_report_data.get("title", f"{city_name} Pharmacy Site Analysis Report")
    description = processed_report_data.get("description", "Comprehensive Location Intelligence & Investment Recommendations")
    summary_metrics = processed_report_data.get("summary_metrics", {})
    executive_summary = processed_report_data.get("executive_summary", {})
    rankings = processed_report_data.get("rankings", [])
    
    total_locations = summary_metrics.get("total_locations", 0)
    average_score = summary_metrics.get("average_score", 0)
    average_price_sar = summary_metrics.get("average_price_sar", 0)
    competing_pharmacies = summary_metrics.get("competing_pharmacies", 0)
    
    top_recommendation = executive_summary.get("top_recommendation", {})
    total_sites_evaluated = executive_summary.get("total_sites_evaluated", 0)
    
    nearby_businesses = 0
    population_age_35_plus = 0
    avg_income = 0
    traffic_score_display = "N/A"
    demographics_score_display = "N/A"
    competition_score_display = "N/A"
    
    # Get additional metrics from top property's detailed insights
    detailed_analysis = processed_report_data.get('detailed_analysis', [])
    if detailed_analysis:
        # Find the top ranking property (rank 1) to get its detailed insights
        top_property = next((prop for prop in detailed_analysis if prop.get('rank') == 1), {})
        detailed_insights = top_property.get('detailed_insights', {})
        business_environment = detailed_insights.get('business_environment', {})
        demographics_match = detailed_insights.get('demographics_match', {})
        traffic_performance = detailed_insights.get('traffic_performance', {})
        
        # Map the available fields for display
        nearby_businesses = business_environment.get('nearby_businesses_500m', 0)
        population_age_35_plus = demographics_match.get('population_age_35_plus_percent', 0)
        avg_income = demographics_match.get('average_income_sar', 0)
        
        # Get competition data
        competitive_position = detailed_insights.get('competitive_position', {})
        competing_pharmacies = competitive_position.get('competing_pharmacies', 0)
        
        # Get scores from rankings data using display_text with icons
        rankings = processed_report_data.get('rankings', [])
        top_ranking = {}
        if rankings:
            top_ranking = next((prop for prop in rankings if prop.get('rank') == 1), {})
        
        # Get display text with icons for each score
        from .html_tables import _get_display_text_with_icon
        traffic_score_display = _get_display_text_with_icon(top_ranking.get('traffic_score_comparison', {}))
        demographics_score_display = _get_display_text_with_icon(top_ranking.get('demographics_score_comparison', {}))
        competition_score_display = _get_display_text_with_icon(top_ranking.get('competition_score_comparison', {}))
    
    return f"""
    <div class="page">
      <div class="hero">
        <h1>{title}</h1>
        <div class="muted">{description}</div>
        <div style="margin-top: 20px; font-size: 0.9em">
          Generated on {datetime.now().strftime('%B %d, %Y')}
        </div>
      </div>

      <div class="executive-summary">
        <h2 style="margin-bottom: 20px; border: none; color: white">
          📊 Executive Summary
        </h2>
        <p style="margin-bottom: 0">
          This comprehensive analysis evaluates {total_sites_evaluated} pharmacy locations across {city_name} using advanced location intelligence methodologies. Our assessment integrates multiple data sources including traffic flow analysis, demographic profiling, healthcare ecosystem mapping, competitive landscape evaluation, and complementary business assessment. Each location is systematically scored using our proprietary weighted methodology, considering market opportunity, accessibility, and business environment factors to provide data-driven investment recommendations.
        </p>
      </div>

      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-value">{total_locations}</div>
          <div class="metric-label">Total Properties Analyzed</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{average_score:.1f}</div>
          <div class="metric-label">Average Performance Score</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{average_price_sar:,.0f} SAR</div>
          <div class="metric-label">Average Price</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{competing_pharmacies}</div>
          <div class="metric-label">Competing Pharmacies</div>
        </div>
      </div>

      <div class="top-recommendation">
        <h2 style="margin-bottom: 20px; border: none; color: white">
          🏆 TOP RECOMMENDATION
        </h2>
        <h3 style="font-size: 1.8em; margin-bottom: 10px">Property #1: {top_recommendation.get('site_name', 'Top Property')}</h3>
        <div class="score-display">{top_recommendation.get('score', 0):.1f}/100</div>
        <p style="display: none">
          <strong>Price:</strong> {top_recommendation.get('price_sar', 0):,.0f} SAR
        </p>
        <div style="
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 20px;
              margin-top: 20px;
            ">
          <div>
            <strong>🚗 Traffic Analysis:</strong><br />
            {traffic_score_display}<br />
            <small>Target: 20–30 km/h | ℹ️ Light traffic</small>
          </div>
          <div>
            <strong>🏪 Business Environment:</strong><br />
            {nearby_businesses} businesses within 500m<br />
            <small>✅ Strong ecosystem</small>
          </div>
          <div>
            <strong>👥 Demographics:</strong><br />
            {demographics_score_display}<br />
            <small>Age: {population_age_35_plus:.1f}% | Income: {avg_income:,.0f} SAR</small>
          </div>
          <div>
            <strong>☕ Competition:</strong><br />
            {competition_score_display}<br />
            <small>({competing_pharmacies} pharmacies)</small>
          </div>
        </div>
      </div>

      {generate_current_location_table(processed_report_data)}
      {generate_custom_locations_table(processed_report_data)}

      <h2 class="section-title">📈 Top 10 Rankings</h2>

      <table class="rankings-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Site Name</th>
            <th>Price (SAR)</th>
            <th>Final Score</th>
            <th>Traffic</th>
            <th>Demographics</th>
            <th>Competition</th>
            <th>Healthcare Ecosystem</th>
            <th>Complementary Businesses</th>
            <th>View</th>
          </tr>
        </thead>
        <tbody>
          {generate_rankings_table(rankings[:10])}
        </tbody>
      </table>
    </div>"""

def generate_methodology_and_analysis_section(report_data, processed_report_data: Dict[str, Any]) -> str:
    """Generate Methodology and Detailed Property Analysis Section"""
    detailed_analysis = processed_report_data.get("detailed_analysis", [])
    print(f"DEBUG: _generate_methodology_and_analysis_section called with {len(detailed_analysis)} items")
    
    # Generate property cards
    property_cards_html = generate_property_cards(detailed_analysis[:10], processed_report_data.get('visual_analysis', {}), processed_report_data)
    print(f"DEBUG: Property cards HTML length: {len(property_cards_html)}")
    print(f"DEBUG: First 500 chars of property cards: {property_cards_html[:500]}")
    
    return f"""
    <div class="page page-break">
      <h1 class="section-title">📈 Analysis Methodology</h1>

      <div class="methodology">
        <h3 style="color: #2c3e50; margin-bottom: 15px">
          📋 How This Analysis Was Conducted
        </h3>
        <p style="margin-bottom: 20px; font-size: 1.1em">
          Our site suitability analysis employs a comprehensive, data-driven
          approach. The methodology integrates multiple data sources and applies weighted
          scoring to identify optimal locations.
        </p>

        <div style="
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
              gap: 20px;
              margin: 20px 0;
            ">
          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #3498db; margin-bottom: 10px">🚦 Traffic Analysis (25%)</h4>
            <p><strong>Method:</strong> Real-time traffic flow analysis within 500m radius</p>
            <p>
              <strong>Scoring:</strong> Perfect score (100) for speeds ≤40 km/h; penalty of 5 points per 40 km/h above
              target
            </p>
            <p>
              <strong>Rationale:</strong> Lower traffic speeds indicate better accessibility and parking availability.
            </p>
          </div>

          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #3498db; margin-bottom: 10px">👥 Demographics (30%)</h4>
            <p><strong>Method:</strong> Spatial join analysis for age and income matching</p>
            <p>
              <strong>Scoring:</strong> Perfect score at target age Above 35; penalty of 5 points per year deviation
            </p>
            <p>
              <strong>Rationale:</strong> Target demographic alignment ensures market-product fit.
            </p>
          </div>

          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #3498db; margin-bottom: 10px">🏪 Competition (15%)</h4>
            <p><strong>Method:</strong> Competitive mapping within analysis radius</p>
            <p>
              <strong>Scoring:</strong> Perfect score for nearest pharmacy is above 500m in living area; penalty of 10
              points per excess competitor
            </p>
            <p>
              <strong>Rationale:</strong> Balanced competition validates demand while avoiding oversaturation.
            </p>
          </div>

          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #3498db; margin-bottom: 10px">🏥 Healthcare Ecosystem (20%)</h4>
            <p><strong>Method:</strong> Scoring based on proximity to nearby hospitals and dentists (≤1500m preferred)
            </p>
            <p><strong>Scoring:</strong> Average of proximity scores; closer and more accessible healthcare improves
              score</p>
            <p>
              <strong>Rationale:</strong> A strong healthcare ecosystem increases site attractiveness and convenience
              for residents.
            </p>
          </div>

          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #3498db; margin-bottom: 10px">🏪 Complementary Businesses (10%)</h4>
            <p><strong>Method:</strong> Proximity-based scoring within 1000m; closer businesses improve accessibility
            </p>
            <p><strong>Scoring:</strong> Average score across all complementary business types</p>
            <p>
              <strong>Rationale:</strong> Access to everyday amenities supports sustained foot traffic and customer
              satisfaction.
            </p>
          </div>
        </div>

        <div style="
              background: #e8f4fd;
              padding: 20px;
              border-radius: 10px;
              margin-top: 20px;
            ">
          <h4 style="color: #2c3e50; margin-bottom: 10px">🧮 Final Score Calculation</h4>
          <p>
            <strong>Formula:</strong> Final Score = (Traffic × 0.25) + (Demographics × 0.30) + (Competition × 0.15) +
            (Healthcare × 0.20) + (Complementary × 0.10)
          </p>
          <p>
            <strong>Range:</strong> 0–100 scale where 100 = optimal conditions across all criteria
          </p>
          <p>
            <strong>Interpretation:</strong> 🟢 ≥80 indicates an excellent potential, 🟡 60–79 indicates a good
            potential, 🔴 &lt; 60 requires careful consideration
          </p>
        </div>
      </div>

      <h1 class="section-title">🔍 Detailed Property Analysis</h1>

      <p style="font-size: 1.1em; color: #7f8c8d; margin-bottom: 30px">
        Comprehensive breakdown of top 10 performing properties with detailed
        scoring analysis and individual site maps.
      </p>

      {property_cards_html}
    </div>"""

def generate_visual_analysis_section(report_data, processed_report_data: Dict[str, Any], generated_maps: List[str], generated_charts: List[str], key_investment_insights: List[Dict[str, Any]]) -> str:
    """Generate Visual Analysis Section with maps, charts, and investment insights"""
    return f"""
    <div class="page page-break">
      <h1 class="section-title">🗺️ Visual Analysis & Regional Overview</h1>

      <p style="font-size: 1.1em; color: #7f8c8d; margin-bottom: 30px">
        Interactive maps and statistical analysis providing comprehensive visual
        insights into market patterns and investment opportunities.
      </p>

      <div style="
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin: 30px 0;
          ">
        <h3 style="color: #2c3e50; margin-bottom: 20px">📊 Regional Overview</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
          <div class="performance-metrics">
            <h4>Market Performance</h4>
            <p>• Central Business District: High traffic, premium demographics</p>
            <p>• Residential Zones: Stable demand, moderate competition</p>
            <p>• Healthcare Corridors: Strong referral potential</p>
          </div>
          <div class="performance-metrics">
            <h4>Market Insights</h4>
            <p>• Score distribution shows clear performance tiers</p>
            <p>• Price-performance correlation analysis</p>
            <p>• Competition density mapping</p>
          </div>
        </div>
      </div>

      <div style="
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin: 30px 0;
          ">
        <h3 style="color: #2c3e50; margin-bottom: 20px">📈 Statistical Analysis</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
          {generate_chart_grid(generated_charts, processed_report_data.get('visual_analysis', {}))}
        </div>
      </div>

      <div class="property-card">
        <div class="property-header">
          <div class="property-title">
            🌍 Riyadh Commercial Properties Overview
          </div>
        </div>

        <div class="map-container">
          <img src="maps/candidates_map.png" alt="Riyadh Properties Overview Map" class="map-image" />

          <p style="margin-top: 15px; color: #7f8c8d">
            <strong>Overview Map Features:</strong> Top 10 analyzed properties
            color-coded by performance score, demographic zones by area, and
            competitive distribution patterns. Green stars indicate top
            performers (80-100), orange shows good potential (60-79), and red
            highlights properties requiring careful consideration (&lt;60).
          </p>
        </div>

        <div style="margin-top: 20px">
          <h4 style="color: #2c3e50; margin-bottom: 10px">
            🎯 Regional Insights
          </h4>
          <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
              ">
            <div>
              <strong>🏆 Top Performing Areas:</strong><br />
              <small>Properties showing superior performance due to optimal
                business density and demographics clustering</small>
            </div>
            <div>
              <strong>📊 Market Distribution:</strong><br />
              <small>Geographic clustering analysis reveals optimal zones
                for pharmacy establishment and expansion</small>
            </div>
            <div>
              <strong>🎯 Strategic Positioning:</strong><br />
              <small>Location optimization based on traffic patterns,
                demographic alignment, and competitive landscape</small>
            </div>
            <div>
              <strong>📈 Growth Opportunities:</strong><br />
              <small>Identified underserved areas with high growth
                potential and minimal competition</small>
            </div>
          </div>
        </div>
      </div>

      <div class="insights" style="margin-top: 30px;">
        <h3 style="margin-bottom: 15px;">💡 Key Investment Insights</h3>
        <ul style="margin-left: 20px; margin-top: 15px; line-height: 1.6;">
          {generate_investment_insights_list(key_investment_insights)}
        </ul>
      </div>
      
      <div class="footer">
        Report generated using advanced geospatial analysis and machine
        learning algorithms
        <br />Analysis covered {processed_report_data.get('summary_metrics', {}).get('total_locations', 0)}
        candidate locations with comprehensive multi-criteria scoring
      </div>
    </div>"""

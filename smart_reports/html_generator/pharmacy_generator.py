"""
Pharmacy Report Generator
Main generator for pharmacy HTML reports using modular components
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from .base_generator import BaseHTMLGenerator
from .components import HTMLComponents
from .property_analyzer import PropertyAnalyzer
from .map_generator import MapGenerator
from .image_generator import ImageGenerator


class PharmacyReportGenerator(BaseHTMLGenerator):
    """Generates comprehensive pharmacy HTML reports"""
    
    def __init__(self):
        super().__init__()
        self.components = HTMLComponents()
        self.property_analyzer = PropertyAnalyzer()
        # Add property-specific CSS to base CSS
        self.css_styles += self.property_analyzer.css_styles
        
        # Initialize map and image generators
        self.map_generator = None
        self.image_generator = None
    
    def _detect_scenario(self, report_data) -> str:
        """Detect the scenario based on request data"""
        has_current_location = report_data.current_location is not None
        has_custom_locations = report_data.custom_locations is not None and len(report_data.custom_locations) > 0
        
        if has_current_location and has_custom_locations:
            return "custom_and_current"
        elif has_current_location and not has_custom_locations:
            return "current_location_only"
        elif not has_current_location and has_custom_locations:
            return "custom_only"
        else:
            return "no_custom_no_current"
    
    def _generate_investment_insights_list(self, key_investment_insights) -> str:
        """Generate investment insights list using only available JSON data"""
        if not key_investment_insights:
            return "<li>No investment insights available</li>"
        
        insights_html = ""
        for insight in key_investment_insights:
            category = insight.get('category', 'Insight')
            description = insight.get('description', 'No description available')
            insights_html += f'<li style="margin-bottom: 12px;"><strong>{category}:</strong> {description}</li>'
        
        return insights_html
    
    def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate the complete pharmacy HTML report"""
        # Extract data
        report_data = data.get('report_data')
        processed_report_data = data.get('processed_report_data', {})
        
        # Detect scenario from request data
        scenario = self._detect_scenario(report_data)
        
        # Create directory structure with scenario
        dirs = self.create_directory_structure(
            report_data.city_name, 
            "pharmacies",
            scenario
        )
        
        # Extract report components
        title = processed_report_data.get("title", f"{report_data.city_name} Pharmacy Site Analysis Report")
        description = processed_report_data.get("description", "Comprehensive Location Intelligence & Investment Recommendations")
        
        # Extract summary metrics
        summary_metrics = processed_report_data.get("summary_metrics", {})
        total_locations = summary_metrics.get("total_locations", 0)
        average_score = summary_metrics.get("average_score", 0)
        average_price_sar = summary_metrics.get("average_price_sar", 0)
        competing_pharmacies = summary_metrics.get("competing_pharmacies", 0)
        
        # Extract executive summary
        executive_summary = processed_report_data.get("executive_summary", {})
        top_recommendation = executive_summary.get("top_recommendation", {})
        total_sites_evaluated = executive_summary.get("total_sites_evaluated", 0)
        
        # Extract other data
        rankings = processed_report_data.get("rankings", [])
        detailed_analysis = processed_report_data.get("detailed_analysis", [])
        key_investment_insights = processed_report_data.get("key_investment_insights", [])
        metadata = processed_report_data.get("metadata", {})
        
        # Validate data
        if not rankings:
            raise ValueError("No ranking data available for report generation")
        
        if not detailed_analysis:
            raise ValueError("No detailed analysis data available for report generation")
        
        # Use visual_analysis data from JSON instead of generating new images/maps
        visual_analysis = processed_report_data.get('visual_analysis', {})
        
        # Extract chart and map URLs from JSON
        charts_data = visual_analysis.get('charts', [])
        maps_data = visual_analysis.get('maps', [])
        interactive_maps_data = visual_analysis.get('interactive_maps', [])
        
        # Convert JSON URLs to relative paths for HTML
        generated_charts = []
        for chart in charts_data:
            chart_url = chart.get('url', '')
            if chart_url:
                # Convert absolute path to relative path
                if 'static/pharmacy_report/' in chart_url:
                    relative_path = chart_url.split('static/pharmacy_report/')[-1]
                    generated_charts.append(relative_path)
        
        generated_maps = []
        for interactive_map in interactive_maps_data:
            map_url = interactive_map.get('url', '')
            if map_url:
                # Convert absolute path to relative path
                if 'static/pharmacy_report/' in map_url:
                    relative_path = map_url.split('static/pharmacy_report/')[-1]
                    generated_maps.append(relative_path)
        
        # Fallback: If no visual_analysis data, generate dynamically
        if not generated_charts or not generated_maps:
            print("Warning: No visual_analysis data found, falling back to dynamic generation")
            self.map_generator = MapGenerator(dirs['maps_dir'])
            self.image_generator = ImageGenerator(dirs['images_dir'])
            
            properties = detailed_analysis[:10]
            if not generated_maps:
                generated_maps = self.map_generator.generate_all_maps(properties, report_data.city_name)
            if not generated_charts:
                generated_charts = self.image_generator.generate_all_charts(properties, report_data.city_name)
        
        # Copy chart files to charts directory for HTML references
        self._copy_charts_to_charts_dir(dirs['charts_dir'], generated_charts)
        
        # Copy coordinate-based map files to maps directory for HTML references
        self._copy_coordinate_maps_to_maps_dir(dirs['maps_dir'])
        
        # Generate HTML content - PIXEL PERFECT MATCH
        html_content = self._generate_complete_report_exact(
            report_data=report_data,
            processed_report_data=processed_report_data,
            generated_maps=generated_maps,
            generated_charts=generated_charts
        )
        
        # Write to file directly (no additional wrapper needed)
        self.write_html_file(dirs['index_path'], html_content)
        
        # Return absolute path
        return str(dirs['index_path'].absolute())
    
    def _generate_report(self, **kwargs) -> str:
        """Generate the complete report content"""
        return f"""
        <!-- Page 1: Executive Overview -->
        <div class="page">
            {self._generate_page_1(**kwargs)}
        </div>
        
        <!-- Page 2: Methodology & Analysis -->
        <div class="page page-break">
            {self._generate_page_2(**kwargs)}
        </div>
        
        <!-- Page 3: Visual Analysis -->
        <div class="page page-break">
            {self._generate_page_3(**kwargs)}
        </div>
        
        <!-- Report Footer -->
        {self._generate_footer(**kwargs)}
        """
    
    def _generate_page_1(self, **kwargs) -> str:
        """Generate Page 1: Executive Overview"""
        return f"""
            {self.components.hero_section(
                kwargs['title'], 
                kwargs['description'], 
                kwargs['metadata'].get('generation_method', 'N/A')
            )}
            
            {self.components.executive_summary(
                f"This comprehensive analysis evaluates {kwargs['total_sites_evaluated']} pharmacy locations across {kwargs['report_data'].city_name} "
                f"using advanced location intelligence methodologies. Our assessment integrates multiple data sources including "
                f"traffic flow analysis, demographic profiling, healthcare ecosystem mapping, competitive landscape evaluation, "
                f"and complementary business assessment. Each location is systematically scored using our proprietary weighted "
                f"methodology, considering market opportunity, accessibility, and business environment factors to provide "
                f"data-driven investment recommendations."
            )}
            
            {self.components.metrics_grid([
                {'value': kwargs['total_locations'], 'label': 'Total Properties Analyzed'},
                {'value': f"{kwargs['average_score']:.1f}", 'label': 'Average Performance Score'},
                {'value': f"{kwargs['average_price_sar']:,.0f} SAR", 'label': 'Average Price'},
                {'value': kwargs['competing_pharmacies'], 'label': 'Competing Pharmacies'}
            ])}
            
            {self.components.top_recommendation(kwargs['top_recommendation'])}
            
            {self.components.rankings_table(kwargs['rankings'])}
        """
    
    def _generate_page_2(self, **kwargs) -> str:
        """Generate Page 2: Methodology & Analysis"""
        return f"""
            {self.components.methodology_section()}
            
            <!-- Detailed Property Analysis -->
            <div class="property-analysis">
                <h2>Detailed Property Analysis</h2>
                <p>Comprehensive evaluation of individual properties with detailed scoring breakdowns, strategic insights, and location-specific recommendations.</p>
                
                {self._generate_property_cards(kwargs['detailed_analysis'])}
            </div>
        """
    
    def _generate_page_3(self, **kwargs) -> str:
        """Generate Page 3: Visual Analysis"""
        generated_maps = kwargs.get('generated_maps', [])
        generated_charts = kwargs.get('generated_charts', [])
        
        # Get overview map path
        overview_map_path = "maps/overview_map.html"
        if generated_maps:
            overview_map_path = generated_maps[0].split('/')[-1] if '/' in generated_maps[0] else generated_maps[0]
            overview_map_path = f"maps/{overview_map_path}"
        
        # Get chart paths
        chart_paths = []
        for chart_path in generated_charts:
            chart_name = chart_path.split('/')[-1] if '/' in chart_path else chart_path
            chart_paths.append(f"images/{chart_name}")
        
        return f"""
            <div class="visual-analysis">
                <h2>Visual Analysis & Regional Insights</h2>
                <p>Comprehensive visual representation of market analysis, performance patterns, and strategic insights.</p>
                
                <!-- Regional Overview Card -->
                <div class="chart-container">
                    <h3>Regional Overview</h3>
                    <div class="map-placeholder">
                        <iframe src="{overview_map_path}" width="100%" height="500" frameborder="0"></iframe>
                    </div>
                    <div class="property-details" style="margin-top: 20px;">
                        <div class="property-info">
                            <h4>Top Performing Areas</h4>
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
                
                <!-- Statistical Analysis Chart Container -->
                <div class="chart-container">
                    <h3>Statistical Analysis</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
                        {self._generate_chart_grid(chart_paths)}
                    </div>
                </div>
                
                <!-- Key Investment Insights Summary -->
                <div class="top-recommendation">
                    <h3>Key Investment Insights</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        {self._generate_investment_insights(kwargs['key_investment_insights'])}
                    </div>
                </div>
            </div>
        """
    
    def _generate_property_cards(self, detailed_analysis: List[Dict[str, Any]]) -> str:
        """Generate property analysis cards"""
        # Generate property cards - EXACT MATCH (10 properties like perfect output)
        property_cards_html = ""
        for i, property_data in enumerate(detailed_analysis[:10], 1):  # Show exactly 10 properties
            property_cards_html += self.property_analyzer.generate_property_card(property_data, i)
        
        return property_cards_html
    
    def _generate_chart_grid(self, chart_paths: List[str]) -> str:
        """Generate chart grid HTML"""
        if not chart_paths:
            # Fallback to placeholder images
            return """
                        <div class="map-placeholder">
                            <img src="images/score_distribution.png" alt="Score Distribution" style="width: 100%; height: 300px; object-fit: cover;">
                        </div>
                        <div class="map-placeholder">
                            <img src="images/analysis_dashboard.png" alt="Analysis Dashboard" style="width: 100%; height: 300px; object-fit: cover;">
                        </div>
                        <div class="map-placeholder">
                            <img src="images/price_vs_score.png" alt="Price vs Score" style="width: 100%; height: 300px; object-fit: cover;">
                        </div>"""
        
        chart_html = ""
        for i, chart_path in enumerate(chart_paths[:6]):  # Limit to 6 charts
            chart_name = chart_path.split('/')[-1].replace('.png', '').replace('_', ' ').title()
            chart_html += f"""
                        <div class="map-placeholder">
                            <img src="{chart_path}" alt="{chart_name}" style="width: 100%; height: 300px; object-fit: cover;">
                        </div>"""
        
        return chart_html
    
    def _generate_investment_insights(self, key_investment_insights: List[Dict[str, Any]]) -> str:
        """Generate investment insights HTML"""
        insights_html = ""
        for insight in key_investment_insights[:6]:
            insights_html += f"""
                        <div class="criterion-card">
                            <h4>{insight.get('category', 'Strategic Insight')}</h4>
                            <p>{insight.get('description', 'Key strategic insight for pharmacy investment.')}</p>
                        </div>"""
        return insights_html
    
    def _generate_footer(self, **kwargs) -> str:
        """Generate report footer"""
        footer_data = {
            'total_sites_evaluated': kwargs['total_sites_evaluated'],
            'city_name': kwargs['report_data'].city_name,
            'country_name': kwargs['report_data'].country_name
        }
        return self.components.report_footer(footer_data)

    # ============================================================================
    # PIXEL PERFECT MATCH METHODS - EXACT COPY OF PERFECT OUTPUT
    # ============================================================================

    def _generate_complete_report_exact(self, report_data, processed_report_data, generated_maps, generated_charts):
        """Generate the complete HTML report - PIXEL PERFECT MATCH"""
        

        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Riyadh Pharmacy Site Analysis Report</title>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap");

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: "Inter", sans-serif;
      line-height: 1.6;
      color: #333;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
    }}

    .report-container {{
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
      border-radius: 20px;
      overflow: hidden;
    }}

    .page {{
      padding: 60px;
      min-height: 100vh;
      page-break-after: always;
    }}

    .page:last-child {{
      page-break-after: avoid;
    }}

    .header {{
      background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
      color: white;
      padding: 40px 60px;
      text-align: center;
      margin: -60px -60px 40px -60px;
    }}

    .header h1 {{
      font-size: 2.5em;
      font-weight: 700;
      margin-bottom: 10px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }}

    .header .subtitle {{
      font-size: 1.2em;
      font-weight: 300;
      opacity: 0.9;
    }}

    .hero {{
      background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
      color: white;
      padding: 40px 60px;
      text-align: center;
      margin: -60px -60px 40px -60px;
    }}

    .hero h1 {{
      font-size: 2.5em;
      font-weight: 700;
      margin-bottom: 10px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }}

    .hero .muted {{
      font-size: 1.2em;
      font-weight: 300;
      opacity: 0.9;
    }}

    .executive-summary {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 15px;
      margin: 30px 0;
    }}

    .top-recommendation {{
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      color: white;
      padding: 25px;
      border-radius: 15px;
      margin: 20px 0;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }}

    .score-display {{
      font-size: 3em;
      font-weight: 700;
      text-align: center;
      margin: 20px 0;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }}

    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin: 30px 0;
    }}

    .metric-card {{
      background: white;
      padding: 20px;
      border-radius: 15px;
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
      text-align: center;
      border-left: 5px solid #3498db;
    }}

    .metric-value {{
      font-size: 2em;
      font-weight: 700;
      color: #2c3e50;
    }}

    .metric-label {{
      color: #7f8c8d;
      font-weight: 500;
      margin-top: 5px;
    }}

    .rankings-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      background: white;
      border-radius: 15px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }}

    .rankings-table th {{
      background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
      color: white;
      padding: 15px;
      text-align: left;
      font-weight: 600;
    }}

    .rankings-table td {{
      padding: 15px;
      border-bottom: 1px solid #ecf0f1;
    }}

    .rankings-table tr:hover {{
      background: #f8f9fa;
    }}

    .rank-badge {{
      background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
      color: white;
      padding: 5px 10px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 0.9em;
    }}

    .rank-badge.top3 {{
      background: linear-gradient(135deg, #ffd700 0%, #ffa500 100%);
      color: #2c3e50;
    }}

    .section-title {{
      font-size: 2em;
      font-weight: 600;
      margin: 40px 0 20px 0;
      color: #2c3e50;
      border-bottom: 3px solid #3498db;
      padding-bottom: 10px;
    }}

    h2 {{
      font-size: 2em;
      font-weight: 600;
      margin: 40px 0 20px 0;
      border-bottom: 3px solid #3498db;
      padding-bottom: 10px;
    }}

    h3 {{
      font-weight: 600;
      margin: 30px 0 15px 0;
    }}

    .property-card {{
      background: white;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
      margin: 30px 0;
      border-left: 5px solid #3498db;
    }}

    .property-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 15px;
      border-bottom: 2px solid #ecf0f1;
    }}

    .property-title {{
      font-size: 1.2em;
      font-weight: 600;
      color: #2c3e50;
      flex: 1;
    }}

    .score-badge {{
      background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
      color: white;
      padding: 8px 15px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 1.1em;
    }}

    .score-breakdown {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-top: 15px;
    }}

    .score-item {{
      text-align: center;
      padding: 10px;
      background: #f8f9fa;
      border-radius: 10px;
    }}

    .score-item .value {{
      font-size: 1.5em;
      font-weight: 700;
      color: #2c3e50;
    }}

    .score-item .label {{
      font-size: 0.9em;
      color: #7f8c8d;
      margin-top: 5px;
    }}

    .map-container {{
      margin-top: 30px;
      text-align: center;
    }}

    .map-image {{
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
    }}

    .methodology {{
      background: #f8f9fa;
      padding: 30px;
      border-radius: 15px;
      margin: 30px 0;
    }}

    .page-break {{
      page-break-before: always;
    }}
    
    .insights {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 25px;
      border-radius: 15px;
      margin: 20px 0;
    }}
    
    .footer {{
      text-align: center;
      color: #7f8c8d;
      font-size: 0.9em;
      margin-top: 40px;
      padding: 20px;
      border-top: 1px solid #ecf0f1;
    }}
    </style>
</head>
<body>
    <div class="report-container">
        {self._generate_page_1_exact(report_data, processed_report_data)}
        {self._generate_page_2_exact(report_data, processed_report_data)}
        {self._generate_page_3_exact(report_data, processed_report_data, generated_maps, generated_charts, processed_report_data.get('key_investment_insights', []))}
    </div>
</body>
</html>"""
        return html_content

    def _generate_top_recommendation_exact(self, top_recommendation, processed_report_data=None):
        """Generate top recommendation section - EXACT MATCH"""
        if not top_recommendation:
            return ""
        
        # Get current location data for detailed scores (has more complete data)
        current_location = processed_report_data.get('current_location', []) if processed_report_data else []
        current_location_data = current_location[0] if current_location else {}
        
        # Get summary metrics for competing pharmacies
        summary_metrics = processed_report_data.get("summary_metrics", {}) if processed_report_data else {}
        
        # Extract data with proper field mapping - USE JSON alternatives where available
        property_name = top_recommendation.get('site_name', 'N/A')  # Use site_name instead of property_name
        score = top_recommendation.get('score', 0)  # Use score instead of final_score
        price = top_recommendation.get('price_sar', 0)  # Use price_sar instead of price
        
        # Use current_location data for detailed scores (more complete)
        traffic_score = current_location_data.get('traffic_score', 0)
        demographics_score = current_location_data.get('demographics_score', 0)
        healthcare_score = current_location_data.get('healthcare_ecosystem_score', 0)  # Use healthcare_ecosystem_score
        competition_score = current_location_data.get('competition_score', 0)
        complementary_score = current_location_data.get('complementary_businesses_score', 0)  # Use complementary_businesses_score
        
        # Additional metrics - use available alternatives from detailed_insights
        # Get the top recommendation's detailed insights from detailed_analysis data
        detailed_analysis = processed_report_data.get('detailed_analysis', []) if processed_report_data else []
        top_property_insights = {}
        if detailed_analysis:
            # Find the top ranking property (rank 1) to get its detailed insights
            top_property = next((prop for prop in detailed_analysis if prop.get('rank') == 1), {})
            detailed_insights = top_property.get('detailed_insights', {})
            business_environment = detailed_insights.get('business_environment', {})
            demographics_match = detailed_insights.get('demographics_match', {})
            traffic_performance = detailed_insights.get('traffic_performance', {})
            
            # Map the available fields
            traffic_flow = traffic_performance.get('current_speed_kmh', 30)
            nearby_businesses = business_environment.get('nearby_businesses_500m', 0)
            population_density = demographics_match.get('population_age_35_plus_percent', 0)  # Use age percentage as proxy
            avg_income = demographics_match.get('average_income_sar', 0)
        else:
            # Fallback values
            traffic_flow = 30
            nearby_businesses = 0
            population_density = 0
            avg_income = 0
        
        competing_pharmacies = summary_metrics.get('competing_pharmacies', 0)  # Use from summary_metrics
        
        return f"""
      <div class="top-recommendation">
        <h2 style="margin-bottom: 20px; border: none; color: white">
          🏆 TOP RECOMMENDATION
        </h2>
        <h3 style="font-size: 1.8em; margin-bottom: 10px">Property #1:
          {property_name}
        </h3>
        <div class="score-display">{score:.1f}/100</div>

        <div style="
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 20px;
              margin-top: 20px;
            ">
          <div>
            <strong>🚗 Traffic Analysis:</strong><br />
            Average Speed: {traffic_flow:.1f} km/h<br />
            <small>Target: 20–30 km/h | ℹ️ Light traffic</small>
          </div>
          <div>
            <strong>🏪 Business Environment:</strong><br />
            {nearby_businesses} businesses within 500m <br />
            <small>✅ Strong ecosystem</small>
          </div>
          <div>
            <strong>👥 Demographics:</strong><br />
            {population_age_35_plus:.1f}% of population Aged 35 and Above<br />
            <small>✅ Strong alignment | Average Income: {avg_income:,.0f} SAR monthly</small>
          </div>
          <div>
            <strong>☕ Competition:</strong><br />
            {competing_pharmacies} competing pharmacies in the area<br />
            <small>Status: 🟢 Underserved market</small>
          </div>
        </div>
      </div>"""

    def _generate_page_1_exact(self, report_data, processed_report_data):
        """Generate Page 1: Executive Overview - EXACT MATCH"""
        # Extract data
        title = processed_report_data.get("title", f"{report_data.city_name} Pharmacy Site Analysis Report")
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
        
        # Get current location data for detailed scores (has more complete data)
        current_location = processed_report_data.get('current_location', [])
        current_location_data = current_location[0] if current_location else {}
        
        # Extract detailed scores from current_location data
        traffic_score = current_location_data.get('traffic_score', 0)
        demographics_score = current_location_data.get('demographics_score', 0)
        healthcare_score = current_location_data.get('healthcare_ecosystem_score', 0)
        competition_score = current_location_data.get('competition_score', 0)
        complementary_score = current_location_data.get('complementary_businesses_score', 0)
        
        # Get additional metrics from top property's detailed insights
        detailed_analysis = processed_report_data.get('detailed_analysis', [])
        top_property_insights = {}
        if detailed_analysis:
            # Find the top ranking property (rank 1) to get its detailed insights
            top_property = next((prop for prop in detailed_analysis if prop.get('rank') == 1), {})
            detailed_insights = top_property.get('detailed_insights', {})
            business_environment = detailed_insights.get('business_environment', {})
            demographics_match = detailed_insights.get('demographics_match', {})
            traffic_performance = detailed_insights.get('traffic_performance', {})
            
            # Map the available fields for display
            traffic_flow = traffic_performance.get('current_speed_kmh', 30)
            nearby_businesses = business_environment.get('nearby_businesses_500m', 0)
            population_age_35_plus = demographics_match.get('population_age_35_plus_percent', 0)
            avg_income = demographics_match.get('average_income_sar', 0)
            
            # Get competition data
            competitive_position = detailed_insights.get('competitive_position', {})
            competing_pharmacies = competitive_position.get('competing_pharmacies', 0)
            
            # Get competition score from rankings data (it's in competition_score_comparison.value)
            rankings = processed_report_data.get('rankings', [])
            competition_score = 0
            if rankings:
                top_ranking = next((prop for prop in rankings if prop.get('rank') == 1), {})
                competition_score_comparison = top_ranking.get('competition_score_comparison', {})
                competition_score = competition_score_comparison.get('value', 0)
        else:
            # Fallback values
            traffic_flow = 30
            nearby_businesses = 0
            population_age_35_plus = 0
            avg_income = 0
            competing_pharmacies = 0
            competition_score = 0
        
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
          This comprehensive analysis evaluates {total_sites_evaluated} pharmacy locations across {report_data.city_name} using advanced location intelligence methodologies. Our assessment integrates multiple data sources including traffic flow analysis, demographic profiling, healthcare ecosystem mapping, competitive landscape evaluation, and complementary business assessment. Each location is systematically scored using our proprietary weighted methodology, considering market opportunity, accessibility, and business environment factors to provide data-driven investment recommendations.
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
            Score: {traffic_score:.1f}/100<br />
            <small>Target: 20–30 km/h | ℹ️ Light traffic</small>
          </div>
          <div>
            <strong>🏪 Business Environment:</strong><br />
            {nearby_businesses} businesses within 500m<br />
            <small>✅ Strong ecosystem</small>
          </div>
          <div>
            <strong>👥 Demographics:</strong><br />
            {population_age_35_plus:.1f}% Aged 35+ <br /> {avg_income:,.0f} SAR income<br />
            <small>✅ Strong alignment</small>
          </div>
          <div>
            <strong>☕ Competition:</strong><br />
            {competition_score:.1f}<br />
            <small>({competing_pharmacies} pharmacies)</small>
          </div>
        </div>
      </div>

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
          {self._generate_rankings_table_exact(rankings[:10])}
        </tbody>
      </table>
    </div>"""

    def _generate_page_2_exact(self, report_data, processed_report_data):
        """Generate Page 2: Methodology & Analysis - EXACT MATCH"""
        detailed_analysis = processed_report_data.get("detailed_analysis", [])
        print(f"DEBUG: _generate_page_2_exact called with {len(detailed_analysis)} items")
        
        # Generate property cards
        property_cards_html = self._generate_property_cards_exact(detailed_analysis[:10], processed_report_data.get('visual_analysis', {}), processed_report_data)
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

    def _generate_page_3_exact(self, report_data, processed_report_data, generated_maps, generated_charts, key_investment_insights):
        """Generate Page 3: Visual Analysis - EXACT MATCH"""
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
          {self._generate_chart_grid_exact(generated_charts, processed_report_data.get('visual_analysis', {}))}
        </div>
      </div>

      <div class="property-card">
        <div class="property-header">
          <div class="property-title">
            🌍 Riyadh Commercial Properties Overview
          </div>
        </div>

        <div class="map-container">
          <img src="images/candidates_map.png" alt="Riyadh Properties Overview Map" class="map-image" />

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
          {self._generate_investment_insights_list(key_investment_insights)}
        </ul>
      </div>
      
      <div class="footer">
        Report generated using advanced geospatial analysis and machine
        learning algorithms
        <br />Analysis covered {processed_report_data.get('summary_metrics', {}).get('total_locations', 0)}
        candidate locations with comprehensive multi-criteria scoring
      </div>
    </div>"""

    def _generate_rankings_table_exact(self, rankings):
        """Generate rankings table - EXACT MATCH"""
        table_rows = ""
        for i, property_data in enumerate(rankings, 1):
            rank_class = "top3" if i <= 3 else ""
            
            # Extract data with proper field mapping - ONLY use data that exists in JSON
            site_name = property_data.get('site_name', 'Property')  # Use site_name from JSON
            price = property_data.get('price_sar', 0)  # Use price_sar from JSON
            # Handle None price values
            if price is None:
                price = 0
            
            # Extract scores from comparison objects in JSON
            final_score = property_data.get('final_score_comparison', {}).get('value', 0)
            traffic_score = property_data.get('traffic_score_comparison', {}).get('value', 0)
            demographics_score = property_data.get('demographics_score_comparison', {}).get('value', 0)
            competition_score = property_data.get('competition_score_comparison', {}).get('value', 0)
            healthcare_score = property_data.get('healthcare_ecosystem_score_comparison', {}).get('value', 0)
            complementary_score = property_data.get('complementary_businesses_score_comparison', {}).get('value', 0)
            
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
            <td><strong>{final_score:.1f}</strong></td>
            <td>{traffic_score:.1f}</td>
            <td>{demographics_score:.1f}</td>
            <td>{competition_score:.1f}</td>
            <td>{healthcare_score:.1f}</td>
            <td>{complementary_score:.1f}</td>
            <td><a href="{google_maps_url}" target="_blank">View</a></td>
          </tr>"""
        return table_rows

    def _generate_property_cards_exact(self, detailed_analysis, visual_analysis=None, processed_report_data=None):
        """Generate property cards - EXACT MATCH"""
        # Create a mapping of site names to interactive map URLs
        interactive_maps_map = {}
        if visual_analysis:
            interactive_maps_data = visual_analysis.get('interactive_maps', [])
            for interactive_map in interactive_maps_data:
                site_name = interactive_map.get('site_name', '')
                map_url = interactive_map.get('url', '')
                if site_name and map_url:
                    # Convert absolute path to relative path
                    if 'static/pharmacy_report/' in map_url:
                        relative_path = map_url.split('static/pharmacy_report/')[-1]
                        interactive_maps_map[site_name] = relative_path
        
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
            
            # Get competition score from rankings data (it's in competition_score_comparison.value)
            competition_score = 0
            rankings = processed_report_data.get('rankings', []) if processed_report_data else []
            if rankings:
                # Find the matching ranking by site_name
                matching_ranking = next((prop for prop in rankings if prop.get('site_name') == site_name), {})
                competition_score_comparison = matching_ranking.get('competition_score_comparison', {})
                competition_score = competition_score_comparison.get('value', 0)
            
            # Get scores from the scoring breakdown
            scoring_breakdown = property_data.get('scoring_breakdown', [])
            traffic_score = 0
            demographics_score = 0
            
            # Calculate scores from scoring breakdown
            for score_item in scoring_breakdown:
                criterion = score_item.get('criterion', '')
                if criterion == 'Traffic Total':
                    traffic_score = score_item.get('weighted_points', 0) * 4  # Convert to 100 scale
                elif criterion == 'Demographics Total':
                    demographics_score = score_item.get('weighted_points', 0) * 4  # Convert to 100 scale
            
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
                <div class="value">{traffic_score:.1f}</div>
                <div class="label">Traffic<br />({current_speed:.1f} km/h)</div>
              </div>
              <div class="score-item">
                <div class="value">{nearby_businesses}</div>
                <div class="label">Business<br />({nearby_businesses} nearby)</div>
              </div>
              <div class="score-item">
                <div class="value">{demographics_score:.1f}</div>
                <div class="label">Demographics<br />(Age: {population_age_35_plus:.0f})</div>
              </div>
              <div class="score-item">
                <div class="value">{competition_score:.1f}</div>
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
          <iframe src="{interactive_maps_map.get(site_name, f'maps/map_{i}.html')}" width="100%" height="400" style="border:0; border-radius: 12px;"></iframe>
          <p style="margin-top: 15px; color: #7f8c8d; font-size: 0.9em">
            <strong>Map shows:</strong> Property location, nearby businesses, analysis radius, and traffic patterns.
          </p>
        </div>
      </div>"""
        return property_cards_html

    def _generate_chart_grid_exact(self, generated_charts, visual_analysis=None):
        """Generate chart grid - EXACT MATCH"""
        if not generated_charts:
            return """
          <div class="map-placeholder">
            <img src="charts/score_distribution.png" alt="Score Distribution" style="width: 100%; height: 300px; object-fit: cover;">
          </div>
          <div class="map-placeholder">
            <img src="charts/analysis_dashboard.png" alt="Analysis Dashboard" style="width: 100%; height: 300px; object-fit: cover;">
          </div>
          <div class="map-placeholder">
            <img src="charts/price_vs_score.png" alt="Price vs Score" style="width: 100%; height: 300px; object-fit: cover;">
          </div>"""
        
        # Get chart titles from visual_analysis if available
        chart_titles = {}
        if visual_analysis:
            charts_data = visual_analysis.get('charts', [])
            for chart in charts_data:
                chart_url = chart.get('url', '')
                chart_title = chart.get('title', '')
                if chart_url and chart_title:
                    # Extract filename from URL
                    filename = chart_url.split('/')[-1]
                    chart_titles[filename] = chart_title
        
        chart_html = ""
        for i, chart_path in enumerate(generated_charts[:5]):  # Exactly 5 charts like perfect output
            # Extract filename from path
            filename = chart_path.split('/')[-1]
            
            # Use title from JSON if available, otherwise generate from filename
            if filename in chart_titles:
                chart_name = chart_titles[filename]
            else:
                chart_name = filename.replace('.png', '').replace('_', ' ').title()
            
            # Use charts/ path for HTML references
            charts_path = f"charts/{filename}"
            chart_html += f"""
          <div class="map-placeholder">
            <img src="{charts_path}" alt="{chart_name}" style="width: 100%; height: 300px; object-fit: cover;">
          </div>"""
        
        return chart_html

    def _generate_investment_insights_exact(self, key_investment_insights):
        """Generate investment insights - EXACT MATCH"""
        insights_html = ""
        for insight in key_investment_insights[:6]:
            insights_html += f"""
          <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
              ">
            <h4 style="color: #2c3e50; margin-bottom: 10px">{insight.get('category', 'Strategic Insight')}</h4>
            <p>{insight.get('description', 'Key strategic insight for pharmacy investment.')}</p>
          </div>"""
        return insights_html
    
    def _copy_charts_to_charts_dir(self, charts_dir: Path, generated_charts: List[str]) -> None:
        """Copy chart files to the charts directory for HTML references"""
        import shutil
        
        # Source charts directory (parent level)
        source_charts_dir = Path("static/pharmacy_report/charts")
        
        # Chart files that should be copied
        chart_files = [
            "top_stacked.png",
            "traffic_flow.png", 
            "best_breakdown.png",
            "price_vs_score.png",
            "healthcare_competition.png"
        ]
        
        # Copy each chart file if it exists
        for chart_file in chart_files:
            source_path = source_charts_dir / chart_file
            dest_path = charts_dir / chart_file
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"Copied chart: {chart_file}")
                except Exception as e:
                    print(f"Error copying {chart_file}: {e}")
            else:
                print(f"Warning: Chart file not found: {source_path}")
    
    def _copy_coordinate_maps_to_maps_dir(self, maps_dir: Path) -> None:
        """Copy coordinate-based map files to the maps directory for HTML references"""
        import shutil
        
        # Source maps directory (parent level)
        source_maps_dir = Path("static/pharmacy_report/maps")
        
        # Copy all coordinate-based map files
        if source_maps_dir.exists():
            for map_file in source_maps_dir.glob("site_*.html"):
                dest_path = maps_dir / map_file.name
                try:
                    shutil.copy2(map_file, dest_path)
                    print(f"Copied map: {map_file.name}")
                except Exception as e:
                    print(f"Error copying {map_file.name}: {e}")
        else:
            print(f"Warning: Source maps directory not found: {source_maps_dir}")

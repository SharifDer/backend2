"""
HTML Charts and Visuals Module for Pharmacy Report Generation
Contains chart and visual component generation functions for pharmacy reports
"""

from typing import Dict, Any, List


def generate_chart_grid(generated_charts: List[str], visual_analysis: Dict[str, Any] = None) -> str:
    """Generate chart grid HTML"""
    if not generated_charts:
        return """
      <div class="map-placeholder">
        <img src="charts/score_distribution.png" alt="Score Distribution" style="width: 100%; height: auto; object-fit: cover;">
      </div>
      <div class="map-placeholder">
        <img src="charts/analysis_dashboard.png" alt="Analysis Dashboard" style="width: 100%; height: auto; object-fit: cover;">
      </div>
      <div class="map-placeholder">
        <img src="charts/price_vs_score.png" alt="Price vs Score" style="width: 100%; height: auto; object-fit: cover;">
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
    for chart_path in generated_charts[:5]:
        # Extract filename from path
        filename = chart_path.split('/')[-1]
        
        # Use title from JSON if available, otherwise generate from filename
        if filename in chart_titles:
            chart_name = chart_titles[filename]
        else:
            chart_name = filename.replace('.png', '').replace('_', ' ').title()
        
        charts_path = f"charts/{filename}"
        chart_html += f"""
      <div class="map-placeholder">
        <img src="{charts_path}" alt="{chart_name}" style="width: 100%; height: 300px; object-fit: cover;">
      </div>"""
    
    return chart_html

def generate_investment_insights_list(key_investment_insights: List[Dict[str, Any]]) -> str:
    """Generate investment insights list using only available JSON data"""
    if not key_investment_insights:
        return "<li>No investment insights available</li>"
    
    insights_html = ""
    for insight in key_investment_insights:
        category = insight.get('category', 'Insight')
        description = insight.get('description', 'No description available')
        insights_html += f'<li style="margin-bottom: 12px;"><strong>{category}:</strong> {description}</li>'
    
    return insights_html

def generate_investment_insights_cards(key_investment_insights: List[Dict[str, Any]]) -> str:
    """Generate investment insights as cards"""
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

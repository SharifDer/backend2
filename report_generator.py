import os
import uuid
import folium
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from plot_generator import create_scatter_plots_html

logger = logging.getLogger(__name__)

def create_property_map(property_data: Dict[str, Any], businesses: List[Dict[str, Any]], 
                       traffic_details: List[Dict[str, Any]], analysis_radius: int) -> folium.Map:
    """Create detailed map for a property"""
    
    # Create map centered on property
    m = folium.Map(
        location=[property_data['lat'], property_data['lng']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    
    # Property marker (red star)
    folium.Marker(
        [property_data['lat'], property_data['lng']],
        popup=folium.Popup(f"""
        <div style='width: 250px'>
            <h4>🏢 {property_data['name']}</h4>
            <b>Final Score:</b> {property_data.get('final_score', 0):.1f}/100<br>
            <b>Price:</b> {property_data.get('price', 0):,} SAR<br>
            <b>Demographics:</b> Age {property_data.get('median_age', 30)}, Income {property_data.get('income', 15000):,.0f} SAR
        </div>
        """, max_width=300),
        tooltip=f"{property_data['name']} - Score: {property_data.get('final_score', 0):.1f}",
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(m)
    
    # Analysis radius circle
    folium.Circle(
        [property_data['lat'], property_data['lng']],
        radius=analysis_radius,
        color='red',
        weight=2,
        fill=False,
        opacity=0.6,
        popup=f"Analysis radius: {analysis_radius}m"
    ).add_to(m)
    
    # Business markers
    business_colors = {
        'restaurant': 'orange', 'hotel': 'blue', 'bank': 'gray',
        'shopping': 'purple', 'clothing': 'pink', 'coffee': 'brown',
        'cafe': 'brown', 'office': 'lightgray', 'other': 'green'
    }
    
    competitor_markers = []
    
    for poi in businesses:
        poi_lat = poi["position"]["lat"]
        poi_lng = poi["position"]["lon"]
        poi_name = poi["poi"]["name"]
        poi_categories = poi["poi"].get("categories", ["other"])
        
        # Determine marker color based on category
        color = 'green'  # default
        for cat in poi_categories:
            cat_lower = cat.lower()
            if any(word in cat_lower for word in ['restaurant', 'fast_food']):
                color = business_colors['restaurant']
            elif 'hotel' in cat_lower:
                color = business_colors['hotel']
            elif 'bank' in cat_lower:
                color = business_colors['bank']
            elif any(word in cat_lower for word in ['shopping', 'mall', 'store']):
                color = business_colors['shopping']
            elif 'clothing' in cat_lower:
                color = business_colors['clothing']
            elif any(word in cat_lower for word in ['coffee', 'cafe']):
                color = business_colors['coffee']
                competitor_markers.append(poi)
            elif 'office' in cat_lower:
                color = business_colors['office']
            break
        
        folium.CircleMarker(
            location=[poi_lat, poi_lng],
            radius=8 if color == 'brown' else 4,
            popup=folium.Popup(f"""
            <b>{poi_name}</b><br>
            Category: {', '.join(poi_categories)}<br>
            Distance: {poi.get('dist', 0):.0f}m
            """, max_width=200),
            tooltip=f"{poi_name}",
            color=color,
            fill=True,
            opacity=0.8,
            weight=2 if color == 'brown' else 1
        ).add_to(m)
    
    # Add traffic information if available
    for traffic in traffic_details:
        folium.CircleMarker(
            location=[property_data['lat'] + random.uniform(-0.005, 0.005), 
                     property_data['lng'] + random.uniform(-0.005, 0.005)],
            radius=3,
            popup=f"Traffic: {traffic['speed']:.1f} km/h on {traffic['description']}",
            color='darkred',
            fill=True
        ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 10px; left: 10px; width: 220px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:10px; padding: 10px">
    
    <h4>📍 {property_data['name']}</h4>
    <p><b>Final Score:</b> {property_data.get('final_score', 0):.1f}/100</p>
    <p><b>Competitors:</b> {len(competitor_markers)} locations</p>
    <p><b>Businesses:</b> {len(businesses)} total</p>
    
    <p><b>Legend:</b></p>
    <p>🏢 <span style="color: red;">Red Star</span> = Property</p>
    <p>☕ <span style="color: brown;">Brown</span> = Cafes/Coffee</p>
    <p>🍽️ <span style="color: orange;">Orange</span> = Restaurants</p>
    <p>🏪 <span style="color: purple;">Purple</span> = Shopping</p>
    <p>🏨 <span style="color: blue;">Blue</span> = Hotels</p>
    <p>🏦 <span style="color: gray;">Gray</span> = Banks</p>
    <p>🚗 <span style="color: darkred;">Dark Red</span> = Traffic</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_overview_map(results: List[Dict[str, Any]]) -> folium.Map:
    """Create overview map showing all properties"""
    lats = [r['lat'] for r in results]
    lngs = [r['lng'] for r in results]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    for result in results:
        if result['final_score'] >= 80:
            color = 'green'
            icon = 'star'
        elif result['final_score'] >= 60:
            color = 'orange'
            icon = 'home'
        else:
            color = 'red'
            icon = 'exclamation'
        
        folium.Marker(
            [result['lat'], result['lng']],
            popup=folium.Popup(f"""
            <div style='width: 250px'>
                <h4>#{result['rank']} Property {result['rank']}</h4>
                <b>Score:</b> {result['final_score']:.1f}/100<br>
                <b>Price:</b> {result['price']:,} SAR<br>
                <b>Businesses:</b> {result['business_count']}<br>
                <b>Competitors:</b> {result['competitor_count']} locations<br>
                <b>Traffic:</b> {result['avg_road_speed']:.1f} km/h
            </div>
            """, max_width=300),
            tooltip=f"#{result['rank']} - Score: {result['final_score']:.1f}",
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)
    
    # Add demographic areas (sample visualization)
    demo_areas = [
        {'center': [24.7300, 46.6800], 'name': 'Area_A', 'age': 28, 'income': 22000, 'color': '#FF6B6B'},
        {'center': [24.7450, 46.6300], 'name': 'Area_C', 'age': 32, 'income': 18000, 'color': '#4ECDC4'},
        {'center': [24.6900, 46.7200], 'name': 'Area_D', 'age': 35, 'income': 15000, 'color': '#45B7D1'},
        {'center': [24.6500, 46.6200], 'name': 'Area_E', 'age': 26, 'income': 25000, 'color': '#96CEB4'},
        {'center': [24.6800, 46.6100], 'name': 'Area_F', 'age': 33, 'income': 27000, 'color': '#FFEAA7'},
    ]
    
    for area in demo_areas:
        folium.Circle(
            area['center'],
            radius=2000,
            popup=f"<b>{area['name']}</b><br>Age: {area['age']}<br>Income: {area['income']:,} SAR",
            color=area['color'],
            fill=True,
            opacity=0.3,
            weight=2
        ).add_to(m)
    
    # Add overview legend
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 280px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:11px; padding: 15px">
    
    <h4>🗺️ Properties Overview</h4>
    
    <p><b>Property Performance:</b></p>
    <p>⭐ <span style="color: green;">Green Star</span> = Excellent (80-100)</p>
    <p>🏠 <span style="color: orange;">Orange Home</span> = Good (60-79)</p>
    <p>❗ <span style="color: red;">Red Alert</span> = Needs Improvement (<60)</p>
    
    <p><b>Demographics Areas:</b></p>
    <p>🔴 <span style="color: #FF6B6B;">Area_A</span> - Young, High Income</p>
    <p>🔵 <span style="color: #4ECDC4;">Area_C</span> - Mixed Demographics</p>
    <p>🟢 <span style="color: #45B7D1;">Area_D</span> - Mature, Moderate Income</p>
    <p>🟡 <span style="color: #96CEB4;">Area_E</span> - Young, Premium</p>
    <p>🟠 <span style="color: #FFEAA7;">Area_F</span> - Affluent</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

async def generate_complete_html_report(results: List[Dict[str, Any]], 
                                      overview_screenshot_base64: Optional[str], 
                                      request_params: Dict[str, Any]) -> str:
    """Generate comprehensive HTML report"""
    
    os.makedirs("static/reports", exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"dine_in_analysis_{request_params['dine_in_type']}_{timestamp}_{str(uuid.uuid4())[:8]}.html"
    
    top_10 = results[:10]
    top_choice = results[0] if results else {}
    report_date = datetime.now().strftime("%B %d, %Y")
    
    # Calculate summary statistics
    import numpy as np
    avg_score = np.mean([r['final_score'] for r in results]) if results else 0
    avg_price = np.mean([r['price'] for r in results]) if results else 0
    total_competitors = sum(r['competitor_count'] for r in results)
    
    scatter_plots_html = create_scatter_plots_html(results)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dine-In Suitability Analysis Report - {request_params['dine_in_type'].replace('_', ' ').title()}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .report-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
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
            background: linear-gradient(135deg, #2C3E50 0%, #3498DB 100%);
            color: white;
            padding: 40px 60px;
            text-align: center;
            margin: -60px -60px 40px -60px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
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
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .score-display {{
            font-size: 3em;
            font-weight: 700;
            text-align: center;
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 5px solid #3498DB;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            color: #2C3E50;
        }}
        
        .metric-label {{
            color: #7F8C8D;
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
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .rankings-table th {{
            background: linear-gradient(135deg, #2C3E50 0%, #3498DB 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .rankings-table td {{
            padding: 15px;
            border-bottom: 1px solid #ECF0F1;
        }}
        
        .rankings-table tr:hover {{
            background: #F8F9FA;
        }}
        
        .rank-badge {{
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .rank-badge.top3 {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #2C3E50;
        }}
        
        .section-title {{
            font-size: 2em;
            font-weight: 600;
            margin: 40px 0 20px 0;
            color: #2C3E50;
            border-bottom: 3px solid #3498DB;
            padding-bottom: 10px;
        }}
        
        .property-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #3498DB;
        }}
        
        .property-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .property-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #2C3E50;
        }}
        
        .score-badge {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        .score-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .score-item {{
            text-align: center;
            padding: 15px;
            background: #F8F9FA;
            border-radius: 10px;
        }}
        
        .score-item .value {{
            font-size: 1.5em;
            font-weight: 600;
            color: #2C3E50;
        }}
        
        .score-item .label {{
            font-size: 0.9em;
            color: #7F8C8D;
            margin-top: 5px;
        }}
        
        .map-container {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: #F8F9FA;
            border-radius: 15px;
        }}
        
        .map-image {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .insights {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
        }}
        
        .methodology {{
            background: #F8F9FA;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        .footer {{
            text-align: center;
            color: #7F8C8D;
            font-size: 0.9em;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ECF0F1;
        }}
        
        @media print {{
            .report-container {{
                box-shadow: none;
                border-radius: 0;
            }}
            
            .page {{
                min-height: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        
        <div class="page">
            <div class="header">
                <h1>🏢 Dine-In Suitability Analysis Report</h1>
                <div class="subtitle">Comprehensive Location Intelligence & Investment Recommendations</div>
                <div style="margin-top: 20px; font-size: 0.9em;">Generated on {report_date}</div>
            </div>
            
            <div class="executive-summary">
                <h2 style="margin-bottom: 20px;">📊 Executive Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{len(results)}</div>
                        <div class="metric-label">Properties Analyzed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{avg_score:.1f}</div>
                        <div class="metric-label">Average Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{avg_price:,.0f}</div>
                        <div class="metric-label">Average Price (SAR)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_competitors}</div>
                        <div class="metric-label">Competing Locations</div>
                    </div>
                </div>
            </div>
            
            <div class="top-recommendation">
                <h2 style="margin-bottom: 20px;">🏆 TOP RECOMMENDATION</h2>
                <h3 style="font-size: 1.8em; margin-bottom: 10px;">Property #{top_choice.get('rank', 1)}</h3>
                <div class="score-display">{top_choice.get('final_score', 0):.1f}/100</div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
                    <div>
                        <strong>📍 Location:</strong><br>
                        <a href="{top_choice.get('url', '#')}" target="_blank" style="color: white; text-decoration: underline;">View Property</a><br>
                        <small>Price: {top_choice.get('price', 0):,} SAR</small>
                    </div>
                    <div>
                        <strong>🎯 Key Metrics:</strong><br>
                        Traffic: {top_choice.get('traffic_score', 0):.1f}/100<br>
                        Business: {top_choice.get('business_score', 0):.1f}/100
                    </div>
                    <div>
                        <strong>👥 Demographics:</strong><br>
                        Age: {top_choice.get('median_age', 30):.0f} years<br>
                        Income: {top_choice.get('income', 15000):,.0f} SAR
                    </div>
                    <div>
                        <strong>☕ Competition:</strong><br>
                        {top_choice.get('competitor_count', 0)} competing locations<br>
                        Score: {top_choice.get('competition_score', 0):.1f}/100
                    </div>
                </div>
            </div>
            
            <h2 class="section-title">📈 Top 10 Rankings</h2>
            <table class="rankings-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Property ID</th>
                        <th>Price (SAR)</th>
                        <th>Final Score</th>
                        <th>Traffic</th>
                        <th>Business</th>
                        <th>Demographics</th>
                        <th>Competition</th>
                        <th>View</th>
                    </tr>
                </thead>
                <tbody>"""

    for result in top_10:
        rank_class = "top3" if result['rank'] <= 3 else ""
        html_content += f"""
                    <tr>
                        <td><span class="rank-badge {rank_class}">#{result['rank']}</span></td>
                        <td><strong>Property {result['rank']}</strong></td>
                        <td>{result['price']:,}</td>
                        <td><strong>{result['final_score']:.1f}</strong></td>
                        <td>{result['traffic_score']:.1f}</td>
                        <td>{result['business_score']:.1f}</td>
                        <td>{result['demographics_score']:.1f}</td>
                        <td>{result['competition_score']:.1f}</td>
                        <td><a href="{result['url']}" target="_blank" style="color: #3498DB; text-decoration: none;">View</a></td>
                    </tr>"""

    html_content += f"""
                </tbody>
            </table>
            
            <div class="insights">
                <h3>💡 Key Investment Insights</h3>
                <ul style="margin-left: 20px; margin-top: 15px;">
                    <li><strong>Prime Opportunity:</strong> Property #{top_choice.get('rank', 1)} emerges as the clear market leader with exceptional potential</li>
                    <li><strong>Market Dynamics:</strong> {"Favorable competitive environment" if top_choice.get('competitor_count', 0) <= request_params.get('max_competitors', 3) else "Competitive market requires differentiation"} with {top_choice.get('competitor_count', 0)} existing competitors</li>
                    <li><strong>Traffic Advantage:</strong> Optimal accessibility with {top_choice.get('avg_road_speed', 20):.1f} km/h average speeds</li>
                    <li><strong>Business Ecosystem:</strong> Strong commercial environment with {top_choice.get('business_count', 0)} nearby businesses</li>
                    <li><strong>Demographic Alignment:</strong> Target market compatibility with {abs(top_choice.get('age_difference', 0)):.1f} years age deviation</li>
                </ul>
            </div>
        </div>
        
        <div class="page page-break">
            <h1 class="section-title">🔍 Detailed Site Analysis</h1>"""

    # Add detailed analysis for top 5 properties
    for i, result in enumerate(top_10[:5]):
        html_content += f"""
            <div class="property-card">
                <div class="property-header">
                    <div class="property-title">#{result['rank']} Property {result['rank']}</div>
                    <div class="score-badge">{result['final_score']:.1f}/100</div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
                    <div>
                        <h4 style="color: #2C3E50; margin-bottom: 10px;">📍 Property Details</h4>
                        <p><strong>Price:</strong> {result['price']:,} SAR</p>
                        <p><strong>Category:</strong> {result['category'].replace('_', ' ').title()}</p>
                        <p><strong>Listing:</strong> <a href="{result['url']}" target="_blank" style="color: #3498DB;">View Property</a></p>
                    </div>
                    
                    <div>
                        <h4 style="color: #2C3E50; margin-bottom: 10px;">🎯 Performance Metrics</h4>
                        <div class="score-breakdown">
                            <div class="score-item">
                                <div class="value">{result['traffic_score']:.1f}</div>
                                <div class="label">Traffic<br>({result['avg_road_speed']:.1f} km/h)</div>
                            </div>
                            <div class="score-item">
                                <div class="value">{result['business_score']:.1f}</div>
                                <div class="label">Business<br>({result['business_count']} nearby)</div>
                            </div>
                            <div class="score-item">
                                <div class="value">{result['demographics_score']:.1f}</div>
                                <div class="label">Demographics<br>(Age: {result['median_age']:.0f})</div>
                            </div>
                            <div class="score-item">
                                <div class="value">{result['competition_score']:.1f}</div>
                                <div class="label">Competition<br>({result['competitor_count']} competitors)</div>
                            </div>
                        </div>
                    </div>
                </div>"""
        
        if result.get('screenshot_base64'):
            html_content += f"""
                <div class="map-container">
                    <h4 style="color: #2C3E50; margin-bottom: 15px;">📍 Site Location Map</h4>
                    <img src="data:image/png;base64,{result['screenshot_base64']}" 
                         alt="Property {result['rank']} Location Map" 
                         class="map-image">
                </div>"""
        
        html_content += """
            </div>"""

    html_content += f"""
        </div>
        
        <div class="page page-break">
            <h1 class="section-title">🗺️ Visual Analysis & Regional Overview</h1>"""

    if overview_screenshot_base64:
        html_content += f"""
            <div class="property-card">
                <div class="property-header">
                    <div class="property-title">🌍 Regional Properties Overview</div>
                </div>
                
                <div class="map-container">
                    <img src="data:image/png;base64,{overview_screenshot_base64}" 
                         alt="Regional Properties Overview Map" 
                         class="map-image">
                </div>
            </div>"""

    html_content += f"""
            <div class="chart-container">
                <h3 style="color: #2C3E50; margin-bottom: 15px;">📊 Statistical Analysis</h3>
                {scatter_plots_html}
            </div>
            
            <div class="insights">
                <h3>💡 Strategic Recommendations</h3>
                <div style="margin-top: 15px;">
                    <h4>🎯 Investment Strategy</h4>
                    <ul style="margin-left: 20px; margin-bottom: 15px;">
                        <li><strong>Priority Investment:</strong> Focus on top 3 ranked properties for maximum ROI potential</li>
                        <li><strong>Portfolio Approach:</strong> Consider securing multiple high-scoring properties across different areas</li>
                        <li><strong>Market Timing:</strong> Properties in emerging areas offer first-mover advantages</li>
                    </ul>
                    
                    <h4>⚠️ Risk Mitigation</h4>
                    <ul style="margin-left: 20px;">
                        <li><strong>Market Validation:</strong> Conduct customer surveys in target demographics before final selection</li>
                        <li><strong>Competition Monitoring:</strong> Establish early warning systems for new {request_params['dine_in_type'].replace('_', ' ')} openings</li>
                        <li><strong>Lease Flexibility:</strong> Negotiate performance-based rent adjustments where applicable</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Report generated using advanced geospatial analysis | {report_date}
            <br>Analysis covered {len(results)} properties with comprehensive scoring across 4 key criteria
        </div>
    </div>
</body>
</html>
"""
    
    filepath = os.path.join("static/reports", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated: {filename}")
    return filename
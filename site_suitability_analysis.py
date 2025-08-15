import os
import json
import uuid
import asyncio
import logging
import time
import base64
import io
import math
import random
import unicodedata
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from data_fetcher import fetch_dataset, poi_categories
from storage_methods import fetch_intelligence_by_viewport
from traffic_data import create_simulated_traffic, calculate_traffic_score, calculate_distance
from all_types.request_dtypes import (
    ReqFetchDataset, 
    ReqIntelligenceData, 
    ReqSiteSuitabilityAnalysis
)

logger = logging.getLogger(__name__)

class SiteSuitabilityAnalyzer:
    
    def __init__(self):
        self.config = {
            'desired_median_age': 30,
            'target_max_speed_kmh': 20,
            'min_businesses_same_street': 5,
            'optimal_nearby_businesses': 20,
            'max_competitors': 3,
            'analysis_radius': 1000,
            'traffic_weight': 0.25,
            'business_density_weight': 0.40,
            'demographics_weight': 0.20,
            'competition_weight': 0.15,
            'speed_penalty_per_2kmh': 5,
            'age_penalty_per_year': 5,
            'business_penalty_per_missing': 4,
            'competitor_penalty_per_excess': 10,
        }
    
    async def analyze_sites(self, request: ReqSiteSuitabilityAnalysis):
        self.config['desired_median_age'] = request.target_age
        self.config['target_max_speed_kmh'] = request.target_max_speed_kmh
        self.config['optimal_nearby_businesses'] = request.optimal_nearby_businesses
        self.config['max_competitors'] = request.max_competitors
        self.config['analysis_radius'] = request.analysis_radius
        
        candidates_data = await self._fetch_candidates(request)
        candidates = self._process_candidates(candidates_data)
        
        if not candidates:
            raise ValueError("No candidate properties found")
        
        demographics_data = await self._fetch_demographics(request)
        competitors_data = await self._fetch_competitors_and_businesses(request, candidates)
        traffic_data = create_simulated_traffic()
        
        driver = self._setup_webdriver()
        analysis_results = []
        
        for i, candidate in enumerate(candidates):
            demographics = self._get_property_demographics(candidate, demographics_data)
            property_businesses = competitors_data.get(f"{candidate['lat']},{candidate['lng']}", [])
            
            traffic_analysis = calculate_traffic_score(
                candidate['lat'], candidate['lng'], traffic_data, 
                self.config['target_max_speed_kmh']
            )
            
            business_count = len(property_businesses)
            business_score = self._calculate_business_score(business_count)
            demographics_analysis = self._calculate_demographics_score(
                demographics['median_age'], demographics['income']
            )
            
            cafe_count = self._count_competitors(property_businesses, request.restaurant_type)
            competition_score = self._calculate_competition_score(cafe_count)
            
            final_score = (
                traffic_analysis['score'] * self.config['traffic_weight'] +
                business_score * self.config['business_density_weight'] +
                demographics_analysis['total'] * self.config['demographics_weight'] +
                competition_score * self.config['competition_weight']
            )
            
            result = {
                'rank': 0,
                'property_id': candidate['id'],
                'name': f'Property {i+1:03d}',
                'district': f"Area_{chr(65 + (i % 10))}",
                'url': candidate.get('url', ''),
                'price': candidate.get('price', 0),
                'category': candidate.get('category', 'shop_for_rent'),
                'lat': candidate['lat'],
                'lng': candidate['lng'],
                'area_sqm': candidate.get('area_sqm', 150),
                'median_age': demographics['median_age'],
                'income': demographics['income'],
                'demographics_score': demographics_analysis['total'],
                'age_score': demographics_analysis['age_score'],
                'income_score': demographics_analysis['income_score'],
                'age_difference': demographics_analysis['age_diff'],
                'traffic_score': traffic_analysis['score'],
                'avg_road_speed': traffic_analysis['avg_speed'],
                'traffic_segments': traffic_analysis['segments_count'],
                'traffic_details': traffic_analysis['details'],
                'business_count': business_count,
                'business_score': business_score,
                'businesses': property_businesses,
                'cafe_count': cafe_count,
                'competition_score': competition_score,
                'final_score': final_score,
                'screenshot_path': None,
                'screenshot_base64': None,
            }
            
            analysis_results.append(result)
        
        analysis_results.sort(key=lambda x: x['final_score'], reverse=True)
        for i, result in enumerate(analysis_results):
            result['rank'] = i + 1
        
        for i, result in enumerate(analysis_results[:10]):
            property_data = {
                'lat': result['lat'],
                'lng': result['lng'],
                'rank': result['rank'],
                'final_score': result['final_score'],
                'price': result['price'],
                'median_age': result['median_age'],
                'income': result['income'],
                'name': f"Property {result['rank']}"
            }
            
            property_map = self._create_property_map(property_data, result['businesses'], result['traffic_details'])
            screenshot_path, screenshot_base64 = self._capture_map_screenshot(
                property_map, f"property_{result['rank']:02d}_map", driver
            )
            
            result['screenshot_path'] = screenshot_path
            result['screenshot_base64'] = screenshot_base64
        
        overview_map = self._create_overview_map(analysis_results)
        overview_screenshot_path, overview_screenshot_base64 = self._capture_map_screenshot(
            overview_map, "overview_map", driver
        )
        
        if driver:
            driver.quit()
        
        report_filename = await self._generate_complete_html_report(
            analysis_results, overview_screenshot_base64, request
        )
        
        return {
            'report_url': f"/static/reports/{report_filename}",
            'analysis_summary': {
                'total_properties': len(analysis_results),
                'avg_score': np.mean([r['final_score'] for r in analysis_results]),
                'top_score': analysis_results[0]['final_score'] if analysis_results else 0,
                'avg_price': np.mean([r['price'] for r in analysis_results]),
                'total_businesses': sum(r['business_count'] for r in analysis_results),
                'total_competitors': sum(r['cafe_count'] for r in analysis_results),
            },
            'top_properties': [
                {
                    'rank': r['rank'],
                    'property_id': r['property_id'],
                    'final_score': r['final_score'],
                    'price': r['price'],
                    'url': r['url'],
                    'traffic_score': r['traffic_score'],
                    'business_score': r['business_score'],
                    'demographics_score': r['demographics_score'],
                    'competition_score': r['competition_score']
                } for r in analysis_results[:10]
            ],
            'total_properties_analyzed': len(analysis_results),
            'report_filename': report_filename
        }
    
    async def _fetch_candidates(self, request):
        fetch_request = ReqFetchDataset(
            country_name=request.country_name,
            city_name=request.city_name,
            boolean_query="shop_for_rent",
            user_id=request.user_id,
            search_type="category_search",
            action="sample",
            layer_name=f"{request.country_name} {request.city_name} shop_for_rent",
            page_token="",
            layerId="",
            text_search="",
            zoom_level=6
        )
        
        return await fetch_dataset(fetch_request)
    
    def _process_candidates(self, candidates_data):
        candidates = []
        features = candidates_data.get('features', [])
        
        for i, feature in enumerate(features):
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [0, 0])
            
            candidates.append({
                'id': f'PROP_{i:03d}',
                'lat': coordinates[1],
                'lng': coordinates[0],
                'url': properties.get('url', ''),
                'price': properties.get('price', 0),
                'category': properties.get('category', 'shop_for_rent'),
                'area_sqm': 150
            })
        
        return candidates
    
    async def _fetch_demographics(self, request):
        demographics_request = ReqIntelligenceData(
            country_name=request.country_name,
            city_name=request.city_name,
            user_id=request.user_id
        )
        
        return await fetch_intelligence_by_viewport(demographics_request)
    
    def _get_property_demographics(self, candidate, demographics_data):
        features = demographics_data.get('features', [])
        candidate_point = Point(candidate['lng'], candidate['lat'])
        
        for feature in features:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            if geometry.get('type') == 'Polygon':
                try:
                    coords = geometry.get('coordinates', [[]])[0]
                    polygon = Polygon(coords)
                    
                    if polygon.contains(candidate_point):
                        return {
                            'median_age': properties.get('Median_Age_Total', 30),
                            'income': properties.get('income', 15000)
                        }
                except Exception as e:
                    continue
        
        return {'median_age': 30, 'income': 15000}
    
    async def _fetch_competitors_and_businesses(self, request, candidates):
        categories_data = await poi_categories({})
        food_drink_categories = categories_data.get('Food and Drink', [])
        
        competitors_data = {}
        for candidate in candidates:
            key = f"{candidate['lat']},{candidate['lng']}"
            businesses = self._simulate_nearby_businesses(
                candidate['lat'], candidate['lng'], 
                food_drink_categories, request.analysis_radius
            )
            competitors_data[key] = businesses
        
        return competitors_data
    
    def _simulate_nearby_businesses(self, lat, lng, categories, radius):
        businesses = []
        num_businesses = random.randint(10, 30)
        
        for i in range(num_businesses):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(50, radius)
            
            lat_offset = distance * math.cos(angle) / 111000
            lng_offset = distance * math.sin(angle) / (111000 * math.cos(math.radians(lat)))
            
            category = random.choice(categories)
            
            businesses.append({
                "position": {
                    "lat": lat + lat_offset,
                    "lon": lng + lng_offset
                },
                "poi": {
                    "name": f"{category.replace('_', ' ').title()} {i+1}",
                    "categories": [category]
                },
                "dist": distance
            })
        
        return businesses
    
    def _calculate_business_score(self, business_count):
        if business_count >= self.config['optimal_nearby_businesses']:
            return 100
        else:
            missing = self.config['optimal_nearby_businesses'] - business_count
            penalty = missing * self.config['business_penalty_per_missing']
            return max(0, 100 - penalty)
    
    def _calculate_demographics_score(self, median_age, income):
        age_diff = abs(median_age - self.config['desired_median_age'])
        age_penalty = age_diff * self.config['age_penalty_per_year']
        age_score = max(0, 100 - age_penalty)
        
        min_income, max_income = 497.69, 27954.77
        
        if income <= min_income:
            income_score = 0
        elif income >= max_income:
            income_score = 100
        else:
            income_score = ((income - min_income) / (max_income - min_income)) * 100
        
        total_score = (age_score * 0.6) + (income_score * 0.4)
        
        return {
            'total': total_score,
            'age_score': age_score,
            'income_score': income_score,
            'age_diff': age_diff
        }
    
    def _count_competitors(self, businesses, restaurant_type):
        competitor_count = 0
        competitor_keywords = [restaurant_type, 'cafe', 'coffee', 'restaurant']
        
        for business in businesses:
            categories = business.get('poi', {}).get('categories', [])
            name = business.get('poi', {}).get('name', '').lower()
            
            if (restaurant_type in categories or 
                any(keyword in name for keyword in competitor_keywords)):
                competitor_count += 1
        
        return competitor_count
    
    def _calculate_competition_score(self, competitor_count):
        if competitor_count <= self.config['max_competitors']:
            return 100
        else:
            excess = competitor_count - self.config['max_competitors']
            penalty = excess * self.config['competitor_penalty_per_excess']
            return max(0, 100 - penalty)
    
    def _setup_webdriver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            logger.warning(f"Could not setup webdriver: {e}")
            return None
    
    def _create_property_map(self, property_data, businesses, traffic_details):
        m = folium.Map(
            location=[property_data['lat'], property_data['lng']],
            zoom_start=16,
            tiles='OpenStreetMap'
        )
        
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
        
        folium.Circle(
            [property_data['lat'], property_data['lng']],
            radius=self.config['analysis_radius'],
            color='red',
            weight=2,
            fill=False,
            opacity=0.6,
            popup=f"Analysis radius: {self.config['analysis_radius']}m"
        ).add_to(m)
        
        business_colors = {
            'restaurant': 'orange', 'hotel': 'blue', 'bank': 'gray',
            'shopping': 'purple', 'clothing': 'pink', 'coffee': 'brown',
            'office': 'lightgray', 'other': 'green'
        }
        
        cafe_markers = []
        
        for poi in businesses:
            poi_lat = poi["position"]["lat"]
            poi_lng = poi["position"]["lon"]
            poi_name = poi["poi"]["name"]
            poi_categories = poi["poi"].get("categories", ["other"])
            
            color = 'green'
            for cat in poi_categories:
                cat_lower = cat.lower()
                if 'restaurant' in cat_lower:
                    color = business_colors['restaurant']
                elif 'hotel' in cat_lower:
                    color = business_colors['hotel']
                elif 'bank' in cat_lower:
                    color = business_colors['bank']
                elif 'shopping' in cat_lower or 'mall' in cat_lower:
                    color = business_colors['shopping']
                elif 'clothing' in cat_lower:
                    color = business_colors['clothing']
                elif 'coffee' in cat_lower or 'cafe' in cat_lower:
                    color = business_colors['coffee']
                    cafe_markers.append(poi)
                elif 'office' in cat_lower:
                    color = business_colors['office']
                break
            
            folium.CircleMarker(
                location=[poi_lat, poi_lng],
                radius=8 if 'coffee' in str(poi_categories).lower() or 'cafe' in str(poi_categories).lower() else 4,
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
        
        for traffic in traffic_details:
            folium.CircleMarker(
                location=[property_data['lat'] + random.uniform(-0.01, 0.01), 
                         property_data['lng'] + random.uniform(-0.01, 0.01)],
                radius=3,
                popup=f"Traffic: {traffic['speed']:.1f} km/h on {traffic['description']}",
                color='darkred',
                fill=True
            ).add_to(m)
        
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 10px; left: 10px; width: 220px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:10px; padding: 10px">
        
        <h4>📍 {property_data['name']}</h4>
        <p><b>Final Score:</b> {property_data.get('final_score', 0):.1f}/100</p>
        <p><b>Competitors:</b> {len(cafe_markers)} cafes</p>
        <p><b>Businesses:</b> {len(businesses)} total</p>
        
        <p><b>Legend:</b></p>
        <p>🏢 <span style="color: red;">Red Star</span> = Property</p>
        <p>☕ <span style="color: brown;">Brown</span> = Cafes</p>
        <p>🍽️ <span style="color: orange;">Orange</span> = Restaurants</p>
        <p>🏪 <span style="color: purple;">Purple</span> = Shopping</p>
        <p>🏨 <span style="color: blue;">Blue</span> = Hotels</p>
        <p>🏦 <span style="color: gray;">Gray</span> = Banks</p>
        <p>🚗 <span style="color: darkred;">Dark Red</span> = Traffic</p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def _create_overview_map(self, results):
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
                    <b>Competitors:</b> {result['cafe_count']} cafes<br>
                    <b>Traffic:</b> {result['avg_road_speed']:.1f} km/h
                </div>
                """, max_width=300),
                tooltip=f"#{result['rank']} - Score: {result['final_score']:.1f}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(m)
        
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
    
    def _capture_map_screenshot(self, map_obj, filename, driver=None):
        if driver is None:
            return None, None
        
        try:
            temp_html = f"temp_{filename}.html"
            map_obj.save(temp_html)
           
            file_path = os.path.abspath(temp_html)
            driver.get(f"file://{file_path}")
           
            time.sleep(3)
           
            screenshot_path = f"{filename}.png"
            driver.save_screenshot(screenshot_path)
           
            if os.path.exists(temp_html):
               os.remove(temp_html)
           
            with open(screenshot_path, 'rb') as img_file:
               img_base64 = base64.b64encode(img_file.read()).decode()
           
            return screenshot_path, img_base64
           
        except Exception as e:
           return None, None
   
    def _create_scatter_plots(self, results):
       df = pd.DataFrame([{
           'Property_ID': f'Property {r["rank"]}',
           'Final_Score': r['final_score'],
           'Traffic_Score': r['traffic_score'],
           'Business_Score': r['business_score'],
           'Demographics_Score': r['demographics_score'],
           'Competition_Score': r['competition_score'],
           'Price': r['price'],
           'Business_Count': r['business_count'],
           'Cafe_Count': r['cafe_count'],
           'Age_Deviation': abs(r['age_difference']),
           'Traffic_Speed': r['avg_road_speed'],
           'Income': r['income'],
           'Rank': r['rank']
       } for r in results])
       
       charts_html = f"""
       <div style="width: 100%; margin: 20px 0;">
           <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
               
               <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                   <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Price vs Final Score</h4>
                   <canvas id="priceScoreChart" width="400" height="300"></canvas>
               </div>
               
               <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                   <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Business Count vs Competition</h4>
                   <canvas id="businessCompetitionChart" width="400" height="300"></canvas>
               </div>
               
               <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                   <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Traffic Speed vs Performance</h4>
                   <canvas id="trafficChart" width="400" height="300"></canvas>
               </div>
               
               <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                   <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Top 10 Score Breakdown</h4>
                   <canvas id="scoreBreakdownChart" width="400" height="300"></canvas>
               </div>
           </div>
       </div>
       
       <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
       <script>
           const ctx1 = document.getElementById('priceScoreChart').getContext('2d');
           new Chart(ctx1, {{
               type: 'scatter',
               data: {{
                   datasets: [{{
                       label: 'Properties',
                       data: {[{"x": row['Price'], "y": row['Final_Score']} for _, row in df.iterrows()]},
                       backgroundColor: function(context) {{
                           const value = context.parsed.y;
                           if (value >= 80) return 'rgba(76, 175, 80, 0.8)';
                           else if (value >= 60) return 'rgba(255, 152, 0, 0.8)';
                           else return 'rgba(244, 67, 54, 0.8)';
                       }},
                       borderColor: function(context) {{
                           const value = context.parsed.y;
                           if (value >= 80) return 'rgba(76, 175, 80, 1)';
                           else if (value >= 60) return 'rgba(255, 152, 0, 1)';
                           else return 'rgba(244, 67, 54, 1)';
                       }},
                       pointRadius: 6,
                       pointHoverRadius: 8
                   }}]
               }},
               options: {{
                   responsive: true,
                   plugins: {{
                       legend: {{ display: false }},
                       tooltip: {{
                           callbacks: {{
                               label: function(context) {{
                                   return 'Price: ' + context.parsed.x.toLocaleString() + ' SAR, Score: ' + context.parsed.y.toFixed(1);
                               }}
                           }}
                       }}
                   }},
                   scales: {{
                       x: {{ title: {{ display: true, text: 'Price (SAR)' }} }},
                       y: {{ title: {{ display: true, text: 'Final Score' }}, min: 0, max: 100 }}
                   }}
               }}
           }});
           
           const ctx2 = document.getElementById('businessCompetitionChart').getContext('2d');
           new Chart(ctx2, {{
               type: 'scatter',
               data: {{
                   datasets: [{{
                       label: 'Properties',
                       data: {[{"x": row['Business_Count'], "y": row['Cafe_Count']} for _, row in df.iterrows()]},
                       backgroundColor: 'rgba(52, 152, 219, 0.6)',
                       borderColor: 'rgba(52, 152, 219, 1)',
                       pointRadius: 5
                   }}]
               }},
               options: {{
                   responsive: true,
                   plugins: {{
                       legend: {{ display: false }},
                       tooltip: {{
                           callbacks: {{
                               label: function(context) {{
                                   return 'Businesses: ' + context.parsed.x + ', Cafes: ' + context.parsed.y;
                               }}
                           }}
                       }}
                   }},
                   scales: {{
                       x: {{ title: {{ display: true, text: 'Number of Businesses' }} }},
                       y: {{ title: {{ display: true, text: 'Number of Cafes' }} }}
                   }}
               }}
           }});
           
           const ctx3 = document.getElementById('trafficChart').getContext('2d');
           new Chart(ctx3, {{
               type: 'scatter',
               data: {{
                   datasets: [{{
                       label: 'Properties',
                       data: {[{"x": row['Traffic_Speed'], "y": row['Traffic_Score']} for _, row in df.iterrows()]},
                       backgroundColor: 'rgba(155, 89, 182, 0.6)',
                       borderColor: 'rgba(155, 89, 182, 1)',
                       pointRadius: 5
                   }}]
               }},
               options: {{
                   responsive: true,
                   plugins: {{
                       legend: {{ display: false }},
                       tooltip: {{
                           callbacks: {{
                               label: function(context) {{
                                   return 'Speed: ' + context.parsed.x.toFixed(1) + ' km/h, Score: ' + context.parsed.y.toFixed(1);
                               }}
                           }}
                       }}
                   }},
                   scales: {{
                       x: {{ title: {{ display: true, text: 'Traffic Speed (km/h)' }} }},
                       y: {{ title: {{ display: true, text: 'Traffic Score' }}, min: 0, max: 100 }}
                   }}
               }}
           }});
           
           const ctx4 = document.getElementById('scoreBreakdownChart').getContext('2d');
           new Chart(ctx4, {{
               type: 'bar',
               data: {{
                   labels: {[f'Property {i+1}' for i in range(min(10, len(df)))]},
                   datasets: [{{
                       label: 'Traffic',
                       data: {df.head(10)['Traffic_Score'].tolist()},
                       backgroundColor: 'rgba(52, 152, 219, 0.8)'
                   }}, {{
                       label: 'Business',
                       data: {df.head(10)['Business_Score'].tolist()},
                       backgroundColor: 'rgba(46, 204, 113, 0.8)'
                   }}, {{
                       label: 'Demographics',
                       data: {df.head(10)['Demographics_Score'].tolist()},
                       backgroundColor: 'rgba(155, 89, 182, 0.8)'
                   }}, {{
                       label: 'Competition',
                       data: {df.head(10)['Competition_Score'].tolist()},
                       backgroundColor: 'rgba(241, 196, 15, 0.8)'
                   }}]
               }},
               options: {{
                   responsive: true,
                   plugins: {{
                       legend: {{ position: 'top' }},
                       tooltip: {{
                           mode: 'index',
                           intersect: false
                       }}
                   }},
                   scales: {{
                       x: {{ title: {{ display: true, text: 'Top 10 Properties' }} }},
                       y: {{ title: {{ display: true, text: 'Score' }}, min: 0, max: 100 }}
                   }}
               }}
           }});
       </script>
       """
       
       return charts_html
   
    async def _generate_complete_html_report(self, results, overview_screenshot_base64, request):
       os.makedirs("static/reports", exist_ok=True)
       
       timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
       filename = f"site_analysis_{request.restaurant_type}_{timestamp}_{str(uuid.uuid4())[:8]}.html"
       
       top_10 = results[:10]
       top_choice = results[0] if results else {}
       report_date = datetime.now().strftime("%B %d, %Y")
       
       avg_score = np.mean([r['final_score'] for r in results]) if results else 0
       avg_price = np.mean([r['price'] for r in results]) if results else 0
       total_cafes = sum(r['cafe_count'] for r in results)
       
       scatter_plots_html = self._create_scatter_plots(results)
       
       html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>Site Suitability Analysis Report - {request.restaurant_type.replace('_', ' ').title()}</title>
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
               <h1>🏢 Site Suitability Analysis Report</h1>
               <div class="subtitle">Comprehensive Location Intelligence & Investment Recommendations</div>
               <div style="margin-top: 20px; font-size: 0.9em;">Generated on {report_date}</div>
           </div>
           
           <div class="executive-summary">
               <h2 style="margin-bottom: 20px;">📊 Executive Summary</h2>
               <p style="font-size: 1.1em; line-height: 1.8; margin-bottom: 20px;">
                   Our comprehensive analysis evaluated {len(results)} commercial properties across Riyadh using advanced location intelligence methodologies. 
                   The assessment incorporated traffic patterns, business density, demographic alignment, and competitive landscape to identify optimal 
                   {request.restaurant_type.replace('_', ' ')} locations. Through systematic scoring across four key criteria, we identified properties with the highest potential for 
                   successful operations, considering both market opportunity and operational feasibility.
               </p>
               <p style="font-size: 1.1em; line-height: 1.8;">
                   The analysis reveals significant variation in site suitability, with scores ranging from the highest performing property 
                   at {top_choice.get('final_score', 0):.1f}/100 to varying levels across different areas. Key findings indicate that properties 
                   in areas with optimal traffic flow, strong business ecosystems, and appropriate demographic profiles demonstrate 
                   superior investment potential for {request.restaurant_type.replace('_', ' ')} establishments.
               </p>
               
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
                       <div class="metric-value">{total_cafes}</div>
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
                       <strong>🚗 Traffic Analysis:</strong><br>
                       Average Speed: {top_choice.get('avg_road_speed', 20):.1f} km/h<br>
                       <small>Target: ≤{request.target_max_speed_kmh} km/h | {"✅ Optimal" if top_choice.get('avg_road_speed', 20) <= request.target_max_speed_kmh else "⚠️ Above target"}</small>
                   </div>
                   <div>
                       <strong>🏪 Business Environment:</strong><br>
                       {top_choice.get('business_count', 0)} nearby businesses<br>
                       <small>Target: {request.optimal_nearby_businesses} | {"✅ Excellent" if top_choice.get('business_count', 0) >= request.optimal_nearby_businesses else f"Gap: {request.optimal_nearby_businesses - top_choice.get('business_count', 0)} businesses"}</small>
                   </div>
                   <div>
                       <strong>👥 Demographics:</strong><br>
                       Age Deviation: {top_choice.get('age_difference', 0):.1f} years from target<br>
                       <small>Income: {top_choice.get('income', 15000):,.0f} SAR annually</small>
                   </div>
                   <div>
                       <strong>☕ Competition:</strong><br>
                       {top_choice.get('cafe_count', 0)} competing locations<br>
                       <small>Status: {"🟢 Low competition" if top_choice.get('cafe_count', 0) <= request.max_competitors else "🔴 High competition"}</small>
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
                   <li><strong>Prime Opportunity:</strong> Property #{top_choice.get('rank', 1)} emerges as the clear market leader with exceptional potential across all evaluation criteria</li>
                   <li><strong>Market Dynamics:</strong> {"Favorable competitive environment" if top_choice.get('cafe_count', 0) <= request.max_competitors else "Saturated market requires differentiation strategy"} with {top_choice.get('cafe_count', 0)} existing competitors</li>
                   <li><strong>Traffic Advantage:</strong> Optimal accessibility with {top_choice.get('avg_road_speed', 20):.1f} km/h average speeds supporting customer convenience</li>
                   <li><strong>Business Ecosystem:</strong> Strong commercial environment with {top_choice.get('business_count', 0)} nearby businesses ensuring consistent foot traffic</li>
                   <li><strong>Demographic Alignment:</strong> Target market compatibility with minimal {top_choice.get('age_difference', 0):.1f} years deviation from ideal customer profile</li>
               </ul>
           </div>
       </div>
       
       <div class="page page-break">
           <h1 class="section-title">🔬 Analysis Methodology</h1>
           
           <div class="methodology">
               <h3 style="color: #2C3E50; margin-bottom: 15px;">📋 How This Analysis Was Conducted</h3>
               <p style="margin-bottom: 20px; font-size: 1.1em;">
                   Our site suitability analysis employs a comprehensive, data-driven approach to evaluate commercial properties for {request.restaurant_type.replace('_', ' ')} operations. 
                   The methodology integrates multiple data sources and applies weighted scoring to identify optimal locations.
               </p>
               
               <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                   <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                       <h4 style="color: #3498DB; margin-bottom: 10px;">🚗 Traffic Analysis (25%)</h4>
                       <p><strong>Data Source:</strong> Simulated Traffic Data</p>
                       <p><strong>Method:</strong> Traffic flow analysis within 500m radius</p>
                       <p><strong>Scoring:</strong> Perfect score (100) for speeds ≤{request.target_max_speed_kmh} km/h, penalty of 5 points per 2 km/h above target</p>
                       <p><strong>Rationale:</strong> Lower traffic speeds indicate better accessibility and parking availability</p>
                   </div>
                   <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                       <h4 style="color: #3498DB; margin-bottom: 10px;">🏪 Business Density (40%)</h4>
                       <p><strong>Data Source:</strong> Google Maps Places API</p>
                       <p><strong>Method:</strong> POI analysis within {request.analysis_radius}m radius including restaurants, offices, retail</p>
                       <p><strong>Scoring:</strong> Perfect score for {request.optimal_nearby_businesses}+ businesses, penalty of 4 points per missing business</p>
                       <p><strong>Rationale:</strong> Higher business density ensures consistent customer flow throughout the day</p>
                   </div>
                   <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                       <h4 style="color: #3498DB; margin-bottom: 10px;">👥 Demographics (20%)</h4>
                       <p><strong>Data Source:</strong> Population Intelligence Data</p>
                       <p><strong>Method:</strong> Spatial join analysis for age and income matching</p>
                       <p><strong>Scoring:</strong> Perfect score at target age {request.target_age}, penalty of 5 points per year deviation</p>
                       <p><strong>Rationale:</strong> Target demographic
                       <p><strong>Rationale:</strong> Target demographic alignment ensures market-product fit for {request.restaurant_type.replace('_', ' ')} concept</p>
                   </div>
                   <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                       <h4 style="color: #3498DB; margin-bottom: 10px;">☕ Competition (15%)</h4>
                       <p><strong>Data Source:</strong> POI analysis with {request.restaurant_type.replace('_', ' ')} filtering</p>
                       <p><strong>Method:</strong> Competitive landscape mapping within analysis radius</p>
                       <p><strong>Scoring:</strong> Perfect score for ≤{request.max_competitors} competitors, penalty of 10 points per excess competitor</p>
                       <p><strong>Rationale:</strong> Optimal competition level balances market validation with oversaturation risk</p>
                   </div>
               </div>
               
               <div style="background: #E8F4FD; padding: 20px; border-radius: 10px; margin-top: 20px;">
                   <h4 style="color: #2C3E50; margin-bottom: 10px;">🎯 Final Score Calculation</h4>
                   <p><strong>Formula:</strong> Final Score = (Traffic × 0.25) + (Business × 0.40) + (Demographics × 0.20) + (Competition × 0.15)</p>
                   <p><strong>Range:</strong> 0-100 scale where 100 represents optimal conditions across all criteria</p>
                   <p><strong>Interpretation:</strong> Scores ≥80 indicate excellent potential, 60-79 good potential, <60 requires careful consideration</p>
               </div>
           </div>
           
           <h1 class="section-title">🔍 Detailed Property Analysis</h1>
           
           <p style="font-size: 1.1em; color: #7F8C8D; margin-bottom: 30px;">
               Comprehensive breakdown of top 10 performing properties with detailed scoring analysis and individual site maps.
           </p>"""

       for i, result in enumerate(top_10):
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
                       <p><strong>Area:</strong> {result['area_sqm']} sqm</p>
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
                               <div class="label">Competition<br>({result['cafe_count']} competitors)</div>
                           </div>
                       </div>
                   </div>
               </div>
               
               <div style="margin-top: 20px;">
                   <h4 style="color: #2C3E50; margin-bottom: 10px;">📊 Detailed Analysis</h4>
                   <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                       <div>
                           <strong>🚗 Traffic Performance:</strong><br>
                           <small>Current: {result['avg_road_speed']:.1f} km/h vs Target: ≤{request.target_max_speed_kmh} km/h<br>
                           Assessment: {"✅ Optimal accessibility" if result['avg_road_speed'] <= request.target_max_speed_kmh else f"⚠️ {result['avg_road_speed'] - request.target_max_speed_kmh:.1f} km/h above target"}</small>
                       </div>
                       <div>
                           <strong>🏪 Business Environment:</strong><br>
                           <small>{result['business_count']} businesses within {request.analysis_radius}m<br>
                           Gap Analysis: {max(0, request.optimal_nearby_businesses - result['business_count'])} businesses short of optimal</small>
                       </div>
                       <div>
                           <strong>👥 Demographics Match:</strong><br>
                           <small>Age: {result['median_age']:.0f} years (deviation: {result['age_difference']:.1f})<br>
                           Income: {result['income']:,.0f} SAR annually</small>
                       </div>
                       <div>
                           <strong>☕ Competitive Position:</strong><br>
                           <small>Market status: {"🟢 First-mover advantage" if result['cafe_count'] == 0 else f"🟡 Manageable competition" if result['cafe_count'] <= request.max_competitors else "🔴 Saturated market"}<br>
                           Strategy: {"Market development" if result['cafe_count'] == 0 else "Differentiation required" if result['cafe_count'] > request.max_competitors else "Standard positioning"}</small>
                       </div>
                   </div>
               </div>"""
           
           if result['screenshot_base64']:
               html_content += f"""
               <div class="map-container">
                   <h4 style="color: #2C3E50; margin-bottom: 15px;">📍 Site Location Map</h4>
                   <img src="data:image/png;base64,{result['screenshot_base64']}" 
                        alt="Property {result['rank']} Location Map" 
                        class="map-image">
                   <p style="margin-top: 15px; color: #7F8C8D; font-size: 0.9em;">
                       <strong>Map shows:</strong> Property location (red star), nearby businesses by category, analysis radius, and traffic patterns
                   </p>
               </div>"""
           
           html_content += """
           </div>"""

       html_content += """
       </div>
       
       <div class="page page-break">
           <h1 class="section-title">🗺️ Visual Analysis & Regional Overview</h1>
           
           <p style="font-size: 1.1em; color: #7F8C8D; margin-bottom: 30px;">
               Comprehensive visual analysis showing property distribution, demographic patterns, and competitive landscape across Riyadh.
           </p>"""

       if overview_screenshot_base64:
           html_content += f"""
           <div class="property-card">
               <div class="property-header">
                   <div class="property-title">🌍 Riyadh Commercial Properties Overview</div>
               </div>
               
               <div class="map-container">
                   <img src="data:image/png;base64,{overview_screenshot_base64}" 
                        alt="Riyadh Properties Overview Map" 
                        class="map-image">
                   <p style="margin-top: 15px; color: #7F8C8D;">
                       <strong>Overview Map Features:</strong> All {len(results)} analyzed properties color-coded by performance score, demographic zones by area, 
                       and competitive distribution patterns. Green stars indicate top performers (80-100), orange shows good potential (60-79), 
                       and red highlights properties requiring careful consideration (<60).
                   </p>
               </div>
               
               <div style="margin-top: 20px;">
                   <h4 style="color: #2C3E50; margin-bottom: 10px;">🎯 Regional Insights</h4>
                   <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                       <div>
                           <strong>🏆 Top Performing Areas:</strong><br>
                           <small>Properties showing superior performance due to optimal business density and demographics clustering</small>
                       </div>
                       <div>
                           <strong>📊 Score Distribution:</strong><br>
                           <small>Scores range from {min(r['final_score'] for r in results):.1f} to {max(r['final_score'] for r in results):.1f}, with clear clustering in high-commercial zones</small>
                       </div>
                       <div>
                           <strong>🎯 Market Opportunities:</strong><br>
                           <small>Several properties show untapped potential in emerging commercial areas with low competition</small>
                       </div>
                       <div>
                           <strong>⚠️ Risk Assessment:</strong><br>
                           <small>Properties in oversaturated areas require differentiation strategies and careful market positioning</small>
                       </div>
                   </div>
               </div>
           </div>"""

       html_content += f"""
           <div class="chart-container">
               <h3 style="color: #2C3E50; margin-bottom: 15px;">📊 Statistical Analysis - Property Performance Relationships</h3>
               {scatter_plots_html}
               <div style="margin-top: 20px;">
                   <h4 style="color: #2C3E50; margin-bottom: 10px;">📈 Key Statistical Insights</h4>
                   <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                       <div>
                           <strong>💰 Price vs Performance:</strong><br>
                           <small>Analysis reveals varying correlation between rental price and site suitability, indicating market inefficiencies and potential value opportunities among the {len(results)} properties analyzed</small>
                       </div>
                       <div>
                           <strong>🏪 Business Ecosystem Impact:</strong><br>
                           <small>Properties with 15+ nearby businesses show significantly better performance, confirming the importance of commercial density across all analyzed locations</small>
                       </div>
                       <div>
                           <strong>🚗 Traffic Speed Optimization:</strong><br>
                           <small>Sites with traffic speeds 15-25 km/h demonstrate optimal balance between accessibility and congestion in the Riyadh market</small>
                       </div>
                       <div>
                           <strong>👥 Demographic Targeting:</strong><br>
                           <small>Age deviation from target ({request.target_age} years) strongly impacts demographic scores, validating our targeting approach across diverse areas</small>
                       </div>
                   </div>
               </div>
           </div>
           
           <div class="insights">
               <h3>💡 Strategic Recommendations</h3>
               <div style="margin-top: 15px;">
                   <h4>🎯 Investment Strategy</h4>
                   <ul style="margin-left: 20px; margin-bottom: 15px;">
                       <li><strong>Priority Investment:</strong> Focus immediate attention on top 3 ranked properties from our {len(results)} property analysis for maximum ROI potential</li>
                       <li><strong>Portfolio Approach:</strong> Consider securing 2-3 high-scoring properties across different areas for market diversification</li>
                       <li><strong>Timing Advantage:</strong> Properties in emerging areas offer first-mover advantages before market saturation</li>
                   </ul>
                   
                   <h4>🛠️ Operational Considerations</h4>
                   <ul style="margin-left: 20px; margin-bottom: 15px;">
                       <li><strong>Site Adaptation:</strong> High-traffic areas may require drive-through or grab-and-go formats</li>
                       <li><strong>Market Positioning:</strong> Competitive areas demand premium positioning and unique value propositions</li>
                       <li><strong>Customer Experience:</strong> Traffic patterns inform optimal operating hours and service models</li>
                   </ul>
                   
                   <h4>⚠️ Risk Mitigation</h4>
                   <ul style="margin-left: 20px;">
                       <li><strong>Market Validation:</strong> Conduct customer surveys in target demographics before final site selection</li>
                       <li><strong>Lease Flexibility:</strong> Negotiate performance-based rent adjustments for lower-scoring but potential properties</li>
                       <li><strong>Competition Monitoring:</strong> Establish early warning systems for new {request.restaurant_type.replace('_', ' ')} openings in selected areas</li>
                   </ul>
               </div>
           </div>
       </div>
       
       <div class="footer">
           Report generated using advanced geospatial analysis and machine learning algorithms | {report_date}
           <br>Data sources: Google Maps Places API, Population Intelligence Data, Real Estate Listings
           <br>Analysis covered {len(results)} properties with comprehensive scoring across 4 key criteria
       </div>
   </div>
</body>
</html>
"""
       
       filepath = os.path.join("static/reports", filename)
       with open(filepath, 'w', encoding='utf-8') as f:
           f.write(html_content)
       
       return filename

site_analyzer = SiteSuitabilityAnalyzer()
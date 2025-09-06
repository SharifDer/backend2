"""
Mock data module for pharmacy reports development.
Provides realistic sample data to test HTML generation without backend dependencies.
"""

import random
from typing import Dict, Any, List
from datetime import datetime

class MockDataGenerator:
    """Generates realistic mock data for pharmacy site analysis reports."""
    
    def __init__(self):
        self.cities = ["Riyadh", "Jeddah", "Dammam", "Mecca", "Medina"]
        self.areas = ["Al Olaya", "King Fahd District", "Al Malaz", "Al Sahafah", "Al Nakheel"]
        
    def generate_mock_request(self, city_name: str = None, user_id: str = "mock_user_123"):
        """Generate a mock request object for testing."""
        from all_types.request_dtypes import Reqsmartreport, EvaluationMetrics
        
        city = city_name or random.choice(self.cities)
        
        # Create proper EvaluationMetrics object
        eval_metrics = EvaluationMetrics(
            traffic=25.0,
            demographics=30.0,
            competition=15.0,
            healthcare=20.0,
            complementary=10.0
        )
        
        # Create proper Reqsmartreport object
        return Reqsmartreport(
            user_id=user_id,
            city_name=city,
            country_name="Saudi Arabia",
            Type="Pharmacy",
            evaluation_metrics=eval_metrics
        )
    
    def generate_mock_shops_for_rent(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate mock shop rental data."""
        shops = []
        for i in range(count):
            lat = 24.7136 + random.uniform(-0.1, 0.1)  # Riyadh area
            lng = 46.6753 + random.uniform(-0.1, 0.1)
            shops.append({
                "properties": {
                    "price": random.randint(15000, 50000),
                    "url": f"https://example.com/shop-{i+1}-rental"
                },
                "geometry": {
                    "coordinates": [lng, lat]
                }
            })
        return shops
    
    def generate_mock_healthcare_data(self) -> Dict[str, Any]:
        """Generate mock healthcare ecosystem data."""
        return {
            "healthcare": {
                "pharmacy": {
                    "num_of_pharmacies": random.randint(2, 8),
                    "pharmacies_per_10k_population": random.uniform(1.5, 4.2),
                    "nearest_pharmacy_distance": random.uniform(200, 800)
                },
                "hospital": {
                    "num_of_hospitals": random.randint(1, 3),
                    "nearest_hospital_distance": random.uniform(500, 2000)
                },
                "dentist": {
                    "num_of_dentists": random.randint(2, 6),
                    "nearest_dentist_distance": random.uniform(300, 1200)
                }
            },
            "num_of_hospitals": random.randint(1, 3),
            "num_of_dentists": random.randint(2, 6)
        }
    
    def generate_mock_traffic_data(self) -> Dict[str, Any]:
        """Generate mock traffic data."""
        return {
            "Average Vehicle Speed in km": random.uniform(25, 65),
            "Functional Road Class": random.choice(["Primary", "Secondary", "Tertiary"]),
            "Traffic Volume": random.randint(500, 2500),
            "Congestion Level": random.choice(["Low", "Medium", "High"])
        }
    
    def generate_mock_demographics(self) -> Dict[str, Any]:
        """Generate mock demographic data."""
        return {
            "total_population": random.randint(15000, 45000),
            "population_density": random.uniform(1200, 3500),
            "age_distribution": {
                "0-14": random.randint(20, 35),
                "15-64": random.randint(55, 70),
                "65+": random.randint(5, 15)
            },
            "household_size": random.uniform(3.2, 5.8),
            "income_level": random.choice(["Low", "Medium", "High", "Very High"])
        }
    
    def generate_mock_amenities(self) -> Dict[str, Any]:
        """Generate mock nearby amenities data."""
        return {
            "grocery_store": {
                "num_of_businesses": random.randint(3, 8),
                "nearest_distance": random.uniform(150, 600)
            },
            "supermarket": {
                "num_of_businesses": random.randint(1, 4),
                "nearest_distance": random.uniform(300, 1000)
            },
            "restaurant": {
                "num_of_businesses": random.randint(5, 15),
                "nearest_distance": random.uniform(100, 500)
            },
            "atm": {
                "num_of_businesses": random.randint(2, 6),
                "nearest_distance": random.uniform(200, 800)
            },
            "bank": {
                "num_of_businesses": random.randint(1, 3),
                "nearest_distance": random.uniform(400, 1200)
            }
        }
    
    def generate_mock_households(self) -> Dict[str, Any]:
        """Generate mock household data."""
        return {
            "total_households": random.randint(3000, 9000),
            "average_household_size": random.uniform(3.2, 5.8),
            "household_income_distribution": {
                "low_income": random.randint(15, 30),
                "middle_income": random.randint(40, 60),
                "high_income": random.randint(20, 35)
            }
        }
    
    def generate_mock_location_data(self, lat: float, lng: float, place_name: str, price: int) -> Dict[str, Any]:
        """Generate complete mock data for a single location."""
        return {
            "place name": place_name,
            "lat": lat,
            "lng": lng,
            "price": price,
            "location_data": {
                "traffic": self.generate_mock_traffic_data(),
                "pop_data": {
                    **self.generate_mock_households(),
                    **self.generate_mock_demographics()
                },
                **self.generate_mock_healthcare_data(),
                **self.generate_mock_amenities(),
                "num of business around": random.randint(15, 45)
            }
        }
    
    def generate_mock_processed_report(self, city_name: str = "Riyadh") -> Dict[str, Any]:
        """Generate a complete mock processed report for testing."""
        mock_req = self.generate_mock_request(city_name)
        shops = self.generate_mock_shops_for_rent(5)
        
        results = {}
        for i, shop in enumerate(shops):
            lat = shop["geometry"]["coordinates"][1]
            lng = shop["geometry"]["coordinates"][0]
            price = shop["properties"]["price"]
            place_name = f"Commercial Space {i+1}"
            
            loc_key = f"{lat},{lng}"
            location_data = self.generate_mock_location_data(lat, lng, place_name, price)
            
            # Generate mock scores
            traffic_score = {
                "overall_score": random.uniform(60, 95),
                "details": {
                    "Average Viechle Speed": random.uniform(60, 95),
                    "highway score": random.uniform(60, 95),
                }
            }
            
            demographics_score = {
                "overall_score": random.uniform(65, 90),
                "details": {
                    "population_density_score": random.uniform(65, 90),
                    "income_level_score": random.uniform(65, 90),
                    "household_size_score": random.uniform(65, 90)
                }
            }
            
            healthcare_score = {
                "overall_score": random.uniform(70, 95),
                "details": {
                    "pharmacy_coverage_score": random.uniform(70, 95),
                    "hospital_access_score": random.uniform(70, 95)
                }
            }
            
            competitive_score = {
                "overall_score": random.uniform(50, 85),
                "details": {
                    "competition_level_score": random.uniform(50, 85),
                    "market_saturation_score": random.uniform(50, 85)
                }
            }
            
            complementary_score = {
                "overall_score": random.uniform(60, 90),
                "details": {
                    "amenity_diversity_score": random.uniform(60, 90),
                    "business_synergy_score": random.uniform(60, 90)
                }
            }
            
            # TEST: Calculate weighted score manually to verify formula
            weighted_score = (
                traffic_score["overall_score"] * 0.25 +
                demographics_score["overall_score"] * 0.30 +
                healthcare_score["overall_score"] * 0.20 +
                competitive_score["overall_score"] * 0.15 +
                complementary_score["overall_score"] * 0.10
            )
            print(f"DEBUG: Individual scores - Traffic: {traffic_score['overall_score']:.1f}, Demographics: {demographics_score['overall_score']:.1f}, Healthcare: {healthcare_score['overall_score']:.1f}, Competition: {competitive_score['overall_score']:.1f}, Complementary: {complementary_score['overall_score']:.1f}")
            print(f"DEBUG: Weighted score: {weighted_score:.1f} (should be ≤ 100)")
            
            results[loc_key] = {
                "place name": place_name,
                "property_name": place_name,  # Add this for chart compatibility
                "lat": lat,
                "lng": lng,
                "price": price,
                "final_score": (traffic_score["overall_score"] + demographics_score["overall_score"] + 
                               healthcare_score["overall_score"] + competitive_score["overall_score"] + 
                               complementary_score["overall_score"]),
                "traffic_score": traffic_score["overall_score"],
                "demographics_score": demographics_score["overall_score"],
                "healthcare_score": healthcare_score["overall_score"],
                "competition_score": competitive_score["overall_score"],
                "complementary_score": complementary_score["overall_score"],
                "scores": {
                    "overall_score": (traffic_score["overall_score"] + demographics_score["overall_score"] + 
                                     healthcare_score["overall_score"] + competitive_score["overall_score"] + 
                                     complementary_score["overall_score"]),
                    "traffic": traffic_score,
                    "demographics": demographics_score,
                    "competition": competitive_score,
                    "healthcare": healthcare_score,
                    "complementary": complementary_score,
                },
                "data": {
                    'nearby Businesses within 500 meters': random.randint(15, 45),
                    **location_data["location_data"]["traffic"],
                    **location_data["location_data"]["pop_data"],
                    'competing_pharmacies': location_data["location_data"]["healthcare"]["pharmacy"]["num_of_pharmacies"],
                    "pharmacies_per_10k_population": location_data["location_data"]["healthcare"]["pharmacy"]["pharmacies_per_10k_population"],
                    "number of hospitals around": location_data["location_data"].get("num_of_hospitals", 0),
                    "number of dentists around": location_data["location_data"].get("num_of_dentists", 0)
                }
            }
            
            # Add additional fields directly to the data
            results[loc_key]["data"]["avg_income"] = random.randint(8000, 25000)
            results[loc_key]["data"]["population_density"] = random.uniform(25.0, 75.0)
        
        return {
            "title": f"{city_name} Pharmacy Site Analysis Report",
            "description": "Comprehensive Location Intelligence & Investment Recommendations",
            "summary_metrics": {
                "total_locations_analyzed": len(results),
                "average_overall_score": sum(r["scores"]["overall_score"] for r in results.values()) / len(results),
                "price_range": f"SAR {min(r['price'] for r in results.values()):,} - SAR {max(r['price'] for r in results.values()):,}",
                "total_locations": len(results),
                "average_score": sum(r["scores"]["overall_score"] for r in results.values()) / len(results),
                "average_price_sar": sum(r["price"] for r in results.values()) / len(results),
                "competing_pharmacies": sum(r['data']['competing_pharmacies'] for r in results.values())
            },
            "executive_summary": {
                "overview": f"Analysis of {len(results)} potential pharmacy locations in {city_name}",
                "key_findings": [
                    "Multiple high-scoring locations identified",
                    "Strong demographic indicators in target areas",
                    "Competitive landscape analysis completed"
                ],
                "total_sites_evaluated": len(results),
                "top_recommendation": {
                    "name": "Top Performing Location",
                    "score": max(r["scores"]["overall_score"] for r in results.values()),
                    "price": max(r["price"] for r in results.values()),
                    "traffic_score": max(r["scores"]["traffic"]["overall_score"] for r in results.values()),
                    "demographics_score": max(r["scores"]["demographics"]["overall_score"] for r in results.values()),
                    "healthcare_score": max(r["scores"]["healthcare"]["overall_score"] for r in results.values()),
                    "competition_score": max(r["scores"]["competition"]["overall_score"] for r in results.values()),
                    "complementary_score": max(r["scores"]["complementary"]["overall_score"] for r in results.values()),
                    "location": max(results.items(), key=lambda x: x[1]["scores"]["overall_score"])[1]["place name"],
                    "coordinates": f"{max(results.items(), key=lambda x: x[1]['scores']['overall_score'])[1]['lat']:.4f}, {max(results.items(), key=lambda x: x[1]['scores']['overall_score'])[1]['lng']:.4f}",
                    # Add normalized scores and additional data
                    # Overall score is sum of individual scores, normalize to 0-100 scale
                    "score_normalized": min(100.0, (max(r["scores"]["overall_score"] for r in results.values()) / 500) * 100),
                    "traffic_score_normalized": max(r["scores"]["traffic"]["overall_score"] for r in results.values()),
                    "demographics_score_normalized": max(r["scores"]["demographics"]["overall_score"] for r in results.values()),
                    "healthcare_score_normalized": max(r["scores"]["healthcare"]["overall_score"] for r in results.values()),
                    "competition_score_normalized": max(r["scores"]["competition"]["overall_score"] for r in results.values()),
                    "complementary_score_normalized": max(r["scores"]["complementary"]["overall_score"] for r in results.values()),
                    "nearby_businesses": max(r["data"]["nearby Businesses within 500 meters"] for r in results.values()),
                    "avg_income": max(r["data"].get("avg_income", 0) for r in results.values()),
                    "competing_pharmacies": max(r["data"]["competing_pharmacies"] for r in results.values())
                }
            },
            "rankings": sorted([{
                "rank": i + 1,
                "name": r['place name'],
                "property_name": r['place name'],
                "location": f"{r['place name']} ({r['lat']:.4f}, {r['lng']:.4f})",
                "score": r["scores"]["overall_score"],
                "final_score": r["scores"]["overall_score"],
                "overall_score": r["scores"]["overall_score"],
                "price": r["price"],
                "price_sar": r["price"],
                "traffic_score": r["scores"]["traffic"]["overall_score"],
                "demographics_score": r["scores"]["demographics"]["overall_score"],
                "healthcare_score": r["scores"]["healthcare"]["overall_score"],
                "competition_score": r["scores"]["competition"]["overall_score"],
                "complementary_score": r["scores"]["complementary"]["overall_score"],
                "lat": r["lat"],
                "lng": r["lng"],
                # Add normalized scores for display (0-100 scale)
                # Overall score is sum of individual scores, normalize to 0-100 scale
                "score_normalized": min(100.0, (r["scores"]["overall_score"] / 500) * 100),  # Normalize to 0-100 scale
                "traffic_score_normalized": r["scores"]["traffic"]["overall_score"],  # Already 0-100
                "demographics_score_normalized": r["scores"]["demographics"]["overall_score"],  # Already 0-100
                "healthcare_score_normalized": r["scores"]["healthcare"]["overall_score"],  # Already 0-100
                "competition_score_normalized": r["scores"]["competition"]["overall_score"],  # Already 0-100
                "complementary_score_normalized": r["scores"]["complementary"]["overall_score"]  # Already 0-100
            } for i, r in enumerate(sorted(results.values(), key=lambda x: x["scores"]["overall_score"], reverse=True))], key=lambda x: x["rank"]),
            "detailed_analysis": [
                {
                    "location": r["place name"],
                    "property_name": r["place name"],
                    "coordinates": f"{r['lat']:.4f}, {r['lng']:.4f}",
                    "analysis": f"Location {r['place name']} shows strong potential with an overall score of {r['scores']['overall_score']:.1f}",
                    "final_score": r["scores"]["overall_score"],
                    "traffic_score": r["scores"]["traffic"]["overall_score"],
                    "demographics_score": r["scores"]["demographics"]["overall_score"],
                    "healthcare_score": r["scores"]["healthcare"]["overall_score"],
                    "competition_score": r["scores"]["competition"]["overall_score"],
                    "complementary_score": r["scores"]["complementary"]["overall_score"],
                    "price": r["price"],
                    "lat": r["lat"],
                    "lng": r["lng"],
                    "nearby_businesses": r["data"]["nearby Businesses within 500 meters"],
                    "population_density": r["data"].get("population_density", 0),
                    "avg_income": r["data"].get("avg_income", 0),
                    "competing_pharmacies": r["data"]["competing_pharmacies"],
                    "traffic_flow": r["data"].get("Average Vehicle Speed in km", 25.0),
                    "property_type": "Pharmacy",
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lng']}",
                    # Add normalized scores for display
                    # Overall score is sum of individual scores, normalize to 0-100 scale
                    "score_normalized": min(100.0, (r["scores"]["overall_score"] / 500) * 100),
                    "traffic_score_normalized": r["scores"]["traffic"]["overall_score"],
                    "demographics_score_normalized": r["scores"]["demographics"]["overall_score"],
                    "healthcare_score_normalized": r["scores"]["healthcare"]["overall_score"],
                    "competition_score_normalized": r["scores"]["competition"]["overall_score"],
                    "complementary_score_normalized": r["scores"]["complementary"]["overall_score"],
                    "recommendations": [
                        "Consider for immediate investment",
                        "Monitor market changes",
                        "Evaluate expansion potential"
                    ]
                } for r in results.values()
            ],
            "visual_analysis": {
                "maps_generated": True,
                "charts_available": True,
                "interactive_elements": True
            },
            "methodology": {
                "scoring_algorithm": "Multi-criteria weighted analysis",
                "data_sources": "Mock data for development purposes",
                "last_updated": datetime.now().isoformat()
            },
            "key_investment_insights": [
                {
                    "title": "Prime Opportunity",
                    "description": f"{max(results.items(), key=lambda x: x[1]['scores']['overall_score'])[1]['place name']} emerges as the clear market leader with exceptional potential scoring {max(r['scores']['overall_score'] for r in results.values()):.1f}/100 points."
                },
                {
                    "title": "Market Dynamics",
                    "description": f"Emerging market with minimal competition with {sum(r['data']['competing_pharmacies'] for r in results.values())} total competing pharmacies."
                },
                {
                    "title": "Traffic Advantage",
                    "description": f"Accessibility scoring {max(r['scores']['traffic']['overall_score'] for r in results.values()):.1f}/100 points supporting consistent customer flow."
                },
                {
                    "title": "Business Ecosystem",
                    "description": f"{sum(r['data']['nearby Businesses within 500 meters'] for r in results.values()) // len(results)} nearby complementary businesses ensure consistent foot traffic and cross-selling opportunities."
                },
                {
                    "title": "Demographic Alignment",
                    "description": f"Scoring {max(r['scores']['demographics']['overall_score'] for r in results.values()):.1f}/100 points indicating strong market fit."
                }
            ],
            "statistical_insights": [
                f"Average overall score: {sum(r['scores']['overall_score'] for r in results.values()) / len(results):.1f}",
                f"Score range: {min(r['scores']['overall_score'] for r in results.values()):.1f} - {max(r['scores']['overall_score'] for r in results.values()):.1f}",
                f"Price correlation with score: {random.uniform(0.3, 0.7):.2f}"
            ],
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "data_type": "mock_data",
                "city": city_name,
                "country": "Saudi Arabia"
            }
        }

# Convenience function for easy access
def get_mock_data(city_name: str = "Riyadh") -> Dict[str, Any]:
    """Get mock data for a specific city."""
    # Try to use the new scenario-based system first
    try:
        from .mock_data_scenarios import MockDataScenarioManager
        manager = MockDataScenarioManager()
        # Create a default request for current_location_only scenario
        req = manager.create_mock_request("current_location_only", city_name)
        return manager.get_mock_data(req)
    except Exception as e:
        print(f"Warning: Could not load scenario-based mock data: {e}")
        print("Falling back to generated mock data...")
        # Fall back to the original generated mock data
        generator = MockDataGenerator()
        return generator.generate_mock_processed_report(city_name)

def get_mock_request(city_name: str = "Riyadh"):
    """Get a mock request object for testing."""
    generator = MockDataGenerator()
    return generator.generate_mock_request(city_name)

from typing import List, Dict, Optional, Any
from .data_processor import normalize_score_to_100, google_maps_link

def generate_detailed_insights_dict(site: Dict) -> Dict[str, Any]:
    """Generate detailed insights as a dictionary structure."""
    insights = {}
    
    # Traffic Performance
    avg_speed = site.get("average speed in km")
    if avg_speed is not None:
        if 20 <= avg_speed <= 30:
            traffic_status = "Optimal traffic — moderate traffic flow ensures both convenience and visibility."
            traffic_level = "optimal"
        elif avg_speed < 20:
            traffic_status = "Heavy congestion — low traffic speed may reduce accessibility but can increase local visibility."
            traffic_level = "congested"
        else:
            traffic_status = "Light traffic — smooth access but potentially less exposure to passersby."
            traffic_level = "light"
        
        insights["traffic_performance"] = {
            "current_speed_kmh": round(avg_speed, 1),
            "target_range": "20-30 km/h",
            "status": traffic_status,
            "level": traffic_level
        }

    # Business Environment
    nearby_businesses = site.get("nearby Businesses within 500 meters", 0)
    if nearby_businesses > 20:
        bus_status = "Strong ecosystem — complementary businesses support customer flow."
        ecosystem_level = "strong"
    elif nearby_businesses >= 10:
        bus_status = "Moderate ecosystem — some opportunities exist, but growth potential remains."
        ecosystem_level = "moderate"
    else:
        bus_status = "Weak ecosystem — limited complementary activity may reduce visibility."
        ecosystem_level = "weak"
    
    insights["business_environment"] = {
        "nearby_businesses_500m": nearby_businesses,
        "assessment": bus_status,
        "ecosystem_level": ecosystem_level
    }

    # Demographics Match
    age_above_35 = site.get("Age above 35")
    avg_income = site.get("Average Income")
    if age_above_35 is not None:
        if age_above_35 >= 40:
            age_status = "Strong alignment — high share of population above 35, consistent with core demand segment."
            alignment_level = "strong"
        elif age_above_35 >= 25:
            age_status = "Partial alignment — balanced age structure with moderate fit."
            alignment_level = "partial"
        else:
            age_status = "Weak alignment — younger population may reduce pharmacy demand."
            alignment_level = "weak"
        
        insights["demographics_match"] = {
            "population_age_35_plus_percent": round(age_above_35, 1),
            "average_income_sar": avg_income,
            "assessment": age_status,
            "alignment_level": alignment_level
        }

    # Competitive Position
    pharm_per_10k = site.get("pharmacies_per_10k_population")
    if pharm_per_10k is not None:
        if pharm_per_10k > 8:
            market_status = "Saturated market - Differentiation is essential to compete effectively."
            market_level = "saturated"
        elif pharm_per_10k >= 4:
            market_status = "Moderately competitive - Focus on service quality and location advantage."
            market_level = "moderate"
        else:
            market_status = "Underserved market - Strong opportunity for entry and growth."
            market_level = "underserved"
        
        insights["competitive_position"] = {
            "pharmacies_per_10k_population": round(pharm_per_10k, 1),
            "competing_pharmacies": site.get('competing_pharmacies', 0),
            "market_status": market_status,
            "market_level": market_level
        }
    hospitals = site.get("num_of_hospitals", 0)
    dentists = site.get("num_of_dentists", 0)
    
    if hospitals + dentists > 10:
        health_status = "✅ Strong healthcare hub — high concentration of facilities ensures steady demand."
    elif hospitals + dentists >= 5:
        health_status = "⚠️ Moderate healthcare presence — demand is supported but with limited spillover."
    else:
        health_status = "❌ Weak healthcare presence — fewer facilities may reduce referral opportunities."
    
    insights["healthcare_environment"] = {
    "hospitals_around" : hospitals,
    "dentists_around" : dentists,
    "healthcare_places" : hospitals + dentists,
    "healthcare_market_status" : health_status
    }
    return insights


def generate_insights_dict(sites: List[Dict],  MAX_TOTAL: float, CRITERION_WEIGHTS: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate key investment insights as structured data."""
    if not sites:
        return []
    
    best_site = max(sites, key=lambda s: s.get('total_score', 0))
    insights = []

    # Prime opportunity
    best_score_100 = (best_site['total_score'] / MAX_TOTAL) * 100
    insights.append({
        "category": "Prime Opportunity",
        "description": f"{best_site['display_name']} emerges as the clear market leader with exceptional potential scoring {best_score_100:.1f}/100 points.",
        "site_name": best_site['display_name'],
        "score": round(best_score_100, 1)
    })

    # Market dynamics
    total_competitors = best_site["competing_pharmacies"]
    avg_competitors = total_competitors / len(sites) if sites else 0

    if avg_competitors > 5:
        market_status = "Highly saturated market requires strong differentiation strategy"
        market_level = "saturated"
    elif avg_competitors > 2:
        market_status = "Moderately competitive market with room for growth"
        market_level = "competitive"
    else:
        market_status = "Emerging market with minimal competition"
        market_level = "emerging"

    insights.append({
        "category": "Market Dynamics",
        "description": f"{market_status} with {total_competitors} total competing pharmacies.",
        "market_level": market_level,
        "total_competitors": total_competitors,
        "avg_competitors": round(avg_competitors, 1)
    })

    # Traffic advantage
    best_traffic_weighted = best_site.get('scores', {}).get('traffic_score', 0)
    best_traffic_100 = normalize_score_to_100(best_traffic_weighted, CRITERION_WEIGHTS['traffic'])
    speed_value = best_site.get("average speed in km")
    
    insights.append({
        "category": "Traffic Advantage",
        "description": f"Accessibility scoring {best_traffic_100:.1f}/100 points with {speed_value:.1f} km/h average speeds supporting consistent customer flow.",
        "traffic_score": round(best_traffic_100, 1),
        "average_speed_kmh": round(speed_value, 1) if speed_value else None
    })

    # Business ecosystem
    nearby_businesses = best_site.get("nearby Businesses within 500 meters", 0)
    insights.append({
        "category": "Business Ecosystem",
        "description": f"{nearby_businesses} nearby complementary businesses ensure consistent foot traffic and cross-selling opportunities.",
        "nearby_businesses_count": nearby_businesses
    })

    # Demographic alignment
    demo_weighted = best_site.get('scores', {}).get('demographics_score', 0)
    demo_100 = normalize_score_to_100(demo_weighted, CRITERION_WEIGHTS['demographics'])
    
    insights.append({
        "category": "Demographic Alignment",
        "description": f"Scoring {demo_100:.1f}/100 points, indicating strong market fit.",
        "demographics_score": round(demo_100, 1)
    })

    return insights


def generate_rankings_dict(sites: List[Dict], MAX_TOTAL: float, CRITERION_WEIGHTS: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate rankings as structured data."""
    
    rankings = []
    for i, site in enumerate(sites, start=1):
        # Convert all scores to 100 scale for display
        final_score_100 = (site['total_score'] / MAX_TOTAL) * 100
        traffic_100 = normalize_score_to_100(
            site.get('scores', {}).get('traffic_score', 0), 
            CRITERION_WEIGHTS['traffic']
        )
        demographics_100 = normalize_score_to_100(
            site.get('scores', {}).get('demographics_score', 0), 
            CRITERION_WEIGHTS['demographics']
        )
        competitive_100 = normalize_score_to_100(
            site.get('scores', {}).get('competition_score', 0), 
            CRITERION_WEIGHTS['competition']
        )
        healthcare_100 = normalize_score_to_100(
            site.get('scores', {}).get('healthcare_score', 0), 
            CRITERION_WEIGHTS['healthcare']
        )
        complementary_100 = normalize_score_to_100(
            site.get('scores', {}).get('complementary_score', 0), 
            CRITERION_WEIGHTS['complementary']
        )
        
        rankings.append({
            "rank": site["rank"],
            "site_name": site['display_name'],
            "price_sar": site.get('price', 0) if site.get('price') else None,
            "final_score": round(final_score_100, 1),
            "traffic_score": round(traffic_100, 1),
            "demographics_score": round(demographics_100, 1),
            "competition_score": round(competitive_100, 1),
            "healthcare_ecosystem_score": round(healthcare_100, 1),
            "complementary_businesses_score": round(complementary_100, 1),
            "url": site["url"]
        })
    
    return rankings


def generate_rankings_dict_with_current_comparison(
    top_sites: List[Dict],
    current_location: List[Dict],  # usually just 1 dict
    MAX_TOTAL: float,
    CRITERION_WEIGHTS: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Generate rankings as structured data with comparisons to current_location.
    Returns comparison format: {
        "value": top_val,
        "current_value": curr_val,
        "percentage_difference": XX.X,
        "comparison_type": "improvement"|"disadvantage"|"same",
        "display_text": "top_val (curr_val, XX% improvement)"
    }
    """
    
    if not top_sites:
        return []
    if not current_location:
        # fallback: no comparison, use original function
        return generate_rankings_dict(top_sites, MAX_TOTAL, CRITERION_WEIGHTS)
    
    current = current_location[0]  # baseline
    rankings = []
    
    # Helper to format comparison data
    def compare_values(top_val, curr_val):
        if curr_val == 0:
            return {
                "value": round(top_val, 1),
                "current_value": round(curr_val, 1),
                "percentage_difference": None,
                "comparison_type": "N/A",
                "display_text": f"{top_val:.1f} ({curr_val:.0f}, N/A)"
            }
        
        diff_pct = abs(top_val - curr_val)
        if top_val > curr_val:
            comparison_type = "improvement"
            display_text = f"{top_val:.1f} ({curr_val:.0f}, {diff_pct:.1f}% improvement)"
        elif top_val < curr_val:
            comparison_type = "disadvantage"
            display_text = f"{top_val:.1f} ({curr_val:.0f}, {diff_pct:.1f}% disadvantage)"
        else:
            comparison_type = "same"
            display_text = f"{top_val:.1f} ({curr_val:.0f}, 0% difference)"
        
        return {
            "value": round(top_val, 1),
            "current_value": round(curr_val, 1),
            "percentage_difference": round(diff_pct, 1),
            "comparison_type": comparison_type,
            "display_text": display_text
        }
    
    for i, site in enumerate(top_sites, start=1):
        # Top site scores normalized to 100
        final_score = (site['total_score'] / MAX_TOTAL) * 100
        traffic = normalize_score_to_100(site.get('scores', {}).get('traffic_score', 0), CRITERION_WEIGHTS['traffic'])
        demographics = normalize_score_to_100(site.get('scores', {}).get('demographics_score', 0), CRITERION_WEIGHTS['demographics'])
        competition = normalize_score_to_100(site.get('scores', {}).get('competition_score', 0), CRITERION_WEIGHTS['competition'])
        healthcare = normalize_score_to_100(site.get('scores', {}).get('healthcare_score', 0), CRITERION_WEIGHTS['healthcare'])
        complementary = normalize_score_to_100(site.get('scores', {}).get('complementary_score', 0), CRITERION_WEIGHTS['complementary'])

        # Current location normalized scores
        curr_final = (current['total_score'] / MAX_TOTAL) * 100
        curr_traffic = normalize_score_to_100(current.get('scores', {}).get('traffic_score', 0), CRITERION_WEIGHTS['traffic'])
        curr_demo = normalize_score_to_100(current.get('scores', {}).get('demographics_score', 0), CRITERION_WEIGHTS['demographics'])
        curr_comp = normalize_score_to_100(current.get('scores', {}).get('competition_score', 0), CRITERION_WEIGHTS['competition'])
        curr_health = normalize_score_to_100(current.get('scores', {}).get('healthcare_score', 0), CRITERION_WEIGHTS['healthcare'])
        curr_complement = normalize_score_to_100(current.get('scores', {}).get('complementary_score', 0), CRITERION_WEIGHTS['complementary'])

        # Generate comparison data for each metric
        final_comparison = compare_values(final_score, curr_final)
        traffic_comparison = compare_values(traffic, curr_traffic)
        demographics_comparison = compare_values(demographics, curr_demo)
        competition_comparison = compare_values(competition, curr_comp)
        healthcare_comparison = compare_values(healthcare, curr_health)
        complementary_comparison = compare_values(complementary, curr_complement)
        
        rankings.append({
            "rank": site["rank"],
            "site_name": site['display_name'],
            "price_sar": site.get('price', 0) if site.get('price') else None,
            "final_score_comparison": final_comparison,
            "traffic_score_comparison": traffic_comparison,
            "demographics_score_comparison": demographics_comparison,
            "competition_score_comparison": competition_comparison,
            "healthcare_ecosystem_score_comparison": healthcare_comparison,
            "complementary_businesses_score_comparison": complementary_comparison,
            "url": site["url"]
        })
    
    return rankings
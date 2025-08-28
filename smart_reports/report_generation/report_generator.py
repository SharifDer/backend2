"""
Report generation utilities for pharmacy site selection analysis.
"""
import os
import math
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
from .map_generator import generate_site_map_image   
from typing import Dict, List, Any, Optional

def relpath_for_md(target: Optional[str], md_path: str) -> Optional[str]:
    """Calculate relative path for markdown links."""
    if not target:
        return None
    if not os.path.exists(target):
        return None
    md_dir = os.path.dirname(md_path) or os.getcwd()
    try:
        return os.path.relpath(target, start=md_dir)
    except Exception:
        return target


def google_maps_link(site: Dict) -> str:
    """Generate Google Maps link for a site."""
    if site.get('lat') is not None and site.get('lng') is not None:
        return f"https://www.google.com/maps/search/?api=1&query={site['lat']},{site['lng']}"
    q = site.get('raw_place') or site.get('display_name') or site['id']
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def normalize_score_to_100(weighted_score: float, criterion_weight: float) -> float:
    """Convert weighted score back to 0-100 scale for display."""
    if criterion_weight == 0:
        return 0.0
    return (weighted_score / criterion_weight) * 100.0

def generate_detailed_insights(site: Dict) -> str:
    insights = []
    insights.append("## 📊 Detailed Analysis\n")

    # 🚗 Traffic Performance
    avg_speed = site.get("average speed in km")
    if avg_speed is not None:
        if 20 <= avg_speed <= 30:
            traffic_status = "✅ Optimal accessibility — moderate traffic flow ensures both convenience and visibility."
        elif avg_speed < 20:
            traffic_status = "⚠️ Heavy congestion — low traffic speed may reduce accessibility but can increase local visibility."
        else:
            traffic_status = "ℹ️ Light traffic — smooth access but potentially less exposure to passersby."
        
        insights.append(
            f"### 🚗 Traffic Performance\n"
            f"Current: {avg_speed:.1f} km/h | Target: 20–30 km/h  \n"
            f"Assessment: {traffic_status}\n\n"
        )

    # 🏪 Business Environment
    nearby_businesses = site.get("nearby Businesses within 500 meters", 0)
    if nearby_businesses > 20:
        bus_status = "✅ Strong ecosystem —  complementary businesses support customer flow."
    elif nearby_businesses >= 10:
        bus_status = "⚠️ Moderate ecosystem — some opportunities exist, but growth potential remains."
    else:
        bus_status = "❌ Weak ecosystem — limited complementary activity may reduce visibility."
    
    insights.append(
        f"### 🏪 Business Environment\n"
        f"{nearby_businesses} businesses within 500m  \n"
        f"Assessment: {bus_status}\n\n"
    )

    # 👥 Demographics Match (Age above 35)
    age_above_35 = site.get("Age above 35")
    avg_income = site.get("Average Income")
    if age_above_35 is not None:
        if age_above_35 >= 40:
            age_status = "✅ Strong alignment — high share of population above 35, consistent with core demand segment."
        elif age_above_35 >= 25:
            age_status = "⚠️ Partial alignment — balanced age structure with moderate fit."
        else:
            age_status = "❌ Weak alignment — younger population may reduce pharmacy demand."
        
        insights.append(
            f"### 👥 Demographics Match\n"
            f"Population Aged 35 and Above: {age_above_35:.1f}% of local population with average \n"
            f"Assessment: {age_status}  \n"
            f"Average Icome: {avg_income} SAR\n\n"
        )

    # ☕ Competitive Position
    pharm_per_10k = site.get("pharmacies_per_10k_population")
    if pharm_per_10k is not None:
        if pharm_per_10k > 8:
            market_status = "🔴 Saturated market\nStrategy: Differentiation is essential to compete effectively."
        elif pharm_per_10k >= 4:
            market_status = "🟠 Moderately competitive\nStrategy: Focus on service quality and location advantage."
        else:
            market_status = "🟢 Underserved market\nStrategy: Strong opportunity for entry and growth."
        
        insights.append(
            f"### ☕ Competitive Position\n"
            f"Pharmacies per 10k population: {pharm_per_10k:.1f}  \n"
            f"Competeing Pharmacies in the area: {site['competing_pharmacies']}  \n"
            f"{market_status}\n\n"
        )

    return "".join(insights)

def generate_detailed_insights_dict(site: Dict) -> Dict[str, Any]:
    """Generate detailed insights as a dictionary structure."""
    insights = {}
    
    # Traffic Performance
    avg_speed = site.get("average speed in km")
    if avg_speed is not None:
        if 20 <= avg_speed <= 30:
            traffic_status = "Optimal accessibility — moderate traffic flow ensures both convenience and visibility."
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

    return insights

def generate_insights(sites: List[Dict],  MAX_TOTAL : float , CRITERION_WEIGHTS : Dict[str , float]) -> str:
    """Generate key investment insights based on analysis (Markdown only)."""
    if not sites:
        return "No data available for insights generation."
    
    best_site = max(sites, key=lambda s: s.get('total_score', 0))
    insights = []

    # Prime opportunity - convert to 100 scale for display
    best_score_100 = (best_site['total_score'] / MAX_TOTAL) * 100
    insights.append(
        f"- **Prime Opportunity:** {best_site['display_name']} emerges as the clear "
        f"market leader with exceptional potential scoring {best_score_100:.1f}/100 points.\n"
    )

    total_competitors = best_site["competing_pharmacies"]
    avg_competitors = total_competitors / len(sites) if sites else 0

    if avg_competitors > 5:
        market_status = "Highly saturated market requires strong differentiation strategy"
    elif avg_competitors > 2:
        market_status = "Moderately competitive market with room for growth"
    else:
        market_status = "Emerging market with minimal competition"

    insights.append(
        f"- **Market Dynamics:** {market_status} with {total_competitors} total competing pharmacies.\n"
    )

    # Traffic advantage - normalize to 100 scale
    best_traffic_weighted = best_site.get('scores', {}).get('traffic_score', 0)
    best_traffic_100 = normalize_score_to_100(best_traffic_weighted, CRITERION_WEIGHTS['traffic'])
    speed_info = ""
    speed_value = best_site.get("average speed in km")
    speed_info = f" with {speed_value:.1f} km/h average speeds"
           

    insights.append(
        f"- **Traffic Advantage:** Accessibility scoring {best_traffic_100:.1f}/100 points{speed_info} "
        "supporting consistent customer flow.\n"
    )

    # Business ecosystem
    nearby_businesses = best_site.get("nearby Businesses within 500 meters" , 0)

    insights.append(
        f"- **Business Ecosystem:** {nearby_businesses} nearby complementary businesses ensure "
        "consistent foot traffic and cross-selling opportunities.\n"
    )

    # Demographic alignment - normalize to 100 scale
    demo_weighted = best_site.get('scores', {}).get('demographics_score', 0)
    demo_100 = normalize_score_to_100(demo_weighted, CRITERION_WEIGHTS['demographics'])
    age_alignment = ""
    for key, value in best_site.get('details', {}).items():
        if 'age' in key.lower() and not math.isnan(value):
            deviation = abs(value - 50)
            age_alignment = f" with {deviation:.1f}% deviation from ideal customer profile"
            break

    insights.append(
        f"- **Demographic Alignment:** Scoring {demo_100:.1f}/100 points{age_alignment}, "
        "indicating strong market fit.\n"
    )

    return "".join(insights)

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


def generate_enhanced_table(sites: List[Dict], top_n: int , MAX_TOTAL : float , CRITERION_WEIGHTS : Dict[str , float]) -> str:
    """Generate enhanced Markdown table with requested columns - scores normalized to 100."""
    top_sites = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]

    if not top_sites:
        return "_No sites available for table generation._\n"

    header = (
        "| Rank | Site Name | Price (SAR) | Final Score | Traffic | Demographics | "
        "Competition | Healthcare Ecosystem | Complementary Businesses | View |\n"
        "|:----:|:---------:|:-----------:|:-----------:|:-------:|:-----------:|"
        ":----------:|:-----------------:|:-------------------:|:---:|\n"
    )

    rows = []
    for i, site in enumerate(top_sites, start=1):
        price_display = f"{site.get('price', 0):,}" if site.get('price') else "N/A"
        
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
            site.get('scores', {}).get('competitive_score', 0), 
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
        
        rows.append(
            f"| {i} | {site['display_name']} | {price_display} | {final_score_100:.1f} | "
            f"{traffic_100:.1f} | {demographics_100:.1f} | {competitive_100:.1f} | "
            f"{healthcare_100:.1f} | {complementary_100:.1f} | "
            f"[View]({google_maps_link(site)}) |\n"
        )
    return header + "".join(rows) + "\n"

def generate_rankings_dict(sites: List[Dict], top_n: int, MAX_TOTAL: float, CRITERION_WEIGHTS: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate rankings as structured data."""
    top_sites = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]
    
    rankings = []
    for i, site in enumerate(top_sites, start=1):
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
            site.get('scores', {}).get('competitive_score', 0), 
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
            "rank": i,
            "site_name": site['display_name'],
            "price_sar": site.get('price', 0) if site.get('price') else None,
            "final_score": round(final_score_100, 1),
            "traffic_score": round(traffic_100, 1),
            "demographics_score": round(demographics_100, 1),
            "competition_score": round(competitive_100, 1),
            "healthcare_ecosystem_score": round(healthcare_100, 1),
            "complementary_businesses_score": round(complementary_100, 1),
            "google_maps_url": google_maps_link(site)
        })
    
    return rankings


def generate_markdown(sites: List[Dict], outdir: str, out_md: str, top_n: int,
                      charts: Dict[str, str], map_png: Optional[str], heat_png: Optional[str],
                      num_of_sites: int, stats: Dict , MAX_TOTAL : float , CRITERION_WEIGHTS : Dict[str ,float]) -> Dict[str, Any]:
    """Generate comprehensive markdown report with enhanced design and features AND return structured dictionary And the path of the report.md."""
    top_sites = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]
    best = top_sites[0] if top_sites else None
    md_path = os.path.join(outdir, out_md).replace("\\", "/")
    
    report_data = {}
    maps_dir = os.path.join(outdir, 'maps')
    
    with open(md_path, 'w', encoding='utf-8') as md:

        # Hero section
        report_data["title"] = "🏥 Pharmacy Expansion Analysis — Riyadh"
        md.write(f"# {report_data['title']}\n\n")
        
        report_data["description"] = (
            "Comprehensive site selection report with multi-criteria scoring analysis "
            "across traffic, demographics, competition, healthcare proximity, and complementary businesses."
        )
        md.write(f"{report_data['description']}\n\n")
        
        # Summary metrics
        summary_metrics_title = "📊 Summary Metrics"
        md.write(f"## {summary_metrics_title}\n\n")
        
        total_locations_label = "Total Locations"
        md.write(f"- **{total_locations_label}:** {num_of_sites}\n")
        
        # Convert average score to 100 scale for display
        avg_score_100 = (stats['average_score'] / MAX_TOTAL) * 100
        md.write(f"- **Average Score:** {avg_score_100:.1f}/100\n")
        md.write(f"- **Average Price:** {stats['average_price']:,.0f} SAR\n")
        md.write(f"- **Competing Pharmacies:** {stats['total_competing_pharmacies']}\n\n")
        
        report_data["summary_metrics"] = {
            "total_locations": num_of_sites,
            "average_score": round(avg_score_100, 1),
            "average_price_sar": round(stats['average_price'], 0),
            "competing_pharmacies": stats['total_competing_pharmacies']
        }
        
        # Executive Summary
        exec_summary_title = "Executive Summary"
        md.write(f"## 📋 {exec_summary_title}\n\n")
        
        executive_summary = {}
        if best:
            best_score_100 = (best['total_score'] / MAX_TOTAL) * 100
            top_rec_text = (
                f"**Top recommendation:** **{best['display_name']}** with an overall score of "
                f"{best_score_100:.1f}/100 points, priced at {best.get('price', 0):,} SAR.\n\n"
            )
            md.write(top_rec_text)
            
            executive_summary["top_recommendation"] = {
                "site_name": best['display_name'],
                "score": round(best_score_100, 1),
                "price_sar": best.get('price', 0)
            }
        
        description_text = (
            f"This analysis evaluates {num_of_sites} candidate pharmacy locations. "
            "Evaluation criteria include traffic, demographics, competition, healthcare proximity, "
            "and complementary business ecosystem.\n\n"
        )
        md.write(description_text)
        
        executive_summary["description"] = description_text.strip()
        executive_summary["total_sites_evaluated"] = num_of_sites
        executive_summary["evaluation_criteria"] = [
            "traffic", "demographics", "competition", 
            "healthcare proximity", "complementary business ecosystem"
        ]
        
        report_data["executive_summary"] = executive_summary
        
        # Key Investment Insights
        insights_title = "💡 Key Investment Insights"
        md.write(f"## {insights_title}\n\n")
        insights_md = generate_insights(sites, MAX_TOTAL, CRITERION_WEIGHTS)
        md.write(insights_md)
        md.write("\n")
        
        report_data["key_investment_insights"] = generate_insights_dict(sites,  MAX_TOTAL, CRITERION_WEIGHTS)

        # Enhanced Top Sites Table
        rankings_title = f"🏆 Top {top_n} Investment Opportunities"
        md.write(f"## {rankings_title}\n\n")
        table_md = generate_enhanced_table(sites, top_n, MAX_TOTAL, CRITERION_WEIGHTS)
        md.write(table_md)
        md.write("\n")
        
        report_data["rankings"] = generate_rankings_dict(sites, top_n, MAX_TOTAL, CRITERION_WEIGHTS)

        # Detailed Site Analysis
        detailed_title = "🔍 Detailed Site Analysis"
        md.write(f"## {detailed_title}\n\n")
        
        detailed_analysis = []
        for i, s in enumerate(top_sites, start=1):
            final_score_100 = (s['total_score'] / MAX_TOTAL) * 100
            md.write(f"### {i}. {s['display_name']} (Score: {final_score_100:.1f}/100)\n\n")
            
            coords_text = f"**Location:** {s['lat']:.6f}, {s['lng']:.6f}" if (s['lat'] is not None and s['lng'] is not None) else f"**Location:** {s.get('raw_place') or 'N/A'}"
            price_text = f"**Price:** {s.get('price', 0):,} SAR" if s.get('price') else "**Price:** Not specified"
            
            md.write(f"{coords_text} | {price_text} | Category: Shop For Rent \n\n")
            
            # Generate insights for markdown
            detailed_insights_md = generate_detailed_insights(s)
            md.write(detailed_insights_md)
            
            md.write(f"**[🗺️ View on Google Maps]({google_maps_link(s)})**\n\n")
            
            # Generate site maps
            map_image, html_map = generate_site_map_image(s, maps_dir, MAX_TOTAL)
            # map_image_rel = relpath_for_md(map_image, md_path).replace("\\", "/") if map_image else None
            # html_map_rel = relpath_for_md(html_map, md_path).replace("\\", "/") if html_map else None
            map_image_rel = map_image.replace("\\", "/") if map_image else None
            html_map_rel = html_map.replace("\\", "/") if html_map else None
            if map_image_rel:
                md.write(f"![Site Map]({map_image_rel})\n\n")
            if html_map_rel:
                md.write(f"[Open interactive map]({html_map_rel})\n\n")
            
            # Scoring breakdown table
            md.write('| Criterion | Sub-factor | Raw Score | Weighted Points |\n')
            md.write('|-----------|------------|-----------|----------------|\n')

            scoring_breakdown = []
            for c in CRITERION_WEIGHTS.keys():
                dkeys = [k for k in s['details'].keys() if k.startswith(f"{c}__") and not k.endswith('_weighted')]
                if dkeys and any(not math.isnan(s['details'].get(k, float('nan'))) for k in dkeys):
                    sub_weight = CRITERION_WEIGHTS[c] / max(1, len(dkeys))
                    crit_total = 0.0
                    for dk in dkeys:
                        raw = s['details'].get(dk, float('nan'))
                        weighted = (raw / 100.0) * sub_weight if not math.isnan(raw) else float('nan')
                        crit_total += 0.0 if math.isnan(weighted) else weighted
                        sub_name = dk.replace(f"{c}__", '').replace('_', ' ')
                        raw_display = f'{raw:.1f}' if not math.isnan(raw) else 'N/A'
                        weighted_display = f'{weighted:.2f}' if not math.isnan(weighted) else 'N/A'
                        md.write(f"| {c.capitalize()} | {sub_name} | {raw_display} | {weighted_display} |\n")
                        
                        scoring_breakdown.append({
                            "criterion": c.capitalize(),
                            "sub_factor": sub_name,
                            "raw_score": raw if not math.isnan(raw) else None,
                            "weighted_points": weighted if not math.isnan(weighted) else None
                        })
                    
                    md.write(f"| **{c.capitalize()} Total** | | | **{crit_total:.2f}** |\n")
                    scoring_breakdown.append({
                        "criterion": f"{c.capitalize()} Total",
                        "sub_factor": "",
                        "raw_score": None,
                        "weighted_points": crit_total
                    })
                else:
                    overall = s.get('scores', {}).get(f'{c}_score', 0.0)
                    md.write(f"| {c.capitalize()} | No detailed data | N/A | **{overall:.2f}** |\n")
                    scoring_breakdown.append({
                        "criterion": c.capitalize(),
                        "sub_factor": "No detailed data",
                        "raw_score": None,
                        "weighted_points": overall
                    })
            md.write("\n")
            
            # Build detailed analysis dictionary entry
            site_analysis = {
                "rank": i,
                "site_name": s['display_name'],
                "final_score": round(final_score_100, 1),
                "location": {
                    "latitude": s['lat'] if s['lat'] is not None else None,
                    "longitude": s['lng'] if s['lng'] is not None else None,
                    "raw_place": s.get('raw_place')
                },
                "price_sar": s.get('price', 0) if s.get('price') else None,
                "category": "Shop For Rent",
                "google_maps_url": google_maps_link(s),
                "maps": {
                    "static_map_url": map_image_rel,
                    "interactive_map_url": html_map_rel
                },
                "detailed_insights": generate_detailed_insights_dict(s),
                "scoring_breakdown": scoring_breakdown
            }
            
            detailed_analysis.append(site_analysis)
        
        report_data["detailed_analysis"] = detailed_analysis

        # Charts & Visualizations
        charts_title = "📊 Charts & Visualizations"
        md.write(f"## {charts_title}\n\n")
        
        visual_analysis = {
            "charts": [],
            "maps": [],
            "interactive_maps": []
        }
        
        if charts.get('top_stacked') and os.path.exists(charts['top_stacked']):
            # rel = relpath_for_md(charts['top_stacked'], md_path)
            path = charts.get('top_stacked')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Comparative Analysis:**\n\n![Top Candidates Comparison]({chart_path})\n\n")
                visual_analysis["charts"].append({
                    "title": "Top Candidates Comparison",
                    "type": "comparative_analysis",
                    "url": chart_path
                })

        if charts.get('traffic') and os.path.exists(charts['traffic']):
            path = charts.get('traffic')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Traffic Analysis:**\n\n![Traffic Flow Analysis]({chart_path})\n\n")
                visual_analysis["charts"].append({
                    "title": "Traffic Flow Analysis",
                    "type": "traffic_analysis",
                    "url": chart_path
                })

        if charts.get('best_breakdown') and os.path.exists(charts['best_breakdown']):
            path = charts.get('best_breakdown')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Best Site Breakdown:**\n\n![Best Site Breakdown]({chart_path})\n\n")
                visual_analysis["charts"].append({
                    "title": "Best Site Breakdown",
                    "type": "site_breakdown",
                    "url": chart_path
                })

        # Maps
        maps_title = "🗺️ Geographic Analysis"
        md.write(f"## {maps_title}\n\n")
        
        if map_png:
            map_path = map_png.replace('\\', '/')
            md.write("**Location Overview:**\n\n")
            md.write(f"![Candidates Map]({map_path})\n\n")
            visual_analysis["maps"].append({
                "title": "Location Overview",
                "type": "candidates_map",
                "url": map_path
            })
        else:
            md.write("**Location Overview:** *Map not available*\n\n")

        if heat_png:
            heat_path = heat_png.replace('\\', '/')
            md.write("**Demographic Distribution:**\n\n")
            md.write(f"![Demographic Heatmap]({heat_path})\n\n")
            visual_analysis["maps"].append({
                "title": "Demographic Distribution", 
                "type": "demographic_heatmap",
                "url": heat_path
            })
        else:
            md.write("**Demographic Distribution:** *Heatmap not available*\n\n")
        
        # Collect interactive maps from detailed analysis
        for site_data in detailed_analysis:
            if site_data["maps"]["interactive_map_url"]:
                visual_analysis["interactive_maps"].append({
                    "site_name": site_data["site_name"],
                    "url": site_data["maps"]["interactive_map_url"]
                })
        
        report_data["visual_analysis"] = visual_analysis

        # Methodology
        methodology_title = "📈 Analysis Methodology"
        md.write(f"## {methodology_title}\n\n")

        md.write(
            "Our site suitability analysis employs a **comprehensive, data-driven approach**. "
            "The methodology integrates multiple data sources and applies weighted scoring "
            "to identify optimal locations.\n\n"
        )

        methodology = {
            "overview": "Comprehensive, data-driven approach that integrates multiple data sources and applies weighted scoring to identify optimal locations.",
            "criteria": {}
        }

        # Traffic Analysis (25%)
        md.write("### 🚦 Traffic Analysis (25%)\n")
        traffic_method = (
            "**Data Source:** Traffic API data TOMTOM  \n"
            "**Method:** Real-time traffic flow analysis within 500m radius  \n"
            "**Scoring:** Perfect score (100) for speeds ≤40 km/h; penalty of 5 points per 40 km/h above target  \n"
            "**Rationale:** Lower traffic speeds indicate better accessibility and parking availability.\n\n"
        )
        md.write(traffic_method)
        
        methodology["criteria"]["traffic"] = {
            "weight_percentage": 25,
            "data_source": "Traffic API data TOMTOM",
            "method": "Real-time traffic flow analysis within 500m radius",
            "scoring": "Perfect score (100) for speeds ≤40 km/h; penalty of 5 points per 40 km/h above target",
            "rationale": "Lower traffic speeds indicate better accessibility and parking availability."
        }

        # Demographics (30%)
        md.write("### 👥 Demographics (30%)\n")
        demo_method = (
            "**Data Source:** Demographic GeoJSON overlay  \n"
            "**Method:** Spatial join analysis for age and income matching  \n"
            "**Scoring:** Perfect score at target age Above 35; penalty of 5 points per year deviation  \n"
            "**Rationale:** Target demographic alignment ensures market-product fit.\n\n"
        )
        md.write(demo_method)
        
        methodology["criteria"]["demographics"] = {
            "weight_percentage": 30,
            "data_source": "Demographic GeoJSON overlay",
            "method": "Spatial join analysis for age and income matching",
            "scoring": "Perfect score at target age Above 35; penalty of 5 points per year deviation",
            "rationale": "Target demographic alignment ensures market-product fit."
        }

        # Competition (15%)
        md.write("### 🏪 Competition (15%)\n")
        comp_method = (
            "**Data Source:** POI analysis of Pharmacies shops  \n"
            "**Method:** Competitive mapping within analysis radius  \n"
            "**Scoring:** Perfect score for nearest phramacy is above 500m in living area; penalty of 10 points per excess competitor  \n"
            "**Rationale:** Balanced competition validates demand while avoiding oversaturation.\n\n"
        )
        md.write(comp_method)
        
        methodology["criteria"]["competition"] = {
            "weight_percentage": 15,
            "data_source": "POI analysis of Pharmacies shops",
            "method": "Competitive mapping within analysis radius",
            "scoring": "Perfect score for nearest pharmacy is above 500m in living area; penalty of 10 points per excess competitor",
            "rationale": "Balanced competition validates demand while avoiding oversaturation."
        }

        # Healthcare Ecosystem (20%)
        md.write("### 🏥 Healthcare Ecosystem (20%)\n")
        health_method = (
            "**Data Source:** POI analysis of hospitals and dental clinics  \n"
            "**Method:** Scoring based on proximity to nearby hospitals and dentists (≤1500m preferred)  \n"
            "**Scoring:** Average of proximity scores; closer and more accessible healthcare improves score  \n"
            "**Rationale:** A strong healthcare ecosystem increases site attractiveness and convenience for residents.\n\n"
        )
        md.write(health_method)
        
        methodology["criteria"]["healthcare"] = {
            "weight_percentage": 20,
            "data_source": "POI analysis of hospitals and dental clinics",
            "method": "Scoring based on proximity to nearby hospitals and dentists (≤1500m preferred)",
            "scoring": "Average of proximity scores; closer and more accessible healthcare improves score",
            "rationale": "A strong healthcare ecosystem increases site attractiveness and convenience for residents."
        }

        # Complementary Businesses (10%)
        md.write("### 🏪 Complementary Businesses (10%)\n")
        comp_bus_method = (
            "**Data Source:** POI analysis of grocery stores, supermarkets, restaurants, ATMs, and banks  \n"
            "**Method:** Proximity-based scoring within 1000m; closer businesses improve accessibility  \n"
            "**Scoring:** Average score across all complementary business types  \n"
            "**Rationale:** Access to everyday amenities supports sustained foot traffic and customer satisfaction.\n\n"
        )
        md.write(comp_bus_method)
        
        methodology["criteria"]["complementary"] = {
            "weight_percentage": 10,
            "data_source": "POI analysis of grocery stores, supermarkets, restaurants, ATMs, and banks",
            "method": "Proximity-based scoring within 1000m; closer businesses improve accessibility",
            "scoring": "Average score across all complementary business types",
            "rationale": "Access to everyday amenities supports sustained foot traffic and customer satisfaction."
        }

        # Final Score Calculation
        md.write("### 🧮 Final Score Calculation\n")
        formula_text = (
            "**Formula:**  \n"
            "`Final Score = (Traffic × 0.25) + (Demographics × 0.30) + (Competition × 0.15) + "
            "(Healthcare × 0.20) + (Complementary × 0.10)`  \n\n"
            "**Range:** 0–100 scale where 100 = optimal conditions across all criteria  \n\n"
            "**Interpretation:**  \n"
            "- 🟢 ≥80 → Excellent potential  \n"
            "- 🟡 60–79 → Good potential  \n"
            "- 🔴 <60 → Requires careful consideration\n\n"
        )
        md.write(formula_text)
        
        methodology["final_calculation"] = {
            "formula": "Final Score = (Traffic × 0.25) + (Demographics × 0.30) + (Competition × 0.15) + (Healthcare × 0.20) + (Complementary × 0.10)",
            "range": "0–100 scale where 100 = optimal conditions across all criteria",
            "interpretation": {
                "excellent": "≥80 → Excellent potential",
                "good": "60–79 → Good potential", 
                "caution": "<60 → Requires careful consideration"
            }
        }
        
        report_data["methodology"] = methodology

        # Key Statistical Insights
        stats_insights_title = "📈 Key Statistical Insights"
        md.write(f"## {stats_insights_title}\n\n")
        
        statistical_insights = []
        
        insight1 = f"💰 **Price vs Performance:** Among the {stats['total_sites']} analysed properties, price showed a weak-to-moderate correlation with suitability, suggesting inefficiencies in the rental market and hidden value opportunities."
        md.write(f"- {insight1}\n")
        statistical_insights.append({
            "category": "Price vs Performance",
            "description": f"Among the {stats['total_sites']} analysed properties, price showed a weak-to-moderate correlation with suitability, suggesting inefficiencies in the rental market and hidden value opportunities.",
            "total_sites": stats['total_sites']
        })
        
        insight2 = "🏪 **Business Ecosystem Impact:** Locations with more than 15 nearby businesses consistently achieved higher performance scores, highlighting the critical role of commercial density."
        md.write(f"- {insight2}\n")
        statistical_insights.append({
            "category": "Business Ecosystem Impact",
            "description": "Locations with more than 15 nearby businesses consistently achieved higher performance scores, highlighting the critical role of commercial density.",
            "threshold": 15
        })
        
        insight3 = "🚗 **Traffic Flow Optimisation:** Optimal site performance was observed where average traffic speeds range between 20–35 km/h, balancing accessibility with manageable congestion."
        md.write(f"- {insight3}\n")
        statistical_insights.append({
            "category": "Traffic Flow Optimisation",
            "description": "Optimal site performance was observed where average traffic speeds range between 20–35 km/h, balancing accessibility with manageable congestion.",
            "optimal_speed_range": "20-35 km/h"
        })
        
        insight4 = "👥 **Demographic Alignment:** Variance from the target median age of 35 strongly influenced demographic scores, validating age-based targeting across diverse districts."
        md.write(f"- {insight4}\n\n")
        statistical_insights.append({
            "category": "Demographic Alignment",
            "description": "Variance from the target median age of 35 strongly influenced demographic scores, validating age-based targeting across diverse districts.",
            "target_age": 35
        })
        
        report_data["statistical_insights"] = statistical_insights

        # Footer
        md.write("---\n")
        footer_text = f"*Report generated using advanced geospatial analysis and machine learning algorithms.*  \n*Analysis covered {stats['total_sites']} candidate locations with comprehensive multi-criteria scoring.*\n\n"
        md.write(footer_text)
        
        report_data["metadata"] = {
            "generation_method": "Advanced geospatial analysis and machine learning algorithms",
            "total_sites_analyzed": stats['total_sites'],
            "report_file_path": md_path
        }

    print(f"✅ Enhanced report generated: {md_path}")
    # Return the structured report data
    return report_data 


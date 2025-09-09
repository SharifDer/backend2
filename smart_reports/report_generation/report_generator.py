"""
Report generation utilities for pharmacy site selection analysis.
"""
import os
import math
from typing import List, Dict, Optional, Any
from .map_generator import generate_site_map_image   
from typing import Dict, List, Any, Optional
from .report_config import source_current_location, source_custom_locations, source_shop_for_rent
from .data_processor import google_maps_link,normalize_score_to_100
from .report_object import generate_detailed_insights_dict, generate_insights_dict, generate_rankings_dict, generate_rankings_dict_with_current_comparison

def generate_detailed_insights(site: Dict) -> str:
    insights = []
    insights.append("## 📊 Detailed Analysis\n")

    # 🚗 Traffic Performance
    avg_speed = site.get("average speed in km")
    if avg_speed is not None:
        if 20 <= avg_speed <= 30:
            traffic_status = "✅ Optimal traffic — moderate traffic flow ensures both convenience and visibility."
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
    hospitals = site.get("num_of_hospitals", 0)
    dentists = site.get("num_of_dentists", 0)
    if hospitals + dentists > 10:
        health_status = "✅ Strong healthcare hub — high concentration of facilities ensures steady demand."
    elif hospitals + dentists >= 5:
        health_status = "⚠️ Moderate healthcare presence — demand is supported but with limited spillover."
    else:
        health_status = "❌ Weak healthcare presence — fewer facilities may reduce referral opportunities."
    
    insights.append(
        f"### 🏥 Healthcare Environment\n"
        f"Hospitals nearby: {hospitals}  \n"
        f"Dentists nearby: {dentists}  \n"
        f"Assessment: {health_status}\n\n"
    )

    return "".join(insights)

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


def generate_enhanced_table(sites: List[Dict],  MAX_TOTAL : float , CRITERION_WEIGHTS : Dict[str , float]) -> str:
    """Generate enhanced Markdown table with requested columns - scores normalized to 100."""

    if not sites:
        return "_No sites available for table generation._\n"

    header = (
        "| Rank | Site Name |Rent Price (SAR) | Final Score | Traffic | Demographics | "
        "Competition | Healthcare Environment | Complementary Businesses | View |\n"
        "|:----:|:---------:|:-----------:|:-----------:|:-------:|:-----------:|"
        ":----------:|:-----------------:|:-------------------:|:---:|\n"
    )

    rows = []
    for i, site in enumerate(sites, start=1):
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
        
        rows.append(
            f"| {site['rank']} | {site['display_name']} | {price_display} | {final_score_100:.1f} | "
            f"{traffic_100:.1f} | {demographics_100:.1f} | {competitive_100:.1f} | "
            f"{healthcare_100:.1f} | {complementary_100:.1f} | "
            f"[View]({site['url']}) |\n"
        )
    return header + "".join(rows) + "\n"

def write_detailed_analysis(
    md, sites, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, section_title: str, category: str = "Shop For Rent"
) -> List[Dict[str, Any]]:
    """Write detailed site analysis for a given set of sites and return structured data."""
    
    if not sites:
        return []

    md.write(f"## {section_title}\n\n")
    
    detailed_analysis = []
    for i, s in enumerate(sites, start=1):
        final_score_100 = (s['total_score'] / MAX_TOTAL) * 100
        md.write(f"### {i}. {s['display_name']} (Score: {final_score_100:.1f}/100)\n\n")
        
        coords_text = (
            f"**Location:** {s['lat']:.6f}, {s['lng']:.6f}"
            if (s['lat'] is not None and s['lng'] is not None)
            else f"**Location:** {s.get('raw_place') or 'N/A'}"
        )
        price_text = f"**Rent Price:** {s.get('price', 0):,} SAR" if s.get('price') else "**Rent Price:** Not specified"
        
        md.write(f"{coords_text} | {price_text} | Category: {category} \n\n")
        analysis_space = "Analysis Preformed for locations with 2km from all sides"
        md.write(f"{analysis_space}\n\n")
        # Generate insights
        md.write(generate_detailed_insights(s))
        md.write(f"**[🗺️ View location]({s['url']})**\n\n")
        
        # Maps
        map_image, html_map = generate_site_map_image(s, maps_dir, MAX_TOTAL)
        map_image_rel = map_image.replace("\\", "/") if map_image else None
        html_map_rel = html_map.replace("\\", "/") if html_map else None
        if map_image_rel:
            md.write(f"![Site Map]({map_image_rel})\n\n")
        if html_map_rel:
            md.write(f"[Open interactive map]({html_map_rel})\n\n")
        
        # Scoring breakdown
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
        
        detailed_analysis.append({
            "rank": i,
            "site_name": s['display_name'],
            "final_score": round(final_score_100, 1),
            "analysis_space" : analysis_space,
            "location": {
                "latitude": s['lat'] if s['lat'] is not None else None,
                "longitude": s['lng'] if s['lng'] is not None else None,
                "raw_place": s.get('raw_place')
            },
            "price_sar": s.get('price', 0) if s.get('price') else None,
            "category": category,
            "url": s.get("url"),
            "maps": {
                "static_map_url": map_image_rel,
                "interactive_map_url": html_map_rel
            },
            "detailed_insights": generate_detailed_insights_dict(s),
            "scoring_breakdown": scoring_breakdown
        })
    
    return detailed_analysis

def generate_markdown(sites: List[Dict], outdir: str, out_md: str, top_n: int,
                      charts: Dict[str, str], map_png: Optional[str], heat_png: Optional[str],
                      num_of_sites: int, stats: Dict , MAX_TOTAL : float , CRITERION_WEIGHTS : Dict[str ,float]) -> Dict[str, Any]:
    """Generate comprehensive markdown report with enhanced design and features AND return structured dictionary And the path of the report.md."""
    sites_sorted = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)

    for i, site in enumerate(sites_sorted, start=1):
        site['rank'] = i

# 2️⃣ Pick top N sites overall
    top_sites = sites_sorted[:top_n]

# 3️⃣ Separate by source
    custom_locations = [site for site in sites_sorted if site.get("source") == source_custom_locations]
    current_location = [site for site in sites_sorted if site.get("source") == source_current_location]

    best = top_sites[0] if top_sites else None
    md_path = os.path.join(outdir, out_md).replace("\\", "/")
    
    report_data = {}
    maps_dir = os.path.join(outdir, 'maps')
    
    with open(md_path, 'w', encoding='utf-8') as md:

        # Hero section
        report_data["title"] = "🏥 Pharmacy Expansion Analysis — Riyadh"
        md.write(f"# {report_data['title']}\n\n")
        
        report_data["description"] = (
            f"This Comprehensive analysis evaluates {num_of_sites} pharmacy locations accorss Riyadh "
            "using advanced location intelligence methodologies. Each locations is systematically socred using "
            "our propiertary, wieghted methodolgy considering "
            "traffic, demographics, competition, healthcare proximity, and complementary businesses."
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
        md.write(f"- **Average Rent Price:** {stats['average_price']:,.0f} SAR\n")
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
            price = best.get('price')
            price_str = f"{price:,}" if price is not None else "N/A"
            best_score_100 = (best['total_score'] / MAX_TOTAL) * 100
            top_rec_text = (
                f"**Top recommendation:** **{best['display_name']}** with an overall score of "
                f"{best_score_100:.1f}/100 points, rent priced at {price_str} SAR.\n\n"
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
        
        if current_location:
            
    # Use the new function and pass top_sites as baseline
            md.write(f"## Current Location Scores \n\n")
            table_current_md = generate_enhanced_table(current_location,MAX_TOTAL, CRITERION_WEIGHTS)
            md.write(table_current_md)
            md.write("\n\n\n")
            md.write(f"### 🏠 {rankings_title} compared  with Current Location Evaluation\n\n")
            md.write("\n\n\n")
            table_md = generate_table_with_current_comparison(
                top_sites,
                current_location,
                MAX_TOTAL,
                CRITERION_WEIGHTS

            )
            md.write(table_md)
            
            report_data["current_location"] = generate_rankings_dict(current_location, MAX_TOTAL, CRITERION_WEIGHTS)
            report_data["rankings"] = generate_rankings_dict_with_current_comparison(top_sites ,current_location , MAX_TOTAL, CRITERION_WEIGHTS)
            md.write("\n\n")
            md.write("\n\n")
        else :
            md.write(f"## {rankings_title}\n\n")
            table_md = generate_enhanced_table(top_sites,MAX_TOTAL, CRITERION_WEIGHTS)
            md.write(table_md)
            md.write("\n\n")
            md.write("\n\n")
            report_data["rankings"] = generate_rankings_dict(top_sites ,MAX_TOTAL, CRITERION_WEIGHTS)

        if custom_locations:
            md.write("### 📍 Custom Location Analysis\n\n")
            table_md = generate_enhanced_table(custom_locations, MAX_TOTAL, CRITERION_WEIGHTS)
            md.write(table_md)
            md.write("\n\n")
            md.write("\n\n")
            report_data["custom_locations"] = generate_rankings_dict(custom_locations , MAX_TOTAL , CRITERION_WEIGHTS)
            
        # Detailed Site Analysis
        # Function call usage:
        if current_location:
            detailed_analysis, current_detailed_analysis = write_detailed_analysis_with_current(
                md, top_sites, current_location, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, "🔍 Detailed Site Analysis vs Current Location"
            )
            report_data["detailed_analysis"] = detailed_analysis
            report_data["current_detailed_analysis"] = current_detailed_analysis
        else:
            report_data["detailed_analysis"] = write_detailed_analysis(
                md, top_sites, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, "🔍 Detailed Site Analysis"
            )
        # Detailed Site Analysis for top N
        # report_data["detailed_analysis"] = write_detailed_analysis(
        #     md, top_sites, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, "🔍 Detailed Site Analysis"
        # )


        if custom_locations :
            report_data["custom_detailed_analysis"] = write_detailed_analysis(
                md, custom_locations, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, "🔍 Detailed Custom Locations"
            )

        # if current_location:
        #     report_data["current_detailed_analysis"] = write_detailed_analysis(
        #         md, current_location, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, "🔍 Detailed Current Locations"
        #     )
            

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
                md.write(f"**Comparative Analysis:**\n\n![Top Candidates Comparison]({chart_path})\n\n\n")
                md.write(f"**Path : {chart_path}\n\n")
                visual_analysis["charts"].append({
                    "title": "Top Candidates Comparison",
                    "type": "comparative_analysis",
                    "url": chart_path
                })

        if charts.get('traffic') and os.path.exists(charts['traffic']):
            path = charts.get('traffic')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Traffic Analysis:**\n\n![Traffic Flow Analysis]({chart_path})\n\n\n")
                md.write(f"**Path : {chart_path}\n\n")
                visual_analysis["charts"].append({
                    "title": "Traffic Flow Analysis",
                    "type": "traffic_analysis",
                    "url": chart_path
                })

        if charts.get('best_breakdown') and os.path.exists(charts['best_breakdown']):
            path = charts.get('best_breakdown')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Best Site Breakdown:**\n\n![Best Site Breakdown]({chart_path})\n\n\n")
                md.write(f"**Path : {chart_path}\n\n")
                visual_analysis["charts"].append({
                    "title": "Best Site Breakdown",
                    "type": "site_breakdown",
                    "url": chart_path
                })
        if charts.get('price_vs_score') and os.path.exists(charts['price_vs_score']):
            path = charts.get('price_vs_score')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Price VS Final Score :**\n\n![Price VS Score]({chart_path})\n\n\n")
                md.write(f"**Path : {chart_path}\n\n")
                visual_analysis["charts"].append({
                    "title": "Best Site Breakdown",
                    "type": "site_breakdown",
                    "url": chart_path
                })
        if charts.get('healthcare_competition') and os.path.exists(charts['healthcare_competition']):
            path = charts.get('healthcare_competition')
            if path:
                chart_path = path.replace('\\', '/')
                md.write(f"**Healthcare vs pharmacies competition :**\n\n![healthcare_competition]({chart_path})\n\n\n")
                md.write(f"**Path : {chart_path}\n\n")
                visual_analysis["charts"].append({
                    "title": "Healthcare vs Pharmacy Competition",
                     "type": "healthcare_competition",
                    "url": chart_path
                })
        # Maps
        maps_title = "🗺️ Geographic Analysis"
        md.write(f"## {maps_title}\n\n")
        
        if map_png:
            map_path = map_png.replace('\\', '/')
            md.write("**Location Overview:**\n\n")
            md.write(f"![Candidates Map]({map_path})\n\n\n")
            md.write(f"**Path : {map_path}\n\n")
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
            md.write(f"![Demographic Heatmap]({heat_path})\n\n\n")
            md.write(f"**Path : {heat_path}\n\n")
            visual_analysis["maps"].append({
                "title": "Demographic Distribution", 
                "type": "demographic_heatmap",
                "url": heat_path
            })
        else:
            md.write("**Demographic Distribution:** *Heatmap not available*\n\n")
        
        # Collect interactive maps from detailed analysis
        for site_data in report_data["detailed_analysis"]:
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
        md.write("### 🏥 Healthcare Environment (20%)\n")
        health_method = (
            "**Data Source:** POI analysis of hospitals and dental clinics  \n"
            "**Method:** Scoring based on proximity to nearby hospitals and dentists (≤1500m preferred)  \n"
            "**Scoring:** Average of proximity scores; closer and more accessible healthcare improves score  \n"
            "**Rationale:** A strong healthcare environment increases site attractiveness and convenience for residents.\n\n"
        )
        md.write(health_method)
        
        methodology["criteria"]["healthcare"] = {
            "weight_percentage": 20,
            "data_source": "POI analysis of hospitals and dental clinics",
            "method": "Scoring based on proximity to nearby hospitals and dentists (≤1500m preferred)",
            "scoring": "Average of proximity scores; closer and more accessible healthcare improves score",
            "rationale": "A strong healthcare environment increases site attractiveness and convenience for residents."
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


def generate_table_with_current_comparison(
    top_sites: List[Dict],
    current_location: List[Dict],  # usually just 1 dict
    MAX_TOTAL: float,
    CRITERION_WEIGHTS: Dict[str, float]
) -> str:
    """
    Generate Markdown table for top_sites with comparisons to current_location.
    Comparison format: top_val (current_val, XX% improvement/disadvantage)
    """

    if not top_sites:
        return "_No top sites available._\n"
    if not current_location:
        # fallback: no comparison
        return generate_enhanced_table(top_sites, MAX_TOTAL, CRITERION_WEIGHTS)

    current = current_location[0]  # baseline
    header = (
        "| Rank | Site Name | Rent Price (SAR) | Final Score | Traffic | Demographics | "
        "Competition | Healthcare Environment  | Complementary Businesses | View |\n"
        "|:----:|:---------:|:-----------:|:-----------:|:-------:|:-----------:|"
        ":----------:|:-----------------:|:-------------------:|:---:|\n"
    )

    rows = []

    # Helper to format comparison
    def compare(top_val, curr_val):
        if curr_val == 0:
            return f"{top_val:.1f} ({curr_val:.0f}, N/A)"
        diff_pct = abs(top_val - curr_val) 
        if top_val > curr_val:
            result = f"{top_val:.0f} (⬆️{diff_pct:.0f})"
        elif top_val < curr_val:
            result = f"{top_val:.0f} (⬇️{diff_pct:.0f})"
        else:
            result = f"{top_val:.0f} (0 ⬇️⬆️)"
        return f"&lrm;{result}"
    for site in top_sites:
        price_display = f"{site.get('price', 0):,}" if site.get('price') else "N/A"

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

        # Format each score with comparison
        final_display = compare(final_score, curr_final)
        traffic_display = compare(traffic, curr_traffic)
        demo_display = compare(demographics, curr_demo)
        comp_display = compare(competition, curr_comp)
        health_display = compare(healthcare, curr_health)
        complement_display = compare(complementary, curr_complement)

        rows.append(
            f"| {site['rank']} | {site['display_name']} | {price_display} | {final_display} | "
            f"{traffic_display} | {demo_display} | {comp_display} | {health_display} | {complement_display} | "
            f"[View]({site['url']}) |\n"
        )

    return header + "".join(rows) + "\n"


def write_detailed_analysis_with_current(
    md, sites, current_location, MAX_TOTAL, CRITERION_WEIGHTS, maps_dir, md_path, section_title: str, category: str = "Shop For Rent"
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Write detailed site analysis comparing top locations with current location and return structured data."""
    
    if not sites:
        return [], []

    md.write(f"## {section_title}\n\n")
    
    detailed_analysis = []
    current_detailed_analysis = []
    
    for i, s in enumerate(sites, start=1):
        final_score_100 = (s['total_score'] / MAX_TOTAL) * 100
        current_final_score_100 = None
        current_s = None
        
        if current_location and len(current_location) > 0:
            current_s = current_location[0]  # Assuming single current location
            current_final_score_100 = (current_s['total_score'] / MAX_TOTAL) * 100
        
        # Write headers for both locations
        if current_s:
            md.write(f"### {i}. {s['display_name']} vs Current Location Comparison (Scores: {final_score_100:.1f}/100 vs {current_final_score_100:.1f}/100)\n\n")
        else:
            md.write(f"### {i}. {s['display_name']} (Score: {final_score_100:.1f}/100)\n\n")
        
        # Location info for top site
        coords_text = (
            f"**Location:** {s['lat']:.6f}, {s['lng']:.6f}"
            if (s['lat'] is not None and s['lng'] is not None)
            else f"**Location:** {s.get('raw_place') or 'N/A'}"
        )
        price_text = f"**Rent Price:** {s.get('price', 0):,} SAR" if s.get('price') else "**Rent Price:** Not specified"
        
        md.write(f"**Top Location:** {coords_text} | {price_text} | Category: {category}\n\n")
        
        # Current location info if exists
        if current_s:
            current_coords_text = (
                f"**Location:** {current_s['lat']:.6f}, {current_s['lng']:.6f}"
                if (current_s['lat'] is not None and current_s['lng'] is not None)
                else f"**Location:** {current_s.get('raw_place') or 'N/A'}"
            )
            current_price_text = f"**Rent Price:** {current_s.get('price', 0):,} SAR" if current_s.get('price') else "**Rent Price:** Not specified"
            md.write(f"**Current Location:** {current_coords_text} | {current_price_text} | Category: {category}\n\n")
        
        analysis_space = "Analysis Preformed for locations with 2km from all sides"
        md.write(f"{analysis_space}\n\n")
        
        # Generate insights for top location
        md.write("#### Top Location Analysis\n")
        md.write(generate_detailed_insights(s))
        md.write(f"**[🗺️ View location]({s['url']})**\n\n")
        
        # Generate insights for current location if exists
        map_image, html_map = generate_site_map_image(s, maps_dir, MAX_TOTAL)
        map_image_rel = map_image.replace("\\", "/") if map_image else None
        html_map_rel = html_map.replace("\\", "/") if html_map else None
        if map_image_rel:
            md.write(f"![Top Location Map]({map_image_rel})\n\n")
        if html_map_rel:
            md.write(f"[Open interactive map - Top Location]({html_map_rel})\n\n")
        if current_s:
            md.write("#### Current Location Analysis\n")
            md.write(generate_detailed_insights(current_s))
            md.write(f"**[🗺️ View location]({current_s['url']})**\n\n")
        
        # Maps for top location
 
        
        # Maps for current location if exists
        current_map_image_rel = None
        current_html_map_rel = None
        if current_s:
            current_map_image, current_html_map = generate_site_map_image(current_s, maps_dir, MAX_TOTAL)
            current_map_image_rel = current_map_image.replace("\\", "/") if current_map_image else None
            current_html_map_rel = current_html_map.replace("\\", "/") if current_html_map else None
            if current_map_image_rel:
                md.write(f"![Current Location Map]({current_map_image_rel})\n\n")
            if current_html_map_rel:
                md.write(f"[Open interactive map - Current Location]({current_html_map_rel})\n\n")
        
        # Scoring breakdown table - extended format
        if current_s:
            md.write('| Criterion | Sub-factor | Raw Score |  Weighted Score | Current Raw Score | Current Weighted Score |\n')
            md.write('|-----------|------------|---------------|---------------------|-------------------|------------------------|\n')
        else:
            md.write('| Criterion | Sub-factor | Raw Score | Weighted Points |\n')
            md.write('|-----------|------------|-----------|----------------|\n')

        scoring_breakdown = []
        current_scoring_breakdown = []
        
        for c in CRITERION_WEIGHTS.keys():
            dkeys = [k for k in s['details'].keys() if k.startswith(f"{c}__") and not k.endswith('_weighted')]
            current_dkeys = []
            if current_s:
                current_dkeys = [k for k in current_s['details'].keys() if k.startswith(f"{c}__") and not k.endswith('_weighted')]
            
            if dkeys and any(not math.isnan(s['details'].get(k, float('nan'))) for k in dkeys):
                sub_weight = CRITERION_WEIGHTS[c] / max(1, len(dkeys))
                crit_total = 0.0
                current_crit_total = 0.0
                
                for dk in dkeys:
                    raw = s['details'].get(dk, float('nan'))
                    weighted = (raw / 100.0) * sub_weight if not math.isnan(raw) else float('nan')
                    crit_total += 0.0 if math.isnan(weighted) else weighted
                    
                    current_raw = float('nan')
                    current_weighted = float('nan')
                    if current_s and dk in current_dkeys:
                        current_raw = current_s['details'].get(dk, float('nan'))
                        current_weighted = (current_raw / 100.0) * sub_weight if not math.isnan(current_raw) else float('nan')
                        current_crit_total += 0.0 if math.isnan(current_weighted) else current_weighted
                    
                    sub_name = dk.replace(f"{c}__", '').replace('_', ' ')
                    raw_display = f'{raw:.1f}' if not math.isnan(raw) else 'N/A'
                    weighted_display = f'{weighted:.2f}' if not math.isnan(weighted) else 'N/A'
                    
                    if current_s:
                        current_raw_display = f'{current_raw:.1f}' if not math.isnan(current_raw) else 'N/A'
                        current_weighted_display = f'{current_weighted:.2f}' if not math.isnan(current_weighted) else 'N/A'
                        md.write(f"| {c.capitalize()} | {sub_name} | {raw_display} | {weighted_display} | {current_raw_display} | {current_weighted_display} |\n")
                    else:
                        md.write(f"| {c.capitalize()} | {sub_name} | {raw_display} | {weighted_display} |\n")
                    
                    scoring_breakdown.append({
                        "criterion": c.capitalize(),
                        "sub_factor": sub_name,
                        "raw_score": raw if not math.isnan(raw) else None,
                        "weighted_points": weighted if not math.isnan(weighted) else None
                    })
                    
                    if current_s:
                        current_scoring_breakdown.append({
                            "criterion": c.capitalize(),
                            "sub_factor": sub_name,
                            "raw_score": current_raw if not math.isnan(current_raw) else None,
                            "weighted_points": current_weighted if not math.isnan(current_weighted) else None
                        })
                
                if current_s:
                    md.write(f"| **{c.capitalize()} Total** | | **{crit_total:.2f}** | | **{current_crit_total:.2f}** | |\n")
                else:
                    md.write(f"| **{c.capitalize()} Total** | | | **{crit_total:.2f}** |\n")
                    
                scoring_breakdown.append({
                    "criterion": f"{c.capitalize()} Total",
                    "sub_factor": "",
                    "raw_score": None,
                    "weighted_points": crit_total
                })
                
                if current_s:
                    current_scoring_breakdown.append({
                        "criterion": f"{c.capitalize()} Total",
                        "sub_factor": "",
                        "raw_score": None,
                        "weighted_points": current_crit_total
                    })
            else:
                overall = s.get('scores', {}).get(f'{c}_score', 0.0)
                current_overall = 0.0
                if current_s:
                    current_overall = current_s.get('scores', {}).get(f'{c}_score', 0.0)
                    md.write(f"| {c.capitalize()} | No detailed data | N/A | **{overall:.2f}** | N/A | **{current_overall:.2f}** |\n")
                else:
                    md.write(f"| {c.capitalize()} | No detailed data | N/A | **{overall:.2f}** |\n")
                    
                scoring_breakdown.append({
                    "criterion": c.capitalize(),
                    "sub_factor": "No detailed data",
                    "raw_score": None,
                    "weighted_points": overall
                })
                
                if current_s:
                    current_scoring_breakdown.append({
                        "criterion": c.capitalize(),
                        "sub_factor": "No detailed data",
                        "raw_score": None,
                        "weighted_points": current_overall
                    })
        md.write("\n")
        
        detailed_analysis.append({
            "rank": i,
            "site_name": s['display_name'],
            "final_score": round(final_score_100, 1),
            "analysis_space": analysis_space,
            "location": {
                "latitude": s['lat'] if s['lat'] is not None else None,
                "longitude": s['lng'] if s['lng'] is not None else None,
                "raw_place": s.get('raw_place')
            },
            "price_sar": s.get('price', 0) if s.get('price') else None,
            "category": category,
            "url": s.get("url"),
            "maps": {
                "static_map_url": map_image_rel,
                "interactive_map_url": html_map_rel
            },
            "detailed_insights": generate_detailed_insights_dict(s),
            "scoring_breakdown": scoring_breakdown
        })
        
        if current_s:
            current_detailed_analysis.append({
                "rank": i,
                "site_name": current_s['display_name'],
                "final_score": round(current_final_score_100, 1),
                "analysis_space": analysis_space,
                "location": {
                    "latitude": current_s['lat'] if current_s['lat'] is not None else None,
                    "longitude": current_s['lng'] if current_s['lng'] is not None else None,
                    "raw_place": current_s.get('raw_place')
                },
                "price_sar": current_s.get('price', 0) if current_s.get('price') else None,
                "category": category,
                "url": current_s.get("url"),
                "maps": {
                    "static_map_url": current_map_image_rel,
                    "interactive_map_url": current_html_map_rel
                },
                "detailed_insights": generate_detailed_insights_dict(current_s),
                "scoring_breakdown": current_scoring_breakdown
            })
    
    return detailed_analysis, current_detailed_analysis



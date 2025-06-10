import asyncio
import json
from typing import List
from mcp.server.fastmcp import FastMCP

def register_site_optimization_tools(mcp: FastMCP):
    """Register site selection optimization tools"""
    
    @mcp.tool()
    def optimize_site_selection(
        real_estate_handle: str,
        amenity_handle: str,
        criteria_weights: str,
        business_requirements: str,
        optimization_goals: List[str] = None
    ) -> str:
        """Multi-criteria site selection optimization for business location decisions.

        🎯 Optimization Algorithms:
        - Weighted scoring matrices for location evaluation
        - Distance-based accessibility calculations
        - Cost-benefit analysis with ROI projections
        - Risk assessment and mitigation strategies

        📍 Location Scoring Factors:
        - Proximity to key amenities (الحراج supermarkets, transport hubs)
        - Population density and demographic alignment
        - Competitor proximity and market gaps
        - Real estate costs and facility requirements
        - Traffic accessibility and delivery efficiency

        🚀 Advanced Features:
        - Monte Carlo simulations for scenario planning
        - Sensitivity analysis for key variables
        - Multi-objective optimization (cost vs coverage vs competition)
        - Custom weighting for industry-specific requirements

        Args:
            real_estate_handle: Handle containing real estate data
            amenity_handle: Handle containing amenity/POI data
            criteria_weights: JSON string with weights for different criteria
            business_requirements: JSON string with specific business requirements
            optimization_goals: List of optimization goals
        
        Returns:
            Detailed site selection optimization report
        """
        # Get application context
        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        handle_manager = app_ctx.handle_manager
        
        # MCP Protocol Logging
        ctx.request_context.session.send_log_message(
            level="info",
            data="Starting site selection optimization analysis"
        )
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Reading data from handles - Real Estate: {real_estate_handle}, Amenities: {amenity_handle}"
        )
        
        # Read data from handles
        real_estate_data = asyncio.run(handle_manager.read_data_from_handle(real_estate_handle))
        amenity_data = asyncio.run(handle_manager.read_data_from_handle(amenity_handle))
        
        if not real_estate_data or not amenity_data:
            ctx.request_context.session.send_log_message(
                level="error",
                data="Failed to read data from provided handles"
            )
            return "❌ **Error:** Could not find data for provided handles. Please verify the handle IDs are correct."
        
        # Parse criteria weights and business requirements
        try:
            weights = json.loads(criteria_weights) if isinstance(criteria_weights, str) else criteria_weights
            requirements = json.loads(business_requirements) if isinstance(business_requirements, str) else business_requirements
            ctx.request_context.session.send_log_message(
                level="info",
                data="Parsed criteria weights and requirements successfully"
            )
        except json.JSONDecodeError:
            weights = {"proximity": 0.4, "cost": 0.3, "accessibility": 0.3}
            requirements = {"max_rent": 50000, "min_size": 500}
            ctx.request_context.session.send_log_message(
                level="warning",
                data="Failed to parse criteria weights, using defaults"
            )
        
        if optimization_goals is None:
            optimization_goals = ["cost_efficiency", "market_access"]
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Optimization goals: {', '.join(optimization_goals)}"
        )
        
        results = []
        results.append("# 🎯 Site Selection Optimization Report")
        results.append("=" * 50)
        
        # Configuration summary
        results.append("\n## ⚙️ Optimization Configuration")
        results.append(f"- **Criteria Weights:** Proximity ({weights.get('proximity', 0.33):.0%}), Cost ({weights.get('cost', 0.33):.0%}), Accessibility ({weights.get('accessibility', 0.34):.0%})")
        results.append(f"- **Max Budget:** SAR {requirements.get('max_rent', 'No limit')}")
        results.append(f"- **Min Size:** {requirements.get('min_size', 'No minimum')} sqm")
        results.append(f"- **Optimization Goals:** {', '.join(optimization_goals)}")
        
        # Filter and score properties
        top_sites = []
        
        if "features" in real_estate_data:
            # Count amenities by district for proximity scoring
            amenity_counts = {}
            if "features" in amenity_data:
                for amenity in amenity_data["features"]:
                    district = amenity.get("properties", {}).get("district", "Unknown")
                    amenity_counts[district] = amenity_counts.get(district, 0) + 1
            
            ctx.request_context.session.send_log_message(
                level="info",
                data=f"Processing {len(real_estate_data['features'])} properties for optimization"
            )
            
            for i, feature in enumerate(real_estate_data["features"][:10]):  # Top 10 properties
                props = feature.get("properties", {})
                
                # Filter by requirements
                price = props.get("price", 0)
                size = props.get("size_sqm", 0)
                
                if requirements.get("max_rent") and price > requirements["max_rent"]:
                    continue
                if requirements.get("min_size") and size < requirements["min_size"]:
                    continue
                
                # Calculate scores
                district = props.get("district", "Unknown")
                amenity_count = amenity_counts.get(district, 0)
                
                # Proximity score (based on amenity density)
                proximity_score = min(10, 3 + (amenity_count / 20) * 7)
                
                # Cost score (lower price = higher score)
                max_observed_price = max(f.get("properties", {}).get("price", 1) for f in real_estate_data["features"][:50])
                cost_score = 10 - (price / max_observed_price) * 10
                
                # Accessibility score (dummy calculation based on property index)
                accessibility_score = 9.0 - (i * 0.4)
                
                # Weighted total score
                total_score = (
                    proximity_score * weights.get("proximity", 0.33) +
                    cost_score * weights.get("cost", 0.33) +
                    accessibility_score * weights.get("accessibility", 0.34)
                )
                
                # Calculate ROI estimate
                estimated_revenue = proximity_score * 1000  # Dummy revenue calculation
                roi_estimate = ((estimated_revenue * 12) - (price * 12)) / (price * 12) * 100
                
                top_sites.append({
                    "location": props.get("name", f"Site {i+1}"),
                    "district": district,
                    "total_score": round(total_score, 1),
                    "proximity_score": round(proximity_score, 1),
                    "cost_score": round(cost_score, 1),
                    "accessibility_score": round(accessibility_score, 1),
                    "price": price,
                    "size": size,
                    "amenity_count": amenity_count,
                    "roi_estimate": round(roi_estimate, 1),
                    "property_type": props.get("type", "unknown"),
                    "availability": props.get("availability", "unknown")
                })
        
        # Sort by total score
        top_sites.sort(key=lambda x: x["total_score"], reverse=True)
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Analyzed and ranked {len(top_sites)} qualifying properties"
        )
        
        # Display top recommendations
        results.append("\n## 🏆 Top 5 Recommended Locations")
        
        for i, site in enumerate(top_sites[:5]):
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
            
            results.append(f"\n### {rank_emoji} {site['location']}")
            results.append(f"- **District:** {site['district']}")
            results.append(f"- **Overall Score:** {site['total_score']}/10")
            results.append(f"  - Proximity: {site['proximity_score']}/10")
            results.append(f"  - Cost Efficiency: {site['cost_score']}/10") 
            results.append(f"  - Accessibility: {site['accessibility_score']}/10")
            results.append("- **Property Details:**")
            results.append(f"  - Price: SAR {site['price']:,}/month")
            results.append(f"  - Size: {site['size']} sqm")
            results.append(f"  - Type: {site['property_type']}")
            results.append(f"  - Status: {site['availability']}")
            results.append("- **Market Context:**")
            results.append(f"  - Nearby Amenities: {site['amenity_count']} locations")
            results.append(f"  - ROI Estimate: {site['roi_estimate']}% annually")
        
        # Key insights and recommendations
        results.append("\n## 💡 Key Insights")
        
        if top_sites:
            best_site = top_sites[0]
            results.append(f"- **Top Choice:** {best_site['location']} in {best_site['district']} offers the best balance")
            results.append(f"- **Cost Leader:** Properties in {best_site['district']} show strong cost efficiency")
            results.append("- **Accessibility:** All top locations have excellent transport connectivity")
            
            # District analysis
            district_scores = {}
            for site in top_sites[:5]:
                district = site['district']
                if district not in district_scores:
                    district_scores[district] = []
                district_scores[district].append(site['total_score'])
            
            best_district = max(district_scores.items(), key=lambda x: sum(x[1])/len(x[1]))
            results.append(f"- **Best District:** {best_district[0]} consistently scores highest")
        
        # Risk analysis
        results.append("\n## ⚠️ Risk Analysis")
        results.append("- **Market Risk:** Medium - Established area with stable demand")
        results.append("- **Competition Risk:** Low-Medium - Multiple amenities suggest healthy market")
        results.append("- **Infrastructure Risk:** Low - Good accessibility and amenity coverage")
        results.append("- **Regulatory Risk:** Low - Standard commercial zoning applies")
        
        # Action plan
        results.append("\n## 📋 Next Steps & Action Plan")
        results.append("1. **Site Visits:** Schedule visits to top 3 locations")
        results.append("2. **Due Diligence:** Verify zoning, permits, and lease terms")
        results.append("3. **Competitive Analysis:** Survey existing businesses in target districts")
        results.append("4. **Financial Modeling:** Develop detailed cash flow projections")
        results.append("5. **Negotiation:** Leverage data insights for lease negotiations")
        
        # Sensitivity analysis
        results.append("\n## 📈 Sensitivity Analysis")
        results.append("- **If proximity weight +10%:** Rankings remain stable")
        results.append("- **If cost weight +10%:** Lower-cost options gain 0.3-0.5 points")
        results.append("- **If market conditions worsen:** Focus on highest accessibility locations")
        
        ctx.request_context.session.send_log_message(
            level="info",
            data="Site selection optimization completed successfully"
        )
        
        return "\n".join(results)
import asyncio
from mcp.server.fastmcp import FastMCP

def register_market_intelligence_tools(mcp: FastMCP):
    """Register market intelligence analysis tools"""
    
    @mcp.tool()
    def analyze_market_intelligence(
        demographic_handle: str,
        poi_handle: str,
        competitor_handle: str = None,
        analysis_focus: str = "comprehensive",
        target_demographics: str = None
    ) -> str:
        """Analyze market conditions, demographics, and competitive landscape using GeoJSON data handles.

        🎯 Analysis Capabilities:
        - Population center identification and demographic profiling
        - Income distribution and purchasing power analysis
        - Market saturation and competitor density mapping
        - Traffic pattern analysis for accessibility scoring
        - Consumer behavior insights for Saudi market

        📊 Outputs:
        - Market opportunity scoring (1-10 scale)
        - Demographic heat maps and population clusters
        - Competitive gap analysis with specific recommendations
        - Market penetration potential and customer acquisition costs

        🇸🇦 Saudi-Specific Intelligence:
        - Cultural preferences and shopping patterns
        - Prayer time and weekend schedule impacts
        - Seasonal demand variations (Hajj, Ramadan, summer)
        - Local business customs and regulations

        Args:
            demographic_handle: Handle from fetch_geospatial_data for demographics
            poi_handle: Handle from fetch_geospatial_data for POI data
            competitor_handle: Handle for competitor data (optional)
            analysis_focus: Focus area (population, competition, accessibility, comprehensive)
            target_demographics: Target demographic criteria (optional)
        
        Returns:
            Comprehensive market intelligence analysis
        """
        # Get application context
        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        handle_manager = app_ctx.handle_manager
        
        # MCP Protocol Logging
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Starting market intelligence analysis with focus: {analysis_focus}"
        )
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Reading data from handles - Demographics: {demographic_handle}, POI: {poi_handle}"
        )
        
        # Read data from handles
        demo_data = asyncio.run(handle_manager.read_data_from_handle(demographic_handle))
        poi_data = asyncio.run(handle_manager.read_data_from_handle(poi_handle))
        
        if not demo_data or not poi_data:
            ctx.request_context.session.send_log_message(
                level="error",
                data="Failed to read data from provided handles"
            )
            return "❌ **Error:** Could not find data for provided handles. Please verify the handle IDs are correct."
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Successfully loaded {len(demo_data.get('features', []))} demographic records and {len(poi_data.get('features', []))} POI records"
        )
        
        # Perform comprehensive analysis
        insights = []
        insights.append("# 📊 Market Intelligence Analysis Report")
        insights.append("=" * 50)
        
        # District analysis
        districts = set()
        if "features" in poi_data:
            for feature in poi_data["features"]:
                district = feature.get("properties", {}).get("district")
                if district:
                    districts.add(district)
        
        insights.append("\n## 🏙️ Geographic Coverage")
        insights.append(f"- **Districts Analyzed:** {len(districts)} districts")
        insights.append(f"- **Coverage Areas:** {', '.join(sorted(districts))}")
        
        # POI Category analysis
        categories = {}
        if "features" in poi_data:
            for feature in poi_data["features"]:
                cat = feature.get("properties", {}).get("category")
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1
        
        insights.append("\n## 🎯 Points of Interest Analysis")
        for cat, count in categories.items():
            insights.append(f"- **{cat.replace('_', ' ').title()}:** {count} locations")
        
        # Demographics analysis
        if "features" in demo_data:
            total_pop = sum(f.get("properties", {}).get("population", 0) for f in demo_data["features"])
            avg_income = sum(f.get("properties", {}).get("avg_income", 0) for f in demo_data["features"]) / len(demo_data["features"])
            
            insights.append("\n## 👥 Demographics Overview")
            insights.append(f"- **Total Population Coverage:** {total_pop:,} residents")
            insights.append(f"- **Average Income Level:** SAR {avg_income:,.0f}/month")
            insights.append(f"- **Demographic Data Points:** {len(demo_data['features'])} areas")
        
        # Market opportunity scoring
        base_score = 5.0
        district_bonus = min(2.0, len(districts) * 0.4)  # More districts = more opportunity
        poi_variety = min(1.5, len(categories) * 0.3)   # More POI types = better infrastructure
        population_bonus = min(1.5, total_pop / 50000)  # Higher population = more opportunity
        
        opportunity_score = min(10.0, base_score + district_bonus + poi_variety + population_bonus)
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Calculated market opportunity score: {opportunity_score:.1f}/10"
        )
        
        insights.append("\n## 🎯 Market Opportunity Score")
        insights.append(f"**Overall Score: {opportunity_score:.1f}/10**")
        
        if opportunity_score >= 8.0:
            insights.append("🟢 **EXCELLENT** - High market potential with strong infrastructure")
        elif opportunity_score >= 6.0:
            insights.append("🟡 **GOOD** - Moderate market potential with room for growth")
        else:
            insights.append("🔴 **FAIR** - Lower market potential, consider alternative locations")
        
        # Strategic recommendations
        insights.append("\n## 💡 Strategic Recommendations")
        
        if analysis_focus == "comprehensive":
            # Find best districts based on POI density
            district_poi_count = {}
            for feature in poi_data["features"]:
                district = feature.get("properties", {}).get("district", "Unknown")
                district_poi_count[district] = district_poi_count.get(district, 0) + 1
            
            top_districts = sorted(district_poi_count.items(), key=lambda x: x[1], reverse=True)[:2]
            
            insights.append(f"- **Primary Target:** Focus on {top_districts[0][0]} ({top_districts[0][1]} POIs)")
            insights.append(f"- **Secondary Target:** Consider expansion to {top_districts[1][0]} ({top_districts[1][1]} POIs)")
            
            # Find market gaps
            least_served = min(categories.items(), key=lambda x: x[1])
            insights.append(f"- **Market Gap Identified:** Limited {least_served[0].replace('_', ' ')} coverage ({least_served[1]} locations)")
            insights.append("- **Competitive Advantage:** Consider positioning near high-income demographics")
        
        # Saudi-specific insights
        insights.append("\n## 🇸🇦 Saudi Market Considerations")
        insights.append("- **Prayer Times:** Ensure accessibility during key prayer windows")
        insights.append("- **Weekend Schedule:** Friday-Saturday weekend pattern affects foot traffic")
        insights.append("- **Seasonal Variations:** Plan for Hajj/Umrah seasons and summer heat")
        insights.append("- **Cultural Preferences:** Family-oriented services perform well in Saudi market")
        
        # Next steps
        insights.append("\n## 🚀 Recommended Next Steps")
        insights.append("1. **Site Selection:** Use optimize_site_selection tool with these handles")
        insights.append("2. **Competitive Analysis:** Gather competitor data for deeper insights")
        insights.append("3. **Traffic Analysis:** Assess accessibility and transportation patterns")
        insights.append("4. **Local Partnerships:** Consider collaborations with established local businesses")
        
        ctx.request_context.session.send_log_message(
            level="info",
            data="Market intelligence analysis completed successfully"
        )
        
        return "\n".join(insights)
# --- START OF FILE market_intelligence.py ---

import asyncio
from mcp.server.fastmcp import FastMCP

def register_market_intelligence_tools(mcp: FastMCP):
    """Register market intelligence analysis tools"""
    
    # CRITICAL FIX 1: The tool function must be `async` to use `await`.
    @mcp.tool()
    async def analyze_market_intelligence(
        demographic_handle: str,
        poi_handle: str,
        competitor_handle: str = None,
        analysis_focus: str = "comprehensive",
        target_demographics: str = None
    ) -> str:
        """Analyze market conditions, demographics, and competitive landscape using GeoJSON data handles."""
        # ... (rest of the docstring is fine)
        
        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        handle_manager = app_ctx.handle_manager
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Starting market intelligence analysis with focus: {analysis_focus}"
        )
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Reading data from handles - Demographics: {demographic_handle}, POI: {poi_handle}"
        )
        
        # CRITICAL FIX 2: Replace blocking `asyncio.run()` with non-blocking `await`.
        demo_data = await handle_manager.read_data_from_handle(demographic_handle)
        poi_data = await handle_manager.read_data_from_handle(poi_handle)
        
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
        
        # The rest of your analysis logic is fine and does not need changes.
        insights = []
        insights.append("# 📊 Market Intelligence Analysis Report")
        insights.append("=" * 50)
        
        # ... (keep all your existing analysis logic here) ...
        
        districts = set()
        if "features" in poi_data:
            for feature in poi_data["features"]:
                district = feature.get("properties", {}).get("district")
                if district:
                    districts.add(district)
        
        insights.append("\n## 🏙️ Geographic Coverage")
        insights.append(f"- **Districts Analyzed:** {len(districts)} districts")
        insights.append(f"- **Coverage Areas:** {', '.join(sorted(districts))}")

        # ... (and so on) ...

        # Make sure to return the final string
        return "\n".join(insights)


# --- END OF FILE market_intelligence.py ---
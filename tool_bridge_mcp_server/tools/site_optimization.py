# --- START OF FILE site_optimization.py ---

import asyncio
import json
from typing import List
from mcp.server.fastmcp import FastMCP

def register_site_optimization_tools(mcp: FastMCP):
    """Register site selection optimization tools"""
    
    # FIX 1: The tool function must be `async` to use `await`.
    @mcp.tool()
    async def optimize_site_selection(
        real_estate_handle: str,
        amenity_handle: str,
        criteria_weights: str,
        business_requirements: str,
        optimization_goals: List[str] = None
    ) -> str:
        """Multi-criteria site selection optimization for business location decisions."""
        # ... (rest of docstring is fine)

        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        handle_manager = app_ctx.handle_manager
        
        ctx.request_context.session.send_log_message(
            level="info",
            data="Starting site selection optimization analysis"
        )
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Reading data from handles - Real Estate: {real_estate_handle}, Amenities: {amenity_handle}"
        )
        
        # FIX 2: Replace blocking `asyncio.run()` with non-blocking `await`.
        real_estate_data = await handle_manager.read_data_from_handle(real_estate_handle)
        amenity_data = await handle_manager.read_data_from_handle(amenity_handle)
        
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
        
        # ... The rest of your analysis logic is perfectly fine and does not need changes ...
        
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
            amenity_counts = {}
            if "features" in amenity_data:
                for amenity in amenity_data["features"]:
                    district = amenity.get("properties", {}).get("district", "Unknown")
                    amenity_counts[district] = amenity_counts.get(district, 0) + 1
            
            ctx.request_context.session.send_log_message(
                level="info",
                data=f"Processing {len(real_estate_data['features'])} properties for optimization"
            )
            
            # Use all features, not just a slice, for a more robust analysis
            all_property_features = real_estate_data.get("features", [])
            max_observed_price = max((f.get("properties", {}).get("price", 1) for f in all_property_features), default=1)
            
            for i, feature in enumerate(all_property_features):
                props = feature.get("properties", {})
                
                price = props.get("price", 0)
                size = props.get("size_sqm", 0)
                
                if requirements.get("max_rent") and price > requirements["max_rent"]:
                    continue
                if requirements.get("min_size") and size < requirements["min_size"]:
                    continue
                
                district = props.get("district", "Unknown")
                amenity_count = amenity_counts.get(district, 0)
                
                proximity_score = min(10, 3 + (amenity_count / 20) * 7)
                cost_score = 10 - (price / max_observed_price) * 10
                accessibility_score = 9.0 - ((i % 20) * 0.4) # Make dummy score more varied
                
                total_score = (
                    proximity_score * weights.get("proximity", 0.33) +
                    cost_score * weights.get("cost", 0.33) +
                    accessibility_score * weights.get("accessibility", 0.34)
                )
                
                # Prevent division by zero for ROI
                annual_cost = price * 12
                if annual_cost == 0:
                    roi_estimate = 0
                else:
                    estimated_revenue = proximity_score * 1000
                    roi_estimate = ((estimated_revenue * 12) - annual_cost) / annual_cost * 100

                top_sites.append({
                    "location": props.get("name", f"Site {props.get('id', i+1)}"),
                    "district": district,
                    "total_score": round(total_score, 1),
                    "price": price,
                    "size": size,
                    # ... other site properties ...
                })
        
        top_sites.sort(key=lambda x: x["total_score"], reverse=True)
        
        # ... (Your reporting logic is great, keep it as is) ...
        # Example of how you would generate the final string
        
        final_report = "\n".join(results) # Assuming 'results' is built up
        return final_report
        

# --- END OF FILE site_optimization.py ---
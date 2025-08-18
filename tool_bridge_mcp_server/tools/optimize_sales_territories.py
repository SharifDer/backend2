# --- START OF FILE optimize_sales_territories.py ---

import logging
import os
import sys

# Add the grandparent directory to sys.path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Import aiohttp if not already there
import aiohttp
from config_factory import CONF
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Import your existing Pydantic models from the FastAPI backend
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from all_types.request_dtypes import ReqClustersForSalesManData
from tool_bridge_mcp_server.context import get_app_context

logger = logging.getLogger(__name__)

# --- Configuration is now a simple module-level constant ---
FASTAPI_BASE_URL = "http://localhost:8000"


def register_territory_optimization_tools(mcp: FastMCP):
    """Register territory optimization tool by defining it within this function's scope."""

    # --- The tool is now a simple decorated function, not a class method ---
    @mcp.tool(
        name="optimize_sales_territories",
        description="""Advanced sales territory optimization using spatial clustering and market analysis.
        
        🎯 Core Functionality:
        - Creates balanced sales territories based on population density and market potential
        - Analyzes accessibility patterns and customer distribution
        - Optimizes workload distribution across sales representatives
        - Generates territory boundaries with comprehensive business intelligence

        📊 Analysis Features:
        - Population and income-weighted clustering
        - Accessibility analysis (distance-based market reach)
        - Market potential calculation per territory
        - Territory equity and balance assessment
        - Competitive landscape analysis

        🗺️ Geographic Intelligence:
        - Spatial contiguity constraints (connected territories)
        - Distance-based accessibility modeling
        - Grid-based aggregation for precise analysis
        - Territory boundary optimization

        💼 Business Applications:
        - Sales team territory assignment
        - Service area optimization
        - Market penetration analysis
        - Resource allocation planning
        - Performance benchmarking

        Args:
            city_name: Target city for territory optimization
            num_sales_man: Number of sales territories to create
            distance_limit: Maximum travel distance customers will accept (km)
            boolean_query: Business type to analyze (e.g., 'supermarket', 'restaurant')
        
        Returns:
            Territory analysis handle with comprehensive BI metrics and visualizations
        """,
    )
    async def optimize_sales_territories(
        city_name: str = Field(
            description="Name of the Saudi city for territory optimization (e.g., Riyadh, Jeddah, Dammam)"
        ),
        country_name: str = Field(
            default="Saudi Arabia", description="Country name"
        ),
        num_sales_man: int = Field(
            default=5,
            description="Number of sales territories to create (recommended: 3-10 for optimal balance)"
        ),
        distance_limit: float = Field(
            default=3.0,
            description="Maximum distance customers will travel to reach services (km). Typical values: 2-5km urban, 5-15km rural"
        ),
        boolean_query: str = Field(
            default="supermarket OR grocery_store OR retail",
            description="Business categories to analyze. Examples: 'supermarket', 'restaurant AND NOT fast_food', 'retail OR shopping'"
        ),
        include_raw_data: bool = Field(
            default=False,
            description="Include raw cluster geometries for advanced GIS analysis"
        ),
    ) -> str:
        """Optimize sales territories using advanced spatial analytics and market intelligence."""

        try:
            app_ctx = get_app_context(mcp)
            session_manager = app_ctx.session_manager
            handle_manager = app_ctx.handle_manager

            # --- THIS IS THE KEY CHANGE ---
            # Get the valid user_id and token for this session
            user_id, id_token = await session_manager.get_valid_id_token()

            if not id_token or not user_id:
                return "❌ Error: You are not logged in. Please use the `user_login` tool first."
            
            # Session for handle management
            session = await session_manager.get_current_session()
            if not session:
                session = await session_manager.create_session()

            # Create request payload
            req_body = ReqClustersForSalesManData(
                city_name=city_name,
                country_name=country_name,
                num_sales_man=num_sales_man,
                distance_limit=distance_limit,
                boolean_query=boolean_query,
                user_id=user_id,
                include_raw_data=include_raw_data,
            )

            request_payload = {
                "message": "Optimizing sales territories using spatial clustering",
                "request_info": {},
                "request_body": req_body.model_dump(),
            }

            # Call the correct territory optimization endpoint
            endpoint_url = f"{FASTAPI_BASE_URL}{CONF.temp_sales_man_problem}"  # Fixed to use the actual endpoint
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {id_token}" # Use the real user's token
            }

            logger.info(f"Calling territory optimization for user {user_id}: {endpoint_url}")

            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    endpoint_url,
                    json=request_payload,
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Territory optimization error: {response.status} - {error_text}")
                        return f"❌ Error optimizing territories: {response.status} - {error_text}"
                    
                    response_data = await response.json()

            # Extract analysis results
            territory_data = response_data.get("data", {})
            if not territory_data:
                return f"❌ Territory optimization failed: No data returned from endpoint."

            # The response structure will depend on your ResModel[ResSalesman] structure
            # Adjust these fields based on your actual response model
            territory_analytics = territory_data.get("territory_analytics", [])
            business_insights = territory_data.get("business_insights", {})
            metadata = territory_data.get("metadata", {})

            # Create summary for the handle
            summary = {
                "analysis_type": "sales_territory_optimization",
                "city": city_name,
                "country": country_name,
                "territories_created": len(territory_analytics) if territory_analytics else num_sales_man,
                "target_territories": num_sales_man,
                "distance_limit_km": distance_limit,
                "business_type": boolean_query,
                "total_customers": metadata.get("total_customers", 0),
                "market_balance_score": business_insights.get("market_balance_score", 0),
                "optimization_date": metadata.get("analysis_date"),
                "plot_urls": territory_data.get("plots", {}),
                "data_files": territory_data.get("data_files", {}),  # NEW: Data files for interactive plotting
            }

            # Store comprehensive territory analysis data
            handle = await handle_manager.store_data(
                data_type="territory_optimization",
                location=city_name.lower().replace(" ", "_"),
                data=territory_data
            )

            # Generate success message with key insights
            # Update the success message to use the simple handle
            success_msg = f"""✅ **Sales Territory Optimization Complete**

            🎯 **Analysis Summary**:
            - **City**: {city_name}, {country_name}
            - **Territories Created**: {summary['territories_created']} (target: {num_sales_man})
            - **Total Market**: {metadata.get('total_customers', 0):,} potential customers
            - **Service Range**: {distance_limit}km maximum travel distance
            - **Business Focus**: {boolean_query}

            📊 **Territory Balance**:
            - **Market Equity Score**: {business_insights.get('market_balance_score', 'N/A')}/100
            - **Population Distribution**: {business_insights.get('population_distribution_score', 'N/A')}/100
            - **Well-Served Areas**: {business_insights.get('accessibility_analysis', {}).get('well_served_territories', 'N/A')} territories
            - **Service Gaps**: {business_insights.get('accessibility_analysis', {}).get('service_desert_territories', 'N/A')} underserved areas

            🗺️ **Visualizations Available**: 
            - **Static Maps**: {len(territory_data.get('plots', {}))} PNG files for reports
            - **Interactive Data**: {len(territory_data.get('data_files', {}))} GeoJSON files for DashApp visualization

            📋 **Data Handle**: `{handle}`
            Use this handle with:
            - `generate_territory_report` for detailed business intelligence reports
            - DashApp MCP client for interactive data visualization"""

            return success_msg

        except Exception as e:
            logger.exception("Critical error in optimize_sales_territories")
            return f"❌ Error during territory optimization: {str(e)}"


# --- END OF FILE optimize_sales_territories.py ---
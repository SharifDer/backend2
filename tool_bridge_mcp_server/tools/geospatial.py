# --- START OF FILE geospatial.py ---

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

from all_types.request_dtypes import ReqFetchDataset
from tool_bridge_mcp_server.context import get_app_context

logger = logging.getLogger(__name__)

# --- Configuration is now a simple module-level constant ---
FASTAPI_BASE_URL = "http://localhost:8000"


def register_geospatial_tools(mcp: FastMCP):
    """Register all geospatial tools by defining them within this function's scope."""

    # --- The tool is now a simple decorated function, not a class method ---
    @mcp.tool(
        name="fetch_geospatial_data",
        description="""Universal geospatial data fetcher for Saudi Arabia that ALWAYS returns GeoJSON format.
        
        🎯 Data Sources Available:
        - Real estate properties (warehouses, commercial, residential)
        - Points of Interest (POI): restaurants, gas stations, mosques, مطاعم, محطات وقود
        - Demographics and population centers
        - Commercial properties and rental listings
        - Traffic patterns and accessibility data
        - Competitor locations and market data

        📍 Geographic Coverage:
        - Cities: Riyadh, Jeddah, Dammam, Mecca, Medina, Khobar
        - Regions: All Saudi provinces and major districts
        - Coordinate-based queries with bounding boxes

        ⚡ PERFORMANCE: Returns lightweight data handle + summary.
        Full GeoJSON dataset stored server-side for analysis tools.

        Args:
            city_name: Saudi city name (Riyadh, Jeddah, Dammam, etc.)
            boolean_query: Search query using OR/AND operators
            data_source: Data source type (poi, real_estate, demographics)
        
        Returns:
            Data handle ID and summary information
        """,
    )
    async def fetch_geospatial_data(
        # Note: 'self' is removed
        lat: float = Field(description="Latitude of the search center point"),
        lng: float = Field(description="Longitude of the search center point"),
        radius: float = Field(
            default=5000, description="Search radius in meters"
        ),
        boolean_query: str = Field(
            description="Boolean search query. Examples: 'warehouse OR logistics', 'restaurant AND NOT fast_food', 'gas_station'"
        ),
        city_name: str = Field(
            description="Name of the Saudi city (e.g., Riyadh, Jeddah, Dammam)"
        ),
        country_name: str = Field(
            default="Saudi Arabia", description="Country name"
        ),
        action: str = Field(
            default="sample",
            description="'sample' for quick preview (20 records) or 'full data' for complete dataset",
        ),
        user_id: str = Field(
            default="default_user", description="User ID for the request"
        ),
        include_only_sub_properties: bool = Field(
            default=True,
            description="If true, returns only essential properties for each feature",
        ),
        include_rating_info: bool = Field(
            default=False,
            description="If true, includes detailed rating and review information",
        ),
    ) -> str:
        """Fetch user-specific geospatial data. Requires user to be logged in."""

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

            req_body = ReqFetchDataset(
                lat=lat,
                lng=lng,
                radius=radius,
                boolean_query=boolean_query,
                city_name=city_name,
                country_name=country_name,
                action=action,
                user_id=user_id,
                include_only_sub_properties=include_only_sub_properties,
                include_rating_info=include_rating_info,
                page_token="",
                ids_and_location_only=False,
                search_type="category_search",
            )

            request_payload = {
                "message": "Fetching Saudi location data via MCP",
                "request_info": {},
                "request_body": req_body.model_dump(),
            }

            # Call the original, secure, user-facing endpoint
            endpoint_url = f"http://localhost:8000{CONF.fetch_dataset}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {id_token}" # Use the real user's token
            }

            logger.info(f"Calling user-specific endpoint for user {user_id}: {endpoint_url}")


            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    endpoint_url,
                    json=request_payload,
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"FastAPI error: {response.status} - {error_text}"
                        )
                        return f"Error fetching data: {response.status} - {error_text}"
                    response_data = await response.json()

            dataset = response_data.get("data", {})
            if not dataset or not dataset.get("features"):
                return f"No data returned from the backend for query: '{boolean_query}' in {city_name}."

            features = dataset.get("features", [])
            districts = {
                f.get("properties", {}).get("district")
                for f in features
                if f.get("properties", {}).get("district")
            }
            property_types = {
                f.get("properties", {}).get("primaryType")
                for f in features
                if f.get("properties", {}).get("primaryType")
            }

            summary = {
                "count": len(features),
                "city": city_name,
                "search_query": boolean_query,
                "districts": list(districts)[:10],
                "property_types": list(property_types)[:10],
                "has_more_data": bool(dataset.get("next_page_token")),
                "progress": dataset.get("progress", 0),
            }

            data_type = (
                "general"  # You can add your logic to determine data_type here
            )

            handle = await handle_manager.store_data(
                data_type="geospatial_data",
                location=city_name.lower().replace(" ", "_"),
                data=dataset
            )

            return f"✅ Data fetched. Handle: `{handle}`. Summary: {summary['count']} records found for '{boolean_query}' in {city_name}."

        except Exception as e:
            logger.exception("Critical error in fetch_geospatial_data")
            return f"Error during data fetch: {str(e)}"


# --- END OF FILE geospatial.py ---

import asyncio
from datetime import datetime
from mcp.server.fastmcp import FastMCP

def register_geospatial_tools(mcp: FastMCP):
    """Register geospatial data fetching tools"""
    
    @mcp.tool()
    def fetch_geospatial_data(
        city_name: str,
        boolean_query: str,
        data_source: str = "poi"
    ) -> str:
        """Universal geospatial data fetcher for Saudi Arabia that ALWAYS returns GeoJSON format.
        
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
        """
        # Get application context
        ctx = mcp.get_context()
        app_ctx = ctx.request_context.lifespan_context
        session_manager = app_ctx.session_manager
        handle_manager = app_ctx.handle_manager
        
        # MCP Protocol Logging
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Starting geospatial data fetch for {city_name} - Data source: {data_source}"
        )
        
        # Ensure we have a session
        session = asyncio.run(session_manager.get_current_session())
        if not session:
            session = asyncio.run(session_manager.create_session())
            ctx.request_context.session.send_log_message(
                level="info",
                data=f"Created new session: {session.session_id}"
            )
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Generating {data_source} data for {city_name} with query: {boolean_query}"
        )
        
        # Generate dummy GeoJSON data based on data source
        if data_source == "real_estate":
            data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [46.6753 + i*0.001, 24.7136 + i*0.001]
                        },
                        "properties": {
                            "id": f"property_{i}",
                            "price": 100000 + (i * 1000),
                            "size_sqm": 200 + (i % 100),
                            "type": "warehouse" if i % 3 == 0 else "commercial",
                            "district": f"District_{i % 5}",
                            "name": f"Property {i}",
                            "availability": "available" if i % 4 != 0 else "rented"
                        }
                    }
                    for i in range(1000)
                ]
            }
        elif data_source == "demographics":
            data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [46.6753 + i*0.002, 24.7136 + i*0.002]
                        },
                        "properties": {
                            "area_id": f"demo_{i}",
                            "population": 1000 + (i * 50),
                            "avg_income": 8000 + (i % 20) * 500,
                            "age_group_dominant": ["18-30", "31-45", "46-60"][i % 3],
                            "district": f"District_{i % 5}",
                            "density_per_sqkm": 500 + (i % 100)
                        }
                    }
                    for i in range(300)
                ]
            }
        else:  # POI
            data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [46.6753 + i*0.001, 24.7136 + i*0.001]
                        },
                        "properties": {
                            "name": f"POI_{i}",
                            "category": ["restaurant", "gas_station", "mosque", "supermarket", "bank"][i % 5],
                            "rating": 4.0 + (i % 10) / 10,
                            "district": f"District_{i % 5}",
                            "opening_hours": "24/7" if i % 3 == 0 else "06:00-22:00",
                            "popular_times": ["morning", "afternoon", "evening"][i % 3]
                        }
                    }
                    for i in range(500)
                ]
            }
        
        # Store data and create handle
        handle = asyncio.run(handle_manager.store_data_and_create_handle(
            data=data,
            data_type=data_source,
            location=city_name.lower(),
            session_id=session.session_id
        ))
        
        ctx.request_context.session.send_log_message(
            level="info",
            data=f"Successfully stored {len(data['features'])} features and created handle: {handle.data_handle}"
        )
        
        districts = handle.summary.get("districts", [])
        response = (
            f"✅ Saudi location data fetched and stored successfully!\n\n"
            f"📋 **Data Handle:** `{handle.data_handle}`\n"
            f"📊 **Summary:** {handle.summary['count']} records covering {len(districts)} districts\n"
            f"🏙️ **City:** {city_name}\n"
            f"🔍 **Query:** {boolean_query}\n"
            f"📈 **Data Source:** {data_source}\n"
            f"📍 **Districts:** {', '.join(districts[:3])}{'...' if len(districts) > 3 else ''}\n\n"
            f"💡 Use this handle with analysis and optimization tools!"
        )
        
        return response
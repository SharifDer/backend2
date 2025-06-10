import os
import sys
# Add the grandparent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



import asyncio
import json
import uuid
import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# FastMCP imports
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import your async JSON utilities
from backend_common.common_storage import use_json, convert_to_serializable

# Tool imports (no __init__.py needed)
from tools.geospatial import register_geospatial_tools
from tools.market_intelligence import register_market_intelligence_tools
from tools.site_optimization import register_site_optimization_tools

# ===== Logging Configuration =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# ===== Configuration =====
class Config(BaseModel):
    """Server configuration"""
    session_ttl_hours: int = 8
    cleanup_interval_hours: int = 1
    temp_storage_path: str = "/tmp/sessions"

config = Config()

# ===== Data Models =====
class DataHandle(BaseModel):
    """Lightweight handle for stored data"""
    data_handle: str = Field(description="Unique identifier for the data")
    session_id: str = Field(description="Session this data belongs to")
    data_type: str = Field(description="Type of data stored")
    location: Optional[str] = Field(default=None, description="Geographic location if applicable")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(description="When this handle expires")
    file_path: str = Field(description="Path to the JSON file storing the data")
    summary: Dict[str, Any] = Field(description="Summary statistics about the data")
    schema_info: Dict[str, str] = Field(description="Schema of the stored data", alias="schema")

class SessionInfo(BaseModel):
    """Session management information"""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    data_handles: List[str] = Field(default_factory=list)

# ===== Session Manager =====
class SessionManager:
    def __init__(self):
        self.base_path = Path(config.temp_storage_path)
        self.current_session: Optional[SessionInfo] = None
        logger.info("Session manager initialized with base path: %s", self.base_path)
        
    async def create_session(self) -> SessionInfo:
        """Create a new session with unique ID"""
        session_id = str(uuid.uuid4())[:8]
        session_path = self.base_path / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        session_info = SessionInfo(
            session_id=session_id,
            expires_at=datetime.now() + timedelta(hours=config.session_ttl_hours)
        )
        
        # Store session metadata using async use_json
        metadata_path = str(session_path / "session_metadata.json")
        session_data = convert_to_serializable(session_info.model_dump())
        await use_json(metadata_path, "w", session_data)
        
        self.current_session = session_info
        logger.info("Created new session: %s (expires: %s)", session_id, session_info.expires_at)
        return session_info
    
    async def get_current_session(self) -> Optional[SessionInfo]:
        """Get current session"""
        return self.current_session
    
    async def load_session(self, session_id: str) -> Optional[SessionInfo]:
        """Load existing session from metadata file"""
        session_path = self.base_path / session_id
        metadata_path = str(session_path / "session_metadata.json")
        
        session_data = await use_json(metadata_path, "r")
        if session_data:
            session_info = SessionInfo(**session_data)
            # Check if session is still valid
            if datetime.now() < session_info.expires_at:
                self.current_session = session_info
                logger.info("Loaded existing session: %s", session_id)
                return session_info
            else:
                logger.info("Session %s has expired", session_id)
                await self.cleanup_session(session_id)
        return None
    
    async def cleanup_session(self, session_id: str):
        """Clean up expired session files"""
        import shutil
        session_path = self.base_path / session_id
        if session_path.exists():
            shutil.rmtree(session_path)
            logger.info("Cleaned up expired session: %s", session_id)

# ===== Data Handle Manager =====
class DataHandleManager:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        logger.info("Data handle manager initialized")
    
    async def store_data_and_create_handle(
        self, 
        data: Any,
        data_type: str,
        location: str,
        session_id: str,
        summary: Dict[str, Any] = None
    ) -> DataHandle:
        """Store data in JSON file and return lightweight handle"""
        timestamp = datetime.now().strftime("%Y%m%d")
        handle_id = f"{data_type}_{location}_{timestamp}_{session_id}"
        
        session_path = self.session_manager.base_path / session_id
        file_name = f"{data_type}_{location}.json"
        file_path = str(session_path / file_name)
        
        # Convert data to serializable format
        if isinstance(data, BaseModel):
            data_dict = convert_to_serializable(data.model_dump())
        else:
            data_dict = convert_to_serializable(data)
            
        # Store data as JSON using async use_json
        await use_json(file_path, "w", data_dict)
        
        if summary is None:
            summary = self._generate_summary(data_dict)
        
        handle = DataHandle(
            data_handle=handle_id,
            session_id=session_id,
            data_type=data_type,
            location=location,
            expires_at=datetime.now() + timedelta(hours=config.session_ttl_hours),
            file_path=file_path,
            summary=summary,
            schema_info=self._extract_schema(data_dict)
        )
        
        logger.info("Created data handle: %s for %s data in %s", handle_id, data_type, location)
        return handle
    
    async def read_data_from_handle(self, handle_id: str) -> Optional[Dict]:
        """Read data from handle"""
        session = await self.session_manager.get_current_session()
        if not session:
            logger.warning("No current session when trying to read handle: %s", handle_id)
            return None
            
        parts = handle_id.split('_')
        if len(parts) >= 3:
            data_type = parts[0]
            location = parts[1]
            
            session_path = self.session_manager.base_path / session.session_id
            file_path = str(session_path / f"{data_type}_{location}.json")
            
            # Read data using async use_json
            data = await use_json(file_path, "r")
            if data is not None:
                logger.info("Successfully read data from handle: %s", handle_id)
                return data
            else:
                logger.warning("File not found for handle: %s at path: %s", handle_id, file_path)
        else:
            logger.warning("Invalid handle format: %s", handle_id)
        return None
    
    async def update_handle_registry(self, session_id: str, handle_id: str):
        """Update session metadata with new handle"""
        session_path = self.session_manager.base_path / session_id
        metadata_path = str(session_path / "session_metadata.json")
        
        # Read current metadata
        metadata = await use_json(metadata_path, "r")
        if metadata:
            if "data_handles" not in metadata:
                metadata["data_handles"] = []
            if handle_id not in metadata["data_handles"]:
                metadata["data_handles"].append(handle_id)
                # Write updated metadata
                await use_json(metadata_path, "w", metadata)
                logger.info("Updated handle registry for session %s with handle %s", session_id, handle_id)
    
    def _generate_summary(self, data: Any) -> Dict[str, Any]:
        """Generate summary statistics for data"""
        if isinstance(data, dict) and "type" in data and data["type"] == "FeatureCollection":
            features = data.get("features", [])
            districts = set()
            for feature in features:
                if "district" in feature.get("properties", {}):
                    districts.add(feature["properties"]["district"])
            
            return {
                "count": len(features),
                "type": "FeatureCollection",
                "districts": list(districts)
            }
        elif isinstance(data, list):
            return {
                "count": len(data),
                "sample_size": min(5, len(data))
            }
        elif isinstance(data, dict):
            return {
                "keys": list(data.keys())[:5],
                "size": len(data)
            }
        return {"type": str(type(data))}
    
    def _extract_schema(self, data: Any) -> Dict[str, str]:
        """Extract basic schema from data"""
        if isinstance(data, dict) and "features" in data and data["features"]:
            properties = data["features"][0].get("properties", {})
            return {k: type(v).__name__ for k, v in properties.items()}
        elif isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                return {k: type(v).__name__ for k, v in item.items()}
        elif isinstance(data, dict):
            return {k: type(v).__name__ for k, v in data.items()}
        return {"type": str(type(data))}

# ===== Application Context =====
@dataclass
class AppContext:
    """Application context for lifespan management"""
    session_manager: SessionManager
    handle_manager: DataHandleManager

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize components
    session_manager = SessionManager()
    handle_manager = DataHandleManager(session_manager)
    
    logger.info("🚀 Saudi Location Intelligence MCP Server starting...")
    
    try:
        yield AppContext(
            session_manager=session_manager,
            handle_manager=handle_manager
        )
    finally:
        logger.info("🛑 Saudi Location Intelligence MCP Server shutting down...")

# ===== FastMCP Server =====
mcp = FastMCP(
    "saudi-location-intelligence",
    lifespan=app_lifespan
)

# Register all tools
register_geospatial_tools(mcp)
register_market_intelligence_tools(mcp)
register_site_optimization_tools(mcp)

# ===== Resource Implementations =====
@mcp.resource("session://current")
async def get_current_session() -> str:
    """Get information about the current session"""
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    session_manager = app_ctx.session_manager
    
    session = await session_manager.get_current_session()
    if session:
        return f"Current session: {session.session_id} (expires: {session.expires_at.isoformat()})"
    else:
        return "No active session"

@mcp.resource("config://server")
def get_server_config() -> str:
    """Get server configuration information"""
    return f"""Saudi Location Intelligence MCP Server Configuration:
- Session TTL: {config.session_ttl_hours} hours  
- Storage Path: {config.temp_storage_path}
- Cleanup Interval: {config.cleanup_interval_hours} hours
- Server Name: saudi-location-intelligence
- Available Tools: 3 (fetch_geospatial_data, analyze_market_intelligence, optimize_site_selection)
- Transport Support: stdio, SSE
"""

# ===== Session Cleanup Task =====
async def cleanup_expired_sessions():
    """Periodic cleanup of expired sessions"""
    while True:
        try:
            session_manager = SessionManager()
            base_path = session_manager.base_path
            
            if base_path.exists():
                for session_dir in base_path.iterdir():
                    if session_dir.is_dir():
                        metadata_path = str(session_dir / "session_metadata.json")
                        metadata = await use_json(metadata_path, "r")
                        
                        if metadata:
                            expires_at = datetime.fromisoformat(metadata["expires_at"])
                            if datetime.now() > expires_at:
                                await session_manager.cleanup_session(session_dir.name)
                        
            await asyncio.sleep(config.cleanup_interval_hours * 3600)  # Sleep for cleanup interval
            
        except Exception as e:
            logger.error("Error in session cleanup: %s", e)
            await asyncio.sleep(300)  # Sleep 5 minutes on error

# ===== Main Function =====
def main():
    """Main entry point with transport selection"""
    parser = argparse.ArgumentParser(description="Saudi Location Intelligence MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default="stdio",
        help="Transport type: stdio (for Claude Desktop) or sse (for web/inspector)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8001,
        help="Port for SSE transport (default: 8001)"
    )
    
    args = parser.parse_args()
    
    logger.info("🇸🇦 Saudi Location Intelligence MCP Server")
    logger.info("Transport: %s", args.transport)
    
    # Start cleanup task
    asyncio.create_task(cleanup_expired_sessions())
    
    if args.transport == "stdio":
        logger.info("📱 Starting stdio transport (compatible with Claude Desktop)")
        logger.info("💡 Add this server to your Claude Desktop configuration:")
        logger.info('   "saudi-location-intelligence": {')
        logger.info('     "command": "python",')
        logger.info('     "args": ["%s", "--transport", "stdio"]', __file__)
        logger.info('   }')
        mcp.run(transport="stdio")
    
    elif args.transport == "sse":
        logger.info("🌐 Starting SSE transport on http://localhost:%d", args.port)
        logger.info("🔍 Test with MCP Inspector: mcp dev --server-url http://localhost:%d", args.port)
        mcp.run(transport="sse", port=args.port)

if __name__ == "__main__":
    main()
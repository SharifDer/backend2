# ===== CONFIGURE LOGGING FIRST =====
# Import the configured logger
from mcp_logging import logger
from mcp_logging import setup_session_logging
import os
import sys

from mcp_dtypes import DataHandle, SessionInfo

# Add the grandparent directory to sys.path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Import aiohttp if not already there
import aiohttp
from config_factory import CONF  # You'll need your FastAPI CONF object
import asyncio
import json
import uuid
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass


# FastMCP imports
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# --- NEW IMPORT FROM THE CONTEXT FILE ---
from context import AppContext

# Import your async JSON utilities
from backend_common.common_storage import use_json, convert_to_serializable

# Tool imports
from tools.geospatial import register_geospatial_tools
from tools.generate_territory_report import register_territory_report_tools
from tools.optimize_sales_territories import (
    register_territory_optimization_tools,
)
from tools.auth_tools import register_auth_tools


# ===== Configuration =====
class Config(BaseModel):
    """Server configuration"""

    session_ttl_hours: int = 8
    cleanup_interval_hours: int = 1
    temp_storage_path: str = str(Path(__file__).parent / "sessions")


config = Config()


# ===== Session Manager =====
class SessionManager:
    def __init__(self):
        self.base_path = Path(config.temp_storage_path)
        self.current_session: Optional[SessionInfo] = None
        logger.info(
            "Session manager initialized with base path: %s", self.base_path
        )

    async def create_session(self) -> SessionInfo:
        """Create a new session with dedicated logging"""
        session_id = str(uuid.uuid4())[:8]
        session_path = self.base_path / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        session_info = SessionInfo(
            session_id=session_id,
            expires_at=datetime.now()
            + timedelta(hours=config.session_ttl_hours),
        )

        # Store session metadata
        metadata_path = str(session_path / "session_metadata.json")
        session_data = convert_to_serializable(session_info.model_dump())
        await use_json(metadata_path, "w", session_data)



        setup_session_logging(session_id, session_path)

        self.current_session = session_info
        logger.info(
            f"Created new session: {session_id} (expires: {session_info.expires_at})"
        )

        return session_info

    async def cleanup_session(self, session_id: str):
        """Clean up session and its logging"""
        from .mcp_logging import end_session_logging

        end_session_logging(session_id)

        import shutil

        session_path = self.base_path / session_id
        if session_path.exists():
            shutil.rmtree(session_path)
            logger.info("Cleaned up expired session: %s", session_id)

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

    async def update_session_auth(
        self,
        session_id: str,
        user_id: str,
        id_token: str,
        refresh_token: str,
        expires_in: int,
    ):
        """Updates the session with new authentication tokens."""
        session_path = self.base_path / session_id
        metadata_path = str(session_path / "session_metadata.json")

        metadata = await use_json(metadata_path, "r")
        if not metadata:
            logger.error(
                f"Could not find session metadata for {session_id} to update auth."
            )
            return

        metadata["user_id"] = user_id
        metadata["id_token"] = id_token
        metadata["refresh_token"] = refresh_token
        metadata["token_expires_at"] = (
            datetime.now() + timedelta(seconds=expires_in - 60)
        ).isoformat()  # -60s buffer

        await use_json(metadata_path, "w", metadata)

        # Update the in-memory session object as well
        if (
            self.current_session
            and self.current_session.session_id == session_id
        ):
            self.current_session.user_id = user_id
            self.current_session.id_token = id_token
            self.current_session.refresh_token = refresh_token
            self.current_session.token_expires_at = datetime.fromisoformat(
                metadata["token_expires_at"]
            )

        logger.info(
            f"Updated auth tokens for user {user_id} in session {session_id}"
        )

    async def get_valid_id_token(self) -> tuple[Optional[str], Optional[str]]:
        """
        Gets a valid ID token for the current session, refreshing it if necessary.
        Returns a tuple of (user_id, id_token).
        """
        session = await self.get_current_session()
        if not session or not session.refresh_token or not session.user_id:
            return None, None  # No user logged in

        # Check if token is expired or close to expiring
        if (
            not session.id_token
            or not session.token_expires_at
            or datetime.now() >= session.token_expires_at
        ):
            logger.info(
                f"Token expired for user {session.user_id}. Refreshing..."
            )
            try:
                # Import CONF here to avoid circular dependency at module level
                from config_factory import CONF

                async with aiohttp.ClientSession() as http_session:
                    endpoint_url = "http://localhost:8000" + CONF.refresh_token
                    payload = {
                        "message": "refreshing token",
                        "request_info": {},
                        "request_body": {
                            "grant_type": "refresh_token",
                            "refresh_token": session.refresh_token,
                        },
                    }
                    async with http_session.post(
                        endpoint_url, json=payload
                    ) as response:
                        if response.status != 200:
                            logger.error(
                                f"Failed to refresh token: {await response.text()}"
                            )
                            return None, None

                        token_data = (await response.json())["data"]
                        await self.update_session_auth(
                            session.session_id,
                            token_data["localId"],
                            token_data["idToken"],
                            token_data["refreshToken"],
                            int(token_data["expiresIn"]),
                        )
                        logger.info(
                            f"Successfully refreshed token for user {session.user_id}."
                        )
                        # Important: return the newly fetched token, not the old one from session
                        return token_data["localId"], token_data["idToken"]
            except Exception as e:
                logger.error(f"Exception during token refresh: {e}")
                return None, None

        # Token is still valid, return it
        return session.user_id, session.id_token


class HandleManager:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        logger.info("Effective data manager initialized")

    async def store_data(self, data_type: str, location: str, data: Any) -> str:
        """Store data and return simple handle"""

        session = await self.session_manager.get_current_session()
        session_path = self.session_manager.base_path / session.session_id
        session_path.mkdir(parents=True, exist_ok=True)
        session_id = session.session_id if session else "unknown"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        handle = f"{data_type}_{location}_{timestamp}_{session_id}.json"
        file_path = str(session_path / handle)

        logger.info(
            f"STORE: Saving {data_type} data for {location} to {handle}"
        )

        # Convert and store data
        serializable_data = convert_to_serializable(data)
        await use_json(file_path, "w", serializable_data)

        # Touch session to update access time for cleanup
        await self._touch_session(session.session_id)

        logger.info(f"STORE: Successfully stored data with handle: {handle}")
        return handle

    async def read_data(self, handle: str) -> Optional[Dict]:
        """Read data using simple handle"""
        session = await self.session_manager.get_current_session()
        session_path = self.session_manager.base_path / session.session_id
        file_path = str(session_path / handle)

        logger.info(f"READ: Loading data from handle: {handle}")

        if os.path.exists(file_path):
            data = await use_json(file_path, "r")
            if data:
                # Update session access time
                await self._touch_session(session.session_id)
                logger.info(f"READ: Successfully loaded data from {handle}")
                return data

        logger.warning(f"READ: No data found for handle: {handle}")
        return None

    async def list_session_data(
        self, session_id: str = None
    ) -> list[Dict[str, Any]]:
        """List all data files in a session"""
        if not session_id:
            session = await self.session_manager.get_current_session()
            session_id = session.session_id if session else None

        if not session_id:
            return []

        session_path = self.session_manager.base_path / session_id

        if not session_path.exists():
            return []

        files = []
        for file_path in session_path.glob("*.json"):
            if file_path.name == "session_info.json":  # Skip metadata
                continue

            stat = file_path.stat()

            # Parse filename to extract data_type and location
            name_parts = file_path.stem.split("_", 1)
            data_type = name_parts[0] if name_parts else "unknown"
            location = name_parts[1] if len(name_parts) > 1 else "unknown"

            files.append(
                {
                    "handle": file_path.name,
                    "data_type": data_type,
                    "location": location,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime),
                }
            )

        return sorted(files, key=lambda x: x["modified_at"], reverse=True)

    async def remove_data(self, handle: str, session_id: str = None) -> bool:
        """Remove specific data file"""
        if not session_id:
            session = await self.session_manager.get_current_session()
            session_id = session.session_id if session else None

        if not session_id:
            return False

        session_path = self.session_manager.base_path / session_id
        file_path = session_path / handle

        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"REMOVE: Deleted data file: {handle}")
                return True
            return False
        except Exception as e:
            logger.error(f"REMOVE: Failed to delete {handle}: {e}")
            return False

    # ===================== CLEANUP METHODS =====================

    async def cleanup_expired_sessions(
        self, max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """Remove sessions older than max_age_hours"""
        logger.info(
            f"CLEANUP: Starting cleanup of sessions older than {max_age_hours} hours"
        )

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_dir = self.session_manager.base_path

        if not sessions_dir.exists():
            return {"cleaned": 0, "freed_mb": 0, "errors": []}

        cleaned_count = 0
        freed_bytes = 0
        errors = []

        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            try:
                # Check last access time
                last_access = await self._get_session_last_access(
                    session_dir.name
                )

                if last_access and last_access < cutoff_time:
                    # Calculate size before deletion
                    size = await self._calculate_directory_size(session_dir)

                    # Remove entire session directory
                    await self._remove_directory_recursive(session_dir)

                    cleaned_count += 1
                    freed_bytes += size
                    logger.info(
                        f"CLEANUP: Removed expired session {session_dir.name}"
                    )

            except Exception as e:
                error_msg = f"Failed to cleanup session {session_dir.name}: {e}"
                errors.append(error_msg)
                logger.error(f"CLEANUP: {error_msg}")

        result = {
            "cleaned": cleaned_count,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "errors": errors,
        }

        logger.info(f"CLEANUP: Completed - {result}")
        return result

    async def cleanup_large_sessions(
        self, max_size_mb: int = 100
    ) -> Dict[str, Any]:
        """Remove sessions larger than max_size_mb"""
        logger.info(
            f"CLEANUP: Starting cleanup of sessions larger than {max_size_mb}MB"
        )

        sessions_dir = self.session_manager.base_path
        max_size_bytes = max_size_mb * 1024 * 1024

        if not sessions_dir.exists():
            return {"cleaned": 0, "freed_mb": 0, "errors": []}

        cleaned_count = 0
        freed_bytes = 0
        errors = []

        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            try:
                size = await self._calculate_directory_size(session_dir)

                if size > max_size_bytes:
                    await self._remove_directory_recursive(session_dir)
                    cleaned_count += 1
                    freed_bytes += size
                    logger.info(
                        f"CLEANUP: Removed large session {session_dir.name} ({size/1024/1024:.1f}MB)"
                    )

            except Exception as e:
                error_msg = (
                    f"Failed to cleanup large session {session_dir.name}: {e}"
                )
                errors.append(error_msg)
                logger.error(f"CLEANUP: {error_msg}")

        result = {
            "cleaned": cleaned_count,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "errors": errors,
        }

        logger.info(f"CLEANUP: Completed large session cleanup - {result}")
        return result

    async def cleanup_oldest_sessions(
        self, keep_count: int = 50
    ) -> Dict[str, Any]:
        """Keep only the newest N sessions, remove the rest"""
        logger.info(f"CLEANUP: Keeping only {keep_count} newest sessions")

        sessions_dir = self.session_manager.base_path

        if not sessions_dir.exists():
            return {"cleaned": 0, "freed_mb": 0, "errors": []}

        # Get all sessions with their last access times
        sessions = []
        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            try:
                last_access = await self._get_session_last_access(
                    session_dir.name
                )
                sessions.append((session_dir, last_access or datetime.min))
            except Exception as e:
                logger.error(
                    f"CLEANUP: Error getting session info for {session_dir.name}: {e}"
                )

        # Sort by last access (newest first) and keep only the top N
        sessions.sort(key=lambda x: x[1], reverse=True)
        sessions_to_remove = sessions[keep_count:]

        cleaned_count = 0
        freed_bytes = 0
        errors = []

        for session_dir, _ in sessions_to_remove:
            try:
                size = await self._calculate_directory_size(session_dir)
                await self._remove_directory_recursive(session_dir)
                cleaned_count += 1
                freed_bytes += size
                logger.info(f"CLEANUP: Removed old session {session_dir.name}")
            except Exception as e:
                error_msg = (
                    f"Failed to cleanup old session {session_dir.name}: {e}"
                )
                errors.append(error_msg)
                logger.error(f"CLEANUP: {error_msg}")

        result = {
            "cleaned": cleaned_count,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "errors": errors,
        }

        logger.info(f"CLEANUP: Completed oldest session cleanup - {result}")
        return result

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        sessions_dir = self.session_manager.base_path

        if not sessions_dir.exists():
            return {
                "total_sessions": 0,
                "total_size_mb": 0,
                "total_files": 0,
                "largest_session_mb": 0,
                "oldest_session": None,
                "newest_session": None,
            }

        total_size = 0
        total_files = 0
        session_count = 0
        largest_size = 0
        oldest_time = datetime.max
        newest_time = datetime.min

        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_count += 1

            try:
                # Calculate session size and file count
                size, files = await self._calculate_directory_stats(session_dir)
                total_size += size
                total_files += files

                if size > largest_size:
                    largest_size = size

                # Get session times
                last_access = await self._get_session_last_access(
                    session_dir.name
                )
                if last_access:
                    if last_access < oldest_time:
                        oldest_time = last_access
                    if last_access > newest_time:
                        newest_time = last_access

            except Exception as e:
                logger.error(
                    f"STATS: Error processing session {session_dir.name}: {e}"
                )

        return {
            "total_sessions": session_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_files": total_files,
            "largest_session_mb": round(largest_size / (1024 * 1024), 2),
            "oldest_session": (
                oldest_time if oldest_time != datetime.max else None
            ),
            "newest_session": (
                newest_time if newest_time != datetime.min else None
            ),
        }

    # ===================== HELPER METHODS =====================

    async def _touch_session(self, session_id: str):
        """Update session access time"""
        session_path = self.session_manager.base_path / session_id
        info_path = session_path / "session_info.json"

        try:
            info = {
                "session_id": session_id,
                "last_access": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            }

            # If session info exists, preserve created_at
            if info_path.exists():
                existing = await use_json(str(info_path), "r")
                if existing and "created_at" in existing:
                    info["created_at"] = existing["created_at"]

            await use_json(str(info_path), "w", info)
        except Exception as e:
            logger.error(f"TOUCH: Failed to update session {session_id}: {e}")

    async def _get_session_last_access(
        self, session_id: str
    ) -> Optional[datetime]:
        """Get last access time for a session"""
        session_path = self.session_manager.base_path / session_id
        info_path = session_path / "session_info.json"

        try:
            if info_path.exists():
                info = await use_json(str(info_path), "r")
                if info and "last_access" in info:
                    return datetime.fromisoformat(info["last_access"])

            # Fallback to directory modification time
            if session_path.exists():
                return datetime.fromtimestamp(session_path.stat().st_mtime)

        except Exception as e:
            logger.error(
                f"ACCESS_TIME: Error getting session time for {session_id}: {e}"
            )

        return None

    async def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"SIZE: Error calculating size for {directory}: {e}")
        return total_size

    async def _calculate_directory_stats(
        self, directory: Path
    ) -> Tuple[int, int]:
        """Calculate total size and file count for directory"""
        total_size = 0
        file_count = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        except Exception as e:
            logger.error(f"STATS: Error calculating stats for {directory}: {e}")
        return total_size, file_count

    async def _remove_directory_recursive(self, directory: Path):
        """Safely remove directory and all contents"""
        try:
            import shutil

            shutil.rmtree(directory)
        except Exception as e:
            logger.error(f"REMOVE: Failed to remove directory {directory}: {e}")
            raise


# ===== Session Cleanup Task =====
async def cleanup_expired_sessions(handle_manager: HandleManager):
    """Periodic cleanup of expired sessions using HandleManager"""
    logger.info("Background session cleanup task started with HandleManager.")
    while True:
        try:
            # Use the HandleManager's built-in cleanup methods
            logger.info("Starting automated cleanup cycle...")

            # Clean expired sessions (older than 24 hours)
            expired_stats = await handle_manager.cleanup_expired_sessions(
                max_age_hours=config.session_ttl_hours or 24
            )

            # Clean large sessions (over 100MB)
            large_stats = await handle_manager.cleanup_large_sessions(
                max_size_mb=100
            )

            # Get storage statistics
            storage_stats = await handle_manager.get_storage_stats()

            # If total storage is too high, clean oldest sessions
            if storage_stats["total_size_mb"] > 500:  # Over 500MB total
                oldest_stats = await handle_manager.cleanup_oldest_sessions(
                    keep_count=50  # Keep only 50 newest sessions
                )
                logger.info(f"Storage cleanup: {oldest_stats}")

            # Log cleanup results
            total_cleaned = expired_stats["cleaned"] + large_stats["cleaned"]
            total_freed = expired_stats["freed_mb"] + large_stats["freed_mb"]

            if total_cleaned > 0:
                logger.info(
                    f"Cleanup completed: {total_cleaned} sessions removed, "
                    f"{total_freed:.1f}MB freed. Storage stats: {storage_stats}"
                )
            else:
                logger.info(
                    f"Cleanup completed: No sessions removed. Storage stats: {storage_stats}"
                )

            # Log any errors
            all_errors = expired_stats["errors"] + large_stats["errors"]
            if all_errors:
                logger.warning(f"Cleanup errors: {all_errors}")

            await asyncio.sleep(
                config.cleanup_interval_hours * 3600
            )  # Sleep for cleanup interval

        except asyncio.CancelledError:
            logger.info("Background session cleanup task cancelled.")
            break  # Exit the loop when cancelled
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            logger.exception("Full cleanup error details:")
            await asyncio.sleep(300)  # Sleep 5 minutes on error


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize components
    session_manager = SessionManager()
    handle_manager = HandleManager(session_manager)  # Updated name
    logger.info("🚀 Saudi Location Intelligence MCP Server starting...")

    # Start the background task with HandleManager
    cleanup_task = asyncio.create_task(
        cleanup_expired_sessions(handle_manager)  # Pass HandleManager
    )

    try:
        yield AppContext(
            session_manager=session_manager,
            handle_manager=handle_manager,  # Updated name
        )
    finally:
        logger.info(
            "🛑 Saudi Location Intelligence MCP Server shutting down..."
        )
        # Cleanly shut down the background task
        logger.info("Cancelling background cleanup task...")
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info(
                "Background cleanup task has been successfully cancelled."
            )


# ===== FastMCP Server =====
mcp = FastMCP("saudi-location-intelligence", lifespan=app_lifespan)

# Register all tools
# --- NEW REGISTRATION CALL ---
register_auth_tools(mcp)
register_geospatial_tools(mcp)
register_territory_report_tools(mcp)
register_territory_optimization_tools(mcp)


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


# ===== Main Function =====
def main():
    """Main entry point with hot reloading enabled"""
    logger.info("🇸🇦 Saudi Location Intelligence MCP Server")

    # You can still check sys.argv manually if needed
    transport = "stdio"  # or "sse"
    port = 8001

    if transport == "stdio":
        logger.info(
            "📱 Starting stdio transport (compatible with Claude Desktop)"
        )
        mcp.run(transport="stdio")
    else:
        logger.info(f"🌐 Starting SSE transport on http://localhost:{port}")
        mcp.run(transport="sse", port=port)


if __name__ == "__main__":
    main()

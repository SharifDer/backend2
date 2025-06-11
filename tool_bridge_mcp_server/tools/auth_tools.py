# --- START OF FILE tools/auth_tools.py ---

import aiohttp
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Import your FastAPI configuration
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)
from config_factory import CONF

# --- NEW, TYPED IMPORT ---
# We import both the helper and the context class for full type support.
from tool_bridge_mcp_server.context import get_app_context
import logging

logger = logging.getLogger(__name__)


def register_auth_tools(mcp: FastMCP):
    """
    Registers authentication-related tools with the MCP server.
    """

    logger.info("Registering authentication tools with MCP server")

    @mcp.tool()
    async def user_login(
        email: str = Field(description="The user's email address."),
        password: str = Field(
            description="The user's password.", sensitive=True
        ),
    ) -> str:
        """
        Logs the user in to access their personal data and purchases.
        This must be done once per session to use other tools.
        """
        try:
            # Get the context and managers from the mcp instance
            app_ctx = get_app_context(mcp)
            session_manager = app_ctx.session_manager

            # Ensure a session exists, or create a new one
            session = await session_manager.get_current_session()
            if not session:
                session = await session_manager.create_session()

            # Prepare the request to your FastAPI login endpoint
            endpoint_url = "http://localhost:8000" + CONF.login
            payload = {
                "message": "login request from mcp server",
                "request_info": {},
                "request_body": {"email": email, "password": password},
            }

            logger.info(
                f"Attempting login for user {email} via endpoint: {endpoint_url}"
            )

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    endpoint_url, json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(
                            f"Login failed for {email}: {error_text}"
                        )
                        return f"Login failed. Please check your credentials. (Status: {response.status})"

                    response_json = await response.json()
                    login_data = response_json.get("data")

                    if not login_data:
                        return (
                            "Login failed: The server response was malformed."
                        )

                    # Update the session with the new auth tokens
                    await session_manager.update_session_auth(
                        session.session_id,
                        login_data["localId"],
                        login_data["idToken"],
                        login_data["refreshToken"],
                        int(login_data["expiresIn"]),
                    )

                    logger.info(
                        f"Successfully logged in user {email} ({login_data['localId']})"
                    )
                    return f"✅ Login successful for {login_data.get('email', email)}! You can now access your personalized data."

        except Exception as e:
            logger.exception(
                "An unexpected error occurred during the login process."
            )
            return "An internal error occurred during login. Please try again later."

    @mcp.tool(
        name="list_stored_data",
        description="List all stored data files in your current session",
    )
    async def list_stored_data() -> str:
        """List all data files stored in the current session"""
        try:
            app_ctx = get_app_context(mcp)
            session_manager = app_ctx.session_manager
            handle_manager = app_ctx.handle_manager

            session = await session_manager.get_current_session()
            if not session:
                return "❌ No active session found."

            files = await handle_manager.list_session_data(session.session_id)

            if not files:
                return "📂 No data files found in current session."

            result = "📂 **Stored Data Files**:\n\n"
            for file_info in files:
                result += f"• **{file_info['handle']}** ({file_info['data_type']} - {file_info['location']})\n"
                result += f"  Size: {file_info['size_bytes']:,} bytes | Modified: {file_info['modified_at']}\n\n"

            return result

        except Exception as e:
            logger.exception("Error listing stored data")
            return f"❌ Error listing data: {str(e)}"

# In your auth_tools.py or create debug_tools.py

    @mcp.tool()
    async def get_current_session_logs(lines: int = 50) -> str:
        """
        Get recent logs from your current session for debugging.
        Shows what happened during your login, tool calls, and other activities.
        """
        try:
            # Get current session from context
            app_ctx = get_app_context(mcp)
            session_manager = app_ctx.session_manager
            
            session = await session_manager.get_current_session()
            if not session:
                return "❌ No active session found"
            
            session_id = session.session_id
            
            # Find the current session log file
            session_path = session_manager.base_path / session_id
            log_files = list(session_path.glob(f"session_{session_id}_*.log"))
            
            if not log_files:
                return f"📂 No log file found for session {session_id}"
            
            # Get the most recent log file for this session
            current_log_file = max(log_files, key=lambda f: f.stat().st_mtime)
            
            with open(current_log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return f"📋 **Your Session ({session_id}) - Recent {len(recent_lines)} log entries:**\n\n" + "".join(recent_lines)
            
        except Exception as e:
            logger.exception("Error reading current session logs")
            return f"❌ Error reading session logs: {str(e)}"
# --- END OF FILE tools/auth_tools.py ---

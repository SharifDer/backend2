# --- START OF FILE tools/auth_tools.py ---

import logging
import aiohttp
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Import your FastAPI configuration
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from config_factory import CONF
# --- NEW, TYPED IMPORT ---
# We import both the helper and the context class for full type support.
from tool_bridge_mcp_server.context import get_app_context

logger = logging.getLogger(__name__)

def register_auth_tools(mcp: FastMCP):
    """
    Registers authentication-related tools with the MCP server.
    """

    @mcp.tool()
    async def user_login(
        email: str = Field(description="The user's email address."),
        password: str = Field(description="The user's password.", sensitive=True)
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
                "request_body": {"email": email, "password": password}
            }
            
            logger.info(f"Attempting login for user {email} via endpoint: {endpoint_url}")

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(endpoint_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"Login failed for {email}: {error_text}")
                        return f"Login failed. Please check your credentials. (Status: {response.status})"
                    
                    response_json = await response.json()
                    login_data = response_json.get('data')

                    if not login_data:
                         return "Login failed: The server response was malformed."

                    # Update the session with the new auth tokens
                    await session_manager.update_session_auth(
                        session.session_id,
                        login_data['localId'],
                        login_data['idToken'],
                        login_data['refreshToken'],
                        int(login_data['expiresIn'])
                    )
                    
                    logger.info(f"Successfully logged in user {email} ({login_data['localId']})")
                    return f"✅ Login successful for {login_data.get('email', email)}! You can now access your personalized data."

        except Exception as e:
            logger.exception("An unexpected error occurred during the login process.")
            return "An internal error occurred during login. Please try again later."

# --- END OF FILE tools/auth_tools.py ---
# --- START OF FILE tool_bridge_mcp_server/context.py ---

from __future__ import annotations
import os
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

# Use a forward reference to avoid importing the full class
# This helps prevent circular dependencies if you add more complex types
if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from .mcp_server import SessionManager, HandleManager

@dataclass
class AppContext:
    """
    Application context for lifespan management.
    This is defined here to be importable by both the server and tools
    without creating a circular dependency.
    """
    session_manager: "SessionManager"
    handle_manager: "HandleManager"

def get_app_context(mcp: "FastMCP") -> AppContext:
    """
    A typed helper to retrieve the specific AppContext from the generic MCP context.
    This provides full IntelliSense for session_manager and handle_manager.
    """
    ctx = mcp.get_context()
    # This cast is the key: it tells the type checker what to expect.
    return cast(AppContext, ctx.request_context.lifespan_context)

# --- END OF FILE tool_bridge_mcp_server/context.py ---
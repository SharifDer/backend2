"""
Configuration file for Geospatial Intelligence Analyst Agent
"""

import os
from pathlib import Path

class AgentConfig:
    """Configuration class for the Geospatial Analysis Agent"""
    
    # ===== PATHS =====
    # Base project path
    PROJECT_ROOT = Path("F:/git/s_locator/my_middle_API")
    
    # Python executable path
    PYTHON_EXECUTABLE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

    # MCP Server path
    MCP_SERVER_PATH = PROJECT_ROOT / "tool_bridge_mcp_server" / "mcp_server.py"
    
    # Reports directory path
    REPORTS_DIR = PROJECT_ROOT / "reports"
    
    # ===== MODEL SETTINGS =====
    DEFAULT_MODEL = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE = 0
    
    # ===== MCP SETTINGS =====
    MCP_SERVER_NAME = "saudi-location-intelligence"
    MCP_TRANSPORT = "stdio"
    
    
    
    # ===== REPORT SETTINGS =====
    SUPPORTED_REPORT_FORMATS = ['.md', '.html']
    DEFAULT_REPORT_TYPE = 'md'
    REPORT_FILE_PATTERNS = {
        'md': '*.md',
        'html': '*.html'
    }
    
    @classmethod
    def get_mcp_config(cls) -> dict:
        """Get MCP client configuration"""
        return {
            cls.MCP_SERVER_NAME: {
                "command": str(cls.PYTHON_EXECUTABLE),
                "args": [str(cls.MCP_SERVER_PATH)],
                "transport": cls.MCP_TRANSPORT,
                "env": {
                    "PYTHONPATH": str(cls.PROJECT_ROOT)
                }
            }
        }
    
    @classmethod
    def validate_paths(cls) -> bool:
        """Validate that all required paths exist"""
        paths_to_check = [
            cls.PROJECT_ROOT,
            cls.PYTHON_EXECUTABLE,
            cls.MCP_SERVER_PATH
        ]
        
        for path in paths_to_check:
            if not Path(path).exists():
                print(f"❌ Missing required path: {path}")
                return False
        
        # Create reports directory if it doesn't exist
        cls.REPORTS_DIR.mkdir(exist_ok=True)
        
        print("✅ All required paths validated successfully")
        return True
    
    @classmethod
    def get_reports_path(cls) -> str:
        """Get the reports directory path as string"""
        return str(cls.REPORTS_DIR)
    
    @classmethod
    def get_report_file_path(cls, filename: str) -> str:
        """Get full path for a report file"""
        return str(cls.REPORTS_DIR / filename)
    
    @classmethod
    def is_valid_report_file(cls, filename: str) -> bool:
        """Check if filename has a valid report format"""
        return any(filename.endswith(ext) for ext in cls.SUPPORTED_REPORT_FORMATS)
    

# Environment-specific configurations
# Use AgentConfig directly as Config
Config = AgentConfig
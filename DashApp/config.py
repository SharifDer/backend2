"""
Configuration file for Geospatial Intelligence Analyst Agent
"""

import os
from pathlib import Path

class AgentConfig:
    """Configuration class for the Geospatial Analysis Agent"""
    
    # ===== PATHS =====
    # Base project path
    PROJECT_ROOT = Path("F:/Upwork Projects/backend22")
    
    # Python executable path
    PYTHON_EXECUTABLE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

    # MCP Server path
    MCP_SERVER_PATH = PROJECT_ROOT / "tool_bridge_mcp_server" / "mcp_server.py"
    
    # Reports directory path
    REPORTS_DIR = PROJECT_ROOT / "reports"
    
    # ===== MODEL SETTINGS =====
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_TEMPERATURE = 0
    
    # ===== MCP SETTINGS =====
    MCP_SERVER_NAME = "saudi-location-intelligence"
    MCP_TRANSPORT = "stdio"
    
    # ===== ANALYSIS SETTINGS =====
    DEFAULT_ANALYSIS_TYPE = "comprehensive"
    DEFAULT_NUM_TERRITORIES = 6
    DEFAULT_DISTANCE_LIMIT = 3.0  # km
    
    # ===== AUTHENTICATION =====
    # Default credentials (should be overridden)
    DEFAULT_EMAIL = "mumerqureshi1994@gmail.com"
    DEFAULT_PASSWORD = "12345678"
    
    # ===== AVAILABLE BUSINESS TYPES =====
    BUSINESS_TYPES = [
        "supermarket",
        "restaurant", 
        "pharmacy",
        "gas_station",
        "retail",
        "hospital",
        "bank",
        "grocery_store",
        "shopping_mall",
        "hotel"
    ]
    
    # ===== AVAILABLE LOCATIONS =====
    SAUDI_CITIES = [
        "Riyadh",
        "Jeddah", 
        "Dammam",
        "Mecca",
        "Medina",
        "Khobar",
        "Taif",
        "Buraidah",
        "Khamis Mushait",
        "Hail"
    ]
    
    # ===== PROMPT TYPES =====
    PROMPT_TYPES = {
        "comprehensive": "Full academic report with detailed methodology",
        "simple": "Basic analysis without detailed methodology",
        "executive": "High-level business insights and strategic recommendations"
    }
    
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
    
    @classmethod
    def get_example_queries(cls) -> list:
        """Get example queries for different business types and locations"""
        return [
            "Create 6 sales territories for restaurants in Jeddah",
            "Optimize supermarket territories in Riyadh with 8 regions", 
            "Analyze pharmacy distribution in Dammam for 5 sales teams",
            "Generate territory plan for gas stations in Mecca",
            "Create 4 balanced territories for retail stores in Khobar",
            "Optimize hospital coverage in Medina with 3 service areas"
        ]

# Environment-specific configurations
class DevelopmentConfig(AgentConfig):
    """Development environment configuration"""
    DEBUG = True
    VERBOSE_LOGGING = True

class ProductionConfig(AgentConfig):
    """Production environment configuration"""
    DEBUG = False
    VERBOSE_LOGGING = False
    
    # Override with production paths if needed
    # PROJECT_ROOT = Path("/opt/geospatial-agent")

# Select configuration based on environment
ENV = os.getenv("AGENT_ENV", "development").lower()

if ENV == "production":
    Config = ProductionConfig
else:
    Config = DevelopmentConfig
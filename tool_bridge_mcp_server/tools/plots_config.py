"""
Plots Configuration Module
Centralized configuration for plot file locations and paths across the application.
"""

import os
from pathlib import Path


class PlotsConfig:
    """
    Centralized configuration for plot file locations and serving.
    
    This configuration supports multiple environments and deployment scenarios:
    - Development: Local file system paths
    - Production: Server-based paths
    - Docker: Container-mounted volumes
    """
    
    # ===== ENVIRONMENT DETECTION =====
    ENVIRONMENT = os.getenv("PLOTS_ENV", "development").lower()
    
    # ===== BASE PATHS CONFIGURATION =====
    
    # Default paths for different environments
    if ENVIRONMENT == "production":
        # Production server paths
        PROJECT_ROOT = Path("/opt/location-api")
        PLOTS_ROOT = PROJECT_ROOT / "static" / "plots"
        WEB_BASE_URL = "https://your-domain.com"
    elif ENVIRONMENT == "docker":
        # Docker container paths
        PROJECT_ROOT = Path("/app")
        PLOTS_ROOT = Path("/app/static/plots")
        WEB_BASE_URL = "http://localhost:8000"
    else:
        # Development environment (default)
        # Auto-detect project root from this file's location
        CURRENT_FILE = Path(__file__).resolve()
        PROJECT_ROOT = CURRENT_FILE.parent.parent  # Go up from tool_bridge_mcp_server/
        PLOTS_ROOT = PROJECT_ROOT / "static" / "plots"
        WEB_BASE_URL = "http://localhost:8000"
    
    # Allow override via environment variables
    PLOTS_ROOT = Path(os.getenv("PLOTS_ROOT_DIR", str(PLOTS_ROOT)))
    WEB_BASE_URL = os.getenv("WEB_BASE_URL", WEB_BASE_URL)
    
    # ===== PLOT SERVING CONFIGURATION =====
    
    # Web URL pattern for serving plots
    PLOTS_WEB_PATH = "/static/plots"
    
    # File patterns and extensions
    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".svg", ".pdf"]
    PLOT_FILE_PATTERN = r".*\.(png|jpg|jpeg|svg|pdf)$"
    
    # Plot categories for organization
    PLOT_CATEGORIES = {
        "territory_mapping": ["cluster", "market", "territory", "boundary"],
        "population_analysis": ["population", "demographic", "density"],
        "facility_distribution": ["supermarket", "facility", "store", "location"],
        "market_potential": ["customer", "potential", "market_share"],
        "accessibility_analysis": ["effective", "accessibility", "distance", "coverage"],
        "performance_metrics": ["performance", "metrics", "statistics", "balance"]
    }
    
    # ===== REPORT INTEGRATION SETTINGS =====
    
    # How plots should be referenced in reports
    PLOT_REFERENCE_MODE = os.getenv("PLOT_REFERENCE_MODE", "web_url")  # "web_url", "relative_path", "absolute_path"
    
    # Copy plots to report directory?
    COPY_PLOTS_TO_REPORTS = os.getenv("COPY_PLOTS_TO_REPORTS", "true").lower() == "true"
    
    # Plot display settings
    DEFAULT_PLOT_WIDTH = "100%"
    DEFAULT_PLOT_MAX_WIDTH = "800px"
    THUMBNAIL_SIZE = (300, 200)  # For thumbnails if needed
    
    # ===== VALIDATION AND UTILITIES =====
    
    @classmethod
    def validate_configuration(cls) -> tuple[bool, list[str]]:
        """
        Validate the plots configuration.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if plots root directory exists
        if not cls.PLOTS_ROOT.exists():
            issues.append(f"Plots root directory does not exist: {cls.PLOTS_ROOT}")
        elif not cls.PLOTS_ROOT.is_dir():
            issues.append(f"Plots root path is not a directory: {cls.PLOTS_ROOT}")
        
        # Check if directory is readable
        if cls.PLOTS_ROOT.exists() and not os.access(cls.PLOTS_ROOT, os.R_OK):
            issues.append(f"Plots root directory is not readable: {cls.PLOTS_ROOT}")
        
        # Validate environment
        valid_environments = ["development", "production", "docker"]
        if cls.ENVIRONMENT not in valid_environments:
            issues.append(f"Invalid environment '{cls.ENVIRONMENT}'. Must be one of: {valid_environments}")
        
        # Validate reference mode
        valid_modes = ["web_url", "relative_path", "absolute_path"]
        if cls.PLOT_REFERENCE_MODE not in valid_modes:
            issues.append(f"Invalid plot reference mode '{cls.PLOT_REFERENCE_MODE}'. Must be one of: {valid_modes}")
        
        return len(issues) == 0, issues
    
    @classmethod
    def get_plot_url(cls, filename: str) -> str:
        """
        Generate the appropriate URL/path for a plot file based on configuration.
        
        Args:
            filename: Name of the plot file
            
        Returns:
            URL or path string for the plot
        """
        if cls.PLOT_REFERENCE_MODE == "web_url":
            return f"{cls.WEB_BASE_URL}{cls.PLOTS_WEB_PATH}/{filename}"
        elif cls.PLOT_REFERENCE_MODE == "relative_path":
            return f"{cls.PLOTS_WEB_PATH}/{filename}"
        elif cls.PLOT_REFERENCE_MODE == "absolute_path":
            return str(cls.PLOTS_ROOT / filename)
        else:
            # Fallback to relative path
            return f"{cls.PLOTS_WEB_PATH}/{filename}"
    
    @classmethod
    def get_plot_file_path(cls, filename: str) -> Path:
        """
        Get the full file system path for a plot file.
        
        Args:
            filename: Name of the plot file
            
        Returns:
            Path object pointing to the plot file
        """
        return cls.PLOTS_ROOT / filename
    
    @classmethod
    def list_available_plots(cls) -> list[str]:
        """
        List all available plot files in the plots directory.
        
        Returns:
            List of plot filenames
        """
        if not cls.PLOTS_ROOT.exists():
            return []
        
        plot_files = []
        for ext in cls.SUPPORTED_EXTENSIONS:
            plot_files.extend([
                f.name for f in cls.PLOTS_ROOT.glob(f"*{ext}")
                if f.is_file()
            ])
        
        return sorted(plot_files)
    
    @classmethod
    def categorize_plot(cls, filename: str) -> str:
        """
        Categorize a plot file based on its filename.
        
        Args:
            filename: Name of the plot file
            
        Returns:
            Category name or 'other_visualizations'
        """
        filename_lower = filename.lower()
        
        for category, keywords in cls.PLOT_CATEGORIES.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        return "other_visualizations"
    
    @classmethod
    def create_plots_directory(cls) -> bool:
        """
        Create the plots directory if it doesn't exist.
        
        Returns:
            True if directory exists or was created successfully
        """
        try:
            cls.PLOTS_ROOT.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create plots directory {cls.PLOTS_ROOT}: {e}")
            return False
    
    @classmethod
    def get_configuration_summary(cls) -> dict:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary with configuration details
        """
        is_valid, issues = cls.validate_configuration()
        available_plots = cls.list_available_plots()
        
        return {
            "environment": cls.ENVIRONMENT,
            "plots_root": str(cls.PLOTS_ROOT),
            "plots_root_exists": cls.PLOTS_ROOT.exists(),
            "web_base_url": cls.WEB_BASE_URL,
            "plots_web_path": cls.PLOTS_WEB_PATH,
            "reference_mode": cls.PLOT_REFERENCE_MODE,
            "copy_to_reports": cls.COPY_PLOTS_TO_REPORTS,
            "supported_extensions": cls.SUPPORTED_EXTENSIONS,
            "is_valid": is_valid,
            "validation_issues": issues,
            "available_plots_count": len(available_plots),
            "sample_plots": available_plots[:5]  # Show first 5 as sample
        }
    
    @classmethod
    def print_configuration(cls):
        """Print a formatted configuration summary."""
        config = cls.get_configuration_summary()
        
        print("📊 PLOTS CONFIGURATION")
        print("=" * 50)
        print(f"🌍 Environment: {config['environment']}")
        print(f"📁 Plots Root: {config['plots_root']}")
        print(f"✅ Directory Exists: {config['plots_root_exists']}")
        print(f"🌐 Web Base URL: {config['web_base_url']}")
        print(f"📊 Available Plots: {config['available_plots_count']}")
        print(f"🔗 Reference Mode: {config['reference_mode']}")
        print(f"📋 Copy to Reports: {config['copy_to_reports']}")
        
        if not config['is_valid']:
            print(f"⚠️  Configuration Issues:")
            for issue in config['validation_issues']:
                print(f"   - {issue}")
        else:
            print("✅ Configuration Valid")
        
        if config['sample_plots']:
            print(f"\n📊 Sample Plots:")
            for plot in config['sample_plots']:
                print(f"   - {plot}")


# Environment-specific configurations
class DevelopmentPlotsConfig(PlotsConfig):
    """Development environment specific configuration."""
    pass


class ProductionPlotsConfig(PlotsConfig):
    """Production environment specific configuration."""
    
    # Production-specific overrides
    COPY_PLOTS_TO_REPORTS = False  # Don't copy in production
    PLOT_REFERENCE_MODE = "web_url"  # Always use web URLs in production


class DockerPlotsConfig(PlotsConfig):
    """Docker environment specific configuration."""
    
    # Docker-specific overrides
    PLOTS_ROOT = Path("/app/static/plots")
    WEB_BASE_URL = "http://localhost:8000"


# Export the appropriate config based on environment
def get_plots_config():
    """Get the appropriate plots configuration for the current environment."""
    env = os.getenv("PLOTS_ENV", "development").lower()
    
    if env == "production":
        return ProductionPlotsConfig
    elif env == "docker":
        return DockerPlotsConfig
    else:
        return DevelopmentPlotsConfig


# Default configuration instance
Config = get_plots_config()


# Convenience functions for common operations
def get_plot_url(filename: str) -> str:
    """Get URL for a plot file."""
    return Config.get_plot_url(filename)


def get_plot_path(filename: str) -> Path:
    """Get file system path for a plot file."""
    return Config.get_plot_file_path(filename)


def list_plots() -> list[str]:
    """List available plot files."""
    return Config.list_available_plots()


def validate_plots_config() -> tuple[bool, list[str]]:
    """Validate plots configuration."""
    return Config.validate_configuration()


if __name__ == "__main__":
    # Print configuration when run directly
    Config.print_configuration()
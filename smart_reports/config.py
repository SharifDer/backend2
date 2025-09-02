"""
Configuration file for smart reports system.
Control various settings including mock data usage.
"""

# Data Source Configuration
USE_MOCK_DATA = False  # Set to False to use real backend data
MOCK_DATA_CITY = "Riyadh"  # Default city for mock data

# Mock Data Customization
MOCK_LOCATIONS_COUNT = 5  # Number of mock locations to generate
MOCK_DATA_VARIANCE = 0.2  # Randomness factor (0.0 = deterministic, 1.0 = very random)

# HTML Generation Settings
HTML_OUTPUT_DIR = "static/pharmacy_report"  # Directory for generated HTML files
HTML_TEMPLATE_DIR = "templates"  # Directory for HTML templates
GENERATE_MAPS = True  # Whether to include map visualizations
GENERATE_CHARTS = True  # Whether to include chart visualizations

# Development Settings
DEBUG_MODE = True  # Enable debug logging and verbose output
SAVE_INTERMEDIATE_DATA = False  # Save intermediate data for debugging
LOG_LEVEL = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR)

# Mock Data Cities (available for testing)
AVAILABLE_CITIES = [
    "Riyadh",
    "Jeddah", 
    "Dammam",
    "Mecca",
    "Medina",
    "Abha",
    "Tabuk",
    "Hail"
]

def get_config():
    """Get current configuration as a dictionary."""
    return {
        "use_mock_data": USE_MOCK_DATA,
        "mock_data_city": MOCK_DATA_CITY,
        "mock_locations_count": MOCK_LOCATIONS_COUNT,
        "mock_data_variance": MOCK_DATA_VARIANCE,
        "html_output_dir": HTML_OUTPUT_DIR,
        "html_template_dir": HTML_TEMPLATE_DIR,
        "generate_maps": GENERATE_MAPS,
        "generate_charts": GENERATE_CHARTS,
        "debug_mode": DEBUG_MODE,
        "save_intermediate_data": SAVE_INTERMEDIATE_DATA,
        "log_level": LOG_LEVEL,
        "available_cities": AVAILABLE_CITIES
    }

def update_config(**kwargs):
    """Update configuration values."""
    global USE_MOCK_DATA, MOCK_DATA_CITY, MOCK_LOCATIONS_COUNT, MOCK_DATA_VARIANCE
    global HTML_OUTPUT_DIR, HTML_TEMPLATE_DIR, GENERATE_MAPS, GENERATE_CHARTS
    global DEBUG_MODE, SAVE_INTERMEDIATE_DATA, LOG_LEVEL
    
    if "use_mock_data" in kwargs:
        USE_MOCK_DATA = kwargs["use_mock_data"]
    if "mock_data_city" in kwargs:
        MOCK_DATA_CITY = kwargs["mock_data_city"]
    if "mock_locations_count" in kwargs:
        MOCK_LOCATIONS_COUNT = kwargs["mock_locations_count"]
    if "mock_data_variance" in kwargs:
        MOCK_DATA_VARIANCE = kwargs["mock_data_variance"]
    if "html_output_dir" in kwargs:
        HTML_OUTPUT_DIR = kwargs["html_output_dir"]
    if "html_template_dir" in kwargs:
        HTML_TEMPLATE_DIR = kwargs["html_template_dir"]
    if "generate_maps" in kwargs:
        GENERATE_MAPS = kwargs["generate_maps"]
    if "generate_charts" in kwargs:
        GENERATE_CHARTS = kwargs["generate_charts"]
    if "debug_mode" in kwargs:
        DEBUG_MODE = kwargs["debug_mode"]
    if "save_intermediate_data" in kwargs:
        SAVE_INTERMEDIATE_DATA = kwargs["save_intermediate_data"]
    if "log_level" in kwargs:
        LOG_LEVEL = kwargs["log_level"]
    
    print(f"✅ Configuration updated: {kwargs}")

def print_config():
    """Print current configuration."""
    config = get_config()
    print("\n🔧 Current Configuration:")
    print("=" * 40)
    for key, value in config.items():
        if key == "available_cities":
            print(f"  {key}: {', '.join(value)}")
        else:
            print(f"  {key}: {value}")
    print("=" * 40)

if __name__ == "__main__":
    print_config()

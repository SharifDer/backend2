"""
Configuration file for smart reports system.
Control various settings for report generation.
"""

# HTML Generation Settings
HTML_OUTPUT_DIR = "static/pharmacy_report"  # Directory for generated HTML files
HTML_TEMPLATE_DIR = "templates"  # Directory for HTML templates
GENERATE_MAPS = True  # Whether to include map visualizations
GENERATE_CHARTS = True  # Whether to include chart visualizations

# Development Settings
DEBUG_MODE = True  # Enable debug logging and verbose output
SAVE_INTERMEDIATE_DATA = False  # Save intermediate data for debugging
LOG_LEVEL = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR)

# Available Cities
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
    global HTML_OUTPUT_DIR, HTML_TEMPLATE_DIR, GENERATE_MAPS, GENERATE_CHARTS
    global DEBUG_MODE, SAVE_INTERMEDIATE_DATA, LOG_LEVEL
    
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

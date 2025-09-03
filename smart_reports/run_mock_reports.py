#!/usr/bin/env python3
"""
Command-line interface for running mock pharmacy reports.
Easy way to test HTML generation without backend dependencies.
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_reports.config import update_config, print_config, AVAILABLE_CITIES
from smart_reports.mock_data import get_mock_data, get_mock_request
from smart_reports.reports import generate_html_pharmacy_report_file

async def generate_report_for_city(city_name: str, output_dir: str = None):
    """Generate a pharmacy report for a specific city using mock data."""
    print(f"🚀 Generating pharmacy report for {city_name}...")
    
    try:
        # Update config for this city
        update_config(mock_data_city=city_name)
        if output_dir:
            update_config(html_output_dir=output_dir)
        
        # Get mock request data
        mock_req = get_mock_request(city_name)
        print(f"   ✅ Mock request generated for {city_name}")
        
        # Generate the HTML report
        html_file_path = await generate_html_pharmacy_report_file(report_data=mock_req)
        
        if html_file_path and os.path.exists(html_file_path):
            print(f"   ✅ HTML report generated successfully!")
            print(f"   📁 File location: {html_file_path}")
            
            # Get file size
            file_size = os.path.getsize(html_file_path) / 1024  # KB
            print(f"   📏 File size: {file_size:.1f} KB")
            
            # Try to open the file in browser
            try:
                import webbrowser
                webbrowser.open(f"file://{html_file_path}")
                print(f"   🌐 Opened report in browser")
            except Exception as e:
                print(f"   ⚠️  Could not open in browser: {e}")
                print(f"   📂 Open manually: {html_file_path}")
            
            return html_file_path
        else:
            print(f"   ❌ Failed to generate HTML report for {city_name}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error generating report for {city_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def generate_all_city_reports(output_dir: str = None):
    """Generate reports for all available cities."""
    print(f"🌍 Generating reports for all cities...")
    
    results = {}
    for city in AVAILABLE_CITIES:
        result = await generate_report_for_city(city, output_dir)
        results[city] = result
        print()  # Add spacing between cities
    
    # Summary
    successful = sum(1 for r in results.values() if r is not None)
    total = len(AVAILABLE_CITIES)
    print(f"📊 Summary: {successful}/{total} reports generated successfully")
    
    return results

def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate mock pharmacy reports for HTML development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for Riyadh
  python run_mock_reports.py --city Riyadh
  
  # Generate reports for all cities
  python run_mock_reports.py --all
  
  # Generate report with custom output directory
  python run_mock_reports.py --city Jeddah --output-dir custom_reports
  
  # Show current configuration
  python run_mock_reports.py --config
  
  # Update configuration
  python run_mock_reports.py --set-config use_mock_data=True mock_data_city=Dammam
        """
    )
    
    parser.add_argument(
        "--city", 
        choices=AVAILABLE_CITIES,
        help="Generate report for specific city"
    )
    
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Generate reports for all available cities"
    )
    
    parser.add_argument(
        "--output-dir", 
        help="Custom output directory for generated reports"
    )
    
    parser.add_argument(
        "--config", 
        action="store_true",
        help="Show current configuration"
    )
    
    parser.add_argument(
        "--set-config", 
        nargs="+",
        help="Update configuration values (e.g., use_mock_data=True mock_data_city=Dammam)"
    )
    
    parser.add_argument(
        "--list-cities", 
        action="store_true",
        help="List all available cities"
    )
    
    args = parser.parse_args()
    
    # Handle configuration commands
    if args.config:
        print_config()
        return
    
    if args.set_config:
        config_updates = {}
        for item in args.set_config:
            if "=" in item:
                key, value = item.split("=", 1)
                # Convert string values to appropriate types
                if value.lower() in ("true", "false"):
                    config_updates[key] = value.lower() == "true"
                elif value.isdigit():
                    config_updates[key] = int(value)
                elif value.replace(".", "").isdigit():
                    config_updates[key] = float(value)
                else:
                    config_updates[key] = value
        
        update_config(**config_updates)
        print_config()
        return
    
    if args.list_cities:
        print("🏙️  Available cities:")
        for i, city in enumerate(AVAILABLE_CITIES, 1):
            print(f"   {i}. {city}")
        return
    
    # Handle report generation
    if not any([args.city, args.all]):
        parser.print_help()
        return
    
    # Ensure output directory exists
    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        print(f"📁 Using custom output directory: {args.output_dir}")
    
    # Generate reports
    if args.city:
        asyncio.run(generate_report_for_city(args.city, args.output_dir))
    elif args.all:
        asyncio.run(generate_all_city_reports(args.output_dir))

if __name__ == "__main__":
    main()

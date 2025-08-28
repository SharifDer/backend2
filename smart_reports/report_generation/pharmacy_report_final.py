#!/usr/bin/env python3
"""
pharmacy_report_final.py

Enhanced pharmacy site selection report generator with modular architecture.
Generates comprehensive 3-page markdown reports with:
- Enhanced visual design and styling
- Investment insights and market analysis  
- Price and competition analysis
- Interactive charts and maps
- Arabic text support

Usage: python pharmacy_report_final.py [scores_path] [output_dir] [output_filename] [top_n]
"""
import os
import logging
from typing import Dict 
# Import our modular components

from .data_processor import  process_sites, calculate_statistics
from .chart_generator import plot_top_stacked, plot_traffic, plot_breakdown
from .map_generator import create_static_map_png, create_demographic_heatmap_png
from .report_generator import generate_markdown
from .report_config import FONT_FAMILY, UNICODE_MINUS, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME
# Set up matplotlib for Arabic text support
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = FONT_FAMILY
plt.rcParams['axes.unicode_minus'] = UNICODE_MINUS


def generate_all_charts(sites: list, outdir: str, top_n: int , criterions : dict) -> dict:
    """Generate all required charts and return their file paths."""
    charts = {
        'top_stacked': os.path.join(outdir, 'charts', 'top_stacked.png'),
        'traffic': os.path.join(outdir, 'charts', 'traffic_flow.png'),
        'best_breakdown': os.path.join(outdir, 'charts', 'best_breakdown.png')
    }
    
    # Generate top stacked chart
    try:
        list_criterions = list(criterions)
        plot_top_stacked(sites, top_n, charts['top_stacked'] , list_criterions)
        logging.info("✅ Generated top stacked chart")
    except Exception as e:
        logging.warning(f"❌ Failed to generate top stacked chart: {e}" , exc_info=True)
    
    # Generate traffic chart
    try:
        plot_traffic(sites, charts['traffic'])
        logging.info("✅ Generated traffic analysis chart")
    except Exception as e:
        logging.warning(f"❌ Failed to generate traffic chart: {e}" , exc_info=True)
    
    # Generate best site breakdown chart
    try:
        if sites:
            best = max(sites, key=lambda s: s.get('total_score', 0))
            plot_breakdown(best, charts['best_breakdown'] , criterions)
            logging.info("✅ Generated best site breakdown chart")
    except Exception as e:
        logging.warning(f"❌ Failed to generate breakdown chart: {e}" , exc_info=True)
    
    return charts

def ensure_directories(outdir: str):
    """Ensure all required output directories exist."""
    for sub in ['charts', 'maps', 'data']:
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)

def generate_all_maps(sites: list, outdir: str, top_n: int) -> tuple:
    """Generate all required maps and return their file paths."""
    map_png = os.path.join(outdir, 'maps', 'candidates_map.png')
    heat_png = os.path.join(outdir, 'maps', 'demographics_heatmap.png')
    
    # Generate candidates map
    extent = None
    try:
        extent = create_static_map_png(sites, map_png, top_n=top_n)
        logging.info("✅ Generated candidates map")
    except Exception as e:
        logging.warning(f"❌ Failed to generate candidates map: {e}", exc_info=True)
    
    # Generate demographic heatmap
    try:
        create_demographic_heatmap_png(sites, heat_png, extent=extent)
        logging.info("✅ Generated demographic heatmap")
    except Exception as e:
        logging.warning(f"❌ Failed to generate demographic heatmap: {e}", exc_info=True)
    
    return map_png, heat_png


async def generate_report_from_data(
    scores_data: dict,
    criterion_weights : Dict[str , float],
    max_total : float ,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    output_filename: str = DEFAULT_OUTPUT_FILENAME,
    top_n: int = 10,
) -> Dict:
    """
    Generate pharmacy site selection report from in-memory data.
    
    Args:
        scores_data: Dictionary containing scores data from generate_pharmacy_report function
        output_dir: Output directory path
        output_filename: Output markdown filename
        top_n: Number of top sites to analyze
        
    Returns:
        Dict Containing all the report data
        
    Raises:
        Exception: If report generation fails
    """
    
    print("🚀 Starting Enhanced Pharmacy Site Analysis...")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Analyzing top {top_n} locations")
    
    # Set up output directory
    os.makedirs(output_dir, exist_ok=True)
    ensure_directories(output_dir)
    
    # Process data directly from memory
    logging.info("📊 Processing site data from memory...")
    try:
        sites, warnings = process_sites(scores_data , criterion_weights)
        stats = calculate_statistics(sites)
        
        logging.info(f"✅ Processed {len(sites)} sites with {len(warnings)} warnings")
        
    except Exception as e:
        logging.error(f"❌ Failed to process data: {e}")
        raise Exception(f"Data processing failed: {e}")

    # Generate charts
    logging.info("📈 Generating charts...")
    criterions = criterion_weights.keys()
    charts = generate_all_charts(sites, output_dir, top_n , criterions)

    # Generate maps
    logging.info("🗺️  Generating maps...")
    map_png, heat_png = generate_all_maps(sites, output_dir, top_n)
    # Generate markdown report
    logging.info("📝 Generating enhanced markdown report...")
    try:
        report_data = generate_markdown(
            sites, output_dir, output_filename, top_n,
            charts, map_png, heat_png, len(sites), stats,
            max_total , criterion_weights
        )
        logging.info("✅ Report generation completed successfully")
        
    except Exception as e:
        logging.error(f"❌ Failed to generate report: {e}")
        raise Exception(f"Report generation failed: {e}")
    print(f"\n🎉 SUCCESS! Enhanced report generated:")
    print(f"\n💡 Open the report in any markdown viewer or browser for best experience!")
    
    return report_data

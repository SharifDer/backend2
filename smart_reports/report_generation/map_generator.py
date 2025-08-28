"""
Map generation utilities for pharmacy site selection analysis.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point
from typing import List, Dict, Optional, Tuple
import logging
from smart_reports.report_generation.report_config import MAP_DPI, MAP_FIGSIZE
import os 
from html2image import Html2Image
import folium
import random

def generate_site_map_image(site_data: Dict, output_dir: str , MAX_TOTAL) -> str:
    """
    Generate map image for a site and return the relative path for markdown
    Adjusted to match depth and visual style of first function.
    """
    # Create map centered on site
    m = folium.Map(
        location=[site_data['lat'], site_data['lng']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )

    # Generate sample businesses around the site
    businesses = []
    business_types = [
    (['pharmacy']*3, 'brown'),
    (['hospital']*8, 'orange'),
    (['dentist']*2, 'blue'),
    (['supermarket']*4, 'gray'),
    (['bank']*6, 'purple')
                            ]

    competitor_markers = []

    # Generate businesses with random positions
    total_businesses = 0
    for keywords, color in business_types:
        count = 5  # default count for example
        for i in range(count):
            dlat = random.uniform(-0.002, 0.002)
            dlng = random.uniform(-0.002, 0.002)
            poi_name = f"{keywords[0].title()} {i+1}"
            poi_categories = keywords

            if color == 'brown':
                competitor_markers.append({'name': poi_name})

            total_businesses += 1

            folium.CircleMarker(
                location=[site_data['lat'] + dlat, site_data['lng'] + dlng],
                radius=12 if color == 'brown' else 8,
                popup=folium.Popup(f"""
                <b>{poi_name}</b><br>
                Category: {', '.join(poi_categories)}<br>
                Distance: {random.randint(50,300)}m
                """, max_width=200),
                tooltip=poi_name,
                color=color,
                fill=True,
                opacity=0.8,
                weight=2 if color == 'brown' else 1
            ).add_to(m)

    # Property marker (red star)
    folium.Marker(
        [site_data['lat'], site_data['lng']],
        popup=folium.Popup(f"""
        <div style='width: 250px'>
            <h4>🏢 {site_data['display_name']}</h4>
            <b>Final Score:</b> {(site_data['total_score'] / MAX_TOTAL) * 100:.1f}<br>
            <b>Competitors:</b> {len(competitor_markers)} pharmacies<br>
            <b>Businesses:</b> {total_businesses} total
        </div>
        """, max_width=300),
        tooltip=f"{site_data['display_name']} - Score: {(site_data['total_score'] / MAX_TOTAL) * 100:.1f}",
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(m)

    # Analysis radius circle
    folium.Circle(
        [site_data['lat'], site_data['lng']],
        radius=300,
        color='red',
        weight=2,
        fill=True,
        fillColor='red',
        fillOpacity=0.1,
        opacity=0.6,
        popup="Analysis radius: 300m"
    ).add_to(m)

    # Traffic line (example coordinates)
    traffic_coords = [
        [site_data['lat'] - 0.003, site_data['lng'] - 0.005],
        [site_data['lat'] + 0.003, site_data['lng'] + 0.005]
    ]
    folium.PolyLine(
        locations=traffic_coords,
        color='red',
        weight=6,
        opacity=0.6,
        popup='Traffic Pattern'
    ).add_to(m)

    # Title
    title_html = '''
    <div style="position: fixed; 
                top: 20px; left: 50%; transform: translateX(-50%);
                background-color: rgba(233, 30, 99, 0.9); 
                color: white;
                padding: 10px 20px; border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                z-index: 9999;">
        <h3 style="margin: 0; color: white;">📍 Site Location Map</h3>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Legend
    legend_html = f'''
    <div style="position: fixed; 
                top: 80px; left: 50px; width: 250px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    
    <div style="background-color: #e8f4f8; padding: 8px; margin-bottom: 8px; border-radius: 4px;">
        <b style="font-size: 14px;">📍 {site_data['display_name']}</b><br>
        <b>Final Score:</b> {(site_data['total_score'] / MAX_TOTAL) * 100:.1f}<br>
        <b>Competitors:</b> {len(competitor_markers)} pharmacies<br>
        <b>Businesses:</b> {total_businesses} total<br>
    </div>
    
    <b>Legend:</b><br>
    ⭐ <span style="color: red;"><b>Red Star</b></span> = Property<br>
    🟤 <span style="color: brown;"><b>Brown</b></span> = Pharmacies<br>
    🟠 <span style="color: orange;"><b>Orange</b></span> = Restaurants<br>
    🟣 <span style="color: purple;"><b>Purple</b></span> = Shopping<br>
    🔵 <span style="color: blue;"><b>Blue</b></span> = Hotels<br>
    🔘 <span style="color: gray;"><b>Gray</b></span> = Banks<br>
    🔴 <span style="color: red;"><b>Dark Red</b></span> = Traffic<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save HTML
    site_rank = site_data.get("id", 1)
    html_filename = f"site_{site_rank}_map.html"
    html_path = os.path.join(output_dir, html_filename)
    m.save(html_path)

    # Save PNG
    png_filename = f"site_{site_rank}_map.png"
    png_path = os.path.join(output_dir, png_filename)

    # try:
    hti = Html2Image(size=(1200, 800))
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    hti.screenshot(html_str=html_content, save_as=png_filename)

    import shutil
    if os.path.exists(png_filename):
        shutil.move(png_filename, png_path)

    print(f"Generated map image: {png_path}")
    return png_path, html_path

def create_static_map_png(sites: List[Dict], outpath: str, top_n: int = 10, extent: Optional[Tuple] = None) -> Optional[Tuple]:
    """
    Create a static map showing candidate locations.
    
    Args:
        sites: List of site dictionaries
        outpath: Output file path
        top_n: Number of top sites to highlight
        extent: Map extent (xmin, xmax, ymin, ymax)
    
    Returns:
        Map extent tuple if successful, None otherwise
    """
    try:
        pad = 0.1
        coords = [(s['lat'], s['lng']) for s in sites if s['lat'] is not None and s['lng'] is not None]
        
        fig, ax = plt.subplots(figsize=MAP_FIGSIZE, dpi=MAP_DPI)

        if not coords:
            ax.text(0.5, 0.5, 'No coordinates available to render map', 
                   ha='center', va='center', fontsize=16)
            ax.axis('off')
            ax.set_title("Candidate Locations Map", fontsize=18, fontweight='bold', pad=20)
            fig.savefig(outpath, pad_inches=pad, bbox_inches='tight')
            plt.close(fig)
            return None

        # Create GeoDataFrame
        valid_sites = [s for s in sites if s['lat'] is not None and s['lng'] is not None]
        gdf = gpd.GeoDataFrame(
            valid_sites, 
            geometry=[Point(s['lng'], s['lat']) for s in valid_sites]
        )
        gdf = gdf.set_crs(epsg=4326).to_crs(epsg=3857)

        # Plot all candidates
        gdf.plot(ax=ax, color='lightblue', alpha=0.7, markersize=60, 
                label='All Candidates', edgecolors='darkblue', linewidth=1)

        # Highlight top sites
        top_sites = sorted(valid_sites, key=lambda x: x.get('total_score', 0), reverse=True)[:top_n]
        for i, site in enumerate(top_sites, start=1):
            # Convert to Web Mercator
            point_3857 = gpd.GeoSeries([Point(site['lng'], site['lat'])], crs=4326).to_crs(epsg=3857)
            x, y = point_3857.geometry[0].coords[0]
            
            # Plot star marker
            ax.scatter(x, y, s=200, color='red', marker='*', 
                      edgecolors='darkred', linewidth=2, zorder=5)
            
            # Add rank number
            ax.text(x, y, f" {i}", fontsize=12, weight='bold', 
                   color='white', ha='left', va='center', zorder=6)

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.8)
        
        ax.set_axis_off()
        ax.set_title("Top Recommended Pharmacy Locations", 
                    fontsize=18, fontweight='bold', pad=20)

        # Set extent if provided
        if extent is None:
            extent = ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1]
        else:
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])

        # Add legend
        ax.legend(loc='upper right', framealpha=0.9)

        fig.savefig(outpath, pad_inches=pad, bbox_inches='tight', dpi=MAP_DPI)
        plt.close(fig)
        
        logging.info(f"Successfully created map: {outpath}")
        return extent

    except Exception as e:
        logging.error(f"Failed to create static map: {e}")
        plt.close('all')
        return None


def create_demographic_heatmap_png(sites: List[Dict], outpath: str, 
                                 demographic_key_prefix: str = 'demographics__', 
                                 extent: Optional[Tuple] = None):
    """
    Create a demographic heatmap showing population density or related metrics.
    
    Args:
        sites: List of site dictionaries
        outpath: Output file path
        demographic_key_prefix: Prefix to identify demographic data keys
        extent: Map extent (xmin, xmax, ymin, ymax)
    """
    try:
        pad = 0.1
        xs, ys, vals = [], [], []

        # Extract demographic data
        for site in sites:
            if site['lat'] is None or site['lng'] is None:
                continue
                
            # Find demographic values
            demo_val = None
            for key, value in site['details'].items():
                if demographic_key_prefix in key and 'density' in key.lower():
                    if not np.isnan(value):
                        demo_val = value
                        break
            
            if demo_val is not None:
                xs.append(site['lng'])
                ys.append(site['lat'])
                vals.append(demo_val)

        if not vals:
            # No demographic data found, create empty map
            fig, ax = plt.subplots(figsize=MAP_FIGSIZE, dpi=MAP_DPI)
            ax.text(0.5, 0.5, 'No demographic data available for heatmap', 
                   ha='center', va='center', fontsize=16)
            ax.axis('off')
            ax.set_title("Demographic Heatmap", fontsize=18, fontweight='bold', pad=20)
            fig.savefig(outpath, pad_inches=pad, bbox_inches='tight')
            plt.close(fig)
            return

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {'value': vals}, 
            geometry=[Point(lon, lat) for lon, lat in zip(xs, ys)], 
            crs=4326
        ).to_crs(epsg=3857)

        # Normalize values
        norm = Normalize(vmin=np.nanmin(vals), vmax=np.nanmax(vals))

        fig, ax = plt.subplots(figsize=MAP_FIGSIZE, dpi=MAP_DPI)
        
        # Plot heatmap
        gdf.plot(ax=ax, column='value', cmap='YlOrRd', markersize=120, 
                alpha=0.8, legend=True, norm=norm, edgecolors='black', linewidth=0.5)

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.6)
        
        ax.set_title("Demographic Density Heatmap", fontsize=18, fontweight='bold', pad=20)
        ax.set_axis_off()

        # Set extent if provided
        if extent is not None:
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])

        fig.savefig(outpath, pad_inches=pad, bbox_inches='tight', dpi=MAP_DPI)
        plt.close(fig)
        
        logging.info(f"Successfully created demographic heatmap: {outpath}")

    except Exception as e:
        logging.error(f"Failed to create demographic heatmap: {e}")
        plt.close('all')
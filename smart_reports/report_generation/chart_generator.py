"""
Chart generation utilities for pharmacy site selection analysis.
"""
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from typing import List, Dict
import arabic_reshaper
from bidi.algorithm import get_display
from .report_config import CHART_DPI,CHART_FIGSIZE
import logging


# Set up matplotlib for Arabic text
from matplotlib import rcParams
rcParams['font.family'] = 'Arial'
rcParams['axes.unicode_minus'] = False


def setup_arabic_text(text: str) -> str:
    """Process Arabic text for proper display in matplotlib."""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text


def plot_top_stacked(sites: List[Dict], top_n: int, outpath: str , criterions : dict):
    """Generate stacked bar chart of top performing sites."""
    top = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]
    if not top:
        return
    
    # Process Arabic labels
    labels = [setup_arabic_text(s['display_name']) for s in top]
    
    # Prepare data for stacking
    comps = [f"{c}_score" for c in criterions]
    data = np.array([[s['scores'].get(c, 0) for s in top] for c in comps])

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    bottoms = np.zeros(len(labels))
    cmap = cm.get_cmap('tab20')

    # Create stacked bars
    for i in range(data.shape[0]):
        ax.bar(labels, data[i], bottom=bottoms, 
               label=criterions[i].capitalize(), color=cmap(i))
        bottoms += data[i]

    ax.set_title(f"Top {top_n} Locations — Component Scores (Stacked)", 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Weighted Points', fontsize=12)
    ax.legend(loc='upper right', fontsize='small')

    # Format x-axis
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)

    plt.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.9)
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)


def plot_traffic(sites: List[Dict], outpath: str):
    """Generate traffic analysis chart."""
    top = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:10]
    if not top:
        return
    
    x = [setup_arabic_text(s['display_name']) for s in top]
    veh_vals = []
    speed_vals = []
    
    # Extract traffic data
    for s in top:
        found_veh = float('nan')
        found_speed = float('nan')
        
        for k, v in s['details'].items():
            kl = k.lower()
            if 'daily' in kl and ('vehicle' in kl or 'vehicles' in kl or 'viechle' in kl or 'veh' in kl):
                found_veh = v
            if 'average' in kl and ('speed' in kl or 'vehicle' in kl or 'viechle' in kl):
                found_speed = v
                
        veh_vals.append(0.0 if math.isnan(found_veh) else float(found_veh))
        speed_vals.append(0.0 if math.isnan(found_speed) else float(found_speed))

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)

    # Choose what to display based on available data
    if any(v > 0 for v in veh_vals):
        bars = ax.bar(x, veh_vals, color='steelblue', alpha=0.8)
        ax.set_ylabel('Daily Vehicle Count')
        ax.set_title('Traffic Analysis — Daily Vehicle Count (Top 10)', 
                     fontsize=16, fontweight='bold')
    elif any(v > 0 for v in speed_vals):
        bars = ax.bar(x, speed_vals, color='orange', alpha=0.8)
        ax.set_ylabel('Average Vehicle Speed (km/h)')
        ax.set_title('Traffic Analysis — Average Speed (Top 10)', 
                     fontsize=16, fontweight='bold')
    else:
        traffic_scores = [s.get('scores', {}).get('traffic_score', 0) for s in top]
        bars = ax.bar(x, traffic_scores, color='green', alpha=0.8)
        ax.set_ylabel('Traffic Score (Points)')
        ax.set_title('Traffic Analysis — Traffic Score (Top 10)', 
                     fontsize=16, fontweight='bold')

    # Format chart
    ax.set_xticklabels(x, rotation=45, ha='right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')

    plt.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.9)
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)


def plot_breakdown(site: Dict, outpath: str , criterions : dict):
    """Generate scoring breakdown chart for the best site."""
    vals = [site.get('scores', {}).get(f'{c}_score', 0.0) for c in criterions]
    
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=150)
    
    # Create horizontal bar chart for better readability
    colors = plt.cm.Set3(np.linspace(0, 1, len(criterions)))
    bars = ax.barh([c.capitalize() for c in criterions], vals, color=colors, alpha=0.8)
    
    ax.set_xlabel('Weighted Points')
    ax.set_title(f"Scoring Breakdown — Best Site: {setup_arabic_text(site['display_name'])}", 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, vals)):
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
               f'{val:.2f}', ha='left', va='center', fontweight='bold')
    
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_axisbelow(True)
    
    fig.tight_layout()
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)


def plot_score_vs_price(sites: List[Dict], top_n: int, outpath: str):
    """Scatter plot of Final Score vs Price for top N sites with colored points like the example."""
    CHART_FIGSIZE = (10, 6)
    CHART_DPI = 100

    # Sort top N sites by total_score
    top_sites = sorted(
    [s for s in sites if isinstance(s.get('price'), (int, float))],
    key=lambda s: s.get('total_score', 0),
    reverse=True
                )[:top_n]
    if not top_sites:
        return

    # Extract data
    scores = [s['total_score'] for s in top_sites]
    prices = [s.get('price', 0) for s in top_sites]
    names = [f"  Number {i}" for i,_ in enumerate(top_sites)]

    # Color points based on score tier
    colors = []
    for score in scores:
        if score >= 75:
            colors.append('green')
        elif score >= 70:
            colors.append('orange')
        else:
            colors.append('red')

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    
    # Scatter plot
    ax.scatter(prices, scores, color=colors, s=80, edgecolor='black', linewidth=0.5, zorder=3)
    
    # Optional: add labels next to points
    for x, y, label in zip(prices, scores, names):
        ax.text(x, y, f" {label}", fontsize=9, ha='left', va='center', zorder=4)

    ax.set_xlabel('Rent Price (SAR)', fontsize=12)
    ax.set_ylabel('Final Score', fontsize=12)
    ax.set_title(f"Rent Price vs Final Score — Top {top_n} Sites", fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)





def plot_healthcare_vs_competition(sites: List[Dict], outpath: str, top_n: int):
    """
    Generates a scatter plot of healthcare facility count vs. competition for the top N sites.
    
    Args:
        sites (List[Dict]): A list of site data dictionaries.
        outpath (str): The file path to save the generated chart image.
        top_n (int): The number of top sites to include in the plot, sorted by score.
    """
    CHART_FIGSIZE = (10, 6)
    CHART_DPI = 100
        
    top_sites = sorted(sites, key=lambda s: s.get('total_score', 0), reverse=True)[:top_n]

    if not top_sites:
        logging.warning("No sites to plot for healthcare vs competition chart.")
        return

    # Extract data for the plot, defaulting to 0 if keys are missing or values are None
    # X-axis: Sum of hospitals and dentists
    healthcare_counts = [
        (s.get('num_of_hospitals')) + (s.get('num_of_dentists'))
        for s in top_sites
    ]
    # Y-axis: Number of competing pharmacies
    competition_counts = [s.get('competing_pharmacies')for s in top_sites]

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)

    # Create the scatter plot with styling similar to the example image
    ax.scatter(
        healthcare_counts, 
        competition_counts, 
        s=100,                  # Marker size
        c='#3498db',            # A clear, medium blue color
        alpha=0.8,              # Semi-transparent markers
        edgecolors='#2980b9'    # A slightly darker edge for definition
    )

    # --- Titles and Labels ---
    ax.set_title('Healthcare Count vs Competition', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Number of Healthcare Facilities (Hospitals & Dentists)', fontsize=12)
    ax.set_ylabel('Number of Competing Pharmacies', fontsize=12)

    # --- Grid and Layout ---
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
    ax.set_axisbelow(True) # Ensure the grid is drawn behind the plot elements

    # Set axis limits to start from 0 and add some padding for clarity
    ax.set_xlim(left=-1, right=max(healthcare_counts or [0]) * 1.1 + 2)
    ax.set_ylim(bottom=-1, top=max(competition_counts or [0]) * 1.1 + 2)

    # --- Save Figure ---
    plt.tight_layout()
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)
    logging.info(f"Successfully generated healthcare vs competition chart at {outpath}")
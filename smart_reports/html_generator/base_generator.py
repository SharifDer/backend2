"""
Base HTML Generator Class
Provides common functionality for HTML report generation
"""

import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseHTMLGenerator(ABC):
    """Base class for HTML report generators"""
    
    def __init__(self):
        self.output_dir = Path("static/pharmacy_report")
        self.css_styles = self._get_base_css()
    
    def create_directory_structure(self, city_name: str, report_type: str, scenario: str = None) -> Dict[str, Path]:
        """Create the standard directory structure for reports"""
        city_name_clean = city_name.lower().replace(" ", "_")
        
        # Include scenario in directory name if provided
        if scenario:
            report_dir = self.output_dir / f"{city_name_clean}_{report_type}_{scenario}"
        else:
            report_dir = self.output_dir / f"{city_name_clean}_{report_type}"
            
        maps_dir = report_dir / "maps"
        images_dir = report_dir / "images"
        charts_dir = report_dir / "charts"
        
        # Create directories
        report_dir.mkdir(parents=True, exist_ok=True)
        maps_dir.mkdir(exist_ok=True)
        images_dir.mkdir(exist_ok=True)
        charts_dir.mkdir(exist_ok=True)
        
        return {
            'report_dir': report_dir,
            'maps_dir': maps_dir,
            'images_dir': images_dir,
            'charts_dir': charts_dir,
            'index_path': report_dir / "index.html"
        }
    
    def _get_base_css(self) -> str:
        """Get the base CSS styles for all reports"""
        return """
        /* Reset and Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        /* Report Container */
        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            min-height: 100vh;
        }
        
        /* Page Layout */
        .page {
            padding: 40px;
            page-break-after: always;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .page:last-child {
            page-break-after: avoid;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        h1 {
            font-size: 2.5rem;
            color: #1a5f7a;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        h2 {
            font-size: 2rem;
            color: #2c5aa0;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
        }
        
        h3 {
            font-size: 1.5rem;
            color: #34495e;
            margin-bottom: 1rem;
        }
        
        /* Hero Section */
        .hero-section {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 40px;
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            opacity: 0.9;
            margin-bottom: 1rem;
        }
        
        .hero-timestamp {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        /* Executive Summary */
        .executive-summary {
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            border-left: 5px solid #3498db;
            margin-bottom: 40px;
        }
        
        .executive-summary p {
            font-size: 1.1rem;
            line-height: 1.8;
            color: #555;
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        /* Top Recommendation */
        .top-recommendation {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
            border: 2px solid #f39c12;
        }
        
        .top-recommendation h3 {
            color: #e67e22;
            font-size: 1.8rem;
            margin-bottom: 1rem;
        }
        
        /* Footer */
        .report-footer {
            background-color: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            margin-top: 40px;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .page {
                padding: 20px;
            }
            
            .hero-title {
                font-size: 2rem;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Print Styles */
        @media print {
            body {
                background-color: white;
            }
            
            .report-container {
                box-shadow: none;
                max-width: none;
            }
            
            .page {
                page-break-after: always;
            }
        }
        """
    
    def generate_html_document(self, title: str, content: str) -> str:
        """Generate the complete HTML document with head and body"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self.css_styles}
    </style>
</head>
<body>
    <div class="report-container">
        {content}
    </div>
</body>
</html>"""
    
    def write_html_file(self, file_path: Path, content: str) -> None:
        """Write HTML content to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate the HTML report - to be implemented by subclasses"""
        pass

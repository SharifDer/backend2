"""
Pharmacy Report Generator
Main generator for pharmacy HTML reports using modular components
"""

from typing import Dict, Any
from pathlib import Path
from .base_generator import BaseHTMLGenerator
from .components import HTMLComponents
from .property_analyzer import PropertyAnalyzer
from .css_styles import get_pharmacy_report_css
from .html_sections import generate_executive_summary_section, generate_methodology_and_analysis_section, generate_visual_analysis_section


class PharmacyReportGenerator(BaseHTMLGenerator):
    """Generates comprehensive pharmacy HTML reports"""
    
    def __init__(self):
        super().__init__()
        self.components = HTMLComponents()
        self.property_analyzer = PropertyAnalyzer()
        self.css_styles += self.property_analyzer.css_styles

    
    def _detect_scenario(self, report_data) -> str:
        """Detect the scenario based on request data"""
        if report_data is None:
            return "no_custom_no_current"
        
        has_current_location = report_data.current_location is not None
        has_custom_locations = report_data.custom_locations is not None and len(report_data.custom_locations) > 0
        
        if has_current_location and has_custom_locations:
            return "custom_and_current"
        elif has_current_location and not has_custom_locations:
            return "current_location_only"
        elif not has_current_location and has_custom_locations:
            return "custom_only"
        else:
            return "no_custom_no_current"
    
    
    def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate the complete pharmacy HTML report"""
        report_data = data.get('user_request')
        processed_report_data = data.get('analysis_results', {})
        
        
        city_name = report_data.city_name if report_data else "Unknown City"
        base_dir = Path("static/pharmacy_report")
        base_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = base_dir / "index.html"
        
        
        
        
        rankings = processed_report_data.get("rankings", [])
        detailed_analysis = processed_report_data.get("detailed_analysis", [])
        
        if not rankings:
            raise ValueError("No ranking data available for report generation")
        
        if not detailed_analysis:
            raise ValueError("No detailed analysis data available for report generation")
        
        visual_analysis = processed_report_data.get('visual_analysis', {})
        
        charts_data = visual_analysis.get('charts', [])
        interactive_maps_data = visual_analysis.get('interactive_maps', [])
        
        generated_charts = []
        for chart in charts_data:
            chart_url = chart.get('url', '')
            if chart_url:
                if 'static/pharmacy_report/' in chart_url:
                    relative_path = chart_url.split('static/pharmacy_report/')[-1]
                    generated_charts.append(relative_path)
        
        generated_maps = []
        for interactive_map in interactive_maps_data:
            map_url = interactive_map.get('url', '')
            if map_url:
                if 'static/pharmacy_report/' in map_url:
                    relative_path = map_url.split('static/pharmacy_report/')[-1]
                    generated_maps.append(relative_path)
        html_content = self._generate_complete__html_report(
            report_data=report_data,
            processed_report_data=processed_report_data,
            generated_maps=generated_maps,
            generated_charts=generated_charts
        )
        
        self.write_html_file(index_path, html_content)
        
        return str(index_path.absolute())
    
    def _generate_complete__html_report(self, report_data, processed_report_data, generated_maps, generated_charts):
        """Generate the HTML report"""
        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">

            <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Riyadh Pharmacy Site Analysis Report</title>
            <style>
                {get_pharmacy_report_css()}
            </style>
            </head>
            <body>
                <div class="report-container">
                    {generate_executive_summary_section(report_data, processed_report_data)}
                    {generate_methodology_and_analysis_section(report_data, processed_report_data)}
                    {generate_visual_analysis_section(report_data, processed_report_data, generated_maps, generated_charts, processed_report_data.get('key_investment_insights', []))}
                </div>
            </body>
            </html>"""
        return html_content
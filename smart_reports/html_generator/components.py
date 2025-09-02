"""
HTML Components Module
Contains reusable HTML components for report generation
"""

from typing import Dict, Any, List


class HTMLComponents:
    """Reusable HTML components for report generation"""
    
    @staticmethod
    def hero_section(title: str, subtitle: str, timestamp: str = "") -> str:
        """Generate hero section HTML"""
        return f"""
            <div class="hero-section">
                <h1 class="hero-title">{title}</h1>
                <p class="hero-subtitle">{subtitle}</p>
                {f'<p class="hero-timestamp">Generated on: {timestamp}</p>' if timestamp else ''}
            </div>"""
    
    @staticmethod
    def executive_summary(content: str) -> str:
        """Generate executive summary HTML"""
        return f"""
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <p>{content}</p>
            </div>"""
    
    @staticmethod
    def metrics_grid(metrics: List[Dict[str, Any]]) -> str:
        """Generate metrics grid HTML"""
        metrics_html = ""
        for metric in metrics:
            metrics_html += f"""
                <div class="metric-card">
                    <div class="metric-value">{metric['value']}</div>
                    <div class="metric-label">{metric['label']}</div>
                </div>"""
        
        return f"""
            <div class="metrics-grid">
                {metrics_html}
            </div>"""
    
    @staticmethod
    def top_recommendation(data: Dict[str, Any]) -> str:
        """Generate top recommendation HTML"""
        return f"""
            <div class="top-recommendation">
                <h3>🏆 Top Recommendation</h3>
                <div class="property-details">
                    <div class="property-info">
                        <p><strong>Property:</strong> {data.get('property_name', 'N/A')}</p>
                        <p><strong>Score:</strong> {data.get('score', 0):.1f}/100</p>
                        <p><strong>Price:</strong> {data.get('price', 0):,.0f} SAR</p>
                    </div>
                    <div class="performance-metrics">
                        <p><strong>Traffic Analysis:</strong> {data.get('traffic_score', 0):.1f}/25</p>
                        <p><strong>Demographics:</strong> {data.get('demographics_score', 0):.1f}/30</p>
                        <p><strong>Healthcare:</strong> {data.get('healthcare_score', 0):.1f}/20</p>
                        <p><strong>Competition:</strong> {data.get('competition_score', 0):.1f}/15</p>
                        <p><strong>Complementary:</strong> {data.get('complementary_score', 0):.1f}/10</p>
                    </div>
                </div>
            </div>"""
    
    @staticmethod
    def rankings_table(rankings: List[Dict[str, Any]], max_rows: int = 20) -> str:
        """Generate rankings table HTML"""
        table_rows = ""
        for i, ranking in enumerate(rankings[:max_rows], 1):
            rank_class = "top-3" if i <= 3 else ""
            table_rows += f"""
                        <tr>
                            <td><span class="rank-badge {rank_class}">#{i}</span></td>
                            <td>{ranking.get('property_name', 'N/A')}</td>
                            <td>{ranking.get('price', 0):,.0f}</td>
                            <td><strong>{ranking.get('final_score', 0):.1f}</strong></td>
                            <td>{ranking.get('traffic_score', 0):.1f}</td>
                            <td>{ranking.get('demographics_score', 0):.1f}</td>
                            <td>{ranking.get('healthcare_score', 0):.1f}</td>
                            <td>{ranking.get('competition_score', 0):.1f}</td>
                            <td>{ranking.get('complementary_score', 0):.1f}</td>
                            <td><a href="{ranking.get('google_maps_url', '#')}" target="_blank">📍 View</a></td>
                        </tr>"""
        
        return f"""
            <div class="rankings-section">
                <h2>Top Performing Locations</h2>
                <table class="rankings-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Site Identifier</th>
                            <th>Price (SAR)</th>
                            <th>Final Score</th>
                            <th>Traffic</th>
                            <th>Demographics</th>
                            <th>Healthcare</th>
                            <th>Competition</th>
                            <th>Complementary</th>
                            <th>Location</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>"""
    
    @staticmethod
    def methodology_section() -> str:
        """Generate methodology section HTML"""
        return """
            <div class="methodology-section">
                <h2>Analysis Methodology</h2>
                <p>
                    Our comprehensive approach integrates multiple data sources and applies a weighted scoring system 
                    to evaluate pharmacy locations systematically. This methodology ensures objective, data-driven 
                    recommendations based on quantifiable metrics and market intelligence.
                </p>
                
                <div class="scoring-criteria">
                    <div class="criterion-card">
                        <span class="criterion-weight">25% Weight</span>
                        <h4>Traffic Analysis</h4>
                        <p>Evaluates vehicular and pedestrian traffic flow, accessibility, and transportation infrastructure.</p>
                    </div>
                    <div class="criterion-card">
                        <span class="criterion-weight">30% Weight</span>
                        <h4>Demographics Scoring</h4>
                        <p>Analyzes population density, age distribution, income levels, and household characteristics.</p>
                    </div>
                    <div class="criterion-card">
                        <span class="criterion-weight">20% Weight</span>
                        <h4>Healthcare Ecosystem</h4>
                        <p>Assesses proximity to hospitals, clinics, and healthcare facilities for referral potential.</p>
                    </div>
                    <div class="criterion-card">
                        <span class="criterion-weight">15% Weight</span>
                        <h4>Competition Analysis</h4>
                        <p>Evaluates existing pharmacy density and competitive landscape within the target area.</p>
                    </div>
                    <div class="criterion-card">
                        <span class="criterion-weight">10% Weight</span>
                        <h4>Complementary Businesses</h4>
                        <p>Analyzes nearby retail, services, and amenities that support pharmacy business.</p>
                    </div>
                </div>
                
                <div class="top-recommendation" style="margin-top: 30px;">
                    <h3>Final Score Calculation</h3>
                    <p><strong>Formula:</strong> (Traffic × 0.25) + (Demographics × 0.30) + (Healthcare × 0.20) + (Competition × 0.15) + (Complementary × 0.10)</p>
                    <p><strong>Score Range:</strong> 0-100 points</p>
                    <p><strong>Performance Thresholds:</strong></p>
                    <ul>
                        <li>90-100: Exceptional opportunity</li>
                        <li>80-89: High potential</li>
                        <li>70-79: Good opportunity</li>
                        <li>60-69: Moderate potential</li>
                        <li>Below 60: Limited opportunity</li>
                    </ul>
                </div>
            </div>"""
    
    @staticmethod
    def report_footer(data: Dict[str, Any]) -> str:
        """Generate report footer HTML"""
        return f"""
            <div class="report-footer">
                <h3>Report Generation Methodology</h3>
                <p>This report was generated using advanced location intelligence algorithms and comprehensive data analysis.</p>
                <p>Analysis scope: {data.get('total_sites_evaluated', 0)} locations across {data.get('city_name', 'N/A')}, {data.get('country_name', 'N/A')}</p>
                <p>Technical approach: Multi-criteria scoring with weighted evaluation metrics</p>
                <p>Data sources: Traffic analysis, demographic profiling, healthcare mapping, competitive analysis</p>
            </div>"""

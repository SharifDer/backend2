"""
CSS Styles Module for HTML Report Generation
Contains all CSS styles used in pharmacy reports
"""

PHARMACY_REPORT_CSS = """
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap");

* {
margin: 0;
padding: 0;
box-sizing: border-box;
}

body {
font-family: "Inter", sans-serif;
line-height: 1.6;
color: #333;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
min-height: 100vh;
}

.report-container {
margin: 0 auto;
max-width: 1400px;
background: white;
box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
border-radius: 20px;
overflow: hidden;
}

.page {
padding: 60px;
min-height: 100vh;
page-break-after: always;
}

.page:last-child {
page-break-after: avoid;
}

.header {
background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
color: white;
padding: 40px 60px;
text-align: center;
margin: -60px -60px 40px -60px;
}

.header h1 {
font-size: 2.5em;
font-weight: 700;
margin-bottom: 10px;
text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.header .subtitle {
font-size: 1.2em;
font-weight: 300;
opacity: 0.9;
}

.hero {
background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
color: white;
padding: 40px 60px;
text-align: center;
margin: -60px -60px 40px -60px;
}

.hero h1 {
font-size: 2.5em;
font-weight: 700;
margin-bottom: 10px;
text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.hero .muted {
font-size: 1.2em;
font-weight: 300;
opacity: 0.9;
}

.executive-summary {
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 30px;
border-radius: 15px;
margin: 30px 0;
}

.top-recommendation {
background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
color: white;
padding: 25px;
border-radius: 15px;
margin: 20px 0;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.score-display {
font-size: 3em;
font-weight: 700;
text-align: center;
margin: 20px 0;
text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.metrics-grid {
display: grid;
grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
gap: 20px;
margin: 30px 0;
}

.metric-card {
background: white;
padding: 20px;
border-radius: 15px;
box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
text-align: center;
border-left: 5px solid #3498db;
}

.metric-value {
font-size: 2em;
font-weight: 700;
color: #2c3e50;
}

.metric-label {
color: #7f8c8d;
font-weight: 500;
margin-top: 5px;
}

.rankings-table {
width: 100%;
border-collapse: collapse;
margin: 20px 0;
background: white;
border-radius: 15px;
overflow: hidden;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.rankings-table th {
background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
color: white;
padding: 15px;
text-align: left;
font-weight: 600;
}

.rankings-table td {
padding: 15px;
border-bottom: 1px solid #ecf0f1;
}

.rankings-table tr:hover {
background: #f8f9fa;
}

.rank-badge {
background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
color: white;
padding: 5px 10px;
border-radius: 20px;
font-weight: 600;
font-size: 0.9em;
}

.rank-badge.top3 {
background: linear-gradient(135deg, #ffd700 0%, #ffa500 100%);
color: #2c3e50;
}

.section-title {
font-size: 2em;
font-weight: 600;
margin: 40px 0 20px 0;
color: #2c3e50;
border-bottom: 3px solid #3498db;
padding-bottom: 10px;
}

h2 {
font-size: 2em;
font-weight: 600;
margin: 40px 0 20px 0;
border-bottom: 3px solid #3498db;
padding-bottom: 10px;
}

h3 {
font-weight: 600;
margin: 30px 0 15px 0;
}

.property-card {
background: white;
padding: 30px;
border-radius: 15px;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
margin: 30px 0;
border-left: 5px solid #3498db;
}

.property-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 20px;
padding-bottom: 15px;
border-bottom: 2px solid #ecf0f1;
}

.property-title {
font-size: 1.2em;
font-weight: 600;
color: #2c3e50;
flex: 1;
}

.score-badge {
background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
color: white;
padding: 8px 15px;
border-radius: 20px;
font-weight: 600;
font-size: 1.1em;
}

.score-breakdown {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 15px;
margin-top: 15px;
}

.score-item {
text-align: center;
padding: 10px;
background: #f8f9fa;
border-radius: 10px;
}

.score-item .value {
font-size: 1.5em;
font-weight: 700;
color: #2c3e50;
}

.score-item .label {
font-size: 0.9em;
color: #7f8c8d;
margin-top: 5px;
}

.map-container {
margin-top: 30px;
text-align: center;
}

.map-image {
max-width: 100%;
height: auto;
border-radius: 10px;
box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
}

.methodology {
background: #f8f9fa;
padding: 30px;
border-radius: 15px;
margin: 30px 0;
}

.page-break {
page-break-before: always;
}

.insights {
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 25px;
border-radius: 15px;
margin: 20px 0;
}

.footer {
text-align: center;
color: #7f8c8d;
font-size: 0.9em;
margin-top: 40px;
padding: 20px;
border-top: 1px solid #ecf0f1;
}
"""


def get_pharmacy_report_css() -> str:
    """
    Get the complete CSS styles for pharmacy reports
    
    Returns:
        str: Complete CSS styles as a string
    """
    return PHARMACY_REPORT_CSS

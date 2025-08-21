import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any

def create_scatter_plots_html(results: List[Dict[str, Any]]) -> str:
    """Generate HTML with Chart.js scatter plots for analysis results"""
    
    # Convert results to DataFrame for easier processing
    df = pd.DataFrame([{
        'Property_ID': f'Property {r["rank"]}',
        'Final_Score': r['final_score'],
        'Traffic_Score': r['traffic_score'],
        'Business_Score': r['business_score'],
        'Demographics_Score': r['demographics_score'],
        'Competition_Score': r['competition_score'],
        'Price': r['price'],
        'Business_Count': r['business_count'],
        'Cafe_Count': r['cafe_count'],
        'Age_Deviation': abs(r['age_difference']),
        'Traffic_Speed': r['avg_road_speed'],
        'Income': r['income'],
        'Rank': r['rank']
    } for r in results])
    
    charts_html = f"""
    <div style="width: 100%; margin: 20px 0;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
            
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Price vs Final Score</h4>
                <canvas id="priceScoreChart" width="400" height="300"></canvas>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Business Count vs Competition</h4>
                <canvas id="businessCompetitionChart" width="400" height="300"></canvas>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Traffic Speed vs Performance</h4>
                <canvas id="trafficChart" width="400" height="300"></canvas>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h4 style="text-align: center; margin-bottom: 15px; color: #2C3E50;">Top 10 Score Breakdown</h4>
                <canvas id="scoreBreakdownChart" width="400" height="300"></canvas>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx1 = document.getElementById('priceScoreChart').getContext('2d');
        new Chart(ctx1, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Properties',
                    data: {json.dumps([{"x": row['Price'], "y": row['Final_Score']} for _, row in df.iterrows()])},
                    backgroundColor: function(context) {{
                        const value = context.parsed.y;
                        if (value >= 80) return 'rgba(76, 175, 80, 0.8)';
                        else if (value >= 60) return 'rgba(255, 152, 0, 0.8)';
                        else return 'rgba(244, 67, 54, 0.8)';
                    }},
                    borderColor: function(context) {{
                        const value = context.parsed.y;
                        if (value >= 80) return 'rgba(76, 175, 80, 1)';
                        else if (value >= 60) return 'rgba(255, 152, 0, 1)';
                        else return 'rgba(244, 67, 54, 1)';
                    }},
                    pointRadius: 6,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Price: ' + context.parsed.x.toLocaleString() + ' SAR, Score: ' + context.parsed.y.toFixed(1);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Price (SAR)' }} }},
                    y: {{ title: {{ display: true, text: 'Final Score' }}, min: 0, max: 100 }}
                }}
            }}
        }});
        
        const ctx2 = document.getElementById('businessCompetitionChart').getContext('2d');
        new Chart(ctx2, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Properties',
                    data: {json.dumps([{"x": row['Business_Count'], "y": row['Cafe_Count']} for _, row in df.iterrows()])},
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    pointRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Businesses: ' + context.parsed.x + ', Competitors: ' + context.parsed.y;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Number of Businesses' }} }},
                    y: {{ title: {{ display: true, text: 'Number of Competitors' }} }}
                }}
            }}
        }});
        
        const ctx3 = document.getElementById('trafficChart').getContext('2d');
        new Chart(ctx3, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Properties',
                    data: {json.dumps([{"x": row['Traffic_Speed'], "y": row['Traffic_Score']} for _, row in df.iterrows()])},
                    backgroundColor: 'rgba(155, 89, 182, 0.6)',
                    borderColor: 'rgba(155, 89, 182, 1)',
                    pointRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Speed: ' + context.parsed.x.toFixed(1) + ' km/h, Score: ' + context.parsed.y.toFixed(1);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Traffic Speed (km/h)' }} }},
                    y: {{ title: {{ display: true, text: 'Traffic Score' }}, min: 0, max: 100 }}
                }}
            }}
        }});
        
        const ctx4 = document.getElementById('scoreBreakdownChart').getContext('2d');
        new Chart(ctx4, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([f'Property {i+1}' for i in range(min(10, len(df)))])},
                datasets: [{{
                    label: 'Traffic',
                    data: {df.head(10)['Traffic_Score'].tolist()},
                    backgroundColor: 'rgba(52, 152, 219, 0.8)'
                }}, {{
                    label: 'Business',
                    data: {df.head(10)['Business_Score'].tolist()},
                    backgroundColor: 'rgba(46, 204, 113, 0.8)'
                }}, {{
                    label: 'Demographics',
                    data: {df.head(10)['Demographics_Score'].tolist()},
                    backgroundColor: 'rgba(155, 89, 182, 0.8)'
                }}, {{
                    label: 'Competition',
                    data: {df.head(10)['Competition_Score'].tolist()},
                    backgroundColor: 'rgba(241, 196, 15, 0.8)'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'top' }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false
                    }}
                }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Top 10 Properties' }} }},
                    y: {{ title: {{ display: true, text: 'Score' }}, min: 0, max: 100 }}
                }}
            }}
        }});
    </script>
    """
    
    return charts_html

def create_score_distribution_chart(results: List[Dict[str, Any]]) -> str:
    """Create histogram of score distribution"""
    scores = [r['final_score'] for r in results]
    
    return f"""
    <div class="chart-container">
        <h3 style="color: #2C3E50; margin-bottom: 15px;">📊 Score Distribution</h3>
        <canvas id="scoreDistributionChart"></canvas>
        <p style="margin-top: 15px; color: #7F8C8D; text-align: center;">
            Distribution of final scores across all analyzed properties
        </p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctxDist = document.getElementById('scoreDistributionChart').getContext('2d');
        const scores = {json.dumps(scores)};
        
        // Create histogram bins
        const bins = [];
        for (let i = 0; i <= 100; i += 10) {{
            bins.push(i);
        }}
        
        const histogram = new Array(bins.length - 1).fill(0);
        scores.forEach(score => {{
            const binIndex = Math.min(Math.floor(score / 10), histogram.length - 1);
            histogram[binIndex]++;
        }});
        
        new Chart(ctxDist, {{
            type: 'bar',
            data: {{
                labels: bins.slice(0, -1).map((bin, i) => `${{bin}}-${{bins[i+1]}}`),
                datasets: [{{
                    label: 'Number of Properties',
                    data: histogram,
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Score Range' }} }},
                    y: {{ title: {{ display: true, text: 'Number of Properties' }} }}
                }}
            }}
        }});
    </script>
    """
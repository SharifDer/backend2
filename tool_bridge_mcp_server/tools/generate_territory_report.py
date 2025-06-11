# --- START OF FILE generate_territory_report.py ---

import logging
import os
import sys
import numpy as np
from datetime import datetime

# Add the grandparent directory to sys.path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Import aiohttp if not already there
import aiohttp
from config_factory import CONF
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Import your existing Pydantic models from the FastAPI backend
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from tool_bridge_mcp_server.context import get_app_context

logger = logging.getLogger(__name__)

# --- Configuration is now a simple module-level constant ---
FASTAPI_BASE_URL = "http://localhost:8000"


def register_territory_report_tools(mcp: FastMCP):
    """Register territory report generation tool by defining it within this function's scope."""

    @mcp.tool(
        name="generate_territory_report",
        description="""Generate comprehensive business intelligence reports from territory optimization analysis.
        
        📊 Report Types Available:
        - executive_summary: High-level strategic insights and recommendations
        - metadata_analysis: Detailed analysis of territory metadata
        - visualization_summary: Summary of generated visualizations
        - optimization_insights: Strategic optimization recommendations

        💼 Business Intelligence Features:
        - Territory balance and market analysis
        - Customer distribution assessment  
        - Visualization catalog and insights
        - Strategic recommendations based on optimization results

        Args:
            data_handle: Territory analysis data from optimize_sales_territories
            report_type: Type of report to generate
            include_visualizations: Include links to generated maps and visualizations
        
        Returns:
            Formatted business intelligence report with actionable insights
        """,
    )
    async def generate_territory_report(
        data_handle: str = Field(
            description="Data handle from optimize_sales_territories containing territory analysis"
        ),
        report_type: str = Field(
            default="executive_summary",
            description="Report type: 'executive_summary', 'metadata_analysis', 'visualization_summary', or 'optimization_insights'"
        ),
        include_visualizations: bool = Field(
            default=True,
            description="Include links to generated maps and visualizations"
        ),
    ) -> str:
        """Generate comprehensive business intelligence reports from territory optimization data."""

        try:
            app_ctx = get_app_context(mcp)
            session_manager = app_ctx.session_manager
            handle_manager = app_ctx.handle_manager

            # Get the valid user_id and token for this session
            user_id, id_token = await session_manager.get_valid_id_token()

            if not id_token or not user_id:
                return "❌ Error: You are not logged in. Please use the `user_login` tool first."

            # Get current session
            session = await session_manager.get_current_session()
            if not session:
                return "❌ Error: No active session found. Please fetch data first."

            # Retrieve territory analysis data
            try:
                territory_data = await handle_manager.read_data(data_handle)
                if not territory_data:
                    return f"❌ Error: No data found for handle `{data_handle}`. Please run optimize_sales_territories first."
            except Exception as e:
                return f"❌ Error retrieving data: {str(e)}"

            # Check if this is the expected territory optimization data
            if not territory_data.get("success"):
                return "❌ Error: Invalid territory data format. Please run territory optimization again."

            # Extract data components
            metadata = territory_data.get("metadata", {})
            plots = territory_data.get("plots", {})
            request_id = territory_data.get("request_id", "unknown")

            if not metadata:
                return "❌ Error: No metadata found in territory data. Please run territory optimization again."

            # Generate report based on type
            if report_type == "executive_summary":
                report = generate_executive_summary_real(metadata, plots, request_id)
            elif report_type == "metadata_analysis":
                report = generate_metadata_analysis(metadata, plots, request_id)
            elif report_type == "visualization_summary":
                report = generate_visualization_summary(plots, metadata, request_id)
            elif report_type == "optimization_insights":
                report = generate_optimization_insights(metadata, plots, request_id)
            else:
                return f"❌ Error: Unknown report type '{report_type}'. Available types: executive_summary, metadata_analysis, visualization_summary, optimization_insights"

            # Add visualizations if requested
            if include_visualizations and plots:
                viz_section = "\n\n🗺️ **Generated Visualizations**:\n"
                for plot_name, plot_url in plots.items():
                    viz_section += f"• **{plot_name.replace('_', ' ').replace('-', ' ').title()}**: `{plot_url}`\n"
                report += viz_section

            # Add metadata footer
            analysis_date = metadata.get('analysis_date', 'N/A')
            city_name = metadata.get('city_name', 'N/A')
            report += f"\n\n---\n📋 **Analysis Details**: Generated from `{data_handle}` | City: {city_name} | Date: {analysis_date} | Request ID: {request_id}"

            return report

        except Exception as e:
            logger.exception("Critical error in generate_territory_report")
            return f"❌ Error generating report: {str(e)}"


def generate_executive_summary_real(metadata, plots, request_id):
    """Generate executive summary based on actual data structure"""
    
    total_customers = metadata.get("total_customers", 0)
    clusters_created = metadata.get("clusters_created", 0)
    target_per_territory = metadata.get("target_customers_per_territory", 0)
    city_name = metadata.get("city_name", "Unknown")
    country_name = metadata.get("country_name", "Unknown")
    distance_limit = metadata.get("distance_limit_km", 0)
    business_type = metadata.get("business_type", "Unknown")
    analysis_date = metadata.get("analysis_date", "Unknown")
    
    # Calculate some basic metrics
    avg_customers_per_territory = total_customers / max(clusters_created, 1)
    
    report = f"""# 📊 Sales Territory Optimization - Executive Summary

## 🎯 Strategic Overview
**Location**: {city_name}, {country_name}  
**Analysis Date**: {analysis_date}  
**Business Focus**: {business_type.title()}  
**Request ID**: {request_id}

## 📈 Key Performance Indicators

### Market Coverage Analysis
- **Total Market Potential**: {total_customers:,} customers
- **Territories Created**: {clusters_created}
- **Target Customers per Territory**: {target_per_territory:,}
- **Actual Average per Territory**: {avg_customers_per_territory:,.0f}
- **Service Range**: {distance_limit}km maximum travel distance

### Territory Balance Assessment
- **Territory Efficiency**: {(avg_customers_per_territory / max(target_per_territory, 1) * 100):.1f}% of target
- **Market Distribution**: {'Well-Balanced' if abs(avg_customers_per_territory - target_per_territory) / target_per_territory < 0.1 else 'Needs Adjustment'}
- **Coverage Status**: {'Optimal' if clusters_created > 0 else 'Failed'}

## 🏆 Territory Performance Overview

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Territories** | {clusters_created} | {clusters_created} | ✅ |
| **Customers/Territory** | {target_per_territory:,} | {avg_customers_per_territory:,.0f} | {'✅' if abs(avg_customers_per_territory - target_per_territory) / target_per_territory < 0.1 else '⚠️'} |
| **Total Market** | - | {total_customers:,} | 📊 |
| **Service Range** | {distance_limit}km | {distance_limit}km | 🎯 |

## 🔍 Strategic Insights

### Market Size Analysis
"""

    # Add market size insights
    if total_customers > 1000000:
        report += "• **Market Classification**: 🔥 Large metropolitan market with significant opportunity\n"
    elif total_customers > 100000:
        report += "• **Market Classification**: ⭐ Medium-sized market with good potential\n"
    else:
        report += "• **Market Classification**: 📈 Smaller market requiring focused strategy\n"

    # Territory balance insights
    balance_ratio = avg_customers_per_territory / max(target_per_territory, 1)
    if balance_ratio > 1.1:
        report += "• **Territory Balance**: ⚠️ Territories are over-capacity - consider adding more territories\n"
    elif balance_ratio < 0.9:
        report += "• **Territory Balance**: 📈 Territories are under-capacity - consider consolidation\n"
    else:
        report += "• **Territory Balance**: ✅ Well-balanced territory distribution\n"

    # Distance analysis
    if distance_limit <= 2:
        report += "• **Service Coverage**: 🏙️ Urban-focused strategy with tight service areas\n"
    elif distance_limit <= 5:
        report += "• **Service Coverage**: 🌆 Suburban strategy with moderate service areas\n"
    else:
        report += "• **Service Coverage**: 🌄 Regional strategy with extended service areas\n"

    # Business type insights
    business_insights = {
        "supermarket": "High-frequency visits expected, focus on convenience and accessibility",
        "restaurant": "Experience-driven visits, consider demographic preferences",
        "retail": "Shopping behavior varies, analyze customer journey patterns",
        "service": "Appointment-based visits, optimize for efficiency"
    }
    
    insight = business_insights.get(business_type.lower(), "Analyze customer behavior patterns for this business type")
    report += f"• **Business Strategy**: 💼 {insight}\n"

    # Add recommendations
    report += "\n## 💡 Strategic Recommendations\n\n"
    
    recommendations = []
    
    if balance_ratio > 1.2:
        recommendations.append("Consider increasing the number of territories to reduce workload per territory")
    elif balance_ratio < 0.8:
        recommendations.append("Consider reducing territories or expanding service areas to optimize resource utilization")
    
    if distance_limit > 5 and business_type.lower() in ['supermarket', 'restaurant']:
        recommendations.append("Large service areas may reduce customer satisfaction - consider smaller, more frequent service zones")
    
    if total_customers < 50000 and clusters_created > 3:
        recommendations.append("Small market size with many territories may lead to inefficiency - consider consolidation")
    
    if not recommendations:
        recommendations.append("Territory optimization appears well-balanced - monitor performance and adjust as market conditions change")
    
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"

    return report


def generate_metadata_analysis(metadata, plots, request_id):
    """Generate detailed metadata analysis"""
    
    report = f"""# 📊 Territory Metadata Analysis

## 📋 Complete Metadata Overview

**Request ID**: {request_id}
**Analysis Timestamp**: {metadata.get('analysis_date', 'N/A')}

### Geographic Parameters
- **City**: {metadata.get('city_name', 'N/A')}
- **Country**: {metadata.get('country_name', 'N/A')}
- **Service Radius**: {metadata.get('distance_limit_km', 0)}km

### Business Configuration
- **Target Business Type**: {metadata.get('business_type', 'N/A').title()}
- **Market Analysis Focus**: Customer accessibility and territory balance

### Optimization Results
- **Total Addressable Market**: {metadata.get('total_customers', 0):,} potential customers
- **Territories Generated**: {metadata.get('clusters_created', 0)}
- **Target Load per Territory**: {metadata.get('target_customers_per_territory', 0):,} customers
- **Optimization Status**: {'✅ Successful' if metadata.get('clusters_created', 0) > 0 else '❌ Failed'}

## 📈 Statistical Analysis

### Market Distribution Metrics
"""
    
    total_customers = metadata.get("total_customers", 0)
    clusters_created = metadata.get("clusters_created", 0)
    target_per_territory = metadata.get("target_customers_per_territory", 0)
    
    if clusters_created > 0:
        actual_avg = total_customers / clusters_created
        variance = abs(actual_avg - target_per_territory) / target_per_territory * 100
        
        report += f"- **Average Customers per Territory**: {actual_avg:,.0f}\n"
        report += f"- **Target vs Actual Variance**: {variance:.1f}%\n"
        report += f"- **Load Distribution**: {'Excellent' if variance < 5 else 'Good' if variance < 15 else 'Needs Improvement'}\n"
        report += f"- **Territory Efficiency Score**: {(100 - variance):.1f}/100\n"
    else:
        report += "- **Status**: ❌ Territory generation failed - check input parameters\n"

    # Analysis insights
    report += f"""

### Configuration Assessment

**Distance Limit Analysis**:
"""
    
    distance_limit = metadata.get('distance_limit_km', 0)
    if distance_limit <= 1:
        report += "- 🏙️ Very tight service area - suitable for dense urban markets\n"
    elif distance_limit <= 3:
        report += "- 🌆 Standard urban service area - good for city business districts\n"
    elif distance_limit <= 7:
        report += "- 🌄 Extended service area - suitable for suburban/regional markets\n"
    else:
        report += "- 🌍 Very large service area - may impact service quality\n"

    business_type = metadata.get('business_type', '').lower()
    report += f"\n**Business Type Optimization**:\n"
    
    if 'supermarket' in business_type:
        report += "- 🛒 Retail optimization focused on convenience and frequency\n"
        report += "- 📍 Accessibility is critical for repeat customer visits\n"
    elif 'restaurant' in business_type:
        report += "- 🍽️ Food service optimization focused on experience and location\n"
        report += "- 🎯 Consider demographic preferences and dining patterns\n"
    else:
        report += f"- 💼 Custom business type: {business_type.title()}\n"
        report += "- 📊 Optimization parameters adapted for business model\n"

    return report


def generate_visualization_summary(plots, metadata, request_id):
    """Generate summary of available visualizations"""
    
    report = f"""# 🗺️ Territory Visualization Summary

## 📊 Generated Maps and Charts

**Request ID**: {request_id}
**Total Visualizations**: {len(plots)}
**Generation Status**: {'✅ Complete' if plots else '❌ No visualizations generated'}

"""
    
    if not plots:
        report += """
⚠️ **No visualizations were generated for this analysis.**

This may indicate:
- Data processing issues during territory optimization
- Insufficient data for visualization generation
- Configuration problems with the mapping system

**Recommendation**: Re-run the territory optimization with verified parameters.
"""
        return report

    # Categorize visualizations
    visualization_categories = {
        "cluster": "🎯 Territory Boundaries",
        "population": "👥 Population Analysis", 
        "market": "💼 Market Analysis",
        "customer": "🛒 Customer Distribution",
        "supermarket": "🏪 Facility Locations",
        "effective": "⚡ Optimization Results"
    }
    
    report += "## 🎨 Visualization Catalog\n\n"
    
    for plot_name, plot_url in plots.items():
        # Determine category
        category = "📊 General Analysis"
        for key, cat in visualization_categories.items():
            if key in plot_name.lower():
                category = cat
                break
        
        # Clean up plot name
        display_name = plot_name.replace('_', ' ').replace('-', ' ').title()
        
        report += f"### {display_name}\n"
        report += f"**Category**: {category}\n"
        report += f"**File Path**: `{plot_url}`\n"
        
        # Add description based on plot type
        if "cluster" in plot_name.lower():
            report += f"**Description**: Territory boundary visualization showing the {metadata.get('clusters_created', 'N/A')} optimized sales territories\n"
        elif "population" in plot_name.lower():
            report += f"**Description**: Population density analysis across {metadata.get('city_name', 'the target area')}\n"
        elif "customer" in plot_name.lower():
            report += f"**Description**: Distribution of {metadata.get('total_customers', 'N/A'):,} potential customers across territories\n"
        elif "supermarket" in plot_name.lower() or "facility" in plot_name.lower():
            report += f"**Description**: Location mapping of {metadata.get('business_type', 'business')} facilities in the analysis area\n"
        elif "effective" in plot_name.lower():
            report += f"**Description**: Effectiveness analysis showing optimization results and accessibility patterns\n"
        else:
            report += f"**Description**: {display_name.lower()} visualization for territory analysis\n"
        
        report += "\n"

    # Usage recommendations
    report += """## 📋 Visualization Usage Guide

### For Executive Presentations
- Use **Territory Boundaries** map to show coverage areas
- Include **Customer Distribution** to demonstrate market potential
- Show **Population Analysis** for demographic insights

### For Operational Planning
- Reference **Facility Locations** for resource allocation
- Use **Optimization Results** for performance evaluation
- Analyze **Market Analysis** for strategic decisions

### For Sales Team Training
- **Territory Boundaries** for area assignment clarity
- **Customer Distribution** for priority targeting
- **Population Analysis** for market understanding

## 🔗 Access Instructions

All visualizations are stored as static files on the server. To access:
1. Use the provided file paths in your application
2. Serve files through your web server's static file handler
3. Consider implementing access controls for sensitive market data
"""

    return report


def generate_optimization_insights(metadata, plots, request_id):
    """Generate optimization insights and recommendations"""
    
    total_customers = metadata.get("total_customers", 0)
    clusters_created = metadata.get("clusters_created", 0)
    target_per_territory = metadata.get("target_customers_per_territory", 0)
    city_name = metadata.get("city_name", "Unknown")
    distance_limit = metadata.get("distance_limit_km", 0)
    business_type = metadata.get("business_type", "Unknown")
    
    report = f"""# 🔧 Territory Optimization Insights

## 🎯 Optimization Analysis Summary

**Request ID**: {request_id}
**Optimization Date**: {metadata.get('analysis_date', 'N/A')}
**Target Market**: {city_name}
**Business Type**: {business_type.title()}

## 📊 Performance Evaluation

### Territory Balance Assessment
"""
    
    if clusters_created > 0:
        actual_avg = total_customers / clusters_created
        balance_score = min(100, max(0, 100 - (abs(actual_avg - target_per_territory) / target_per_territory * 100)))
        
        report += f"""
- **Target Load**: {target_per_territory:,} customers per territory
- **Actual Average**: {actual_avg:,.0f} customers per territory
- **Balance Score**: {balance_score:.1f}/100
- **Optimization Status**: {'🎯 Excellent' if balance_score > 90 else '✅ Good' if balance_score > 75 else '⚠️ Needs Improvement'}

### Efficiency Metrics
- **Territory Utilization**: {(actual_avg / target_per_territory * 100):.1f}%
- **Market Coverage**: {clusters_created} territories for {total_customers:,} customers
- **Workload Distribution**: {'Balanced' if balance_score > 80 else 'Unbalanced'}
"""
    else:
        report += "❌ **Optimization Failed**: No territories were created. Check input parameters.\n"

    # Strategic recommendations
    report += "\n## 💡 Strategic Optimization Recommendations\n\n"
    
    recommendations = []
    
    if clusters_created > 0:
        actual_avg = total_customers / clusters_created
        
        # Balance recommendations
        if actual_avg > target_per_territory * 1.2:
            recommendations.append({
                "priority": "🔴 HIGH",
                "action": "Increase Territory Count",
                "reason": f"Current territories are overloaded ({actual_avg:,.0f} vs {target_per_territory:,} target)",
                "implementation": f"Consider creating {int(total_customers / target_per_territory)} territories instead of {clusters_created}"
            })
        elif actual_avg < target_per_territory * 0.8:
            recommendations.append({
                "priority": "🟡 MEDIUM", 
                "action": "Reduce Territory Count",
                "reason": f"Current territories are underutilized ({actual_avg:,.0f} vs {target_per_territory:,} target)",
                "implementation": f"Consider consolidating to {int(total_customers / target_per_territory)} territories"
            })
        
        # Distance recommendations
        if distance_limit > 7 and business_type.lower() in ['supermarket', 'restaurant', 'retail']:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "action": "Reduce Service Area",
                "reason": f"{distance_limit}km may be too large for {business_type} customers",
                "implementation": "Consider reducing to 3-5km for better customer experience"
            })
        elif distance_limit < 2 and total_customers / clusters_created > 100000:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "action": "Expand Service Area",
                "reason": "Very tight service areas with high customer density",
                "implementation": "Consider expanding to 3-4km to balance workload"
            })
        
        # Market size recommendations
        if total_customers < 50000:
            recommendations.append({
                "priority": "📈 LOW",
                "action": "Market Analysis",
                "reason": "Small market size may not justify multiple territories",
                "implementation": "Consider single territory or regional approach"
            })
    else:
        recommendations.append({
            "priority": "🚨 URGENT",
            "action": "Troubleshoot Optimization",
            "reason": "Territory generation failed completely",
            "implementation": "Check data availability, parameters, and API configuration"
        })

    # Add general recommendations
    recommendations.append({
        "priority": "✅ ONGOING",
        "action": "Performance Monitoring",
        "reason": "Continuous optimization requires regular assessment",
        "implementation": "Schedule quarterly reviews of territory performance and customer feedback"
    })

    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        report += f"""
### {i}. {rec['action']} ({rec['priority']})
**Reasoning**: {rec['reason']}
**Implementation**: {rec['implementation']}
"""

    # Implementation roadmap
    report += """

## 🛠️ Implementation Roadmap

### Phase 1: Immediate Actions (0-30 days)
1. **Territory Assignment**: Deploy optimized boundaries to sales team
2. **System Updates**: Update CRM and routing systems with new territories
3. **Team Communication**: Brief sales representatives on new coverage areas
4. **Performance Baseline**: Establish current metrics for comparison

### Phase 2: Optimization Period (30-90 days)
1. **Performance Monitoring**: Track key metrics across all territories
2. **Feedback Collection**: Gather input from sales team and customers
3. **Boundary Adjustments**: Fine-tune territories based on real-world performance
4. **Process Refinement**: Optimize territory management workflows

### Phase 3: Continuous Improvement (90+ days)
1. **Regular Reviews**: Quarterly territory performance analysis
2. **Market Adaptation**: Adjust for changing market conditions
3. **Expansion Planning**: Plan for new territories as business grows
4. **Advanced Analytics**: Implement predictive territory optimization

## 📊 Success Metrics to Track

### Primary KPIs
- Sales performance by territory
- Customer satisfaction scores
- Territory balance metrics
- Sales representative workload

### Secondary Metrics
- Market penetration rates
- Customer acquisition costs
- Travel time and efficiency
- Territory revenue per square kilometer

### Monitoring Frequency
- **Daily**: Sales activity and coverage
- **Weekly**: Territory performance summaries
- **Monthly**: Customer satisfaction and balance metrics
- **Quarterly**: Comprehensive territory optimization review
"""

    return report


# --- END OF FILE generate_territory_report.py ---
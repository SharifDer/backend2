"""
Report Display Module
Handles Dash UI components for displaying reports
"""
from dash import html, dcc
import dash_bootstrap_components as dbc
import markdown
from typing import Optional, List, Dict, Any
import re

class ReportDisplay:
    """Handle report display components and formatting for Dash"""
    
    def __init__(self):
        self.markdown_extensions = ['tables', 'fenced_code', 'codehilite']
    
    def create_report_layout(self) -> html.Div:
        """
        Create the main report display layout for the left panel
        
        Returns:
            Dash HTML div containing report display components
        """
        return html.Div([
            # Report header section
            html.Div([
                html.H5("📊 Territory Analysis Report", 
                       style={'margin-bottom': '10px', 'color': '#495057'}),
                html.Div(id="report-status", 
                        children=[
                            html.Small("No report loaded", 
                                     style={'color': '#6c757d', 'font-style': 'italic'})
                        ])
            ], style={'margin-bottom': '20px', 'text-align': 'center'}),
            
            # Store for tracking interactive data availability
            dcc.Store(id="interactive-data-available", data=False),
            
            # Report content area with tabs for static and interactive content
            html.Div([
                # Tab navigation
                dbc.Tabs([
                    dbc.Tab(label="📄 Report", tab_id="static-report", active_tab_style={"font-weight": "bold"}),
                    dbc.Tab(label="📊 Interactive Maps", tab_id="interactive-plots", disabled=True, active_tab_style={"font-weight": "bold"})
                ], id="report-tabs", active_tab="static-report", style={"margin-bottom": "15px"}),
                
                # Tab content
                html.Div(
                    id="report-content",
                    children=[
                        self._create_empty_state()
                    ],
                    style={
                        'height': 'calc(100vh - 200px)',
                        'overflow-y': 'auto',
                        'padding': '20px',
                        'background-color': 'white',
                        'border': '1px solid #dee2e6',
                        'border-radius': '8px',
                        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }
                ),
                
                # Interactive plots content (initially hidden)
                html.Div(
                    id="interactive-plots-content",
                    children=[
                        self._create_interactive_plots_placeholder()
                    ],
                    style={'display': 'none'}
                )
            ])
        ], id="report-display-container")
    
    def _create_empty_state(self) -> html.Div:
        """Create empty state when no report is loaded"""
        return html.Div([
            html.Div([
                html.I(className="fas fa-file-alt", 
                      style={'font-size': '48px', 'color': '#dee2e6', 'margin-bottom': '20px'}),
                html.H6("No Report Available", 
                       style={'color': '#6c757d', 'margin-bottom': '10px'}),
                html.P("Start a conversation with the AI assistant to generate territory analysis reports. "
                      "Reports will appear here automatically when generated.",
                      style={'color': '#6c757d', 'font-style': 'italic', 'text-align': 'center'})
            ], style={
                'text-align': 'center', 
                'margin-top': '100px',
                'padding': '40px'
            })
        ])
    
    def _create_interactive_plots_placeholder(self) -> html.Div:
        """Create placeholder content for interactive plots tab"""
        return html.Div([
            html.Div([
                html.I(className="fas fa-map", 
                      style={'font-size': '48px', 'color': '#dee2e6', 'margin-bottom': '20px'}),
                html.H6("Interactive Maps Available", 
                       style={'color': '#6c757d', 'margin-bottom': '10px'}),
                html.P("Interactive territory visualization maps will be loaded here when data is available.",
                      style={'color': '#6c757d', 'font-style': 'italic', 'text-align': 'center'})
            ], style={
                'text-align': 'center', 
                'margin-top': '100px',
                'padding': '40px'
            })
        ])
    
    def create_interactive_plots_layout(self, available_variables: Dict[str, str], default_variable: str = None) -> html.Div:
        """
        Create interactive plots layout with dropdown and map components
        
        Args:
            available_variables: Dictionary mapping variable keys to display names
            default_variable: Default variable to select
            
        Returns:
            Dash HTML div containing interactive plots components
        """
        if not available_variables:
            return self._create_interactive_plots_placeholder()
        
        default_var = default_variable or list(available_variables.keys())[0]
        
        return html.Div([
            # Header section
            html.Div([
                html.H5("🗺️ Interactive Territory Visualization", 
                       style={'margin-bottom': '15px', 'color': '#495057', 'text-align': 'center'}),
                html.P("Explore your territory optimization results with interactive maps. "
                      "Select different variables to visualize population, purchasing power, and facility distribution.",
                      style={'color': '#6c757d', 'text-align': 'center', 'margin-bottom': '20px'})
            ]),
            
            # Variable selector
            html.Div([
                html.Label("Select Variable to Visualize:", 
                          style={'font-weight': 'bold', 'margin-bottom': '10px', 'display': 'block'}),
                dcc.Dropdown(
                    id='interactive-variable-dropdown',
                    options=[{'label': display_name, 'value': var_key} 
                            for var_key, display_name in available_variables.items()],
                    value=default_var,
                    clearable=False,
                    style={'width': '100%', 'margin-bottom': '20px'}
                )
            ], style={'margin-bottom': '25px'}),
            
            # Choropleth map
            html.Div([
                html.H6("Population and Economic Data by Territory", 
                       style={'margin-bottom': '15px', 'color': '#495057'}),
                dcc.Graph(
                    id='interactive-choropleth-map',
                    style={
                        'height': '500px',
                        'border': '1px solid #dee2e6',
                        'border-radius': '8px',
                        'margin-bottom': '30px'
                    }
                )
            ]),
            
            # Supermarket scatter map
            html.Div([
                html.H6("Facility Locations", 
                       style={'margin-bottom': '15px', 'color': '#495057'}),
                dcc.Graph(
                    id='interactive-scatter-map',
                    style={
                        'height': '500px',
                        'border': '1px solid #dee2e6',
                        'border-radius': '8px'
                    }
                )
            ])
        ], style={'padding': '0 10px'})
    
    def _fix_image_paths(self, content: str) -> str:
        """
        Fix image paths, resize to 500x500px, and center images for Dash static file serving
        
        Args:
            content: Raw markdown content with potentially broken image paths
            
        Returns:
            Content with fixed image paths, properly sized (500x500px), and centered images
        """
        import re
        
        # Pattern to match image tags with relative paths and add 500x500 sizing
        # Converts both HTML img tags and markdown images to properly sized HTML
        patterns = [
            # HTML img tags - add size attributes and centering styling
            (r'<img\s+src="\.\.\/static\/plots\/([^"]+)"([^>]*?)>', r'<div style="text-align: center; margin: 20px 0;"><img src="/static/plots/\1" width="500" height="500" style="object-fit: contain; display: block; margin: 0 auto;"\2></div>'),
            # Markdown image syntax - convert to HTML with size attributes and centering
            (r'!\[([^\]]*)\]\(\.\.\/static\/plots\/([^)]+)\)', r'<div style="text-align: center; margin: 20px 0;"><img src="/static/plots/\2" alt="\1" width="500" height="500" style="object-fit: contain; display: block; margin: 0 auto;"></div>'),
            # Catch any remaining absolute static/plots images and resize them with centering
            (r'<img\s+src="\/static\/plots\/([^"]+)"([^>]*?)>', r'<div style="text-align: center; margin: 20px 0;"><img src="/static/plots/\1" width="500" height="500" style="object-fit: contain; display: block; margin: 0 auto;"\2></div>'),
            # Handle markdown images with absolute paths and centering
            (r'!\[([^\]]*)\]\(\/static\/plots\/([^)]+)\)', r'<div style="text-align: center; margin: 20px 0;"><img src="/static/plots/\2" alt="\1" width="500" height="500" style="object-fit: contain; display: block; margin: 0 auto;"></div>')
        ]
        
        fixed_content = content
        for pattern, replacement in patterns:
            fixed_content = re.sub(pattern, replacement, fixed_content)
            
        return fixed_content
    
    def format_markdown_for_dash(self, content: str) -> html.Div:
        """
        Convert markdown content to Dash HTML components
        
        Args:
            content: Raw markdown content
            
        Returns:
            Dash HTML div with formatted content
        """
        if not content or not content.strip():
            return self._create_empty_state()
        
        try:
            # Fix image paths before converting markdown
            content = self._fix_image_paths(content)
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                content, 
                extensions=self.markdown_extensions,
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight'
                    }
                }
            )
            
            # Create Dash component with the HTML content
            return html.Div([
                dcc.Markdown(
                    content,
                    dangerously_allow_html=True,
                    style={
                        'font-family': 'system-ui, -apple-system, sans-serif',
                        'line-height': '1.6',
                        'color': '#333'
                    }
                )
            ], style={'padding': '10px'})
            
        except Exception as e:
            print(f"❌ Error formatting markdown: {str(e)}")
            return html.Div([
                dbc.Alert([
                    html.H6("Error Displaying Report", className="alert-heading"),
                    html.P(f"Could not format the report content: {str(e)}"),
                    html.Hr(),
                    html.P("Please try regenerating the report.", className="mb-0")
                ], color="warning")
            ])
    
    def create_report_status_indicator(self, status: str, report_info: Dict[str, Any] = None) -> html.Div:
        """
        Create status indicator for report loading/display
        
        Args:
            status: Status text ('loading', 'loaded', 'error', 'empty')
            report_info: Optional report metadata
            
        Returns:
            Dash HTML div with status information
        """
        if status == 'loading':
            return html.Div([
                dbc.Spinner(size="sm", color="primary"),
                html.Small(" Loading report...", 
                          style={'margin-left': '10px', 'color': '#007bff'})
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
        
        elif status == 'loaded' and report_info:
            return html.Div([
                html.Small("📄 ", style={'color': '#28a745'}),
                html.Small(f"Report loaded: {report_info.get('filename', 'Unknown')}", 
                          style={'color': '#28a745', 'font-weight': 'bold'}),
                html.Br(),
                html.Small(f"Generated: {report_info.get('created_time', 'Unknown')}", 
                          style={'color': '#6c757d', 'font-size': '0.8em'})
            ], style={'text-align': 'center'})
        
        elif status == 'error':
            return html.Div([
                html.Small("❌ Error loading report", 
                          style={'color': '#dc3545', 'font-weight': 'bold'})
            ], style={'text-align': 'center'})
        
        else:  # empty
            return html.Div([
                html.Small("No report loaded", 
                          style={'color': '#6c757d', 'font-style': 'italic'})
            ], style={'text-align': 'center'})
    
    def create_loading_spinner(self) -> html.Div:
        """Create loading spinner for report generation"""
        return html.Div([
            dbc.Spinner(color="primary", size="lg"),
            html.H6("Generating Report...", 
                   style={'margin-top': '20px', 'color': '#007bff'}),
            html.P("Please wait while the AI assistant generates your territory analysis report.",
                  style={'color': '#6c757d', 'text-align': 'center'})
        ], style={
            'text-align': 'center',
            'margin-top': '100px',
            'padding': '40px'
        })
    
    def format_report_preview(self, content: str, max_length: int = 200) -> str:
        """
        Create a preview of the report content
        
        Args:
            content: Full report content
            max_length: Maximum length of preview
            
        Returns:
            Truncated preview text
        """
        if not content:
            return "No content available"
        
        # Remove markdown formatting for preview
        clean_content = re.sub(r'[#*`\[\]()]', '', content)
        clean_content = re.sub(r'\n+', ' ', clean_content)
        clean_content = clean_content.strip()
        
        if len(clean_content) <= max_length:
            return clean_content
        
        return clean_content[:max_length] + "..."
    
    def create_report_metadata_card(self, metadata: Dict[str, Any]) -> dbc.Card:
        """
        Create a card displaying report metadata
        
        Args:
            metadata: Report metadata dictionary
            
        Returns:
            Dash Bootstrap Card component
        """
        return dbc.Card([
            dbc.CardBody([
                html.H6("Report Information", className="card-title"),
                html.P([
                    html.Strong("File: "), metadata.get('filename', 'Unknown'), html.Br(),
                    html.Strong("City: "), metadata.get('city', 'Unknown'), html.Br(),
                    html.Strong("Type: "), metadata.get('report_type', 'Unknown'), html.Br(),
                    html.Strong("Generated: "), str(metadata.get('created_time', 'Unknown')), html.Br(),
                    html.Strong("Size: "), f"{metadata.get('file_size', 0)} bytes"
                ], className="card-text small")
            ])
        ], style={'margin-bottom': '15px'}, size="sm")
    
    def create_error_display(self, error_message: str) -> html.Div:
        """
        Create error display component
        
        Args:
            error_message: Error message to display
            
        Returns:
            Dash HTML div with error formatting
        """
        return html.Div([
            dbc.Alert([
                html.H6("Report Error", className="alert-heading"),
                html.P(error_message),
                html.Hr(),
                html.P("Please try the following:", className="mb-2"),
                html.Ul([
                    html.Li("Check that your query includes login credentials"),
                    html.Li("Ensure you've requested a specific analysis type"),
                    html.Li("Try rephrasing your request"),
                    html.Li("Contact support if the problem persists")
                ])
            ], color="danger")
        ], style={'margin': '20px'})

# Global instance for easy import
report_display = ReportDisplay()
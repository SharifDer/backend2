import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import asyncio
from langchain_core.messages import HumanMessage

# Import our custom modules
from report_handler import report_handler
from report_display import report_display
from interactive_plots import plotter, load_and_create_plots

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

# Configure static file serving for plots
import os
from pathlib import Path

# Add static file serving for plots
static_plots_path = Path(__file__).parent.parent / "static" / "plots"
if static_plots_path.exists():
    # Tell Dash where to find static files
    app.server.static_folder = str(Path(__file__).parent.parent / "static")
    app.server.static_url_path = '/static'
    print(f"📁 Static files configured: {static_plots_path}")
else:
    print(f"⚠️ Static plots directory not found: {static_plots_path}")

# Store for conversation history
conversation_history = []

# Global MCP client instance for memory persistence - LAZY INITIALIZATION
mcp_client = None
DASH_THREAD_ID = "dash_conversation_main"

def get_or_create_client():
    """Get or create a persistent MCP client with memory - LAZY INITIALIZATION"""
    global mcp_client
    if mcp_client is None:
        print("🚀 Creating new MCP client with memory...")
        from report_agent import SimpleMCPClient
        # Create client with specific session for Dash app
        mcp_client = SimpleMCPClient(session_id="dash_session")
        print("✅ MCP client created, will connect on first use")
    return mcp_client

async def ensure_client_connected():
    """Ensure the MCP client is connected"""
    client = get_or_create_client()
    if client and not client.agent:
        print("🔌 Connecting MCP client...")
        await client.connect()
        print("✅ MCP client connected with memory!")
    return client

# Define the layout (following original pattern exactly)
app.layout = html.Div([
    dbc.Row([
        # Left column (70% width) - Report display area
        dbc.Col([
            html.Div(
                id="left-column-content",
                children=[
                    report_display.create_report_layout()
                ],
                style={
                    'height': '100vh',
                    'overflow-y': 'auto',
                    'padding': '20px',
                    'background-color': '#f8f9fa'
                }
            )
        ], id="left-column", width=8),
        
        # Right column (30% width) - Chat interface
        dbc.Col([
            html.Div([
                # Header with memory indicator
                html.Div([
                    html.H4("AI Assistant", style={'margin': '0', 'text-align': 'center'}),
                    # Memory status indicator
                    html.Div([
                        html.Small("🧠 Memory: Active", 
                                  style={'color': '#28a745', 'font-weight': 'bold'}),
                        html.Br(),
                        html.Small(f"Thread: {DASH_THREAD_ID}", 
                                  style={'color': '#6c757d', 'font-size': '0.8em'})
                    ], style={'margin-top': '10px', 'padding': '8px', 
                             'background-color': '#f8f9fa', 'border-radius': '5px',
                             'text-align': 'center'})
                ], style={'margin-bottom': '20px'}),
                
                # Results area (scrollable)
                html.Div(
                    id="conversation-div",
                    children=[],
                    style={
                        'height': 'calc(100vh - 250px)',  # Adjusted for memory indicator
                        'overflow-y': 'auto',
                        'padding': '15px',
                        'border': '1px solid #dee2e6',
                        'border-radius': '5px',
                        'background-color': 'white',
                        'margin-bottom': '15px',
                        'display': 'flex',
                        'flex-direction': 'column-reverse'  # Show latest messages at bottom
                    }
                ),
                
                # Input area (fixed at bottom)
                html.Div([
                    dbc.InputGroup([
                        dbc.Input(
                            id="query-input",
                            placeholder="Enter your query here...",
                            type="text",
                            style={'border-radius': '20px 0 0 20px'}
                        ),
                        dbc.Button(
                            "Send",
                            id="send-button",
                            color="primary",
                            n_clicks=0,
                            style={'border-radius': '0 20px 20px 0'}
                        )
                    ])
                ], style={'position': 'sticky', 'bottom': '0'})
            ], style={
                'height': '100vh',
                'padding': '20px',
                'display': 'flex',
                'flex-direction': 'column'
            })
        ], id="right-column", width=4)
    ], style={'margin': '0', 'height': '100vh'}),
    
    # Floating toggle button
    dbc.Button(
        "−",
        id="minimize-button",
        style={
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'width': '50px',
            'height': '50px',
            'border-radius': '50%',
            'background-color': '#28a745',
            'border': 'none',
            'color': 'white',
            'font-size': '24px',
            'font-weight': 'bold',
            'box-shadow': '0 4px 8px rgba(0,0,0,0.3)',
            'z-index': '1000',
            'display': 'flex',
            'align-items': 'center',
            'justify-content': 'center'
        },
        n_clicks=0
    )
], style={'height': '100vh', 'overflow': 'hidden'})


# Callback for minimize/expand functionality (unchanged)
@app.callback(
    [Output('left-column', 'width'),
     Output('right-column', 'width'),
     Output('minimize-button', 'children')],
    [Input('minimize-button', 'n_clicks')]
)
def toggle_right_panel(n_clicks):
    if n_clicks % 2 == 1:  # Odd clicks = minimized
        return 12, 0, "+"  # Left column full width, right hidden, show expand button
    else:  # Even clicks = expanded
        return 8, 4, "−"   # Normal layout, show minimize button

# Main callback function with memory support and report display
@app.callback(
    [Output('conversation-div', 'children'),
     Output('query-input', 'value'),
     Output('report-content', 'children'),
     Output('report-status', 'children'),
     Output('interactive-plots-content', 'children'),
     Output('interactive-data-available', 'data')],
    [Input('send-button', 'n_clicks'),
     Input('query-input', 'n_submit')],
    [State('query-input', 'value'),
     State('conversation-div', 'children'),
     State('report-content', 'children'),
     State('report-status', 'children'),
     State('interactive-plots-content', 'children'),
     State('interactive-data-available', 'data')]
)
def process_query(n_clicks, n_submit, query, current_conversation, current_report_content, current_report_status, current_interactive_plots, current_data_available):
    if (n_clicks and n_clicks > 0) or n_submit:
        if query and query.strip():
            try:
                # Add user message to conversation
                user_message = html.Div([
                    html.Div("Me:", style={
                        'font-weight': 'bold', 
                        'color': '#007bff',
                        'margin-bottom': '5px'
                    }),
                    html.Div(query, style={
                        'background-color': '#e3f2fd',
                        'padding': '10px',
                        'border-radius': '10px',
                        'margin-bottom': '10px'
                    })
                ], style={'margin-bottom': '15px'})
                
                # Process MCP client query with memory and file handle support
                async def run_query_with_memory():
                    client = await ensure_client_connected()
                    if not client:
                        return {"response": "Error: Could not connect to MCP client", "raw_content": ""}
                    
                    try:
                        # Use persistent thread ID for conversation continuity
                        # Use the new method that returns both response and raw content
                        result = await client.analyze_territories_with_file_handle(query, thread_id=DASH_THREAD_ID)
                        return result
                    except Exception as e:
                        return {"response": f"Error processing query: {str(e)}", "raw_content": ""}
                
                # Create new event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(run_query_with_memory())
                
                # Extract response and raw content
                if isinstance(result, dict):
                    agent_response = str(result.get('response', ''))
                    raw_content = result.get('raw_content', '')
                else:
                    agent_response = str(result)
                    raw_content = str(result)
                
                # Add agent message to conversation
                agent_message = html.Div([
                    html.Div("Agent:", style={
                        'font-weight': 'bold', 
                        'color': '#28a745',
                        'margin-bottom': '5px'
                    }),
                    html.Div(agent_response, style={
                        'background-color': '#f8f9fa',
                        'padding': '10px',
                        'border-radius': '10px',
                        'white-space': 'pre-wrap'
                    })
                ], style={'margin-bottom': '15px'})
                
                # Update conversation history
                if current_conversation is None:
                    current_conversation = []
                
                updated_conversation = [agent_message, user_message] + current_conversation
                
                # Handle report display - Start with current report state (preserve existing reports)
                report_content = current_report_content if current_report_content is not None else report_display._create_empty_state()
                report_status = current_report_status if current_report_status is not None else report_display.create_report_status_indicator('empty')
                interactive_plots_content = current_interactive_plots if current_interactive_plots is not None else report_display._create_interactive_plots_placeholder()
                interactive_data_available = current_data_available if current_data_available is not None else False
                
                # Try to extract file handle from structured output and display report
                structured_output = result.get('structured_output')
                if structured_output:
                    print(f"[DEBUG] Processing structured output for file handle extraction...")
                    file_handle = report_handler.parse_file_handle_from_response(structured_output)
                    if file_handle:
                        print(f"📄 Found file handle: {file_handle}")
                        # Try to read the report
                        md_content = report_handler.read_md_report(file_handle)
                        if md_content:
                            report_content = report_display.format_markdown_for_dash(md_content)
                            # Get report metadata
                            metadata = report_handler.extract_report_metadata(file_handle)
                            report_status = report_display.create_report_status_indicator('loaded', metadata)
                            print(f"✅ Report loaded and displayed")
                            
                            # Check for interactive data files
                            data_files = report_handler.get_data_files(structured_output)
                            print(f"[DEBUG] Checking for data files from report handler: {len(data_files)} files found")
                            
                            if data_files:
                                print(f"[DEBUG] Found data files for interactive plotting: {list(data_files.keys())}")
                                success, plot_info = load_and_create_plots(data_files)
                                if success:
                                    interactive_plots_content = report_display.create_interactive_plots_layout(
                                        plot_info['variables'], 
                                        plot_info['default_variable']
                                    )
                                    interactive_data_available = True
                                    print(f"✅ Interactive plots ready with variables: {list(plot_info['variables'].keys())}")
                                else:
                                    print(f"❌ Failed to load interactive plots: {plot_info.get('error', 'Unknown error')}")
                            else:
                                # FALLBACK: Try to find data files in the MCP client session
                                print("[DEBUG] No data files from report handler, trying fallback method...")
                                try:
                                    # Get the MCP client to check for recent territory data
                                    client = ensure_client_connected()
                                    if client and hasattr(client, 'session_manager'):
                                        # This is a more advanced fallback - we could implement this later
                                        print("[DEBUG] Could implement session-based data file retrieval here")
                                    
                                    # For now, let's try to construct expected file paths based on recent session data
                                    # Check if there are recent GeoJSON files in static/data
                                    import os
                                    import glob
                                    from pathlib import Path
                                    
                                    static_data_dir = Path("static/data")
                                    if static_data_dir.exists():
                                        # Get the most recent set of territory data files
                                        geojson_files = list(static_data_dir.glob("*_*.geojson"))
                                        if len(geojson_files) >= 3:
                                            # Group by request ID (assuming format: requestid_type.geojson)
                                            file_groups = {}
                                            for file_path in geojson_files:
                                                parts = file_path.stem.split('_', 1)
                                                if len(parts) == 2:
                                                    request_id, file_type = parts
                                                    if request_id not in file_groups:
                                                        file_groups[request_id] = {}
                                                    file_groups[request_id][file_type] = str(file_path)
                                            
                                            # Get the most recent complete set
                                            for request_id, files in sorted(file_groups.items(), reverse=True):
                                                if all(key in files for key in ['grid_data', 'places_data', 'boundaries']):
                                                    fallback_data_files = {
                                                        'grid_data': files['grid_data'],
                                                        'places_data': files['places_data'],
                                                        'boundaries': files['boundaries']
                                                    }
                                                    print(f"[DEBUG] Found fallback data files: {list(fallback_data_files.keys())}")
                                                    success, plot_info = load_and_create_plots(fallback_data_files)
                                                    if success:
                                                        interactive_plots_content = report_display.create_interactive_plots_layout(
                                                            plot_info['variables'], 
                                                            plot_info['default_variable']
                                                        )
                                                        interactive_data_available = True
                                                        print(f"✅ Interactive plots ready using fallback data with variables: {list(plot_info['variables'].keys())}")
                                                    break
                                    
                                except Exception as e:
                                    print(f"❌ Error in fallback data file detection: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                        else:
                            print(f"❌ Could not read report from handle: {file_handle}")
                            report_status = report_display.create_report_status_indicator('error')
                    else:
                        print("ℹ️ No file handle found in response")
                
                return updated_conversation, "", report_content, report_status, interactive_plots_content, interactive_data_available
                
            except Exception as e:
                # Add error message to conversation
                error_message = html.Div([
                    html.Div("Agent:", style={
                        'font-weight': 'bold', 
                        'color': '#dc3545',
                        'margin-bottom': '5px'
                    }),
                    html.Div(f"Error: {str(e)}", style={
                        'background-color': '#f8d7da',
                        'padding': '10px',
                        'border-radius': '10px',
                        'color': '#721c24'
                    })
                ], style={'margin-bottom': '15px'})
                
                user_message = html.Div([
                    html.Div("Me:", style={
                        'font-weight': 'bold', 
                        'color': '#007bff',
                        'margin-bottom': '5px'
                    }),
                    html.Div(query, style={
                        'background-color': '#e3f2fd',
                        'padding': '10px',
                        'border-radius': '10px',
                        'margin-bottom': '10px'
                    })
                ], style={'margin-bottom': '15px'})
                
                if current_conversation is None:
                    current_conversation = []
                
                updated_conversation = [error_message, user_message] + current_conversation
                
                # Return error state for report display
                error_report_content = report_display.create_error_display(str(e))
                error_report_status = report_display.create_report_status_indicator('error')
                error_interactive_plots = report_display._create_interactive_plots_placeholder()
                
                return updated_conversation, "", error_report_content, error_report_status, error_interactive_plots, False
    
    # Return current state if no valid input - preserve existing reports
    preserved_report = current_report_content if current_report_content is not None else report_display._create_empty_state()
    preserved_status = current_report_status if current_report_status is not None else report_display.create_report_status_indicator('empty')
    preserved_interactive_plots = current_interactive_plots if current_interactive_plots is not None else report_display._create_interactive_plots_placeholder()
    preserved_data_available = current_data_available if current_data_available is not None else False
    return current_conversation or [], query or "", preserved_report, preserved_status, preserved_interactive_plots, preserved_data_available

# Callback to enable/disable interactive plots tab based on data availability
@app.callback(
    Output('report-tabs', 'children'),
    [Input('interactive-data-available', 'data')]
)
def update_tab_state(data_available):
    print(f"🔄 Updating tab state - Interactive data available: {data_available}")
    if data_available:
        print("✅ Enabling interactive plots tab")
        return [
            dbc.Tab(label="📄 Report", tab_id="static-report", active_tab_style={"font-weight": "bold"}),
            dbc.Tab(label="📊 Interactive Maps", tab_id="interactive-plots", active_tab_style={"font-weight": "bold"})
        ]
    else:
        print("⏸️ Disabling interactive plots tab")
        return [
            dbc.Tab(label="📄 Report", tab_id="static-report", active_tab_style={"font-weight": "bold"}),
            dbc.Tab(label="📊 Interactive Maps", tab_id="interactive-plots", disabled=True, active_tab_style={"font-weight": "bold"})
        ]

# Callback for tab switching between static report and interactive plots
@app.callback(
    [Output('report-content', 'style'),
     Output('interactive-plots-content', 'style')],
    [Input('report-tabs', 'active_tab')]
)
def switch_report_tabs(active_tab):
    print(f"🔄 Switching tabs - Active tab: {active_tab}")
    if active_tab == 'interactive-plots':
        print("📊 Showing interactive plots content")
        return {'display': 'none'}, {'display': 'block', 'height': 'calc(100vh - 200px)', 'overflow-y': 'auto', 'padding': '20px', 'background-color': 'white', 'border': '1px solid #dee2e6', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}
    else:
        print("📄 Showing static report content")
        return {'height': 'calc(100vh - 200px)', 'overflow-y': 'auto', 'padding': '20px', 'background-color': 'white', 'border': '1px solid #dee2e6', 'border-radius': '8px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}, {'display': 'none'}

# Callback for updating the choropleth map based on selected variable
@app.callback(
    Output('interactive-choropleth-map', 'figure'),
    [Input('interactive-variable-dropdown', 'value')],
    prevent_initial_call=True
)
def update_interactive_choropleth(selected_variable):
    print(f"🔄 Updating choropleth map with variable: {selected_variable}")
    if not selected_variable:
        print("⚠️ No variable selected for choropleth")
        return {}
    
    try:
        print(f"🎯 Creating choropleth map for: {selected_variable}")
        fig = plotter.create_choropleth_map(selected_variable)
        if fig:
            print("✅ Choropleth map created successfully")
            return fig
        else:
            print("❌ Choropleth map creation returned None")
            return {}
    except Exception as e:
        print(f"❌ Error updating choropleth map: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

# Callback for updating the scatter map (supermarket locations)
@app.callback(
    Output('interactive-scatter-map', 'figure'),
    [Input('interactive-variable-dropdown', 'value')],  # Trigger on dropdown change
    prevent_initial_call=True
)
def update_interactive_scatter(selected_variable):
    print(f"🔄 Updating scatter map (triggered by variable: {selected_variable})")
    try:
        print("🎯 Creating scatter map for supermarkets")
        fig = plotter.create_supermarket_scatter_map()
        if fig:
            print("✅ Scatter map created successfully")
            return fig
        else:
            print("❌ Scatter map creation returned None")
            return {}
    except Exception as e:
        print(f"❌ Error updating scatter map: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == '__main__':
    app.run(debug=True)
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import time
import uuid

# Enable debug mode for console output
DEBUG = True

def debug_print(*args, **kwargs):
    """Print debug information if DEBUG is enabled"""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force immediate output

debug_print("Dashboard module loading...")

# Load data
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
debug_print(f"Parent directory: {parent_dir}")

weigh_events_file = os.path.join(parent_dir, 'extracted_weigh_events.csv')
vehicles_file = os.path.join(parent_dir, 'extracted_vehicles.csv')
companies_file = os.path.join(parent_dir, 'extracted_companies.csv')

debug_print(f"Data files:")
debug_print(f"  Weigh events: {weigh_events_file} (exists: {os.path.exists(weigh_events_file)})")
debug_print(f"  Vehicles: {vehicles_file} (exists: {os.path.exists(vehicles_file)})")
debug_print(f"  Companies: {companies_file} (exists: {os.path.exists(companies_file)})")

# Load datasets
def load_data():
    debug_print("Loading datasets...")
    
    # Load the datasets
    debug_print(f"Reading weigh events from {weigh_events_file}")
    weigh_df = pd.read_csv(weigh_events_file)
    debug_print(f"Loaded {len(weigh_df)} weigh event records")
    
    debug_print(f"Reading vehicles from {vehicles_file}")
    vehicles_df = pd.read_csv(vehicles_file)
    debug_print(f"Loaded {len(vehicles_df)} vehicle records")
    
    debug_print(f"Reading companies from {companies_file}")
    companies_df = pd.read_csv(companies_file)
    debug_print(f"Loaded {len(companies_df)} company records")
    
    # Convert event_time to datetime
    weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time'])
    
    # Extract date components
    weigh_df['date'] = weigh_df['event_time'].dt.date
    weigh_df['day'] = weigh_df['event_time'].dt.day
    weigh_df['month'] = weigh_df['event_time'].dt.month
    weigh_df['year'] = weigh_df['event_time'].dt.year
    weigh_df['day_of_week'] = weigh_df['event_time'].dt.day_name()
    weigh_df['hour'] = weigh_df['event_time'].dt.hour
    
    # Map event types
    event_type_map = {1: 'Entry (Gross Weight)', 2: 'Exit (Tare Weight)'}
    weigh_df['event_type_name'] = weigh_df['event_type'].map(event_type_map)
    
    # Add delivery type (normal vs recycle)
    # Recycle events have "R" in the remarks, normal events have location names
    weigh_df['is_recycle'] = weigh_df['remarks'].str.contains('R', case=False, na=False)
    weigh_df['delivery_type'] = weigh_df['is_recycle'].map({True: 'Recycle Collection', False: 'Normal Disposal'})
    
    # Merge with vehicle and company data
    try:
        merged_df = weigh_df.merge(vehicles_df, on='vehicle_id', how='left')
        if 'company_id_x' in merged_df.columns and 'company_id_y' in merged_df.columns:
            # Handle case where company_id appears in both tables
            merged_df = merged_df.rename(columns={'company_id_x': 'company_id'})
            merged_df = merged_df.drop(columns=['company_id_y'])
        
        # Check if name column exists in companies_df
        if 'name' in companies_df.columns:
            merged_df = merged_df.merge(companies_df[['company_id', 'name']], on='company_id', how='left')
            merged_df.rename(columns={'name': 'company_name'}, inplace=True)
        else:
            # Add placeholder for company_name
            merged_df['company_name'] = 'Unknown'
    except Exception as e:
        print(f"Error during merge: {e}")
        # Create basic merged_df without joins
        merged_df = weigh_df.copy()
        merged_df['company_name'] = 'Unknown'
    
    return merged_df, weigh_df, vehicles_df, companies_df

# Calculate net weights for entry-exit pairs
def calculate_net_weights(df):
    # Group by session_id
    sessions = df.groupby('session_id')
    
    results = []
    
    for session_id, group in sessions:
        if len(group) >= 2:  # Need at least entry and exit
            # Sort by event_time to get entry first, exit second
            group = group.sort_values('event_time')
            
            # Get entry and exit weights
            entry = group[group['event_type'] == 1]
            exit = group[group['event_type'] == 2]
            
            if not entry.empty and not exit.empty:
                entry_row = entry.iloc[0]
                exit_row = exit.iloc[0]
                
                # Calculate net weight based on delivery type
                is_recycle = entry_row.get('is_recycle', False)
                
                if is_recycle:
                    # For recycle events, exit weight is higher than entry weight
                    # They collect recyclables, so net_weight should be positive
                    gross_weight = exit_row['weight_kg']
                    tare_weight = entry_row['weight_kg']
                    if gross_weight <= tare_weight:
                        # Skip invalid data where the pattern doesn't match
                        continue
                else:
                    # For normal events, entry weight is higher than exit weight
                    # They drop off waste, so net_weight should be positive
                    gross_weight = entry_row['weight_kg']
                    tare_weight = exit_row['weight_kg']
                    if gross_weight <= tare_weight:
                        # Skip invalid data where the pattern doesn't match
                        continue
                
                # Calculate the absolute difference for net weight
                net_weight = abs(gross_weight - tare_weight)
                
                # Get company name for fee calculation
                company_name = entry_row.get('company_name', 'Unknown')
                
                # Calculate fee: K50 per tonne only for non-LISWMC/LCC companies AND normal disposal (not recycle)
                fee_per_tonne = 0
                if company_name not in ['LISWMC', 'LCC', 'LISWMC/LCC'] and not is_recycle:
                    fee_per_tonne = 50  # K50 per tonne for dumping waste
                
                # Calculate fee in Kwacha (convert kg to tonnes first)
                fee_amount = (net_weight / 1000) * fee_per_tonne
                
                result = {
                    'session_id': session_id,
                    'vehicle_id': entry_row['vehicle_id'],
                    'company_id': entry_row['company_id'],
                    'company_name': company_name,
                    'license_plate': entry_row.get('license_plate', 'Unknown'),
                    'entry_time': entry_row['event_time'],
                    'exit_time': exit_row['event_time'],
                    'duration_minutes': (exit_row['event_time'] - entry_row['event_time']).total_seconds() / 60,
                    'entry_weight': entry_row['weight_kg'],
                    'exit_weight': exit_row['weight_kg'],
                    'net_weight': net_weight,
                    'is_recycle': is_recycle,
                    'delivery_type': entry_row.get('delivery_type', 'Normal Disposal'),
                    'date': entry_row['date'],
                    'day': entry_row['day'],
                    'month': entry_row['month'],
                    'year': entry_row['year'],
                    'day_of_week': entry_row['day_of_week'],
                    'hour': entry_row['hour'],
                    'location': entry_row['remarks'] if not is_recycle else 'Recycle Collection',
                    'fee_per_tonne': fee_per_tonne,
                    'fee_amount': fee_amount
                }
                
                results.append(result)
    
    if results:
        net_weights_df = pd.DataFrame(results)
        return net_weights_df
    return pd.DataFrame()

# Create a tailwind-styled Dash app
external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
    "/static/css/styles.css"
]

# Get absolute path for assets folder
assets_folder = os.path.join(os.path.dirname(__file__), 'assets')
debug_print(f"Assets folder path: {assets_folder}")
debug_print(f"Assets folder exists: {os.path.exists(assets_folder)}")
debug_print(f"Assets folder content: {os.listdir(assets_folder) if os.path.exists(assets_folder) else 'Not found'}")

# Initialize the Dash app with basic configuration
dash_app = dash.Dash(
    __name__, 
    requests_pathname_prefix='/dashboards/weigh_events/',
    external_stylesheets=external_stylesheets,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    assets_folder=assets_folder
)

# Show debug information to verify configuration
debug_print(f"Dash app configuration:")
debug_print(f"- requests_pathname_prefix: {dash_app.config.requests_pathname_prefix}")
debug_print(f"- routes_pathname_prefix: {dash_app.config.routes_pathname_prefix}")
debug_print(f"- assets_folder: {dash_app.config.assets_folder}")
debug_print(f"- assets_url_path: {dash_app.config.assets_url_path}")

# Add database polling interval setting (in seconds)
polling_interval = 300  # Updated to 5 minutes (300 seconds) to match db_dashboard.py

# App layout with Tailwind CSS styling
dash_app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("Waste Collection Analytics", className="text-3xl font-bold text-gray-800"),
            html.P("LISWMC Weigh Events Dashboard", className="text-gray-600")
        ], className="px-4 py-6 bg-white shadow-sm rounded-lg mx-auto max-w-7xl")
    ], className="w-full bg-gray-50 border-b border-gray-200 py-4"),
    
    # Main content
    html.Div([
        html.Div([
            # Filters panel
            html.Div([
                html.H3("Filters", className="text-lg font-medium text-gray-700 mb-4"),
                
                # Date range filter
                html.Div([
                    html.Label("Date Range", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=datetime(2020, 1, 1),
                        max_date_allowed=datetime.now() + timedelta(days=1),
                        start_date=datetime.now() - timedelta(days=30),
                        end_date=datetime.now(),
                        display_format='YYYY-MM-DD',
                        className="w-full"
                    )
                ], className="mb-4"),
                
                # Delivery type filter
                html.Div([
                    html.Label("Delivery Type", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.Dropdown(
                        id='delivery-type-filter',
                        options=[
                            {'label': 'All Types', 'value': 'all'},
                            {'label': 'Normal Disposal', 'value': 'normal'},
                            {'label': 'Recycle Collection', 'value': 'recycle'}
                        ],
                        value='all',
                        className="w-full"
                    )
                ], className="mb-4"),
                
                # Company filter
                html.Div([
                    html.Label("Company", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.Dropdown(
                        id='company-filter',
                        multi=True,
                        placeholder="Select companies...",
                        className="w-full"
                    )
                ], className="mb-4"),
                
                # Vehicle filter
                html.Div([
                    html.Label("Vehicle", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.Dropdown(
                        id='vehicle-filter',
                        multi=True,
                        placeholder="Select vehicles...",
                        className="w-full"
                    )
                ], className="mb-4"),
                
                # Location filter
                html.Div([
                    html.Label("Location", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.Dropdown(
                        id='location-filter',
                        multi=True,
                        placeholder="Select locations...",
                        className="w-full"
                    )
                ], className="mb-4"),
                
                # Polling interval setting
                html.Div([
                    html.Label("Auto Refresh (seconds)", className="block text-sm font-medium text-gray-700 mb-1"),
                    dcc.Input(
                        id='polling-interval-input',
                        type='number',
                        min=5,
                        max=300,
                        step=5,
                        value=polling_interval,
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    )
                ], className="mb-4"),
                
                # Filter buttons
                html.Div([
                    html.Button(
                        "Apply Filters", 
                        id='apply-filters', 
                        className="w-full px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mb-2"
                    ),
                    html.Button(
                        "Reset Filters", 
                        id='reset-filters', 
                        className="w-full px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                    )
                ], className="mt-6"),
                
                # Manual refresh button (new)
                html.Div([
                    html.Button(
                        "Refresh Data Now", 
                        id='manual-refresh', 
                        className="w-full px-4 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    )
                ], className="mt-4"),
                
                # Data info
                html.Div(
                    id='data-info', 
                    className="mt-4 p-3 bg-gray-50 rounded-md text-sm text-gray-600"
                ),
                
                # Last refresh time
                html.Div(
                    id='last-refresh-time',
                    className="mt-2 text-xs text-gray-500 italic"
                ),
                
                # Connection status indicator (new)
                html.Div(
                    id='connection-status',
                    className="mt-2 p-2 rounded-md text-xs font-medium"
                )
            ], className="w-full lg:w-1/5 bg-white p-6 rounded-lg shadow-sm"),
            
            # Main dashboard content
            html.Div([
                dcc.Tabs(
                    id='tabs', 
                    value='overview',
                    className="mb-4", 
                    children=[
                        dcc.Tab(
                            label='Overview',
                            value='overview',
                            className="px-4 py-2 font-medium focus:outline-none",
                            selected_className="border-b-2 border-indigo-500 text-indigo-600"
                        ),
                        dcc.Tab(
                            label='Data Analysis',
                            value='analysis',
                            className="px-4 py-2 font-medium focus:outline-none",
                            selected_className="border-b-2 border-indigo-500 text-indigo-600"
                        ),
                        dcc.Tab(
                            label='Location Insights',
                            value='locations',
                            className="px-4 py-2 font-medium focus:outline-none",
                            selected_className="border-b-2 border-indigo-500 text-indigo-600"
                        ),
                        dcc.Tab(
                            label='Data Table',
                            value='data-table',
                            className="px-4 py-2 font-medium focus:outline-none",
                            selected_className="border-b-2 border-indigo-500 text-indigo-600"
                        )
                    ]
                ),
                
                # Overview Tab
                html.Div(id='overview-tab-content', className="py-4"),
                
                # Analysis Tab
                html.Div(id='analysis-tab-content', className="py-4"),
                
                # Locations Tab
                html.Div(id='locations-tab-content', className="py-4"),
                
                # Data Table Tab
                html.Div(id='data-table-tab-content', className="py-4")
                
            ], className="w-full lg:w-4/5 bg-white p-6 rounded-lg shadow-sm ml-0 lg:ml-4")
        ], className="flex flex-col lg:flex-row gap-4")
    ], className="container mx-auto px-4 py-8"),
    
    # Footer
    html.Footer([
        html.P("© 2025 Lusaka Integrated Solid Waste Management Company", 
               className="text-center text-sm text-gray-500")
    ], className="w-full py-4 mt-8 bg-gray-100"),
    
    # Hidden div to store filtered data
    dcc.Store(id='filtered-data'),
    
    # Database polling interval
    dcc.Interval(
        id='database-poll-interval',
        interval=polling_interval * 1000,  # Convert to milliseconds
        n_intervals=0
    ),
    
    # Load custom JavaScript - properly reference assets path
    html.Script(src="/dashboards/weigh_events/assets/scripts.js"),
])

# Define direct database reload function
def reload_from_database():
    """Reload data directly from the database"""
    debug_print("Reloading data from database...")
    
    try:
        # Import the database connection module
        sys.path.append(parent_dir)
        from database_connection import read_companies, read_vehicles, read_weigh_events
        
        # Read data from database
        weigh_df = read_weigh_events()
        vehicles_df = read_vehicles()
        companies_df = read_companies()
        
        # Write to CSV files for future use
        weigh_df.to_csv(weigh_events_file, index=False)
        vehicles_df.to_csv(vehicles_file, index=False)
        companies_df.to_csv(companies_file, index=False)
        
        debug_print(f"Successfully reloaded data from database:")
        debug_print(f"  - {len(weigh_df)} weigh events")
        debug_print(f"  - {len(vehicles_df)} vehicles")
        debug_print(f"  - {len(companies_df)} companies")
        
        # Process data
        weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time'])
        
        # Extract date components
        weigh_df['date'] = weigh_df['event_time'].dt.date
        weigh_df['day'] = weigh_df['event_time'].dt.day
        weigh_df['month'] = weigh_df['event_time'].dt.month
        weigh_df['year'] = weigh_df['event_time'].dt.year
        weigh_df['day_of_week'] = weigh_df['event_time'].dt.day_name()
        weigh_df['hour'] = weigh_df['event_time'].dt.hour
        
        # Map event types
        event_type_map = {1: 'Entry (Gross Weight)', 2: 'Exit (Tare Weight)'}
        weigh_df['event_type_name'] = weigh_df['event_type'].map(event_type_map)
        
        # Add delivery type
        weigh_df['is_recycle'] = weigh_df['remarks'].str.contains('R', case=False, na=False)
        weigh_df['delivery_type'] = weigh_df['is_recycle'].map({True: 'Recycle Collection', False: 'Normal Disposal'})
        
        # Merge with vehicle and company data
        try:
            merged_df = weigh_df.merge(vehicles_df, on='vehicle_id', how='left')
            if 'company_id_x' in merged_df.columns and 'company_id_y' in merged_df.columns:
                merged_df = merged_df.rename(columns={'company_id_x': 'company_id'})
                merged_df = merged_df.drop(columns=['company_id_y'])
            
            if 'name' in companies_df.columns:
                merged_df = merged_df.merge(companies_df[['company_id', 'name']], on='company_id', how='left')
                merged_df.rename(columns={'name': 'company_name'}, inplace=True)
            else:
                merged_df['company_name'] = 'Unknown'
        except Exception as e:
            debug_print(f"Error during merge: {e}")
            merged_df = weigh_df.copy()
            merged_df['company_name'] = 'Unknown'
        
        # Calculate net weights
        net_weights_df = calculate_net_weights(merged_df)
        
        # Ensure entry_time and exit_time are datetime objects
        if not pd.api.types.is_datetime64_any_dtype(net_weights_df['entry_time']):
            net_weights_df['entry_time'] = pd.to_datetime(net_weights_df['entry_time'])
        
        if not pd.api.types.is_datetime64_any_dtype(net_weights_df['exit_time']):
            net_weights_df['exit_time'] = pd.to_datetime(net_weights_df['exit_time'])
            
        # Set connection status to success
        connection_status = {"status": "success", "message": "Connected to database"}
        
        return merged_df, weigh_df, vehicles_df, companies_df, net_weights_df, connection_status
        
    except Exception as e:
        debug_print(f"Error reloading from database: {e}")
        import traceback
        debug_print(traceback.format_exc())
        
        # Set connection status to error
        connection_status = {"status": "error", "message": f"Database error: {str(e)[:50]}..."}
        
        return None, None, None, None, None, connection_status

# Load initial data
try:
    merged_df, weigh_df, vehicles_df, companies_df = load_data()
    print(f"Loaded {len(weigh_df)} weigh events...")
    print(f"Entry events: {len(weigh_df[weigh_df['event_type'] == 1])}")
    print(f"Exit events: {len(weigh_df[weigh_df['event_type'] == 2])}")
    
    # Check if we have entry-exit pairs
    net_weights_df = calculate_net_weights(merged_df)
    
    if net_weights_df.empty:
        print("Warning: No paired entry/exit events found in data")
        print("Generating sample data for dashboard demonstration...")
        
        # Create sample data for demonstration if no real pairs exist
        # This allows the dashboard to show something even without complete data
        sample_data = []
        
        # Use the actual entry events as a basis for sample data
        entry_events = merged_df[merged_df['event_type'] == 1]
        
        for idx, entry_row in entry_events.iterrows():
            # Create a synthetic exit event based on the entry
            exit_time = entry_row['event_time'] + pd.Timedelta(minutes=30)
            
            # For normal disposal: entry_weight > exit_weight
            entry_weight = entry_row['weight_kg']
            exit_weight = max(500, entry_weight * 0.7)  # Simulate 30% reduction, minimum 500kg
            
            # Calculate net_weight
            net_weight = entry_weight - exit_weight
            
            # Create sample record
            sample_record = {
                'session_id': entry_row['session_id'],
                'vehicle_id': entry_row['vehicle_id'],
                'company_id': entry_row['company_id'],
                'company_name': entry_row.get('company_name', 'Sample Company'),
                'license_plate': entry_row.get('license_plate', 'ABC123'),
                'entry_time': entry_row['event_time'],
                'exit_time': exit_time,
                'duration_minutes': 30,
                'entry_weight': entry_weight,
                'exit_weight': exit_weight,
                'net_weight': net_weight,
                'is_recycle': False,
                'delivery_type': 'Normal Disposal',
                'date': entry_row['date'],
                'day': entry_row['day'],
                'month': entry_row['month'],
                'month_name': entry_row.get('month_name', 'January'),
                'year': entry_row['year'],
                'day_of_week': entry_row['day_of_week'],
                'day_of_week_num': entry_row.get('day_of_week_num', 0),
                'hour': entry_row['hour'],
                'week': entry_row.get('week', 1),
                'location': entry_row['remarks']
            }
            
            sample_data.append(sample_record)
        
        # Create a DataFrame from the sample data
        if sample_data:
            net_weights_df = pd.DataFrame(sample_data)
            print(f"Created {len(net_weights_df)} sample paired events for demonstration")
        else:
            # Create a minimal placeholder DataFrame with required columns
            print("No entry events found to create sample data")
            net_weights_df = pd.DataFrame(columns=[
                'session_id', 'vehicle_id', 'company_id', 'company_name', 'license_plate',
                'entry_time', 'exit_time', 'duration_minutes', 'entry_weight', 'exit_weight',
                'net_weight', 'is_recycle', 'delivery_type', 'date', 'day', 'month', 
                'month_name', 'year', 'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
            ])
except Exception as e:
    import traceback
    print(f"Error loading initial data: {e}")
    print(traceback.format_exc())
    # Create dummy DataFrames to prevent app from crashing
    empty_cols = ['session_id', 'vehicle_id', 'company_id', 'event_type', 'weight_kg', 
                 'event_time', 'remarks', 'date', 'day', 'month', 'year', 'day_of_week', 
                 'hour', 'event_type_name', 'is_recycle', 'delivery_type', 'company_name']
    merged_df = pd.DataFrame(columns=empty_cols)
    weigh_df = pd.DataFrame(columns=empty_cols)
    vehicles_df = pd.DataFrame(columns=['vehicle_id', 'license_plate'])
    companies_df = pd.DataFrame(columns=['company_id', 'name'])
    net_weights_df = pd.DataFrame(columns=[
        'session_id', 'vehicle_id', 'company_id', 'company_name', 'license_plate',
        'entry_time', 'exit_time', 'duration_minutes', 'entry_weight', 'exit_weight',
        'net_weight', 'is_recycle', 'delivery_type', 'date', 'day', 'month', 
        'month_name', 'year', 'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
    ])

# Initial connection status
connection_status = {"status": "unknown", "message": "Connection status unknown"}

# Check if dashboard components are loaded
debug_print("✅ Dashboard layout defined")
debug_print(f"✅ Layout has {len(dash_app.layout.children) if hasattr(dash_app.layout, 'children') else 0} children")

# Update polling interval based on user input
@dash_app.callback(
    Output('database-poll-interval', 'interval'),
    Input('polling-interval-input', 'value'),
    prevent_initial_call=True
)
def update_polling_interval(seconds):
    global polling_interval
    if seconds is not None and seconds >= 5:
        polling_interval = seconds
        return seconds * 1000  # Convert to milliseconds
    # If invalid value, return the current interval
    return polling_interval * 1000

# Database polling callback to refresh data
@dash_app.callback(
    [Output('filtered-data', 'data'),
     Output('last-refresh-time', 'children'),
     Output('connection-status', 'children'),
     Output('connection-status', 'className')],
    [Input('database-poll-interval', 'n_intervals'),
     Input('apply-filters', 'n_clicks'),
     Input('manual-refresh', 'n_clicks'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('delivery-type-filter', 'value'),
     Input('company-filter', 'value'),
     Input('vehicle-filter', 'value'),
     Input('location-filter', 'value')],
    [State('filtered-data', 'data')],
    prevent_initial_call=False
)
def refresh_data(n_intervals, n_clicks, manual_refresh, start_date, end_date, delivery_type, 
                 selected_companies, selected_vehicles, selected_locations, current_data):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    debug_print(f"Callback triggered by: {trigger_id}")
    debug_print(f"Date range: {start_date} to {end_date}")
    
    # Initialize filtered_df
    filtered_df = None
    connection_message = ""
    status_class = "mt-2 p-2 rounded-md text-xs font-medium"
    
    # Only reload from database for interval trigger, manual refresh, or first load
    if trigger_id == 'database-poll-interval' or trigger_id == 'manual-refresh' or (trigger_id is None and n_intervals == 0):
        # Try to reload from database
        reload_result = reload_from_database()
        
        if reload_result is not None:
            global merged_df, weigh_df, vehicles_df, companies_df, net_weights_df, connection_status
            merged_df, weigh_df, vehicles_df, companies_df, net_weights_df, connection_status = reload_result
            debug_print(f"Data refreshed from database with {len(net_weights_df)} records")
            
            # Set connection status message and class
            if connection_status["status"] == "success":
                connection_message = f"✅ {connection_status['message']}"
                status_class += " bg-green-100 text-green-800"
            else:
                connection_message = f"❌ {connection_status['message']}"
                status_class += " bg-red-100 text-red-800"
        else:
            # Database error
            connection_message = "❌ Database connection failed"
            status_class += " bg-red-100 text-red-800"
            
            # Use existing data if available
            if current_data:
                filtered_df = pd.read_json(current_data, orient='split')
    
    # Apply filters to the current data
    if filtered_df is None:
        filtered_df = net_weights_df.copy()
    
    # Apply date filter
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        # Add one day to end_date to include the full end date (up to 23:59:59)
        end_date = pd.to_datetime(end_date) + timedelta(days=1) - timedelta(seconds=1)
        
        # Debug the date filtering
        debug_print(f"Filtering dates: {start_date} to {end_date}")
        debug_print(f"Before date filter: {len(filtered_df)} records")
        
        # Convert entry_time to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(filtered_df['entry_time']):
            filtered_df['entry_time'] = pd.to_datetime(filtered_df['entry_time'])
            
        # Apply the filter
        filtered_df = filtered_df[(filtered_df['entry_time'] >= start_date) & 
                              (filtered_df['entry_time'] <= end_date)]
        
        debug_print(f"After date filter: {len(filtered_df)} records")
    
    # Apply delivery type filter
    if delivery_type and delivery_type != 'all':
        if delivery_type == 'normal':
            filtered_df = filtered_df[~filtered_df['is_recycle']]
        elif delivery_type == 'recycle':
            filtered_df = filtered_df[filtered_df['is_recycle']]
    
    # Apply company filter
    if selected_companies and len(selected_companies) > 0:
        filtered_df = filtered_df[filtered_df['company_id'].isin(selected_companies)]
    
    # Apply vehicle filter
    if selected_vehicles and len(selected_vehicles) > 0:
        filtered_df = filtered_df[filtered_df['vehicle_id'].isin(selected_vehicles)]
    
    # Apply location filter
    if selected_locations and len(selected_locations) > 0:
        filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]
    
    # Add last refresh time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    refresh_message = f"Last refreshed: {current_time}"
    
    # If connection message is empty but we have data, set a default message
    if not connection_message and not filtered_df.empty:
        connection_message = "✅ Using cached data"
        status_class += " bg-yellow-100 text-yellow-800"
    elif not connection_message:
        connection_message = "❓ Connection status unknown"
        status_class += " bg-gray-100 text-gray-800"
    
    # Convert to json for storage
    # Handle any UUID objects by converting them to strings first
    for column in filtered_df.columns:
        if filtered_df[column].apply(lambda x: isinstance(x, uuid.UUID)).any():
            filtered_df[column] = filtered_df[column].astype(str)
    
    return filtered_df.to_json(date_format='iso', orient='split'), refresh_message, connection_message, status_class

# Populate filter dropdowns on load and when database is polled
@dash_app.callback(
    [Output('company-filter', 'options'),
     Output('vehicle-filter', 'options'),
     Output('location-filter', 'options')],
    [Input('filtered-data', 'data'),
     Input('apply-filters', 'n_clicks'),
     Input('database-poll-interval', 'n_intervals'),
     Input('manual-refresh', 'n_clicks')],
    [State('delivery-type-filter', 'value'),
     State('company-filter', 'value'),
     State('vehicle-filter', 'value'),
     State('location-filter', 'value')],
    prevent_initial_call=False
)
def populate_filter_options(json_data, n_clicks, n_intervals, manual_refresh, 
                           delivery_type, selected_companies, selected_vehicles, selected_locations):
    # Read the current filtered data if available
    if json_data:
        filtered_df = pd.read_json(json_data, orient='split')
    else:
        filtered_df = net_weights_df.copy()
    
    # Apply delivery type filter for cascading options
    delivery_filtered = filtered_df.copy()
    
    if delivery_type and delivery_type != 'all':
        if delivery_type == 'normal':
            delivery_filtered = delivery_filtered[~delivery_filtered['is_recycle']]
        elif delivery_type == 'recycle':
            delivery_filtered = delivery_filtered[delivery_filtered['is_recycle']]
    
    # Apply company filter if selected for cascading options
    if selected_companies and len(selected_companies) > 0:
        company_filtered = delivery_filtered[delivery_filtered['company_id'].isin(selected_companies)]
    else:
        company_filtered = delivery_filtered.copy()
    
    # Apply vehicle filter if selected for cascading options
    if selected_vehicles and len(selected_vehicles) > 0:
        vehicle_filtered = company_filtered[company_filtered['vehicle_id'].isin(selected_vehicles)]
    else:
        vehicle_filtered = company_filtered.copy()
    
    # Get unique company options from filtered data
    companies_in_filter = delivery_filtered['company_id'].unique()
    company_options = []
    
    for company_id in companies_in_filter:
        company_name = 'Unknown'
        # Find the company name
        company_rows = companies_df[companies_df['company_id'] == company_id]
        if not company_rows.empty and 'name' in company_rows.columns:
            company_name = company_rows.iloc[0]['name']
        
        # Use shortened UUID for display
        short_id = str(company_id)[:8]
        company_options.append({
            'label': f"{company_name} (ID: {short_id}...)", 
            'value': company_id
        })
    
    # Get unique vehicle options from company-filtered data
    vehicles_in_filter = company_filtered['vehicle_id'].unique()
    vehicle_options = []
    
    for vehicle_id in vehicles_in_filter:
        plate = 'Unknown'
        # Find the license plate
        vehicle_rows = vehicles_df[vehicles_df['vehicle_id'] == vehicle_id]
        if not vehicle_rows.empty and 'license_plate' in vehicle_rows.columns:
            plate = vehicle_rows.iloc[0]['license_plate']
        
        # Use shortened UUID for display
        short_id = str(vehicle_id)[:8]
        vehicle_options.append({
            'label': f"{plate} (ID: {short_id}...)", 
            'value': vehicle_id
        })
    
    # Get unique location options from vehicle-filtered data
    locations = sorted([loc for loc in vehicle_filtered['location'].dropna().unique() 
                      if loc and loc != 'LEGACY DATA' and loc != 'Recycle Collection'])
    location_options = [{'label': loc, 'value': loc} for loc in locations]
    # Add Recycle option if not filtered out
    if delivery_type != 'normal' and 'Recycle Collection' in filtered_df['location'].values:
        location_options.append({'label': 'Recycle Collection', 'value': 'Recycle Collection'})
    
    return company_options, vehicle_options, location_options

# Reset filters
@dash_app.callback(
    [Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('delivery-type-filter', 'value'),
     Output('company-filter', 'value'),
     Output('vehicle-filter', 'value'),
     Output('location-filter', 'value')],
    [Input('reset-filters', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    return datetime.now() - timedelta(days=30), datetime.now(), 'all', [], [], []

# Update data info
@dash_app.callback(
    Output('data-info', 'children'),
    [Input('filtered-data', 'data')],
    prevent_initial_call=False
)
def update_data_info(json_data):
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    # Calculate basic stats
    total_sessions = len(filtered_df)
    total_weight = filtered_df['net_weight'].sum() / 1000  # Convert to tons
    
    # Count by delivery type
    if 'is_recycle' in filtered_df.columns:
        normal_count = len(filtered_df[~filtered_df['is_recycle']])
        recycle_count = len(filtered_df[filtered_df['is_recycle']])
    else:
        normal_count = total_sessions
        recycle_count = 0
    
    # Calculate fee stats if available
    fee_info = []
    if 'fee_amount' in filtered_df.columns:
        total_fees = filtered_df['fee_amount'].sum()
        fee_companies = filtered_df[filtered_df['fee_amount'] > 0]['company_name'].nunique()
        fee_info = [
            html.Div([
                html.P("Fee Information:", className="font-medium mt-2 text-red-600"),
                html.P(f"• Total fees: K {total_fees:,.2f}", className="ml-2"),
                html.P(f"• Companies charged: {fee_companies}", className="ml-2"),
            ])
        ]
    
    return [
        html.P(f"Total Sessions: {total_sessions:,}", className="font-medium"),
        html.P(f"Total Waste: {total_weight:,.2f} tons", className="text-green-600 font-medium"),
        html.Div([
            html.P("Session Types:", className="font-medium mt-2"),
            html.P(f"• Normal Disposal: {normal_count:,}", className="ml-2"),
            html.P(f"• Recycle Collection: {recycle_count:,}", className="ml-2"),
        ]),
        *fee_info,
        html.P(f"Date Range: {filtered_df['entry_time'].min().strftime('%Y-%m-%d') if not filtered_df.empty else 'N/A'} to "
              f"{filtered_df['entry_time'].max().strftime('%Y-%m-%d') if not filtered_df.empty else 'N/A'}", 
              className="mt-2 text-xs")
    ]

# Overview Tab Content
@dash_app.callback(
    Output('overview-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value')],
    prevent_initial_call=False
)
def update_overview_tab(json_data, tab_value):
    if tab_value != 'overview':
        return []
    
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    if filtered_df.empty:
        return html.Div("No data available. Please adjust your filters.", className="text-gray-500 text-center py-10")
    
    # Calculate key metrics
    total_sessions = len(filtered_df)
    total_waste = filtered_df['net_weight'].sum() / 1000  # Convert to tons
    avg_waste = filtered_df['net_weight'].mean()
    max_load = filtered_df['net_weight'].max()
    
    # Normal vs Recycle stats
    normal_df = filtered_df[~filtered_df['is_recycle']] if 'is_recycle' in filtered_df.columns else filtered_df
    recycle_df = filtered_df[filtered_df['is_recycle']] if 'is_recycle' in filtered_df.columns else pd.DataFrame()
    
    normal_total = normal_df['net_weight'].sum() / 1000 if not normal_df.empty else 0
    recycle_total = recycle_df['net_weight'].sum() / 1000 if not recycle_df.empty else 0
    
    # Prepare daily trend data
    # Convert date to string to avoid Period serialization issues
    filtered_df.loc[:, 'date_str'] = filtered_df['date'].astype(str)
    daily_data = filtered_df.groupby(['date_str', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    daily_data.rename(columns={'date_str': 'date'}, inplace=True)
    
    # Create time series chart for the overview
    daily_fig = go.Figure()
    
    # Add normal disposal trend
    normal_daily = daily_data[~daily_data['is_recycle']] if 'is_recycle' in daily_data.columns else daily_data
    if not normal_daily.empty:
        daily_fig.add_trace(go.Scatter(
            x=normal_daily['date'],
            y=normal_daily['net_weight']/1000,
            name='Normal Disposal',
            line=dict(color='#3B82F6', width=2),
            mode='lines'
        ))
    
    # Add recycle collection trend
    recycle_daily = daily_data[daily_data['is_recycle']] if 'is_recycle' in daily_data.columns else pd.DataFrame()
    if not recycle_daily.empty:
        daily_fig.add_trace(go.Scatter(
            x=recycle_daily['date'],
            y=recycle_daily['net_weight']/1000,
            name='Recycle Collection',
            line=dict(color='#10B981', width=2),
            mode='lines'
        ))
    
    daily_fig.update_layout(
        title=None,
        xaxis=dict(title=None, gridcolor='#F3F4F6'),
        yaxis=dict(title='Metric Tons', gridcolor='#F3F4F6'),
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='top', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=0, b=30),
        height=300
    )
    
    # Create pie chart for normal vs recycle
    pie_data = pd.DataFrame({
        'Type': ['Normal Disposal', 'Recycle Collection'],
        'Weight': [normal_total, recycle_total]
    })
    
    pie_fig = px.pie(
        pie_data,
        values='Weight',
        names='Type',
        color='Type',
        color_discrete_map={
            'Normal Disposal': '#3B82F6',
            'Recycle Collection': '#10B981'
        },
        hole=0.4
    )
    
    pie_fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>%{value:.2f} tons<br>%{percent}'
    )
    
    pie_fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=250
    )
    
    # Create hourly heatmap
    # Ensure day_of_week is a string to avoid Period serialization issues
    filtered_df.loc[:, 'day_of_week'] = filtered_df['day_of_week'].astype(str)
    hour_dow = filtered_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    
    # Custom day order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hour_dow['day_of_week'] = pd.Categorical(hour_dow['day_of_week'], categories=day_order, ordered=True)
    hour_dow = hour_dow.sort_values(['day_of_week', 'hour'])
    
    # Create a pivot table for the heatmap
    heatmap_data = hour_dow.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    # Create the heatmap
    heatmap_fig = px.imshow(
        heatmap_data,
        labels=dict(x='Hour of Day', y='Day of Week', color='Sessions'),
        x=list(range(24)),
        y=day_order,
        color_continuous_scale='Blues',
        aspect='auto'
    )
    
    heatmap_fig.update_layout(
        title=None,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(24)),
            ticktext=[f"{h:02d}:00" for h in range(24)],
            tickangle=0
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=250
    )
    
    # Calculate total fees if available
    total_fees = 0
    if 'fee_amount' in filtered_df.columns:
        total_fees = filtered_df['fee_amount'].sum()
    
    # Create the overview layout
    return html.Div([
        # Key metrics row
        html.Div([
            html.Div([
                html.H4("Total Sessions", className="text-sm font-medium text-gray-500"),
                html.P(f"{total_sessions:,}", className="text-3xl font-bold text-gray-900"),
                html.P("weighing events", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            html.Div([
                html.H4("Total Waste", className="text-sm font-medium text-gray-500"),
                html.P(f"{total_weight:,.2f}", className="text-3xl font-bold text-blue-600"),
                html.P("metric tons", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            html.Div([
                html.H4("Average Load", className="text-sm font-medium text-gray-500"),
                html.P(f"{avg_waste:,.2f}", className="text-3xl font-bold text-gray-900"),
                html.P("kg per session", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            # Show total fees or normal/recycle ratio based on whether fees exist
            html.Div([
                html.H4("Total Fees", className="text-sm font-medium text-gray-500"),
                html.P(f"K {total_fees:,.2f}", className="text-3xl font-bold text-red-600"),
                html.P("non-LISWMC companies", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100") if 'fee_amount' in filtered_df.columns else
            html.Div([
                html.H4("Normal / Recycle", className="text-sm font-medium text-gray-500"),
                html.P(f"{normal_total:,.2f} / {recycle_total:,.2f}", className="text-2xl font-bold text-gray-900"),
                html.P("metric tons", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")
        ], className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"),
        
        # Charts
        html.Div([
            # Daily trend chart
            html.Div([
                html.H3("Daily Waste Collection Trend", className="text-lg font-medium text-gray-800 mb-4"),
                dcc.Graph(figure=daily_fig, config={'displayModeBar': False})
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            # Second row - split with pie chart and heatmap
            html.Div([
                # Pie chart
                html.Div([
                    html.H3("Collection Type Distribution", className="text-lg font-medium text-gray-800 mb-4"),
                    dcc.Graph(figure=pie_fig, config={'displayModeBar': False})
                ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
                
                # Heatmap
                html.Div([
                    html.H3("Activity Heatmap", className="text-lg font-medium text-gray-800 mb-4"),
                    dcc.Graph(figure=heatmap_fig, config={'displayModeBar': False})
                ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")
            ], className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4")
        ], className="")
    ])

# Analysis Tab Content
@dash_app.callback(
    Output('analysis-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value')],
    prevent_initial_call=False
)
def update_analysis_tab(json_data, tab_value):
    if tab_value != 'analysis':
        return []
    
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    if filtered_df.empty:
        return html.Div("No data available. Please adjust your filters.", className="text-gray-500 text-center py-10")
    
    # Day of week analysis
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Ensure day_of_week is a string to avoid serialization issues
    filtered_df.loc[:, 'day_of_week'] = filtered_df['day_of_week'].astype(str)
    
    day_data = filtered_df.groupby(['day_of_week', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
    # Set proper day order
    day_data['day_of_week'] = pd.Categorical(day_data['day_of_week'], categories=day_order, ordered=True)
    day_data = day_data.sort_values('day_of_week')
    
    # Create grouped bar chart for day of week
    dow_fig = go.Figure()
    
    # Add normal disposal
    normal_day = day_data[~day_data['is_recycle']] if 'is_recycle' in day_data.columns else day_data
    if not normal_day.empty:
        dow_fig.add_trace(go.Bar(
            x=normal_day['day_of_week'],
            y=normal_day['net_weight']/1000,
            name='Normal Disposal',
            marker_color='#3B82F6'
        ))
    
    # Add recycle collection
    recycle_day = day_data[day_data['is_recycle']] if 'is_recycle' in day_data.columns else pd.DataFrame()
    if not recycle_day.empty:
        dow_fig.add_trace(go.Bar(
            x=recycle_day['day_of_week'],
            y=recycle_day['net_weight']/1000,
            name='Recycle Collection',
            marker_color='#10B981'
        ))
    
    dow_fig.update_layout(
        title=None,
        xaxis=dict(title=None),
        yaxis=dict(title='Metric Tons', gridcolor='#F3F4F6'),
        plot_bgcolor='white',
        barmode='group',
        legend=dict(orientation='h', yanchor='top', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=0, b=40),
        height=300
    )
    
    # Vehicle analysis
    vehicle_data = filtered_df.groupby(['license_plate', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
    vehicle_data = vehicle_data.sort_values('net_weight', ascending=False)
    
    # Get top 10 vehicles
    top_vehicles = set(vehicle_data.nlargest(10, 'net_weight')['license_plate'])
    top_vehicle_data = vehicle_data[vehicle_data['license_plate'].isin(top_vehicles)]
    
    # Create the vehicle chart
    vehicle_fig = px.bar(
        top_vehicle_data,
        x='license_plate',
        y='net_weight',
        color='is_recycle',
        barmode='group',
        color_discrete_map={
            False: '#3B82F6',
            True: '#10B981'
        },
        labels={
            'license_plate': 'Vehicle',
            'net_weight': 'Total Weight (kg)',
            'is_recycle': 'Type'
        },
        height=350
    )
    
    vehicle_fig.update_layout(
        title=None,
        xaxis_title=None,
        yaxis_title='Weight (kg)',
        legend_title=None,
        plot_bgcolor='white',
        xaxis={'categoryorder': 'total descending'},
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5,
            title=None
        ),
        margin=dict(l=0, r=0, t=0, b=40)
    )
    
    # Update legend labels
    vehicle_fig.for_each_trace(lambda t: t.update(
        name='Recycle Collection' if t.name == 'True' else 'Normal Disposal'
    ))
    
    # Duration vs weight analysis
    duration_fig = px.scatter(
        filtered_df,
        x='duration_minutes',
        y='net_weight',
        color='is_recycle',
        size='net_weight',
        hover_name='license_plate',
        color_discrete_map={
            False: '#3B82F6',
            True: '#10B981'
        },
        opacity=0.7,
        height=400,
        labels={
            'duration_minutes': 'Duration (minutes)',
            'net_weight': 'Net Weight (kg)',
            'is_recycle': 'Type'
        }
    )
    
    duration_fig.update_layout(
        title=None,
        legend_title=None,
        plot_bgcolor='white',
        xaxis=dict(title='Duration (minutes)', gridcolor='#F3F4F6'),
        yaxis=dict(title='Weight (kg)', gridcolor='#F3F4F6'),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=0, r=0, t=0, b=40)
    )
    
    # Update legend labels
    duration_fig.for_each_trace(lambda t: t.update(
        name='Recycle Collection' if t.name == 'True' else 'Normal Disposal'
    ))
    
    # Set reasonable axis limits
    duration_fig.update_xaxes(range=[0, filtered_df['duration_minutes'].quantile(0.99)])
    duration_fig.update_yaxes(range=[0, filtered_df['net_weight'].quantile(0.99)])
    
    # Monthly trend analysis - avoid using Period objects directly
    # Format as string to avoid serialization issues
    filtered_df.loc[:, 'month_year_str'] = pd.to_datetime(filtered_df['entry_time']).dt.strftime('%Y-%m')
    
    monthly_data = filtered_df.groupby(['month_year_str', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
    # Rename for consistency
    monthly_data.rename(columns={'month_year_str': 'month_year'}, inplace=True)
    
    # Create monthly trend chart
    monthly_fig = go.Figure()
    
    # Add normal disposal trend
    normal_monthly = monthly_data[~monthly_data['is_recycle']] if 'is_recycle' in monthly_data.columns else monthly_data
    if not normal_monthly.empty:
        monthly_fig.add_trace(go.Bar(
            x=normal_monthly['month_year'],
            y=normal_monthly['net_weight']/1000,
            name='Normal Disposal',
            marker_color='#3B82F6'
        ))
    
    # Add recycle collection trend
    recycle_monthly = monthly_data[monthly_data['is_recycle']] if 'is_recycle' in monthly_data.columns else pd.DataFrame()
    if not recycle_monthly.empty:
        monthly_fig.add_trace(go.Bar(
            x=recycle_monthly['month_year'],
            y=recycle_monthly['net_weight']/1000,
            name='Recycle Collection',
            marker_color='#10B981'
        ))
    
    monthly_fig.update_layout(
        title=None,
        xaxis=dict(title=None, tickangle=45),
        yaxis=dict(title='Metric Tons', gridcolor='#F3F4F6'),
        plot_bgcolor='white',
        barmode='group',
        legend=dict(orientation='h', yanchor='top', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=0, b=60),
        height=350
    )
    
    return html.Div([
        # First row - Day of Week Analysis
        html.Div([
            html.H3("Waste Collection by Day of Week", className="text-lg font-medium text-gray-800 mb-4"),
            dcc.Graph(figure=dow_fig, config={'displayModeBar': False})
        ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 mb-6"),
        
        # Second row - Vehicle Analysis
        html.Div([
            html.H3("Top 10 Vehicles by Waste Volume", className="text-lg font-medium text-gray-800 mb-4"),
            dcc.Graph(figure=vehicle_fig, config={'displayModeBar': False})
        ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 mb-6"),
        
        # Third row - Monthly Trend and Duration Analysis
        html.Div([
            # Monthly Trend
            html.Div([
                html.H3("Monthly Collection Trend", className="text-lg font-medium text-gray-800 mb-4"),
                dcc.Graph(figure=monthly_fig, config={'displayModeBar': False})
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            # Duration Analysis
            html.Div([
                html.H3("Duration vs Weight Analysis", className="text-lg font-medium text-gray-800 mb-4"),
                dcc.Graph(figure=duration_fig, config={'displayModeBar': False})
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")
        ], className="grid grid-cols-1 lg:grid-cols-2 gap-6")
    ])

# Locations Tab Content
@dash_app.callback(
    Output('locations-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value')],
    prevent_initial_call=False
)
def update_locations_tab(json_data, tab_value):
    if tab_value != 'locations':
        return []
    
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    if filtered_df.empty:
        return html.Div("No data available. Please adjust your filters.", className="text-gray-500 text-center py-10")
    
    # Filter out recycle collection to focus on normal disposal with locations
    normal_df = filtered_df[~filtered_df['is_recycle']] if 'is_recycle' in filtered_df.columns else filtered_df
    
    # Skip locations with "LEGACY DATA" or empty values
    location_df = normal_df[~normal_df['location'].isin(['LEGACY DATA', ''])]
    
    # Group by location
    location_data = location_df.groupby('location').agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
    location_data = location_data.sort_values('net_weight', ascending=False)
    
    # Create horizontal bar chart for locations
    location_fig = px.bar(
        location_data,
        y='location',
        x='net_weight',
        color='session_id',
        orientation='h',
        color_continuous_scale='Blues',
        labels={
            'location': 'Area',
            'net_weight': 'Total Waste (kg)',
            'session_id': 'Number of Sessions'
        },
        height=500
    )
    
    location_fig.update_layout(
        title=None,
        xaxis=dict(title='Weight (kg)', gridcolor='#F3F4F6'),
        yaxis=dict(title=None, autorange="reversed"),
        plot_bgcolor='white',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    # Location trends over time
    top_locations = location_data.head(5)['location'].tolist()
    top_locations_df = location_df[location_df['location'].isin(top_locations)]
    
    # Convert date to string to avoid serialization issues
    top_locations_df.loc[:, 'date_str'] = top_locations_df['date'].astype(str)
    
    # Group by location and date
    daily_location_data = top_locations_df.groupby(['location', 'date_str']).agg({
        'net_weight': 'sum'
    }).reset_index()
    
    # Rename for clarity
    daily_location_data.rename(columns={'date_str': 'date'}, inplace=True)
    
    # Create line chart for location trends
    location_trend_fig = px.line(
        daily_location_data,
        x='date',
        y='net_weight',
        color='location',
        labels={
            'date': 'Date',
            'net_weight': 'Weight (kg)',
            'location': 'Area'
        },
        height=400
    )
    
    location_trend_fig.update_layout(
        title=None,
        xaxis=dict(title=None, gridcolor='#F3F4F6'),
        yaxis=dict(title='Weight (kg)', gridcolor='#F3F4F6'),
        plot_bgcolor='white',
        legend=dict(orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5),
        margin=dict(l=0, r=0, t=0, b=40)
    )
    
    # Calculate average weights by location
    avg_weights = location_df.groupby('location').agg({
        'net_weight': 'mean'
    }).reset_index()
    
    avg_weights = avg_weights.sort_values('net_weight', ascending=False)
    
    # Create bar chart for average weights
    avg_weight_fig = px.bar(
        avg_weights.head(10),
        x='location',
        y='net_weight',
        color='net_weight',
        color_continuous_scale='Blues',
        labels={
            'location': 'Area',
            'net_weight': 'Average Weight (kg)'
        },
        height=350
    )
    
    avg_weight_fig.update_layout(
        title=None,
        xaxis=dict(title=None, tickangle=45),
        yaxis=dict(title='Average Weight per Session (kg)', gridcolor='#F3F4F6'),
        plot_bgcolor='white',
        margin=dict(l=0, r=0, t=0, b=80)
    )
    
    return html.Div([
        # First row - Location Bar Chart
        html.Div([
            html.H3("Waste Collection by Area", className="text-lg font-medium text-gray-800 mb-4"),
            dcc.Graph(figure=location_fig, config={'displayModeBar': False})
        ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 mb-6"),
        
        # Second row - split with location trend and average weight
        html.Div([
            # Location Trend
            html.Div([
                html.H3("Top 5 Areas Trend Over Time", className="text-lg font-medium text-gray-800 mb-4"),
                dcc.Graph(figure=location_trend_fig, config={'displayModeBar': False})
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            # Average Weight by Location
            html.Div([
                html.H3("Average Load by Area", className="text-lg font-medium text-gray-800 mb-4"),
                dcc.Graph(figure=avg_weight_fig, config={'displayModeBar': False})
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")
        ], className="grid grid-cols-1 lg:grid-cols-2 gap-6")
    ])

# Data Table Tab Content
@dash_app.callback(
    Output('data-table-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value')],
    prevent_initial_call=False
)
def update_data_table_tab(json_data, tab_value):
    if tab_value != 'data-table':
        return []
    
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    if filtered_df.empty:
        return html.Div("No data available. Please adjust your filters.", className="text-gray-500 text-center py-10")
    
    # Limit to 1000 rows for performance
    display_df = filtered_df.head(1000)
    
    # Format dates and times
    display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['exit_time'] = pd.to_datetime(display_df['exit_time']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Select columns to display
    display_cols = [
        'session_id', 'license_plate', 'location', 'company_name',
        'entry_time', 'exit_time', 'duration_minutes',
        'entry_weight', 'exit_weight', 'net_weight', 'delivery_type',
        'fee_per_tonne', 'fee_amount'
    ]
    
    # Ensure all columns exist
    display_cols = [col for col in display_cols if col in display_df.columns]
    
    if display_cols:
        table_df = display_df[display_cols].copy()
    else:
        return html.Div("No data available with the required columns.", className="text-gray-500 text-center py-10")
    
    # Round numeric columns
    for col in ['duration_minutes', 'entry_weight', 'exit_weight', 'net_weight']:
        if col in table_df.columns:
            table_df[col] = table_df[col].round(2)
            
    # Format fee columns
    if 'fee_amount' in table_df.columns:
        table_df['fee_amount'] = table_df['fee_amount'].round(2)
        table_df['fee_amount'] = table_df['fee_amount'].apply(lambda x: f"K {x:,.2f}" if x > 0 else "-")
        
    if 'fee_per_tonne' in table_df.columns:
        table_df['fee_per_tonne'] = table_df['fee_per_tonne'].apply(lambda x: f"K {x}" if x > 0 else "-")
    
    # Create data table with Tailwind styling
    table_header = [
        html.Thead(
            html.Tr([
                html.Th(col.replace('_', ' ').title(), className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider")
                for col in table_df.columns
            ])
        )
    ]
    
    table_rows = []
    for i in range(len(table_df)):
        row = []
        for col in table_df.columns:
            value = table_df.iloc[i][col]
            # Style numeric values
            if col in ['net_weight', 'entry_weight', 'exit_weight']:
                cell_class = "px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900"
            # Style the delivery type
            elif col == 'delivery_type':
                if value == 'Recycle Collection':
                    cell_class = "px-4 py-2 whitespace-nowrap text-sm text-green-800 bg-green-100 rounded-full py-1 px-3 text-xs"
                else:
                    cell_class = "px-4 py-2 whitespace-nowrap text-sm text-blue-800 bg-blue-100 rounded-full py-1 px-3 text-xs"
            # Style fee amount
            elif col == 'fee_amount' and value != "-":
                cell_class = "px-4 py-2 whitespace-nowrap text-sm font-bold text-red-600"
            # Style fee per tonne
            elif col == 'fee_per_tonne' and value != "-":
                cell_class = "px-4 py-2 whitespace-nowrap text-sm font-medium text-red-500"
            else:
                cell_class = "px-4 py-2 whitespace-nowrap text-sm text-gray-500"
            
            row.append(html.Td(value, className=cell_class))
        
        # Alternate row colors
        row_class = "bg-white" if i % 2 == 0 else "bg-gray-50"
        table_rows.append(html.Tr(row, className=row_class))
    
    table_body = [html.Tbody(table_rows)]
    
    # Create Export buttons with timestamped filename option
    export_buttons = html.Div([
        html.Button(
            "Export Current View", 
            id='export-button', 
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mr-2"
        ),
        html.Button(
            "Export All Records", 
            id='export-all-button', 
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        )
    ], className="flex")
    
    # Create CSV download components
    download_component = dcc.Download(id="download-dataframe-csv")
    download_all_component = dcc.Download(id="download-all-dataframe-csv")
    
    return html.Div([
        html.Div([
            html.H3("Weigh Event Records", className="text-lg font-medium text-gray-800"),
            html.Div([
                html.P(f"Showing {len(table_df)} of {len(filtered_df)} records", 
                    className="text-sm text-gray-500"),
                export_buttons
            ], className="flex justify-between items-center")
        ], className="flex justify-between items-center mb-4"),
        
        download_component,
        download_all_component,
        
        # Create the table with fixed header
        html.Div([
            html.Table(
                table_header + table_body,
                className="min-w-full divide-y divide-gray-200"
            )
        ], className="overflow-x-auto shadow overflow-hidden border-b border-gray-200 sm:rounded-lg")
    ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")

# Export current view to CSV
@dash_app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-button", "n_clicks"),
    State('filtered-data', 'data'),
    prevent_initial_call=True,
)
def export_data(n_clicks, json_data):
    if not json_data:
        return None
    
    filtered_df = pd.read_json(json_data, orient='split')
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"weigh_events_export_{timestamp}.csv"
    
    return dcc.send_data_frame(filtered_df.to_csv, filename, index=False)

# Export all records to CSV (regardless of current filter view)
@dash_app.callback(
    Output("download-all-dataframe-csv", "data"),
    Input("export-all-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_all_data(n_clicks):
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"weigh_events_full_export_{timestamp}.csv"
    
    return dcc.send_data_frame(net_weights_df.to_csv, filename, index=False)

# Get the Flask app server
server = dash_app.server

if __name__ == '__main__':
    dash_app.run_server(debug=True)
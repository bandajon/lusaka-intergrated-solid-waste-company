#!/usr/bin/env python3
"""
Standalone Dashboard Application
--------------------------------
This is a completely standalone version of the dashboard that does not
depend on Flask or the DispatcherMiddleware.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go

# Enable debug mode for console output
DEBUG = True

def debug_print(*args, **kwargs):
    """Print debug information if DEBUG is enabled"""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force immediate output

debug_print("Loading standalone dashboard...")

# Get data file paths
base_dir = os.path.dirname(__file__)
weigh_events_file = os.path.join(base_dir, 'extracted_weigh_events.csv')
vehicles_file = os.path.join(base_dir, 'extracted_vehicles.csv')
companies_file = os.path.join(base_dir, 'extracted_companies.csv')

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
                
                result = {
                    'session_id': session_id,
                    'vehicle_id': entry_row['vehicle_id'],
                    'company_id': entry_row['company_id'],
                    'company_name': entry_row.get('company_name', 'Unknown'),
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
                    'location': entry_row['remarks'] if not is_recycle else 'Recycle Collection'
                }
                
                results.append(result)
    
    if results:
        net_weights_df = pd.DataFrame(results)
        return net_weights_df
    return pd.DataFrame()

# Create a tailwind-styled Dash app
external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"
]

# Get assets folder paths
assets_folder = os.path.abspath(os.path.join(base_dir, 'flask_app/dashboards/assets'))
debug_print(f"Assets folder path: {assets_folder}")
debug_print(f"Assets folder exists: {os.path.exists(assets_folder)}")
debug_print(f"Assets folder content: {os.listdir(assets_folder) if os.path.exists(assets_folder) else 'Not found'}")

# Initialize the Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=external_stylesheets,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    assets_folder=assets_folder
)

# Create a simple layout with diagnostic information
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1("Waste Collection Analytics Dashboard", className="text-3xl font-bold text-gray-800"),
            html.P("LISWMC Weigh Events Dashboard", className="text-gray-600")
        ], className="px-4 py-6 bg-white shadow-sm rounded-lg mx-auto max-w-7xl")
    ], className="w-full bg-gray-50 border-b border-gray-200 py-4"),
    
    # Dashboard diagnostics
    html.Div([
        html.Div([
            html.H2("Dashboard Status", className="text-2xl font-bold mb-4"),
            html.Div([
                html.P("This is a minimal standalone version of the LISWMC waste analytics dashboard.", className="mb-2"),
                html.P("Use this to verify that the Dash app is running correctly.", className="mb-4"),
                
                html.Div([
                    html.H3("Dataset Status", className="text-xl font-bold mt-4 mb-2"),
                    html.Div(id="data-info", className="p-4 bg-gray-50 rounded-lg"),
                ]),
                
                html.Div([
                    html.H3("Sample Visualization", className="text-xl font-bold mt-6 mb-2"),
                    dcc.Graph(id="sample-chart", className="border rounded-lg p-4 bg-white")
                ]),
                
                html.Div([
                    html.Button(
                        "Load Data", 
                        id="load-data-btn", 
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg mt-4 hover:bg-blue-700"
                    ),
                    html.Div(id="data-loading-output", className="mt-2")
                ])
            ], className="bg-white p-6 rounded-lg shadow-sm")
        ], className="max-w-5xl mx-auto")
    ], className="container mx-auto p-6"),
    
    # Footer
    html.Footer([
        html.P("© 2025 Lusaka Integrated Solid Waste Management Company", 
               className="text-center text-sm text-gray-500")
    ], className="w-full py-4 mt-8 bg-gray-100"),
    
    # Hidden divs for data
    dcc.Store(id="stored-data"),
])

# Load data callback
@app.callback(
    [Output("data-info", "children"),
     Output("sample-chart", "figure"),
     Output("data-loading-output", "children"),
     Output("stored-data", "data")],
    [Input("load-data-btn", "n_clicks")],
    prevent_initial_call=False
)
def load_and_display_data(n_clicks):
    # Always load the base data
    try:
        merged_df, weigh_df, vehicles_df, companies_df = load_data()
        debug_print(f"Loaded {len(weigh_df)} weigh events...")
        debug_print(f"Entry events: {len(weigh_df[weigh_df['event_type'] == 1])}")
        debug_print(f"Exit events: {len(weigh_df[weigh_df['event_type'] == 2])}")
        
        # Calculate net weights
        net_weights_df = calculate_net_weights(merged_df)
        
        if net_weights_df.empty:
            debug_print("No paired entry/exit events found")
            return (
                html.Div([
                    html.P("⚠️ No paired entry/exit events found in data", className="text-yellow-600 font-bold"),
                    html.P(f"Total weigh events: {len(weigh_df)}", className="mb-1"),
                    html.P(f"Entry events: {len(weigh_df[weigh_df['event_type'] == 1])}", className="mb-1"),
                    html.P(f"Exit events: {len(weigh_df[weigh_df['event_type'] == 2])}", className="mb-1"),
                ]),
                px.bar(x=["Entry", "Exit"], y=[len(weigh_df[weigh_df['event_type'] == 1]), len(weigh_df[weigh_df['event_type'] == 2])], 
                       title="Entry vs Exit Events Count"),
                html.P("Data loaded, but no paired events found. Charts may be empty.", className="text-yellow-600"),
                None
            )
        
        # Create a daily summary for sample chart
        daily_data = net_weights_df.groupby('date').agg({
            'net_weight': 'sum',
            'session_id': 'count'
        }).reset_index()
        
        # Create sample figure
        fig = px.line(
            daily_data, 
            x='date', 
            y='net_weight', 
            title='Daily Net Weight',
            labels={'net_weight': 'Net Weight (kg)', 'date': 'Date'},
            markers=True
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        # Store the net weights data for other components
        stored_data = net_weights_df.to_json(date_format='iso', orient='split')
        
        return (
            html.Div([
                html.P("✅ Data loaded successfully", className="text-green-600 font-bold mb-2"),
                html.P(f"Total weigh events: {len(weigh_df)}", className="mb-1"),
                html.P(f"Entry events: {len(weigh_df[weigh_df['event_type'] == 1])}", className="mb-1"),
                html.P(f"Exit events: {len(weigh_df[weigh_df['event_type'] == 2])}", className="mb-1"),
                html.P(f"Paired events: {len(net_weights_df)}", className="mb-1 font-semibold"),
                html.P(f"Total net weight: {net_weights_df['net_weight'].sum():,.2f} kg", className="mb-1"),
                html.P(f"Average load: {net_weights_df['net_weight'].mean():,.2f} kg", className="mb-1"),
                html.P(f"Date range: {net_weights_df['date'].min()} to {net_weights_df['date'].max()}", className="text-sm text-gray-500 mt-2"),
            ]),
            fig,
            html.P("Data loaded successfully!", className="text-green-600 mt-2"),
            stored_data
        )
    
    except Exception as e:
        import traceback
        debug_print(f"Error loading data: {e}")
        debug_print(traceback.format_exc())
        
        # Return error state
        return (
            html.Div([
                html.P("❌ Error loading data", className="text-red-600 font-bold"),
                html.P(str(e), className="text-red-600"),
                html.Pre(traceback.format_exc(), className="text-xs text-gray-700 bg-gray-100 p-2 mt-2 overflow-x-auto")
            ]),
            px.scatter(x=[0], y=[0], title="Error: No data available"),
            html.P(f"Error: {str(e)}", className="text-red-600 mt-2"),
            None
        )

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5005, host='0.0.0.0')
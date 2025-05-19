#!/usr/bin/env python3
"""
Full Analytics Dashboard
-----------------------
A comprehensive analytics dashboard for waste collection data.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go

# Enable debug mode for console output
DEBUG = True

def debug_print(*args, **kwargs):
    """Print debug information if DEBUG is enabled"""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force immediate output

debug_print("Loading full analytics dashboard...")

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
    weigh_df['month_name'] = weigh_df['event_time'].dt.strftime('%B')
    weigh_df['year'] = weigh_df['event_time'].dt.year
    weigh_df['day_of_week'] = weigh_df['event_time'].dt.day_name()
    weigh_df['day_of_week_num'] = weigh_df['event_time'].dt.dayofweek
    weigh_df['hour'] = weigh_df['event_time'].dt.hour
    weigh_df['week'] = weigh_df['event_time'].dt.isocalendar().week
    
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
                    'month_name': entry_row.get('month_name', ''),
                    'year': entry_row['year'],
                    'day_of_week': entry_row['day_of_week'],
                    'day_of_week_num': entry_row.get('day_of_week_num', 0),
                    'hour': entry_row['hour'],
                    'week': entry_row.get('week', 0),
                    'location': entry_row['remarks'] if not is_recycle else 'Recycle Collection'
                }
                
                results.append(result)
    
    if results:
        net_weights_df = pd.DataFrame(results)
        return net_weights_df
    return pd.DataFrame()

# Create a Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Load data and calculate net weights
try:
    merged_df, weigh_df, vehicles_df, companies_df = load_data()
    debug_print(f"Loaded data:")
    debug_print(f"- {len(weigh_df)} weigh events")
    debug_print(f"- {len(weigh_df[weigh_df['event_type'] == 1])} entry events")
    debug_print(f"- {len(weigh_df[weigh_df['event_type'] == 2])} exit events")
    
    net_weights_df = calculate_net_weights(merged_df)
    
    if net_weights_df.empty:
        debug_print("Warning: No paired entry/exit events found!")
        # Create sample data for demonstration
        debug_print("Creating sample data for demonstration")
        # This will allow the dashboard to run even without matched pairs
    else:
        debug_print(f"Created {len(net_weights_df)} paired entry/exit records")
    
except Exception as e:
    import traceback
    debug_print(f"Error during data loading: {e}")
    debug_print(traceback.format_exc())
    # Create empty DataFrames to prevent app from crashing
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

# App layout with Tailwind CSS styling
app.layout = html.Div([
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
                
                # Data info
                html.Div(
                    id='data-info', 
                    className="mt-4 p-3 bg-gray-50 rounded-md text-sm text-gray-600"
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
])

# Populate filter dropdowns on load
@app.callback(
    [Output('company-filter', 'options'),
     Output('vehicle-filter', 'options'),
     Output('location-filter', 'options')],
    [Input('apply-filters', 'n_clicks')],
    prevent_initial_call=False
)
def populate_filter_options(n_clicks):
    try:
        # Company options - use a safer approach to handle string truncation
        company_options = []
        for _, row in companies_df.iterrows():
            if 'name' in companies_df.columns and 'company_id' in companies_df.columns:
                company_name = row['name'] if pd.notna(row['name']) else 'Unknown'
                company_id = row['company_id']
                
                # Safely get first 8 chars of ID if available
                short_id = company_id[:8] if isinstance(company_id, str) and len(company_id) >= 8 else company_id
                
                company_options.append({
                    'label': f"{company_name} (ID: {short_id})",
                    'value': company_id
                })
        
        # Vehicle options - use a safer approach
        vehicle_options = []
        for _, row in vehicles_df.iterrows():
            if 'license_plate' in vehicles_df.columns and 'vehicle_id' in vehicles_df.columns:
                license_plate = row['license_plate'] if pd.notna(row['license_plate']) else 'Unknown'
                vehicle_id = row['vehicle_id']
                
                # Safely get first 8 chars of ID if available
                short_id = vehicle_id[:8] if isinstance(vehicle_id, str) and len(vehicle_id) >= 8 else vehicle_id
                
                vehicle_options.append({
                    'label': f"{license_plate} (ID: {short_id})",
                    'value': vehicle_id
                })
        
        # Location options (from location/remarks)
        location_options = []
        if 'location' in net_weights_df.columns:
            locations = net_weights_df['location'].dropna().unique().tolist()
            valid_locations = [loc for loc in locations if pd.notna(loc) and loc != 'LEGACY DATA']
            
            for loc in sorted(valid_locations):
                if loc and loc != 'Recycle Collection':
                    location_options.append({'label': loc, 'value': loc})
            
            # Add Recycle option if it exists in the data
            if 'Recycle Collection' in locations:
                location_options.append({'label': 'Recycle Collection', 'value': 'Recycle Collection'})
    
    except Exception as e:
        import traceback
        print(f"Error in populate_filter_options: {e}")
        print(traceback.format_exc())
        company_options = []
        vehicle_options = []
        location_options = []
    
    return company_options, vehicle_options, location_options

# Filter data based on selected criteria
@app.callback(
    Output('filtered-data', 'data'),
    [Input('apply-filters', 'n_clicks')],
    [State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('delivery-type-filter', 'value'),
     State('company-filter', 'value'),
     State('vehicle-filter', 'value'),
     State('location-filter', 'value')],
    prevent_initial_call=False
)
def filter_data(n_clicks, start_date, end_date, delivery_type, selected_companies, selected_vehicles, selected_locations):
    try:
        filtered_df = net_weights_df.copy()
        
        if filtered_df.empty:
            # Return empty dataframe if no data
            return filtered_df.to_json(date_format='iso', orient='split')
        
        # Apply date filter
        if start_date and end_date:
            try:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                if 'entry_time' in filtered_df.columns:
                    filtered_df = filtered_df[(filtered_df['entry_time'] >= start_date) & 
                                            (filtered_df['entry_time'] <= end_date)]
            except Exception as e:
                print(f"Date filtering error: {e}")
        
        # Apply delivery type filter
        if delivery_type and delivery_type != 'all':
            if 'is_recycle' in filtered_df.columns:
                if delivery_type == 'normal':
                    filtered_df = filtered_df[~filtered_df['is_recycle']]
                elif delivery_type == 'recycle':
                    filtered_df = filtered_df[filtered_df['is_recycle']]
        
        # Apply company filter
        if selected_companies and len(selected_companies) > 0:
            if 'company_id' in filtered_df.columns:
                # Convert selected_companies to list if it's not already
                if not isinstance(selected_companies, list):
                    selected_companies = [selected_companies]
                # Filter only on valid IDs
                valid_companies = [c for c in selected_companies if c is not None and c != ""]
                if valid_companies:
                    filtered_df = filtered_df[filtered_df['company_id'].isin(valid_companies)]
        
        # Apply vehicle filter
        if selected_vehicles and len(selected_vehicles) > 0:
            if 'vehicle_id' in filtered_df.columns:
                # Convert selected_vehicles to list if it's not already
                if not isinstance(selected_vehicles, list):
                    selected_vehicles = [selected_vehicles]
                # Filter only on valid IDs
                valid_vehicles = [v for v in selected_vehicles if v is not None and v != ""]
                if valid_vehicles:
                    filtered_df = filtered_df[filtered_df['vehicle_id'].isin(valid_vehicles)]
        
        # Apply location filter
        if selected_locations and len(selected_locations) > 0:
            if 'location' in filtered_df.columns:
                # Convert selected_locations to list if it's not already
                if not isinstance(selected_locations, list):
                    selected_locations = [selected_locations]
                # Filter only on valid locations
                valid_locations = [l for l in selected_locations if l is not None and l != ""]
                if valid_locations:
                    filtered_df = filtered_df[filtered_df['location'].isin(valid_locations)]
        
        # Convert to json for storage
        return filtered_df.to_json(date_format='iso', orient='split')
    
    except Exception as e:
        import traceback
        print(f"Error in filter_data: {e}")
        print(traceback.format_exc())
        # Return the original data if there's an error
        return net_weights_df.to_json(date_format='iso', orient='split')

# Reset filters
@app.callback(
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
@app.callback(
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
    
    return [
        html.P(f"Total Sessions: {total_sessions:,}", className="font-medium"),
        html.P(f"Total Waste: {total_weight:,.2f} tons", className="text-green-600 font-medium"),
        html.Div([
            html.P("Session Types:", className="font-medium mt-2"),
            html.P(f"• Normal Disposal: {normal_count:,}", className="ml-2"),
            html.P(f"• Recycle Collection: {recycle_count:,}", className="ml-2"),
        ]),
        html.P(f"Date Range: {filtered_df['entry_time'].min().strftime('%Y-%m-%d') if not filtered_df.empty else 'N/A'} to "
              f"{filtered_df['entry_time'].max().strftime('%Y-%m-%d') if not filtered_df.empty else 'N/A'}", 
              className="mt-2 text-xs")
    ]

# Overview Tab Content
@app.callback(
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
    daily_data = filtered_df.groupby(['date', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
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
    hour_dow = filtered_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    
    # Custom day order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hour_dow['day_of_week'] = pd.Categorical(hour_dow['day_of_week'], categories=day_order, ordered=True)
    hour_dow = hour_dow.sort_values(['day_of_week', 'hour'])
    
    # Create a pivot table for the heatmap
    heatmap_data = hour_dow.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    # Make sure all days are present in the pivot table
    for day in day_order:
        if day not in heatmap_data.index:
            # Add missing day with zeros
            heatmap_data.loc[day] = [0] * len(heatmap_data.columns) if len(heatmap_data.columns) > 0 else [0] * 24
    
    # Sort the index to match day_order
    heatmap_data = heatmap_data.reindex(day_order)
    
    # Make sure all hours are present and in order
    for hour in range(24):
        if hour not in heatmap_data.columns:
            heatmap_data[hour] = 0
    
    # Ensure columns are properly ordered (0-23)
    all_hours = list(range(24))
    heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)
    
    # Create the heatmap with clearly formatted hours
    hour_labels = [f"{h:02d}:00" for h in range(24)]  # Format as 00:00, 01:00, etc.
    
    heatmap_fig = px.imshow(
        heatmap_data,
        labels=dict(x='Hour of Day', y='Day of Week', color='Sessions'),
        x=all_hours,  # Use consistent list of hours
        y=heatmap_data.index.tolist(),
        color_continuous_scale='Blues',
        aspect='auto'
    )
    
    heatmap_fig.update_layout(
        title=None,
        xaxis=dict(
            title="Hour of Day",
            titlefont=dict(size=12),
            tickmode='array',
            tickvals=list(range(24)),
            ticktext=hour_labels,
            tickangle=0,
            tickfont=dict(size=10),
            gridcolor='rgba(211, 211, 211, 0.3)'
        ),
        yaxis=dict(
            title="Day of Week",
            titlefont=dict(size=12),
            tickfont=dict(size=11)
        ),
        coloraxis_colorbar=dict(
            title="Sessions",
            titlefont=dict(size=12),
            tickfont=dict(size=10)
        ),
        margin=dict(l=20, r=20, t=5, b=20),
        height=250
    )
    
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
                html.P(f"{total_waste:,.2f}", className="text-3xl font-bold text-blue-600"),
                html.P("metric tons", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
            html.Div([
                html.H4("Average Load", className="text-sm font-medium text-gray-500"),
                html.P(f"{avg_waste:,.2f}", className="text-3xl font-bold text-gray-900"),
                html.P("kg per session", className="text-xs text-gray-500")
            ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100"),
            
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
@app.callback(
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
    
    # Monthly trend analysis
    filtered_df['month_year'] = pd.to_datetime(filtered_df['entry_time']).dt.to_period('M')
    monthly_data = filtered_df.groupby(['month_year', 'is_recycle']).agg({
        'net_weight': 'sum',
        'session_id': 'count'
    }).reset_index()
    
    # Convert period to string for plotting
    monthly_data['month_year'] = monthly_data['month_year'].astype(str)
    
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
@app.callback(
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
    
    # Group by location and date
    daily_location_data = top_locations_df.groupby(['location', 'date']).agg({
        'net_weight': 'sum'
    }).reset_index()
    
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
@app.callback(
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
        'entry_weight', 'exit_weight', 'net_weight', 'delivery_type'
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
    
    # Create data table
    table = dash_table.DataTable(
        id='data-table',
        columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in table_df.columns],
        data=table_df.to_dict('records'),
        style_table={
            'overflowX': 'auto',
            'height': '600px', 
            'overflowY': 'auto'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'borderBottom': '2px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f1f5f9'
            },
            {
                'if': {'column_id': 'net_weight'},
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{delivery_type} = "Recycle Collection"',
                    'column_id': 'delivery_type'
                },
                'backgroundColor': '#d1fae5',
                'color': '#065f46'
            },
            {
                'if': {
                    'filter_query': '{delivery_type} = "Normal Disposal"',
                    'column_id': 'delivery_type'
                },
                'backgroundColor': '#dbeafe',
                'color': '#1e40af'
            }
        ],
        page_size=25,
        filter_action='native',
        sort_action='native',
    )
    
    # Create download button
    download_button = html.Button(
        "Export to CSV", 
        id='export-button', 
        className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 mt-4"
    )
    
    return html.Div([
        html.Div([
            html.H3("Weigh Event Records", className="text-lg font-medium text-gray-800"),
            html.Div([
                html.P(f"Showing {len(table_df)} of {len(filtered_df)} records", 
                    className="text-sm text-gray-500"),
                download_button
            ], className="flex justify-between items-center")
        ], className="flex justify-between items-center mb-4"),
        
        # Data table
        table,
    ], className="bg-white rounded-lg p-5 shadow-sm border border-gray-100")

# Export data to CSV callback
@app.callback(
    Output('dummy-export-output', 'children', allow_duplicate=True),
    Input('export-button', 'n_clicks'),
    State('filtered-data', 'data'),
    prevent_initial_call=True,
)
def export_data(n_clicks, json_data):
    if not n_clicks:
        return None
    
    if not json_data:
        filtered_df = net_weights_df.copy()
    else:
        filtered_df = pd.read_json(json_data, orient='split')
    
    # Export to CSV
    export_path = os.path.join(base_dir, 'weigh_events_export.csv')
    filtered_df.to_csv(export_path, index=False)
    
    return html.Div([
        html.P(f"Data exported to {export_path}", className="text-green-600 mt-2")
    ])

# Add a dummy div for the export callback
app.layout.children.append(html.Div(id='dummy-export-output', style={'display': 'none'}))

# Run the app
if __name__ == '__main__':
    debug_print("Starting Full Analytics Dashboard...")
    debug_print(f"Dashboard will be available at: http://localhost:5006/")
    app.run(debug=True, port=5006, host='0.0.0.0')
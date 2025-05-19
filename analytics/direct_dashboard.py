#!/usr/bin/env python3
"""
Simple Direct Dashboard for LISWMC
----------------------------------
This version provides a single direct dashboard that polls
the database automatically.
"""

import os
import sys
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time

# Set up configuration
APP_PORT = 5005
DATABASE_POLL_INTERVAL = 30  # seconds

# Enable debug output
print(f"Starting Direct Dashboard on port {APP_PORT}")
print(f"Will poll database every {DATABASE_POLL_INTERVAL} seconds")

def load_from_database():
    """Get data directly from database"""
    try:
        from database_connection import read_companies, read_vehicles, read_weigh_events
        
        # Read data from database
        weigh_df = read_weigh_events()
        vehicles_df = read_vehicles()
        companies_df = read_companies()
        
        # Map ARRIVAL/DEPARTURE to numeric values
        event_type_map = {
            'ARRIVAL': 1,
            'DEPARTURE': 2,
            'Entry': 1,
            'Exit': 2,
            1: 1, 
            2: 2
        }
        
        if 'event_type' in weigh_df.columns:
            weigh_df['event_type'] = weigh_df['event_type'].map(event_type_map)
            print(f"Event types: {weigh_df['event_type'].value_counts().to_dict()}")
        
        # Add timestamp for this data load
        refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return weigh_df, vehicles_df, companies_df, refresh_time
    
    except Exception as e:
        print(f"Error loading from database: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Initial data load
weigh_df, vehicles_df, companies_df, last_refresh = load_from_database()
print(f"Initial data loaded - {len(weigh_df)} weigh events")

# Process data for visualization
def process_data_for_viz(weigh_df, vehicles_df, companies_df):
    """Process data for visualization"""
    
    if weigh_df is None or weigh_df.empty:
        print("No data available!")
        # Return empty DataFrames
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        # Convert date/time if needed
        if 'event_time' in weigh_df.columns:
            weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time'])
            
            # Extract date components
            weigh_df['date'] = weigh_df['event_time'].dt.date
            weigh_df['day'] = weigh_df['event_time'].dt.day
            weigh_df['month'] = weigh_df['event_time'].dt.month
            weigh_df['year'] = weigh_df['event_time'].dt.year
            weigh_df['day_of_week'] = weigh_df['event_time'].dt.day_name()
            weigh_df['hour'] = weigh_df['event_time'].dt.hour
        
        # Make sure all required data types are available
        if 'event_type' not in weigh_df.columns:
            weigh_df['event_type'] = 1  # Default all to Entry for display
        
        # Add event type name
        event_type_map = {1: 'Entry (Gross Weight)', 2: 'Exit (Tare Weight)'}
        weigh_df['event_type_name'] = weigh_df['event_type'].map(event_type_map)
        
        # Merge with vehicle and company data
        if vehicles_df is not None and not vehicles_df.empty:
            merged_df = weigh_df.copy()
            if 'vehicle_id' in weigh_df.columns and 'vehicle_id' in vehicles_df.columns:
                merged_df = weigh_df.merge(vehicles_df, on='vehicle_id', how='left')
            
            if companies_df is not None and not companies_df.empty:
                if 'company_id' in merged_df.columns and 'company_id' in companies_df.columns:
                    if 'name' in companies_df.columns:
                        merged_df = merged_df.merge(companies_df[['company_id', 'name']], 
                                                   on='company_id', how='left')
                        merged_df.rename(columns={'name': 'company_name'}, inplace=True)
        else:
            merged_df = weigh_df.copy()
            
        # Final check if company_name is available
        if 'company_name' not in merged_df.columns:
            merged_df['company_name'] = 'Unknown'
            
        # Add delivery type info
        merged_df['is_recycle'] = merged_df['remarks'].str.contains('R', case=False, na=False) if 'remarks' in merged_df.columns else False
        merged_df['delivery_type'] = merged_df['is_recycle'].map({True: 'Recycle Collection', False: 'Normal Disposal'})
            
        return merged_df, weigh_df
        
    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame()

# Create the dashboard app
app = dash.Dash(__name__, 
                title="LISWMC Analytics Dashboard",
                update_title="Updating...")

# Define the app layout with auto-refresh
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("LISWMC Weigh Events Dashboard", 
                style={'textAlign': 'center', 'color': '#2c3e50'}),
        html.P(id='last-update-time', 
               style={'textAlign': 'center', 'fontStyle': 'italic', 'fontSize': 14})
    ]),
    
    # Controls
    html.Div([
        html.Button('Refresh Data', id='refresh-button', 
                   style={
                       'backgroundColor': '#3498db',
                       'color': 'white',
                       'border': 'none',
                       'padding': '10px 20px',
                       'borderRadius': '5px',
                       'cursor': 'pointer',
                       'margin': '10px'
                   }
        ),
        html.Div([
            html.Label("Date Range:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                display_format='YYYY-MM-DD',
                style={'margin': '5px'}
            )
        ], style={'display': 'inline-block', 'margin': '10px'}),
        
        html.Div([
            html.Label("Event Type:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='event-type-filter',
                options=[
                    {'label': 'All Events', 'value': 'all'},
                    {'label': 'Entry Events', 'value': 'entry'},
                    {'label': 'Exit Events', 'value': 'exit'}
                ],
                value='all',
                style={'width': '200px', 'display': 'inline-block'}
            )
        ], style={'display': 'inline-block', 'margin': '10px'})
    ], style={'textAlign': 'center', 'margin': '20px'}),
    
    # Data summary section
    html.Div([
        html.Div([
            html.H3("Data Summary", style={'textAlign': 'center'}),
            html.Div(id='data-summary')
        ], style={
            'backgroundColor': '#f8f9fa', 
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
            'margin': '10px'
        })
    ]),
    
    # Charts section
    html.Div([
        html.Div([
            html.H3("Event History", style={'textAlign': 'center'}),
            dcc.Graph(id='events-timeline')
        ], style={
            'backgroundColor': 'white', 
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
            'margin': '10px'
        }, className='six columns'),
        
        html.Div([
            html.H3("Events by Type", style={'textAlign': 'center'}),
            dcc.Graph(id='events-by-type')
        ], style={
            'backgroundColor': 'white', 
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
            'margin': '10px'
        }, className='six columns'),
    ], className='row'),
    
    # Table section
    html.Div([
        html.H3("Recent Events", style={'textAlign': 'center'}),
        html.Div(id='recent-events-table')
    ], style={
        'backgroundColor': 'white', 
        'padding': '15px',
        'borderRadius': '5px',
        'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
        'margin': '20px'
    }),
    
    # Hidden components for storing data and timers
    dcc.Store(id='data-store'),
    dcc.Interval(
        id='interval-component',
        interval=DATABASE_POLL_INTERVAL * 1000,  # Convert to milliseconds
        n_intervals=0
    ),
    
    # Footer
    html.Div([
        html.Hr(),
        html.P("© 2025 Lusaka Integrated Solid Waste Management Company",
               style={'textAlign': 'center'})
    ])
], style={'margin': '20px', 'maxWidth': '1200px', 'margin': '0 auto'})

# Callback to update data periodically or on refresh button click
@app.callback(
    [Output('data-store', 'data'),
     Output('last-update-time', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_data(n_intervals, n_clicks):
    """Update data from database"""
    # Either automated update or manual refresh button click
    global weigh_df, vehicles_df, companies_df, last_refresh
    
    print(f"Data update triggered (interval={n_intervals}, clicks={n_clicks})")
    
    # Get fresh data
    new_weigh_df, new_vehicles_df, new_companies_df, refresh_time = load_from_database()
    
    if new_weigh_df is not None:
        weigh_df = new_weigh_df
        vehicles_df = new_vehicles_df
        companies_df = new_companies_df
        last_refresh = refresh_time
        
        # Process data
        merged_df, _ = process_data_for_viz(weigh_df, vehicles_df, companies_df)
        
        # Convert to JSON for storage
        data_json = {
            'weigh_events': merged_df.to_json(date_format='iso', orient='split')
        }
        
        return data_json, f"Last updated: {refresh_time}"
    
    # If data load failed, return current data
    merged_df, _ = process_data_for_viz(weigh_df, vehicles_df, companies_df)
    data_json = {
        'weigh_events': merged_df.to_json(date_format='iso', orient='split')
    }
    
    return data_json, f"Last updated: {last_refresh} (update failed, showing previous data)"

# Callback to filter data and update summary stats
@app.callback(
    Output('data-summary', 'children'),
    [Input('data-store', 'data'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('event-type-filter', 'value')]
)
def update_data_summary(data, start_date, end_date, event_type):
    """Update data summary based on filters"""
    if not data:
        return html.P("No data available.")
    
    # Convert stored data back to DataFrame
    df = pd.read_json(data['weigh_events'], orient='split')
    
    # Apply filters
    filtered_df = filter_data(df, start_date, end_date, event_type)
    
    # Calculate summary statistics
    total_events = len(filtered_df)
    entry_events = len(filtered_df[filtered_df['event_type'] == 1]) if 'event_type' in filtered_df.columns else 0
    exit_events = len(filtered_df[filtered_df['event_type'] == 2]) if 'event_type' in filtered_df.columns else 0
    
    # Calculate average weights
    avg_entry_weight = filtered_df[filtered_df['event_type'] == 1]['weight_kg'].mean() if 'event_type' in filtered_df.columns and 'weight_kg' in filtered_df.columns else 0
    avg_exit_weight = filtered_df[filtered_df['event_type'] == 2]['weight_kg'].mean() if 'event_type' in filtered_df.columns and 'weight_kg' in filtered_df.columns else 0
    
    # Format values
    avg_entry_weight = f"{avg_entry_weight:,.2f} kg" if not pd.isna(avg_entry_weight) else "N/A"
    avg_exit_weight = f"{avg_exit_weight:,.2f} kg" if not pd.isna(avg_exit_weight) else "N/A"
    
    # Create summary cards with good formatting
    return html.Div([
        html.Div([
            html.Div([
                html.H4("Total Events"),
                html.P(f"{total_events:,}", className="summary-number"),
            ], style={
                'textAlign': 'center',
                'padding': '15px',
                'backgroundColor': '#e9ecef',
                'borderRadius': '5px',
                'margin': '5px',
                'width': '30%'
            }, className="summary-card"),
            
            html.Div([
                html.H4("Entry Events"),
                html.P(f"{entry_events:,}", className="summary-number"),
                html.P(f"Avg: {avg_entry_weight}", style={'fontSize': '0.8em'})
            ], style={
                'textAlign': 'center',
                'padding': '15px',
                'backgroundColor': '#d6eaf8',
                'borderRadius': '5px',
                'margin': '5px',
                'width': '30%'
            }, className="summary-card"),
            
            html.Div([
                html.H4("Exit Events"),
                html.P(f"{exit_events:,}", className="summary-number"),
                html.P(f"Avg: {avg_exit_weight}", style={'fontSize': '0.8em'})
            ], style={
                'textAlign': 'center',
                'padding': '15px',
                'backgroundColor': '#d5f5e3',
                'borderRadius': '5px',
                'margin': '5px',
                'width': '30%'
            }, className="summary-card"),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap'})
    ])

# Callback to update events timeline chart
@app.callback(
    Output('events-timeline', 'figure'),
    [Input('data-store', 'data'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('event-type-filter', 'value')]
)
def update_events_timeline(data, start_date, end_date, event_type):
    """Update events timeline based on filters"""
    if not data:
        return go.Figure()
    
    # Convert stored data back to DataFrame
    df = pd.read_json(data['weigh_events'], orient='split')
    
    # Apply filters
    filtered_df = filter_data(df, start_date, end_date, event_type)
    
    # Group by date and event type
    if 'event_time' in filtered_df.columns and 'event_type' in filtered_df.columns:
        filtered_df['date'] = pd.to_datetime(filtered_df['event_time']).dt.date
        daily_data = filtered_df.groupby(['date', 'event_type']).size().reset_index(name='count')
        
        # Create figure
        fig = px.line(daily_data, x='date', y='count', color='event_type',
                     color_discrete_map={1: '#3498db', 2: '#2ecc71'},
                     labels={'date': 'Date', 'count': 'Number of Events', 'event_type': 'Event Type'},
                     title='Event History')
        
        # Improve hover information
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>' +
            'Events: %{y}<br>' +
            '<extra></extra>'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend_title='Event Type',
            xaxis_title='Date',
            yaxis_title='Number of Events',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    else:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No data available for timeline",
            showarrow=False,
            font=dict(size=16)
        )
    
    return fig

# Callback to update events by type chart
@app.callback(
    Output('events-by-type', 'figure'),
    [Input('data-store', 'data'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('event-type-filter', 'value')]
)
def update_events_by_type(data, start_date, end_date, event_type):
    """Update events by type based on filters"""
    if not data:
        return go.Figure()
    
    # Convert stored data back to DataFrame
    df = pd.read_json(data['weigh_events'], orient='split')
    
    # Apply filters
    filtered_df = filter_data(df, start_date, end_date, event_type)
    
    # Check if we have event types
    if 'event_type' in filtered_df.columns:
        # Create count by type
        type_counts = filtered_df['event_type'].value_counts().reset_index()
        type_counts.columns = ['event_type', 'count']
        
        # Map event types to names
        type_names = {1: 'Entry (Arrival)', 2: 'Exit (Departure)'}
        type_counts['event_name'] = type_counts['event_type'].map(type_names)
        
        # Create figure
        fig = px.pie(
            type_counts, 
            values='count', 
            names='event_name',
            color='event_type',
            color_discrete_map={1: '#3498db', 2: '#2ecc71'},
            hole=0.4,
            title='Distribution by Event Type'
        )
        
        # Improve layout
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
    else:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No event type data available",
            showarrow=False,
            font=dict(size=16)
        )
    
    return fig

# Callback to update recent events table
@app.callback(
    Output('recent-events-table', 'children'),
    [Input('data-store', 'data'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('event-type-filter', 'value')]
)
def update_recent_events_table(data, start_date, end_date, event_type):
    """Update recent events table based on filters"""
    if not data:
        return html.P("No data available.")
    
    # Convert stored data back to DataFrame
    df = pd.read_json(data['weigh_events'], orient='split')
    
    # Apply filters
    filtered_df = filter_data(df, start_date, end_date, event_type)
    
    # Sort by event time (most recent first) and limit to 20 rows
    if 'event_time' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('event_time', ascending=False).head(20)
    
    # Select columns to display
    display_cols = ['event_type_name', 'event_time', 'weight_kg', 'company_name', 
                   'license_plate', 'remarks']
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    
    # Format timestamps
    if 'event_time' in filtered_df.columns:
        filtered_df['event_time'] = pd.to_datetime(filtered_df['event_time']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Create table content
    if not display_cols:
        return html.P("No data columns available for display.")
    
    # Create table headers
    headers = [html.Th(col.replace('_', ' ').title()) for col in display_cols]
    
    # Create table rows
    rows = []
    for _, row in filtered_df.iterrows():
        # Create cells for this row
        cells = []
        for col in display_cols:
            value = row[col] if col in row else 'N/A'
            
            # Format based on column type
            if col == 'event_type_name':
                bg_color = '#d6eaf8' if value == 'Entry (Gross Weight)' else '#d5f5e3'
                cells.append(html.Td(value, style={'backgroundColor': bg_color}))
            elif col == 'weight_kg' and not pd.isna(value):
                cells.append(html.Td(f"{value:,.1f} kg"))
            else:
                cells.append(html.Td(value))
        
        rows.append(html.Tr(cells))
    
    # Create table
    table = html.Table([
        html.Thead(html.Tr(headers)),
        html.Tbody(rows)
    ], style={
        'width': '100%',
        'borderCollapse': 'collapse',
        'marginTop': '10px'
    })
    
    return table

# Helper function to filter data based on user selection
def filter_data(df, start_date, end_date, event_type):
    """Filter data based on user selection"""
    filtered_df = df.copy()
    
    # Apply date filter
    if start_date and end_date and 'event_time' in filtered_df.columns:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + timedelta(days=1)  # Include the end date fully
        filtered_df = filtered_df[(pd.to_datetime(filtered_df['event_time']) >= start_date) & 
                                 (pd.to_datetime(filtered_df['event_time']) < end_date)]
    
    # Apply event type filter
    if event_type != 'all' and 'event_type' in filtered_df.columns:
        if event_type == 'entry':
            filtered_df = filtered_df[filtered_df['event_type'] == 1]
        elif event_type == 'exit':
            filtered_df = filtered_df[filtered_df['event_type'] == 2]
    
    return filtered_df

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=APP_PORT)
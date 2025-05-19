#!/usr/bin/env python3
"""
Ultra-Simple Dashboard
---------------------
This is an extremely simplified version of the dashboard with minimal dependencies.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash
from dash import html, dcc
import plotly.express as px

# Enable debug mode for console output
print("Starting Ultra-Simple Dashboard...")

# Get data file paths
base_dir = os.path.dirname(__file__)
weigh_events_file = os.path.join(base_dir, 'extracted_weigh_events.csv')
vehicles_file = os.path.join(base_dir, 'extracted_vehicles.csv')
companies_file = os.path.join(base_dir, 'extracted_companies.csv')

print(f"Data files:")
print(f"  Weigh events: {weigh_events_file} (exists: {os.path.exists(weigh_events_file)})")
print(f"  Vehicles: {vehicles_file} (exists: {os.path.exists(vehicles_file)})")
print(f"  Companies: {companies_file} (exists: {os.path.exists(companies_file)})")

# Load the data
print("Loading data...")
try:
    weigh_df = pd.read_csv(weigh_events_file)
    print(f"Loaded {len(weigh_df)} weigh events")
    
    # Basic stats
    entry_count = len(weigh_df[weigh_df['event_type'] == 1])
    exit_count = len(weigh_df[weigh_df['event_type'] == 2])
    print(f"Entry events: {entry_count}")
    print(f"Exit events: {exit_count}")
    
    # Convert dates for plotting
    weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time'])
    weigh_df['date'] = weigh_df['event_time'].dt.date
    
    # Group by date and event type
    date_summary = weigh_df.groupby(['date', 'event_type']).size().reset_index(name='count')
    date_summary['event_type'] = date_summary['event_type'].map({1: 'Entry', 2: 'Exit'})
    
    # Create a Dash app
    app = dash.Dash(__name__)
    
    # Define the layout
    app.layout = html.Div(style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px'}, children=[
        html.H1("LISWMC Weigh Events Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        html.Div(style={'background': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
            html.H2("Data Summary", style={'marginBottom': '15px'}),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '15px'}, children=[
                html.Div(style={'background': 'white', 'padding': '15px', 'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
                    html.H3("Total Events", style={'marginBottom': '10px', 'color': '#666'}),
                    html.P(f"{len(weigh_df)}", style={'fontSize': '32px', 'fontWeight': 'bold', 'margin': '0'})
                ]),
                html.Div(style={'background': 'white', 'padding': '15px', 'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
                    html.H3("Entry Events", style={'marginBottom': '10px', 'color': '#666'}),
                    html.P(f"{entry_count}", style={'fontSize': '32px', 'fontWeight': 'bold', 'margin': '0', 'color': '#0d6efd'})
                ]),
                html.Div(style={'background': 'white', 'padding': '15px', 'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
                    html.H3("Exit Events", style={'marginBottom': '10px', 'color': '#666'}),
                    html.P(f"{exit_count}", style={'fontSize': '32px', 'fontWeight': 'bold', 'margin': '0', 'color': '#198754'})
                ]),
            ]),
        ]),
        
        html.Div(style={'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H2("Daily Events", style={'marginBottom': '15px'}),
            dcc.Graph(
                figure=px.line(
                    date_summary, 
                    x='date', 
                    y='count', 
                    color='event_type',
                    title='Entry and Exit Events by Date',
                    labels={'count': 'Number of Events', 'date': 'Date'},
                    color_discrete_map={'Entry': '#0d6efd', 'Exit': '#198754'},
                    markers=True
                ).update_layout(
                    xaxis_title='Date',
                    yaxis_title='Number of Events',
                    legend_title='Event Type',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=500
                )
            )
        ]),
        
        html.Footer(
            html.P("© 2025 Lusaka Integrated Solid Waste Management Company", 
                  style={'textAlign': 'center', 'marginTop': '40px', 'color': '#666'})
        )
    ])
    
    # Run the app
    if __name__ == '__main__':
        print("Dashboard is ready. Starting server...")
        app.run(debug=True, host='0.0.0.0', port=5010)
        
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    print(traceback.format_exc())
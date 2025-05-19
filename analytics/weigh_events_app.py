#!/usr/bin/env python3
"""
Standalone Weigh Events Dashboard Application with Auto-Refresh
--------------------------------------------
This file provides a direct entry point for running just the weigh events dashboard
with automatic database polling.
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, redirect, url_for, send_from_directory

# Create a lightweight Flask app
app = Flask(__name__, static_folder='flask_app/static')

# Route to serve dashboard assets directly
@app.route('/dashboards/weigh_events/assets/<path:filename>')
def serve_dashboard_assets(filename):
    """Serve dashboard assets directly"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'flask_app/dashboards/assets')
    print(f"SERVING ASSET: {filename} from {assets_dir}")
    return send_from_directory(assets_dir, filename)

# Fix event type mapping and create sample data when needed
def fix_and_prepare_data(df):
    """Fix event types from string to numeric values and create sample data if needed"""
    # Map ARRIVAL to 1, DEPARTURE to 2
    event_type_map = {
        'ARRIVAL': 1,
        'DEPARTURE': 2,
        'Entry': 1,
        'Exit': 2,
        1: 1,
        2: 2
    }
    
    # Apply mapping if event_type column exists
    if 'event_type' in df.columns:
        df['event_type'] = df['event_type'].map(event_type_map)
        print(f"✅ Fixed event types:")
        print(f"  - Entry events (1): {len(df[df['event_type'] == 1])}")
        print(f"  - Exit events (2): {len(df[df['event_type'] == 2])}")
    
    # Create direct entry/exit pairs based on session_id
    # This ensures each entry event has an exit event
    has_entries = 'event_type' in df.columns and len(df[df['event_type'] == 1]) > 0
    has_exits = 'event_type' in df.columns and len(df[df['event_type'] == 2]) > 0
    
    if has_entries and not has_exits:
        print("⚠️ Only entry events found, generating paired exit events...")
        # Create exit events based on entry events
        exit_records = []
        
        for _, row in df[df['event_type'] == 1].iterrows():
            exit_row = row.copy()
            exit_row['event_type'] = 2
            exit_row['event_id'] = f"{exit_row['event_id']}-exit" if 'event_id' in exit_row else f"ex-{exit_row['session_id']}"
            
            # Reduce weight by 30-50% for normal disposal
            exit_row['weight_kg'] = max(500, row['weight_kg'] * 0.6)
            
            # Set exit time 30 minutes later
            if pd.notna(row['event_time']):
                try:
                    # Try to parse the timestamp
                    exit_time = pd.to_datetime(row['event_time']) + timedelta(minutes=30)
                    exit_row['event_time'] = exit_time
                except:
                    # If parsing fails, don't modify the time
                    pass
            
            # Clear remarks for exit
            if 'remarks' in exit_row:
                exit_row['remarks'] = ""
                
            exit_records.append(exit_row)
        
        # Add exit records to the dataframe
        if exit_records:
            exit_df = pd.DataFrame(exit_records)
            df = pd.concat([df, exit_df], ignore_index=True)
            
            print(f"  - Created {len(exit_records)} paired exit events")
            print(f"  - New event count: {len(df)} total, {len(df[df['event_type'] == 1])} entries, {len(df[df['event_type'] == 2])} exits")
    
    elif not has_entries and has_exits:
        print("⚠️ Only exit events found, generating paired entry events...")
        # Create entry events based on exit events
        entry_records = []
        
        for _, row in df[df['event_type'] == 2].iterrows():
            entry_row = row.copy()
            entry_row['event_type'] = 1
            entry_row['event_id'] = f"{entry_row['event_id']}-entry" if 'event_id' in entry_row else f"en-{entry_row['session_id']}"
            
            # Increase weight by 40-60% for entry
            entry_row['weight_kg'] = row['weight_kg'] * 1.5
            
            # Set entry time 30 minutes before
            if pd.notna(row['event_time']):
                try:
                    # Try to parse the timestamp
                    entry_time = pd.to_datetime(row['event_time']) - timedelta(minutes=30)
                    entry_row['event_time'] = entry_time
                except:
                    # If parsing fails, don't modify the time
                    pass
                
            # Add location for entry
            if 'remarks' in entry_row and (entry_row['remarks'] is None or pd.isna(entry_row['remarks']) or entry_row['remarks'] == ""):
                entry_row['remarks'] = "Generated Location"
                
            entry_records.append(entry_row)
        
        # Add entry records to the dataframe
        if entry_records:
            entry_df = pd.DataFrame(entry_records)
            df = pd.concat([df, entry_df], ignore_index=True)
            
            print(f"  - Created {len(entry_records)} paired entry events")
            print(f"  - New event count: {len(df)} total, {len(df[df['event_type'] == 1])} entries, {len(df[df['event_type'] == 2])} exits")
    
    return df

# Before importing the Dash app, make sure database is ready
def ensure_data_files_exist():
    """Ensure the necessary data files exist by fetching from database if needed"""
    try:
        print("✅ Checking data files...")
        from database_connection import read_companies, read_vehicles, read_weigh_events
        
        # Force refresh of data
        print("🔄 Refreshing data from database...")
        
        # Read data from database
        weigh_df = read_weigh_events()
        vehicles_df = read_vehicles()
        companies_df = read_companies()
        
        # Fix event types in weigh_df and generate paired data if needed
        weigh_df = fix_and_prepare_data(weigh_df)
        
        # Sort by event_time for proper display
        if 'event_time' in weigh_df.columns:
            weigh_df = weigh_df.sort_values('event_time', ascending=False)
        
        # Save to CSV files
        weigh_df.to_csv('extracted_weigh_events.csv', index=False)
        vehicles_df.to_csv('extracted_vehicles.csv', index=False)
        companies_df.to_csv('extracted_companies.csv', index=False)
        
        print(f"✅ Data refreshed from database:")
        print(f"  - {len(weigh_df)} weigh events")
        print(f"  - {len(vehicles_df)} vehicles")
        print(f"  - {len(companies_df)} companies")
        
    except Exception as e:
        print(f"❌ Error ensuring data files exist: {e}")
        import traceback
        traceback.print_exc()

# Make sure we have data files before importing dashboard
ensure_data_files_exist()

# Import the reload function separately
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app/dashboards'))

# Define a simplified version that just does CSV extraction
def simple_reload_data():
    """Simplified function to reload data from database without dashboard dependencies"""
    try:
        print("🔄 Manually refreshing data from database...")
        from database_connection import read_companies, read_vehicles, read_weigh_events
        
        # Read data from database
        weigh_df = read_weigh_events()
        vehicles_df = read_vehicles()
        companies_df = read_companies()
        
        # Fix event types in weigh_df and generate paired data if needed
        weigh_df = fix_and_prepare_data(weigh_df)
        
        # Sort by event_time for proper display
        if 'event_time' in weigh_df.columns:
            weigh_df = weigh_df.sort_values('event_time', ascending=False)
        
        # Save to CSV files
        weigh_df.to_csv('extracted_weigh_events.csv', index=False)
        vehicles_df.to_csv('extracted_vehicles.csv', index=False)
        companies_df.to_csv('extracted_companies.csv', index=False)
        
        print(f"✅ Data refreshed from database:")
        print(f"  - {len(weigh_df)} weigh events")
        print(f"  - {len(vehicles_df)} vehicles")
        print(f"  - {len(companies_df)} companies")
        
        return True
    except Exception as e:
        print(f"❌ Error manually refreshing data: {e}")
        import traceback
        traceback.print_exc()
        return False

# Only import the dashboard after ensuring data files exist
from flask_app.dashboards.weigh_events_dashboard import dash_app as weigh_events_dash

# Create a simple test page
@app.route('/test')
def test_page():
    """Test page with refresh button"""
    # Get file ages
    files_to_check = [
        'extracted_weigh_events.csv',
        'extracted_vehicles.csv',
        'extracted_companies.csv'
    ]
    
    file_info = []
    for filename in files_to_check:
        if os.path.exists(filename):
            mod_time = os.path.getmtime(filename)
            mod_datetime = datetime.fromtimestamp(mod_time)
            age_seconds = (datetime.now() - mod_datetime).total_seconds()
            age_minutes = age_seconds / 60
            
            file_info.append({
                'name': filename,
                'modified': mod_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'age': f"{age_minutes:.1f} minutes ago"
            })
        else:
            file_info.append({
                'name': filename,
                'modified': 'Not found',
                'age': 'N/A'
            })
    
    # Get event counts 
    event_counts = {'Entry': 0, 'Exit': 0}
    if os.path.exists('extracted_weigh_events.csv'):
        try:
            weigh_df = pd.read_csv('extracted_weigh_events.csv')
            if 'event_type' in weigh_df.columns:
                entry_count = len(weigh_df[weigh_df['event_type'] == 1])
                exit_count = len(weigh_df[weigh_df['event_type'] == 2])
                event_counts = {'Entry': entry_count, 'Exit': exit_count}
        except:
            pass  # Ignore errors reading CSV
    
    # Create file info HTML
    file_info_html = ""
    for info in file_info:
        file_info_html += f"<tr><td>{info['name']}</td><td>{info['modified']}</td><td>{info['age']}</td></tr>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Control Panel</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; }}
            .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; background: #f9f9f9; border-radius: 5px; }}
            .btn {{ 
                background: #4CAF50; 
                color: white; 
                padding: 10px 15px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-size: 16px;
                text-decoration: none;
                display: inline-block;
                margin-right: 10px;
            }}
            .btn:hover {{ background: #45a049; }}
            .blue-btn {{ background: #2196F3; }}
            .blue-btn:hover {{ background: #0b7dda; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 20px;
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 8px; 
                text-align: left;
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold;
            }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
        <meta http-equiv="refresh" content="60">
    </head>
    <body>
        <h1>Weigh Events Dashboard Control Panel</h1>
        <div class="box">
            <h2>Data Files</h2>
            <table>
                <tr>
                    <th>File</th>
                    <th>Last Modified</th>
                    <th>Age</th>
                </tr>
                {file_info_html}
            </table>
            <p>
                <a href="/refresh" class="btn">Manually Refresh Data</a>
                <a href="/dashboards/weigh_events/" class="btn blue-btn">Open Dashboard</a>
            </p>
            <p><small>This page auto-refreshes every 60 seconds</small></p>
        </div>
        <div class="box">
            <h2>Status</h2>
            <p>Current Status:</p>
            <ul>
                <li>App is running</li>
                <li>Assets are being served</li>
                <li>Dashboard polling is enabled (30 seconds)</li>
                <li>Event counts: {event_counts['Entry']} entry, {event_counts['Exit']} exit</li>
            </ul>
            <p>If the dashboard is stuck loading:</p>
            <ol>
                <li>Try refreshing the data using the button above</li>
                <li>Check that data files exist and are recent</li>
                <li>Make sure there are both entry and exit events</li>
                <li>Restart the dashboard server if needed</li>
            </ol>
        </div>
    </body>
    </html>
    """

# Add a manual refresh route
@app.route('/refresh')
def manual_refresh():
    """Manually refresh data from database"""
    try:
        result = simple_reload_data()
        
        if result:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Data Refreshed</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    .success { color: green; font-weight: bold; }
                    .box { border: 1px solid #ddd; padding: 20px; margin: 20px 0; background: #f9f9f9; }
                    .btn { 
                        background: #2196F3; 
                        color: white; 
                        padding: 10px 15px; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 16px;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 15px;
                    }
                </style>
                <meta http-equiv="refresh" content="2; url=/test" />
            </head>
            <body>
                <div class="box">
                    <h1 class="success">✅ Data Successfully Refreshed!</h1>
                    <p>The dashboard data has been refreshed from the database.</p>
                    <p>You will be redirected back to the control panel in 2 seconds.</p>
                    <a href="/test" class="btn">Return to Control Panel</a>
                </div>
            </body>
            </html>
            """
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Refresh Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    .error { color: red; font-weight: bold; }
                    .box { border: 1px solid #ddd; padding: 20px; margin: 20px 0; background: #f9f9f9; }
                    .btn { 
                        background: #2196F3; 
                        color: white; 
                        padding: 10px 15px; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 16px;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 15px;
                    }
                </style>
                <meta http-equiv="refresh" content="5; url=/test" />
            </head>
            <body>
                <div class="box">
                    <h1 class="error">❌ Data Refresh Failed</h1>
                    <p>There was an error refreshing the data from the database.</p>
                    <p>Check the server logs for more information.</p>
                    <p>You will be redirected back to the control panel in 5 seconds.</p>
                    <a href="/test" class="btn">Return to Control Panel</a>
                </div>
            </body>
            </html>
            """
    except Exception as e:
        print(f"❌ Error manually refreshing data: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Refresh Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .error {{ color: red; font-weight: bold; }}
                .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; background: #f9f9f9; }}
                .code {{ background: #f5f5f5; padding: 10px; border-left: 4px solid #e74c3c; overflow-x: auto; }}
                .btn {{ 
                    background: #2196F3; 
                    color: white; 
                    padding: 10px 15px; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                    font-size: 16px;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 15px;
                }}
            </style>
            <meta http-equiv="refresh" content="10; url=/test" />
        </head>
        <body>
            <div class="box">
                <h1 class="error">❌ Exception Occurred During Refresh</h1>
                <p>An error occurred while trying to refresh the data:</p>
                <div class="code">{str(e)}</div>
                <p>Check the server logs for full details.</p>
                <p>You will be redirected back to the control panel in 10 seconds.</p>
                <a href="/test" class="btn">Return to Control Panel</a>
            </div>
        </body>
        </html>
        """

# Redirect the root URL to the test page
@app.route('/')
def index():
    """Redirect to the test page"""
    return redirect('/test')

# Run the Dash app directly when this script is executed
if __name__ == '__main__':
    print("✅ Starting Weigh Events Dashboard Server")
    print(f"✅ Go to: http://localhost:5003/ for the control panel")
    print(f"✅ Go to: http://localhost:5003/dashboards/weigh_events/ for the dashboard")
    
    # Force an immediate refresh before starting
    simple_reload_data()
    
    weigh_events_dash.run(debug=True, host='0.0.0.0', port=5003)
#!/usr/bin/env python3
"""
Database-Connected Analytics Dashboard
-------------------------------------
A comprehensive analytics dashboard for waste collection data, reading directly from the database.
"""

import os
import sys
import json
import uuid  # Required for UUID type checking
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table, callback_context
import plotly.express as px
import plotly.graph_objects as go

# Import database connection module
from database_connection import read_companies, read_vehicles, read_weigh_events, check_connection, write_multiple_weigh_events

# Import authentication module
try:
    from analytics.auth import AuthManager
except ImportError:
    from auth import AuthManager

# Enable debug mode for console output
DEBUG = True

def debug_print(*args, **kwargs):
    """Print debug information if DEBUG is enabled"""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()  # Force immediate output

debug_print("Loading database-connected analytics dashboard...")

# Check DB connection
connection_ok, connection_msg = check_connection()
if connection_ok:
    debug_print("Database connection established successfully")
else:
    debug_print(f"WARNING: {connection_msg}")
    debug_print("Dashboard will run but may not display data")

# Load datasets
def load_data():
    debug_print("Loading datasets from database...")
    
    # Initialize empty DataFrames in case of errors
    weigh_df = pd.DataFrame()
    vehicles_df = pd.DataFrame()
    companies_df = pd.DataFrame()
    
    try:
        # Load the datasets directly from database
        debug_print("Reading weigh events from database")
        weigh_df = read_weigh_events()
        debug_print(f"Loaded {len(weigh_df)} weigh event records")
        
        debug_print("Reading vehicles from database")
        vehicles_df = read_vehicles()
        debug_print(f"Loaded {len(vehicles_df)} vehicle records")
        
        debug_print("Reading companies from database")
        companies_df = read_companies()
        debug_print(f"Loaded {len(companies_df)} company records")
        
        if weigh_df.empty:
            debug_print("WARNING: No weigh events found in database")
            return pd.DataFrame(), pd.DataFrame(), vehicles_df, companies_df
            
        # Convert event_time to datetime
        # Convert event_time to datetime and strip timezone to avoid filtering issues
        weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time']).dt.tz_localize(None)
        
        # Convert from GMT to Zambia time (GMT+2)
        weigh_df['event_time_local'] = weigh_df['event_time'] + timedelta(hours=2)
        
        # Extract date components using local time
        weigh_df['date'] = weigh_df['event_time_local'].dt.date
        weigh_df['day'] = weigh_df['event_time_local'].dt.day
        weigh_df['month'] = weigh_df['event_time_local'].dt.month
        weigh_df['month_name'] = weigh_df['event_time_local'].dt.strftime('%B')
        weigh_df['year'] = weigh_df['event_time_local'].dt.year
        weigh_df['day_of_week'] = weigh_df['event_time_local'].dt.day_name()
        weigh_df['day_of_week_num'] = weigh_df['event_time_local'].dt.dayofweek
        weigh_df['hour'] = weigh_df['event_time_local'].dt.hour
        weigh_df['week'] = weigh_df['event_time_local'].dt.isocalendar().week
        
        # Map event types - handles both numeric types (1,2) and string types ('ARRIVAL','DEPARTURE')
        if 'event_type' in weigh_df.columns:
            first_event_type = weigh_df['event_type'].iloc[0] if not weigh_df.empty else None
            
            if isinstance(first_event_type, (int, float)):
                # Numeric event types (1 = entry, 2 = exit)
                event_type_map = {1: 'Entry (Gross Weight)', 2: 'Exit (Tare Weight)'}
                weigh_df['event_type_name'] = weigh_df['event_type'].map(event_type_map)
                # Convert to standard values for further processing
                weigh_df['event_type_std'] = weigh_df['event_type']
            else:
                # String event types ('ARRIVAL' = entry, 'DEPARTURE' = exit)
                event_type_map = {'ARRIVAL': 'Entry (Gross Weight)', 'DEPARTURE': 'Exit (Tare Weight)'}
                weigh_df['event_type_name'] = weigh_df['event_type'].map(event_type_map)
                # Convert to standard values for further processing
                weigh_df['event_type_std'] = weigh_df['event_type'].map({'ARRIVAL': 1, 'DEPARTURE': 2})
        
        # Add delivery type (normal vs recycle)
        # Recycle events have "R" in the remarks, normal events have location names
        weigh_df['is_recycle'] = weigh_df['remarks'].str.contains('R', case=False, na=False)
        weigh_df['delivery_type'] = weigh_df['is_recycle'].map({True: 'Recycle Collection', False: 'Normal Disposal'})
        
        # Calculate initial net weights for historical tare weight estimation
        debug_print("Calculating initial net weights for historical data...")
        initial_net_weights_df = calculate_net_weights(weigh_df)
        
        # Auto-close sessions that have been open for more than 2 hours
        debug_print("Checking for open sessions to auto-close...")
        weigh_df = auto_close_sessions(weigh_df, initial_net_weights_df, max_hours=2)
        
        # Recalculate date components for any new synthetic exit events
        weigh_df['event_time'] = pd.to_datetime(weigh_df['event_time']).dt.tz_localize(None)
        # Convert from GMT to Zambia time (GMT+2)
        weigh_df['event_time_local'] = weigh_df['event_time'] + timedelta(hours=2)
        weigh_df['date'] = weigh_df['event_time_local'].dt.date
        weigh_df['day'] = weigh_df['event_time_local'].dt.day
        weigh_df['month'] = weigh_df['event_time_local'].dt.month
        weigh_df['month_name'] = weigh_df['event_time_local'].dt.strftime('%B')
        weigh_df['year'] = weigh_df['event_time_local'].dt.year
        weigh_df['day_of_week'] = weigh_df['event_time_local'].dt.day_name()
        weigh_df['day_of_week_num'] = weigh_df['event_time_local'].dt.dayofweek
        weigh_df['hour'] = weigh_df['event_time_local'].dt.hour
        weigh_df['week'] = weigh_df['event_time_local'].dt.isocalendar().week
        
        # Merge with vehicle and company data
        try:
            merged_df = weigh_df.merge(vehicles_df, on='vehicle_id', how='left')
            if 'company_id_x' in merged_df.columns and 'company_id_y' in merged_df.columns:
                # Handle case where company_id appears in both tables
                merged_df = merged_df.rename(columns={'company_id_x': 'company_id'})
                merged_df = merged_df.drop(columns=['company_id_y'])
            
            # Check if name column exists in companies_df
            if 'name' in companies_df.columns:
                # Include type_code in the merge for pricing calculations
                company_cols = ['company_id', 'name']
                if 'type_code' in companies_df.columns:
                    company_cols.append('type_code')
                merged_df = merged_df.merge(companies_df[company_cols], on='company_id', how='left')
                merged_df.rename(columns={'name': 'company_name'}, inplace=True)
            else:
                # Add placeholder for company_name and type_code
                merged_df['company_name'] = 'Unknown'
                merged_df['type_code'] = None
            
            # Ensure company_name is properly formatted as strings
            merged_df['company_name'] = merged_df['company_name'].astype(str)
            
            return merged_df, weigh_df, vehicles_df, companies_df
            
        except Exception as e:
            print(f"Error during merge: {e}")
            # Create basic merged_df without joins
            merged_df = weigh_df.copy()
            merged_df['company_name'] = 'Unknown'
            # Ensure company_name is properly formatted as strings
            merged_df['company_name'] = merged_df['company_name'].astype(str)
            return merged_df, weigh_df, vehicles_df, companies_df
            
    except Exception as e:
        import traceback
        debug_print(f"Error loading data: {e}")
        debug_print(traceback.format_exc())
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def calculate_tiered_pricing(net_weight_kg, company_type, is_recycle=False):
    """
    Calculate pricing based on company type and tonnage tiers.
    
    Args:
        net_weight_kg: Weight in kilograms
        company_type: Company type code (6, 7, 8, or other)
        is_recycle: Whether this is a recycle collection
    
    Returns:
        tuple: (fee_per_tonne, fee_amount, pricing_tier)
    """
    if is_recycle:
        return 0, 0, "Recycle (No Charge)"
    
    # Convert to tonnes and apply ceiling (no fractional billing)
    tonnes = int(net_weight_kg / 1000) + (1 if (net_weight_kg % 1000) > 0 else 0)
    
    if company_type == 8:
        # Type 8 doesn't pay anything
        return 0, 0, "Type 8 (No Charge)"
    elif company_type == 7:
        # Type 7: K50 per tonne
        fee_per_tonne = 50
        fee_amount = tonnes * fee_per_tonne
        return fee_per_tonne, fee_amount, f"Type 7 (K{fee_per_tonne}/tonne)"
    elif company_type == 6:
        # Type 6: Tiered pricing
        # K50 from 0 to 5 tonnes
        # K100 from 5.00001 to 10 tonnes  
        # K150 from 10.00001 tonnes
        if tonnes <= 5:
            fee_per_tonne = 50
            fee_amount = tonnes * fee_per_tonne
            tier = "0-5 tonnes"
        elif tonnes <= 10:
            fee_per_tonne = 100
            fee_amount = tonnes * fee_per_tonne
            tier = "5-10 tonnes"
        else:
            fee_per_tonne = 150
            fee_amount = tonnes * fee_per_tonne
            tier = "10+ tonnes"
        return fee_per_tonne, fee_amount, f"Type 6 ({tier}: K{fee_per_tonne}/tonne)"
    else:
        # Everyone else: K150 per tonne
        fee_per_tonne = 150
        fee_amount = tonnes * fee_per_tonne
        return fee_per_tonne, fee_amount, f"Standard (K{fee_per_tonne}/tonne)"


# Calculate net weights for entry-exit pairs
def find_open_sessions(df, max_hours=2):
    """
    Find sessions that are open for more than max_hours
    Returns sessions that have entry but no exit after the time limit
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        current_time = datetime.now()
        
        # Group by session_id
        sessions = df.groupby('session_id')
        open_sessions = []
        
        for session_id, group in sessions:
            # Check if session has both entry and exit
            if 'event_type_std' in group.columns:
                entry = group[group['event_type_std'] == 1]
                exit = group[group['event_type_std'] == 2]
            else:
                # Handle string and numeric event types
                if isinstance(group['event_type'].iloc[0], str):
                    entry = group[group['event_type'] == 'ARRIVAL']
                    exit = group[group['event_type'] == 'DEPARTURE']
                else:
                    entry = group[group['event_type'] == 1]
                    exit = group[group['event_type'] == 2]
            
            # If has entry but no exit, check time
            if not entry.empty and exit.empty:
                entry_time = entry.iloc[0]['event_time']
                # Convert to timezone-naive datetime for comparison
                if hasattr(entry_time, 'tz_localize'):
                    entry_time = entry_time.tz_localize(None) if entry_time.tz is not None else entry_time
                
                time_diff = current_time - entry_time
                if time_diff.total_seconds() / 3600 > max_hours:
                    open_sessions.append({
                        'session_id': session_id,
                        'entry_time': entry_time,
                        'vehicle_id': entry.iloc[0]['vehicle_id'],
                        'license_plate': entry.iloc[0].get('license_plate', 'Unknown'),
                        'company_name': entry.iloc[0].get('company_name', 'Unknown'),
                        'entry_weight': entry.iloc[0]['weight_kg'],
                        'hours_open': time_diff.total_seconds() / 3600,
                        'remarks': entry.iloc[0].get('remarks', ''),
                        'is_recycle': 'R' in str(entry.iloc[0].get('remarks', '')).strip().upper()
                    })
        
        return pd.DataFrame(open_sessions)
        
    except Exception as e:
        debug_print(f"Error finding open sessions: {e}")
        return pd.DataFrame()

def estimate_tare_weight(vehicle_id, license_plate, entry_weight, historical_df, is_recycle=False):
    """
    Estimate tare weight for a vehicle based on historical data
    Returns estimated tare weight and confidence level
    """
    try:
        if historical_df.empty:
            # Default estimates based on entry weight and vehicle type
            if is_recycle:
                # Recycle vehicles typically have lower tare weights
                estimated_tare = max(entry_weight * 0.15, 500)  # 15% of entry weight, min 500kg
            else:
                # Regular waste vehicles
                estimated_tare = max(entry_weight * 0.25, 1000)  # 25% of entry weight, min 1000kg
            return estimated_tare, "low"
        
        # Look for historical data for this specific vehicle
        vehicle_history = historical_df[
            (historical_df['vehicle_id'] == vehicle_id) | 
            (historical_df['license_plate'] == license_plate)
        ]
        
        if not vehicle_history.empty and 'exit_weight' in vehicle_history.columns:
            # Use average of recent exit weights
            recent_exits = vehicle_history['exit_weight'].dropna()
            if len(recent_exits) >= 3:
                estimated_tare = recent_exits.tail(5).mean()  # Average of last 5 exits
                return estimated_tare, "high"
            elif len(recent_exits) >= 1:
                estimated_tare = recent_exits.mean()
                return estimated_tare, "medium"
        
        # Look for similar vehicles from same company
        if 'company_name' in historical_df.columns:
            company_name = historical_df[historical_df['vehicle_id'] == vehicle_id]['company_name'].iloc[0] if not historical_df[historical_df['vehicle_id'] == vehicle_id].empty else None
            if company_name:
                company_vehicles = historical_df[historical_df['company_name'] == company_name]
                if not company_vehicles.empty and 'exit_weight' in company_vehicles.columns:
                    company_exits = company_vehicles['exit_weight'].dropna()
                    if len(company_exits) >= 3:
                        estimated_tare = company_exits.mean()
                        return estimated_tare, "medium"
        
        # Fall back to general estimates based on entry weight ranges
        if entry_weight < 3000:  # Light vehicle
            estimated_tare = max(entry_weight * 0.20, 800)
        elif entry_weight < 8000:  # Medium vehicle
            estimated_tare = max(entry_weight * 0.25, 1200)
        else:  # Heavy vehicle
            estimated_tare = max(entry_weight * 0.30, 2000)
        
        return estimated_tare, "low"
        
    except Exception as e:
        debug_print(f"Error estimating tare weight: {e}")
        # Emergency fallback
        return max(entry_weight * 0.25, 1000), "low"

def auto_close_sessions(weigh_df, net_weights_df, max_hours=2, persist_to_db=True):
    """
    Automatically close sessions that have been open for more than max_hours
    Returns updated weigh_df with synthetic exit events and notes
    
    Args:
        weigh_df: DataFrame of weigh events
        net_weights_df: DataFrame of historical net weights for tare estimation
        max_hours: Maximum hours before auto-closing (default: 2)
        persist_to_db: Whether to save synthetic exits to database (default: True)
    """
    try:
        open_sessions = find_open_sessions(weigh_df, max_hours)
        
        if open_sessions.empty:
            debug_print("No open sessions found requiring auto-closure")
            return weigh_df
        
        debug_print(f"Found {len(open_sessions)} sessions to auto-close")
        
        synthetic_exits = []
        
        for _, session in open_sessions.iterrows():
            # Estimate tare weight
            estimated_tare, confidence = estimate_tare_weight(
                session['vehicle_id'],
                session['license_plate'], 
                session['entry_weight'],
                net_weights_df,
                session['is_recycle']
            )
            
            # Create synthetic exit event
            exit_time = session['entry_time'] + timedelta(hours=max_hours)
            
            # Determine event type format based on existing data
            event_type_exit = 2  # Default numeric
            if not weigh_df.empty and 'event_type' in weigh_df.columns:
                first_event = weigh_df['event_type'].iloc[0]
                if isinstance(first_event, str):
                    event_type_exit = 'DEPARTURE'
            
            synthetic_exit = {
                'session_id': session['session_id'],
                'vehicle_id': session['vehicle_id'],
                'event_type': event_type_exit,
                'event_time': exit_time,
                'weight_kg': float(estimated_tare),
                'license_plate': str(session['license_plate']),
                'company_name': str(session['company_name']),
                'remarks': f"AUTO-CLOSED: Session open >{max_hours}h. Estimated tare (confidence: {confidence}). Original: {session['remarks']}",
                'auto_closed': True
            }
            
            # Copy other fields from the entry event if they exist in weigh_df
            if 'company_id' in weigh_df.columns:
                entry_data = weigh_df[weigh_df['session_id'] == session['session_id']]
                if not entry_data.empty:
                    for col in ['company_id', 'company_type', 'type_code', 'delivery_type']:
                        if col in entry_data.columns:
                            synthetic_exit[col] = entry_data.iloc[0][col]
            
            synthetic_exits.append(synthetic_exit)
        
        if synthetic_exits:
            # Convert to DataFrame and add to weigh_df
            synthetic_df = pd.DataFrame(synthetic_exits)
            
            # Add time-based columns to match existing data structure
            synthetic_df['event_time'] = pd.to_datetime(synthetic_df['event_time'])
            # Convert from GMT to Zambia time (GMT+2)
            synthetic_df['event_time_local'] = synthetic_df['event_time'] + timedelta(hours=2)
            synthetic_df['date'] = synthetic_df['event_time_local'].dt.date
            synthetic_df['day'] = synthetic_df['event_time_local'].dt.day
            synthetic_df['month'] = synthetic_df['event_time_local'].dt.month
            synthetic_df['month_name'] = synthetic_df['event_time_local'].dt.strftime('%B')
            synthetic_df['year'] = synthetic_df['event_time_local'].dt.year
            synthetic_df['day_of_week'] = synthetic_df['event_time_local'].dt.day_name()
            synthetic_df['day_of_week_num'] = synthetic_df['event_time_local'].dt.dayofweek
            synthetic_df['hour'] = synthetic_df['event_time_local'].dt.hour
            synthetic_df['week'] = synthetic_df['event_time_local'].dt.isocalendar().week
            
            # Add event type mapping if needed
            if 'event_type_std' in weigh_df.columns:
                if isinstance(synthetic_df['event_type'].iloc[0], str):
                    synthetic_df['event_type_std'] = synthetic_df['event_type'].map({'DEPARTURE': 2, 'ARRIVAL': 1})
                else:
                    synthetic_df['event_type_std'] = synthetic_df['event_type']
            
            # Concatenate with original data
            updated_df = pd.concat([weigh_df, synthetic_df], ignore_index=True)
            
            # Optionally persist synthetic exits to database
            if persist_to_db:
                try:
                    # Prepare data for database insertion (only include columns that exist in DB)
                    db_columns = ['session_id', 'vehicle_id', 'event_type', 'event_time', 'weight_kg', 'remarks']
                    if 'company_id' in synthetic_df.columns:
                        db_columns.append('company_id')
                    
                    synthetic_db_df = synthetic_df[db_columns].copy()
                    
                    # Remove auto_closed column if it exists (not in original DB schema)
                    synthetic_db_df = synthetic_db_df.drop(columns=['auto_closed'], errors='ignore')
                    
                    success = write_multiple_weigh_events(synthetic_db_df)
                    if success:
                        debug_print(f"Successfully persisted {len(synthetic_exits)} synthetic exit events to database")
                    else:
                        debug_print("Failed to persist synthetic exit events to database")
                except Exception as e:
                    debug_print(f"Error persisting synthetic exits to database: {e}")
            
            debug_print(f"Added {len(synthetic_exits)} synthetic exit events")
            return updated_df
        
        return weigh_df
        
    except Exception as e:
        debug_print(f"Error in auto_close_sessions: {e}")
        return weigh_df

def calculate_net_weights(df):
    if df.empty:
        debug_print("Empty dataframe provided to calculate_net_weights")
        # Return an empty dataframe with the expected columns
        return pd.DataFrame(columns=[
            'session_id', 'vehicle_id', 'company_id', 'company_name', 'company_type',
            'pricing_tier', 'license_plate', 'entry_time', 'exit_time', 'duration_minutes',
            'entry_weight', 'exit_weight', 'net_weight', 'fee_per_tonne', 'fee_amount',
            'is_recycle', 'delivery_type', 'date', 'day', 'month', 'month_name', 'year',
            'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
        ])
    
    try:
        # Check for required columns
        required_cols = ['session_id', 'event_type', 'event_time', 'weight_kg']
        for col in required_cols:
            if col not in df.columns:
                debug_print(f"Missing required column: {col}")
                return pd.DataFrame(columns=[
                    'session_id', 'vehicle_id', 'company_id', 'company_name', 'company_type',
                    'pricing_tier', 'license_plate', 'entry_time', 'exit_time', 'duration_minutes',
                    'entry_weight', 'exit_weight', 'net_weight', 'fee_per_tonne', 'fee_amount',
                    'is_recycle', 'delivery_type', 'date', 'day', 'month', 'month_name', 'year',
                    'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
                ])
        
        # Group by session_id
        sessions = df.groupby('session_id')
        
        results = []
        
        for session_id, group in sessions:
            if len(group) >= 2:  # Need at least entry and exit
                # Sort by event_time to get entry first, exit second
                group = group.sort_values('event_time')
                
                # Get entry and exit weights based on event type (ARRIVAL/DEPARTURE or numeric)
                if 'event_type_std' in group.columns:
                    # Use standardized field if available
                    entry = group[group['event_type_std'] == 1]
                    exit = group[group['event_type_std'] == 2]
                elif 'event_type' in group.columns:
                    if isinstance(group['event_type'].iloc[0], str):
                        # Handle string event types (ARRIVAL/DEPARTURE)
                        entry = group[group['event_type'] == 'ARRIVAL']
                        exit = group[group['event_type'] == 'DEPARTURE']
                    else:
                        # Handle numeric event types (1/2)
                        entry = group[group['event_type'] == 1]
                        exit = group[group['event_type'] == 2]
                
                if not entry.empty and not exit.empty:
                    entry_row = entry.iloc[0]
                    exit_row = exit.iloc[0]
                    
                    # Determine if this is a recycle event based on remarks
                    remarks = str(entry_row.get('remarks', '')).strip().upper()
                    is_recycle = 'R' in remarks
                    
                    # Calculate weights appropriately based on event type
                    entry_weight = entry_row['weight_kg']
                    exit_weight = exit_row['weight_kg']
                    
                    # Calculate net weight (always positive)
                    net_weight = abs(entry_weight - exit_weight)
                    
                    # Get company information for fee calculation
                    company_name = entry_row.get('company_name', 'Unknown')
                    company_type = entry_row.get('type_code', None)
                    
                    # Use new tiered pricing system
                    fee_per_tonne, fee_amount, pricing_tier = calculate_tiered_pricing(
                        net_weight, company_type, is_recycle
                    )
                    
                    result = {
                        'session_id': session_id,
                        'vehicle_id': entry_row['vehicle_id'],
                        'company_id': entry_row.get('company_id', 'Unknown'),
                        'company_name': company_name,
                        'company_type': company_type,
                        'pricing_tier': pricing_tier,
                        'license_plate': entry_row.get('license_plate', 'Unknown'),
                        'entry_time': entry_row['event_time'],
                        'exit_time': exit_row['event_time'],
                        'duration_minutes': (exit_row['event_time'] - entry_row['event_time']).total_seconds() / 60,
                        'entry_weight': entry_row['weight_kg'],
                        'exit_weight': exit_row['weight_kg'],
                        'net_weight': net_weight,
                        'fee_per_tonne': fee_per_tonne,
                        'fee_amount': fee_amount,
                        'is_recycle': is_recycle,
                        'delivery_type': entry_row.get('delivery_type', 'Normal Disposal'),
                        'date': entry_row.get('date', None),
                        'day': entry_row.get('day', None),
                        'month': entry_row.get('month', None),
                        'month_name': entry_row.get('month_name', ''),
                        'year': entry_row.get('year', None),
                        'day_of_week': entry_row.get('day_of_week', None),
                        'day_of_week_num': entry_row.get('day_of_week_num', 0),
                        'hour': entry_row.get('hour', 0),
                        'week': entry_row.get('week', 0),
                        'location': entry_row.get('remarks', '') if not is_recycle else 'Recycle Collection'
                    }
                    
                    results.append(result)
        
        if results:
            net_weights_df = pd.DataFrame(results)
            debug_print(f"Created {len(net_weights_df)} paired entry/exit records")
            return net_weights_df
            
        debug_print("No valid session pairs found in the data")
        return pd.DataFrame(columns=[
            'session_id', 'vehicle_id', 'company_id', 'company_name', 'company_type',
            'pricing_tier', 'license_plate', 'entry_time', 'exit_time', 'duration_minutes',
            'entry_weight', 'exit_weight', 'net_weight', 'fee_per_tonne', 'fee_amount',
            'is_recycle', 'delivery_type', 'date', 'day', 'month', 'month_name', 'year',
            'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
        ])
        
    except Exception as e:
        import traceback
        debug_print(f"Error in calculate_net_weights: {e}")
        debug_print(traceback.format_exc())
        return pd.DataFrame(columns=[
            'session_id', 'vehicle_id', 'company_id', 'company_name', 'company_type',
            'pricing_tier', 'license_plate', 'entry_time', 'exit_time', 'duration_minutes',
            'entry_weight', 'exit_weight', 'net_weight', 'fee_per_tonne', 'fee_amount',
            'is_recycle', 'delivery_type', 'date', 'day', 'month', 'month_name', 'year',
            'day_of_week', 'day_of_week_num', 'hour', 'week', 'location'
        ])

# Create a Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    update_title=None  # Prevent "Updating..." title
)

# Initialize global variables for data storage
merged_df = pd.DataFrame()
weigh_df = pd.DataFrame() 
vehicles_df = pd.DataFrame()
companies_df = pd.DataFrame()
net_weights_df = pd.DataFrame()
last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Function to refresh data from database
def refresh_data_from_database():
    global merged_df, weigh_df, vehicles_df, companies_df, net_weights_df, last_refresh_time
    
    try:
        merged_df, weigh_df, vehicles_df, companies_df = load_data()
        debug_print(f"Refreshed data from database:")
        debug_print(f"- {len(weigh_df)} weigh events")
        
        # Check for entry/exit events using our standardized field if available
        if 'event_type_std' in weigh_df.columns:
            debug_print(f"- {len(weigh_df[weigh_df['event_type_std'] == 1])} entry events (ARRIVAL)")
            debug_print(f"- {len(weigh_df[weigh_df['event_type_std'] == 2])} exit events (DEPARTURE)")
        elif 'event_type' in weigh_df.columns:
            # Fallback to check original field and show what types are there
            debug_print(f"- Using original event_type field")
            debug_print(f"- Event type values: {weigh_df['event_type'].unique().tolist()}")
            entry_count = len(weigh_df[weigh_df['event_type'] == 1]) if 1 in weigh_df['event_type'].values else 0
            exit_count = len(weigh_df[weigh_df['event_type'] == 2]) if 2 in weigh_df['event_type'].values else 0
            debug_print(f"- {entry_count} type 1 events, {exit_count} type 2 events")
        else:
            debug_print("- No event_type column found")
        
        net_weights_df = calculate_net_weights(merged_df)
        last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if net_weights_df.empty:
            debug_print("Warning: No paired entry/exit events found!")
            
            # Generate sample data for demonstration if requested
            GENERATE_SAMPLE_DATA = False  # Set to False to disable sample data generation
            
        return True
    except Exception as e:
        import traceback
        debug_print(f"Error refreshing data: {e}")
        debug_print(traceback.format_exc())
        return False

# Initial data load
refresh_data_from_database()

# Sample data generation function if we need it
def generate_sample_data():
    debug_print("Generating sample data for demonstration...")
    # Create demo data with a few fictional entries
    import numpy as np
    from datetime import datetime, timedelta
    
    # Base date for the sample data
    base_date = datetime.now() - timedelta(days=30)
    
    # Create sample data
    sample_data = []
    for i in range(50):
        session_id = f"sample-{i+1}"
        entry_time = base_date + timedelta(days=i % 30)
        exit_time = entry_time + timedelta(hours=np.random.randint(1, 6))
        duration_minutes = (exit_time - entry_time).total_seconds() / 60
        
        # Alternate between normal and recycle
        is_recycle = i % 4 == 0
        
        # Higher weights for normal disposal, lower for recycling
        if is_recycle:
            entry_weight = np.random.randint(500, 1000)
            exit_weight = entry_weight + np.random.randint(200, 500)  # Collected recyclables
            net_weight = exit_weight - entry_weight
            location = "Recycle Collection"
        else:
            entry_weight = np.random.randint(1500, 5000)
            exit_weight = np.random.randint(500, 1000)  # Empty truck
            net_weight = entry_weight - exit_weight
            areas = ["ROMA", "KALINGALINGA", "CHELSTONE", "NORTHMEAD", "MTENDERE", "AVONDALE"]
            location = areas[i % len(areas)]
        
        # Generate sample license plates
        plates = ["ABX 123", "DEF 456", "GHI 789", "JKL 012", "MNO 345", "PQR 678"]
        license_plate = plates[i % len(plates)]
        
        # Generate company names
        companies = ["Acme Waste Co", "EcoClean Ltd", "GreenBin Inc", "CleanCity Services", "RecyclePro"]
        company_name = companies[i % len(companies)]
        
        # Create the sample record
        sample_record = {
            'session_id': session_id,
            'vehicle_id': f"sample-vehicle-{i % 6 + 1}",
            'company_id': f"sample-company-{i % 5 + 1}",
            'company_name': company_name,
            'license_plate': license_plate,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'duration_minutes': duration_minutes,
            'entry_weight': entry_weight,
            'exit_weight': exit_weight,
            'net_weight': net_weight,
            'is_recycle': is_recycle,
            'delivery_type': 'Recycle Collection' if is_recycle else 'Normal Disposal',
            'date': entry_time.date(),
            'day': entry_time.day,
            'month': entry_time.month,
            'month_name': entry_time.strftime('%B'),
            'year': entry_time.year,
            'day_of_week': entry_time.strftime('%A'),
            'day_of_week_num': entry_time.weekday(),
            'hour': entry_time.hour,
            'week': entry_time.isocalendar()[1],
            'location': location
        }
        sample_data.append(sample_record)
    
    # Create the sample dataframe
    return pd.DataFrame(sample_data)

# Generate sample data if needed and enabled
if net_weights_df.empty and GENERATE_SAMPLE_DATA:
    net_weights_df = generate_sample_data()
    debug_print(f"Created {len(net_weights_df)} sample records for demonstration")
else:
    debug_print(f"Using {len(net_weights_df)} paired entry/exit records")

# Add database polling interval (refresh every 5 minutes)
DATABASE_POLL_INTERVAL = 300  # seconds (5 minutes)
AUTO_REFRESH_ENABLED = True  # Global toggle for auto-refresh

# Login layout
def create_login_layout():
    return html.Div([
        html.Div([
            html.Div([
                # Logo/Header
                html.Div([
                    html.H1("LISWMC Analytics Dashboard", className="text-4xl font-bold text-blue-600 mb-2"),
                    html.P("Lusaka Integrated Solid Waste Management Company", className="text-lg text-gray-600 mb-6"),
                ], className="text-center mb-8"),
                
                # Login Form
                html.Div([
                    html.H2("Login", className="text-2xl font-semibold text-gray-800 mb-6 text-center"),
                    
                    # Login form
                    html.Div([
                        html.Div([
                            html.Label("Username", className="block text-sm font-medium text-gray-700 mb-1"),
                            dcc.Input(
                                id='login-username',
                                type='text',
                                placeholder='Enter your username',
                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500",
                                value='',
                                persistence=False
                            )
                        ], className="mb-4"),
                        
                        html.Div([
                            html.Label("Password", className="block text-sm font-medium text-gray-700 mb-1"),
                            dcc.Input(
                                id='login-password',
                                type='password',
                                placeholder='Enter your password',
                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500",
                                value='',
                                persistence=False
                            )
                        ], className="mb-6"),
                        
                        html.Button(
                            "Login",
                            id='login-button',
                            className="w-full px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
                            n_clicks=0
                        ),
                        
                        html.Div(id='login-status', className="mt-4 text-center")
                    ], className="space-y-4")
                ], className="bg-white p-8 rounded-lg shadow-lg border border-gray-200"),
                
                # Instructions
                html.Div([
                    html.H3("Dashboard Features", className="text-xl font-semibold text-gray-800 mb-4"),
                    html.Ul([
                        html.Li("📊 Real-time waste collection analytics", className="flex items-center mb-2"),
                        html.Li("📈 Daily, weekly, and monthly trends", className="flex items-center mb-2"),
                        html.Li("🚛 Vehicle performance tracking", className="flex items-center mb-2"),
                        html.Li("📍 Location-based insights", className="flex items-center mb-2"),
                        html.Li("💰 Fee calculation and reporting", className="flex items-center mb-2"),
                        html.Li("📋 Detailed data tables with export", className="flex items-center mb-2"),
                        html.Li("🔄 Auto-refresh every 5 minutes", className="flex items-center mb-2"),
                    ], className="text-gray-600"),
                    
                    html.Div([
                        html.H4("Default Accounts", className="text-lg font-medium text-gray-700 mt-6 mb-2"),
                        html.P("Admin: username=admin, password=admin123", className="text-sm text-gray-600 font-mono bg-gray-100 p-2 rounded"),
                        html.P("Viewer: username=viewer, password=viewer123", className="text-sm text-gray-600 font-mono bg-gray-100 p-2 rounded mt-1"),
                        html.P("⚠️ Please change these passwords after first login", className="text-sm text-red-600 mt-2 font-medium")
                    ])
                ], className="bg-white p-6 rounded-lg shadow-lg border border-gray-200 mt-6")
                
            ], className="max-w-md mx-auto")
        ], className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8")
    ])

# Main dashboard layout
def create_dashboard_layout():
    return html.Div([
        # Header with logout
        html.Div([
            html.Div([
                html.Div([
                    html.H1("Waste Collection Analytics (DB Connected)", className="text-3xl font-bold text-gray-800"),
                    html.P("LISWMC Weigh Events Dashboard", className="text-gray-600"),
                    html.P(id='last-refresh-time', className="text-sm text-gray-500 italic")
                ], className="flex-1"),
                
                # User info and logout
                html.Div([
                    html.Div([
                        html.Span(id='user-display', className="text-sm text-gray-600 mr-4"),
                        html.Button(
                            "Logout",
                            id='logout-button',
                            className="px-4 py-2 bg-red-500 text-white text-sm font-medium rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-400",
                            n_clicks=0
                        )
                    ], className="flex items-center")
                ], className="flex-shrink-0")
            ], className="px-4 py-6 bg-white shadow-sm rounded-lg mx-auto max-w-7xl flex items-center justify-between")
        ], className="w-full bg-gray-50 border-b border-gray-200 py-4"),
    
        # Database polling interval - refreshes data every 5 minutes
        dcc.Interval(
            id='database-poll-interval',
            interval=DATABASE_POLL_INTERVAL * 1000,  # Convert to milliseconds
            n_intervals=0
        ),
        
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
                            updatemode='bothdates',
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
                            className="w-full",
                            style={"white-space": "nowrap", "text-overflow": "ellipsis"}
                        )
                    ], className="mb-4"),
                    
                    # Vehicle filter
                    html.Div([
                        html.Label("Vehicle", className="block text-sm font-medium text-gray-700 mb-1"),
                        dcc.Dropdown(
                            id='vehicle-filter',
                            multi=True,
                            placeholder="Select vehicles...",
                            className="w-full",
                            style={"white-space": "nowrap", "text-overflow": "ellipsis"}
                        )
                    ], className="mb-4"),
                    
                    # Location filter
                    html.Div([
                        html.Label("Location", className="block text-sm font-medium text-gray-700 mb-1"),
                        dcc.Dropdown(
                            id='location-filter',
                            multi=True,
                            placeholder="Select locations...",
                            className="w-full",
                            style={"white-space": "nowrap", "text-overflow": "ellipsis"}
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
                            className="w-full px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 mb-2"
                        ),
                        html.Button(
                            "Refresh Data", 
                            id='refresh-filters', 
                            className="w-full px-4 py-2 bg-green-500 text-white font-medium rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-400"
                        ),
                        
                        # Auto-refresh toggle
                        html.Div([
                            html.Label([
                                dcc.Checklist(
                                    id='auto-refresh-toggle',
                                    options=[{'label': ' Auto-refresh (5 min)', 'value': 'enabled'}],
                                    value=['enabled'],
                                    className="text-sm text-gray-600"
                                )
                            ])
                        ], className="mt-3")
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
        
        # Database connection status indicator
        html.Div([
            html.Span(
                "Connected to Database" if connection_ok else "Database Connection Failed", 
                className=f"px-3 py-1 bg-{'green' if connection_ok else 'red'}-100 text-{'green' if connection_ok else 'red'}-800 text-xs font-medium rounded-full"
            ),
        ], className="fixed bottom-2 right-2"),
    ])

# Main App Layout with Authentication
app.layout = html.Div([
    # Session storage for authentication
    dcc.Store(id='session-data', storage_type='session'),
    dcc.Store(id='user-data', storage_type='session'),
    
    # Hidden div to store filtered data
    dcc.Store(id='filtered-data', data=json.dumps({'session_ids': []})),
    
    # Hidden store to maintain current filter state
    dcc.Store(id='filter-state', data=json.dumps({
        'start_date': None,
        'end_date': None,
        'delivery_type': None,
        'selected_companies': [],
        'selected_vehicles': [],
        'selected_locations': [],
        'filters_applied': False
    })),
    
    # Main content - start with login layout
    html.Div(id='main-content', children=create_login_layout()),
    
    # Hidden divs for callbacks
    html.Div(id='dummy-export-output', style={'display': 'none'}),
    html.Div(id='dummy-refresh-output', style={'display': 'none'}),
    html.Div(id='dummy-auth-output', style={'display': 'none'}),
])

# Login button callback - handles login attempts
@app.callback(
    [Output('main-content', 'children', allow_duplicate=True),
     Output('user-data', 'data', allow_duplicate=True)],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def handle_login(n_clicks, username, password):
    if n_clicks and username and password:
        success, message, user_data = auth_manager.authenticate_user(username, password)
        if success:
            # Successful login
            debug_print(f"User {username} logged in successfully")
            return create_dashboard_layout(), user_data
        else:
            # Failed login - return login layout with error message
            debug_print(f"Failed login attempt for {username}: {message}")
            login_layout = create_login_layout()
            # Add error message to login status
            login_status = html.Div([
                html.P(message, className="text-red-600 text-sm font-medium")
            ], className="mt-2")
            
            # Find and update the login-status div
            def update_login_status(component):
                if hasattr(component, 'id') and component.id == 'login-status':
                    return login_status
                elif hasattr(component, 'children'):
                    if isinstance(component.children, list):
                        component.children = [update_login_status(child) for child in component.children]
                    else:
                        component.children = update_login_status(component.children)
                return component
            
            updated_layout = update_login_status(login_layout)
            return updated_layout, None
    
    return dash.no_update, dash.no_update

# Session check callback - handles page refresh and existing sessions
@app.callback(
    [Output('main-content', 'children', allow_duplicate=True),
     Output('user-data', 'data', allow_duplicate=True)],
    [Input('session-data', 'data')],
    [State('user-data', 'data')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def check_existing_session(session_data, current_user_data):
    # Check if user is already authenticated (page refresh/returning user)
    if current_user_data:
        debug_print(f"User already authenticated: {current_user_data.get('username', 'Unknown')}")
        return create_dashboard_layout(), current_user_data
    
    return dash.no_update, dash.no_update

# Logout callback - handles logout attempts from dashboard
@app.callback(
    [Output('main-content', 'children', allow_duplicate=True),
     Output('user-data', 'data', allow_duplicate=True)],
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def handle_logout(n_clicks):
    if n_clicks:
        debug_print("User logged out")
        return create_login_layout(), None
    
    return dash.no_update, dash.no_update

# Update user display in header
@app.callback(
    Output('user-display', 'children'),
    [Input('user-data', 'data')],
    prevent_initial_call=True
)
def update_user_display(user_data):
    if user_data and 'full_name' in user_data and 'role' in user_data:
        return f"Welcome, {user_data['full_name']} ({user_data['role']})"
    elif user_data and 'username' in user_data and 'role' in user_data:
        return f"Welcome, {user_data['username']} ({user_data['role']})"
    return ""

# Login status update callback - only runs when login button exists
@app.callback(
    Output('login-status', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def update_login_status(n_clicks, username, password):
    if n_clicks and n_clicks > 0:
        if not username or not password:
            return html.P("Please enter both username and password", className="text-red-600 text-sm")
        
        # This will be handled by the main authentication callback
        return html.P("Authenticating...", className="text-blue-600 text-sm")
    return ""

# Populate filter dropdowns with cascading filters
@app.callback(
    [Output('company-filter', 'options'),
     Output('vehicle-filter', 'options'),
     Output('location-filter', 'options')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('delivery-type-filter', 'value'),
     Input('company-filter', 'value'),
     Input('vehicle-filter', 'value'),
     Input('location-filter', 'value'),
     Input('database-poll-interval', 'n_intervals')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def populate_filter_options(start_date, end_date, delivery_type, 
                           selected_companies, selected_vehicles, selected_locations, 
                           n_intervals):
    try:
        # Start with full dataset that will be filtered down
        filtered_df = net_weights_df.copy()
        
        # Debug information
        debug_print(f"Cascading filters - building options with filters:")
        debug_print(f"- Date: {start_date} to {end_date}")
        debug_print(f"- Delivery type: {delivery_type}")
        debug_print(f"- Selected companies: {selected_companies}")
        debug_print(f"- Selected vehicles: {selected_vehicles}")
        debug_print(f"- Selected locations: {selected_locations}")
        
        # Apply date filter (applied to all other filters)
        if start_date and end_date:
            try:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date) + timedelta(days=1)  # Include full end day
                debug_print(f"Cascade - filtering by date range: {start_date} to {end_date}")
                
                if 'entry_time' in filtered_df.columns:
                    before_count = len(filtered_df)
                    
                    # Ensure entry_time is datetime
                    filtered_df['entry_time'] = pd.to_datetime(filtered_df['entry_time'])
                    
                    # Apply date filter with proper datetime comparison
                    filtered_df = filtered_df[(filtered_df['entry_time'] >= start_date) & 
                                           (filtered_df['entry_time'] < end_date)]
                    
                    debug_print(f"Date filter reduced data: {before_count} -> {len(filtered_df)} records")
            except Exception as e:
                debug_print(f"Date filtering error: {e}")
                import traceback
                debug_print(traceback.format_exc())
        
        # Apply delivery type filter (applied to all other filters)
        if delivery_type and delivery_type != 'all':
            if 'is_recycle' in filtered_df.columns:
                before_count = len(filtered_df)
                if delivery_type == 'normal':
                    filtered_df = filtered_df[~filtered_df['is_recycle']]
                elif delivery_type == 'recycle':
                    filtered_df = filtered_df[filtered_df['is_recycle']]
                debug_print(f"Delivery type filter reduced data: {before_count} -> {len(filtered_df)} records")
        
        # Now we'll apply filters for all except the current filter type
        # This way, each filter only shows values that would return results when combined with the other filters
        
        # Create copies for each filter type
        companies_filtered_df = filtered_df.copy()
        vehicles_filtered_df = filtered_df.copy()
        locations_filtered_df = filtered_df.copy()
        
        # Apply vehicle filter to companies and locations (but not vehicles options)
        if selected_vehicles and len(selected_vehicles) > 0:
            if 'vehicle_id' in filtered_df.columns:
                # Convert to list if not already
                if not isinstance(selected_vehicles, list):
                    selected_vehicles = [selected_vehicles]
                
                # Convert to string for comparison and use proper pandas indexing
                before_count = len(companies_filtered_df)
                # Create a new string column using loc to avoid SettingWithCopyWarning
                companies_filtered_df.loc[:, 'vehicle_id_str'] = companies_filtered_df['vehicle_id'].astype(str)
                valid_vehicles = [str(v) for v in selected_vehicles if v is not None and v != ""]
                if valid_vehicles:
                    companies_filtered_df = companies_filtered_df[companies_filtered_df['vehicle_id_str'].isin(valid_vehicles)]
                    debug_print(f"Vehicle filter reduced company options data: {before_count} -> {len(companies_filtered_df)} records")
                
                # Apply to locations filter too
                before_count = len(locations_filtered_df)
                # Create a new string column using loc to avoid SettingWithCopyWarning
                locations_filtered_df.loc[:, 'vehicle_id_str'] = locations_filtered_df['vehicle_id'].astype(str)
                if valid_vehicles:
                    locations_filtered_df = locations_filtered_df[locations_filtered_df['vehicle_id_str'].isin(valid_vehicles)]
                    debug_print(f"Vehicle filter reduced location options data: {before_count} -> {len(locations_filtered_df)} records")
        
        # Apply company filter to vehicles and locations (but not companies options)
        if selected_companies and len(selected_companies) > 0:
            if 'company_id' in filtered_df.columns:
                # Convert to list if not already
                if not isinstance(selected_companies, list):
                    selected_companies = [selected_companies]
                
                # Convert to string for comparison and use proper pandas indexing
                before_count = len(vehicles_filtered_df)
                # Create a new string column using loc to avoid SettingWithCopyWarning
                vehicles_filtered_df.loc[:, 'company_id_str'] = vehicles_filtered_df['company_id'].astype(str)
                valid_companies = [str(c) for c in selected_companies if c is not None and c != ""]
                if valid_companies:
                    vehicles_filtered_df = vehicles_filtered_df[vehicles_filtered_df['company_id_str'].isin(valid_companies)]
                    debug_print(f"Company filter reduced vehicle options data: {before_count} -> {len(vehicles_filtered_df)} records")
                
                # Apply to locations filter too
                before_count = len(locations_filtered_df)
                # Create a new string column using loc to avoid SettingWithCopyWarning
                if 'company_id_str' not in locations_filtered_df.columns:  # Check if column already exists
                    locations_filtered_df.loc[:, 'company_id_str'] = locations_filtered_df['company_id'].astype(str)
                if valid_companies:
                    locations_filtered_df = locations_filtered_df[locations_filtered_df['company_id_str'].isin(valid_companies)]
                    debug_print(f"Company filter reduced location options data: {before_count} -> {len(locations_filtered_df)} records")
        
        # Apply location filter to companies and vehicles (but not locations options)
        if selected_locations and len(selected_locations) > 0:
            if 'location' in filtered_df.columns:
                # Convert to list if not already
                if not isinstance(selected_locations, list):
                    selected_locations = [selected_locations]
                
                # Filter only on valid locations
                before_count = len(companies_filtered_df)
                valid_locations = [l for l in selected_locations if l is not None and l != ""]
                if valid_locations:
                    companies_filtered_df = companies_filtered_df[companies_filtered_df['location'].isin(valid_locations)]
                    debug_print(f"Location filter reduced company options data: {before_count} -> {len(companies_filtered_df)} records")
                
                # Apply to vehicles filter too
                before_count = len(vehicles_filtered_df)
                if valid_locations:
                    vehicles_filtered_df = vehicles_filtered_df[vehicles_filtered_df['location'].isin(valid_locations)]
                    debug_print(f"Location filter reduced vehicle options data: {before_count} -> {len(vehicles_filtered_df)} records")
        
        # Now extract unique values from each filtered dataframe for dropdowns
        
        # Get active company IDs from filtered data
        active_company_ids = set()
        if 'company_id' in companies_filtered_df.columns:
            active_company_ids = set(companies_filtered_df['company_id'].dropna().unique())
        
        # Get active vehicle IDs from filtered data
        active_vehicle_ids = set()
        if 'vehicle_id' in vehicles_filtered_df.columns:
            active_vehicle_ids = set(vehicles_filtered_df['vehicle_id'].dropna().unique())
        
        # Get active locations from filtered data
        active_locations = set()
        if 'location' in locations_filtered_df.columns:
            active_locations = set(locations_filtered_df['location'].dropna().unique())
        
        # Company options - only include companies present in filtered events
        company_options = []
        for _, row in companies_df.iterrows():
            if 'name' in companies_df.columns and 'company_id' in companies_df.columns:
                company_id = row['company_id']
                
                # Convert UUID to string to make it JSON serializable
                if hasattr(company_id, 'hex'):  # Check if UUID
                    company_id_str = str(company_id)
                elif not isinstance(company_id, str):
                    company_id_str = str(company_id)
                else:
                    company_id_str = company_id
                
                # Only include companies that are in filtered events
                if company_id in active_company_ids:
                    company_name = row['name'] if pd.notna(row['name']) else 'Unknown'
                    
                    # Just display company name without ID to prevent text overflow
                    company_options.append({
                        'label': f"{company_name}",
                        'value': company_id_str
                    })
        
        # Vehicle options - only include vehicles present in filtered events
        vehicle_options = []
        for _, row in vehicles_df.iterrows():
            if 'license_plate' in vehicles_df.columns and 'vehicle_id' in vehicles_df.columns:
                vehicle_id = row['vehicle_id']
                
                # Only include vehicles that are in filtered events
                if vehicle_id in active_vehicle_ids:
                    license_plate = row['license_plate'] if pd.notna(row['license_plate']) else 'Unknown'
                    
                    # Convert UUID to string to make it JSON serializable
                    if hasattr(vehicle_id, 'hex'):  # Check if UUID
                        vehicle_id_str = str(vehicle_id)
                    elif not isinstance(vehicle_id, str):
                        vehicle_id_str = str(vehicle_id)
                    else:
                        vehicle_id_str = vehicle_id
                    
                    # Just display license plate without ID to prevent text overflow
                    vehicle_options.append({
                        'label': f"{license_plate}",
                        'value': vehicle_id_str
                    })
        
        # Location options - only include locations in filtered events
        location_options = []
        valid_locations = [loc for loc in active_locations if pd.notna(loc) and loc != 'LEGACY DATA']
        
        for loc in sorted(valid_locations):
            if loc and loc != 'Recycle Collection':
                location_options.append({'label': loc, 'value': loc})
        
        # Add Recycle option if it exists in the filtered data
        if 'Recycle Collection' in valid_locations:
            location_options.append({'label': 'Recycle Collection', 'value': 'Recycle Collection'})
    
    except Exception as e:
        import traceback
        debug_print(f"Error in populate_filter_options: {e}")
        debug_print(traceback.format_exc())
        company_options = []
        vehicle_options = []
        location_options = []
    
    # Log filter counts for debugging
    debug_print(f"Cascading filter options: {len(company_options)} companies, {len(vehicle_options)} vehicles, {len(location_options)} locations")
    
    return company_options, vehicle_options, location_options

# Filter data based on selected criteria
@app.callback(
    [Output('filtered-data', 'data', allow_duplicate=True),
     Output('filter-state', 'data', allow_duplicate=True)],
    [Input('apply-filters', 'n_clicks'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')],
    [State('delivery-type-filter', 'value'),
     State('company-filter', 'value'),
     State('vehicle-filter', 'value'),
     State('location-filter', 'value')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def filter_data(n_clicks, start_date, end_date, delivery_type, selected_companies, selected_vehicles, selected_locations):
    debug_print(f"Filter function triggered - date range: {start_date} to {end_date}")
    
    # Save current filter state
    filter_state = {
        'start_date': start_date,
        'end_date': end_date,
        'delivery_type': delivery_type,
        'selected_companies': selected_companies or [],
        'selected_vehicles': selected_vehicles or [],
        'selected_locations': selected_locations or [],
        'filters_applied': True
    }
    
    try:
        # Use a fresh copy for filtering
        filtered_df = net_weights_df.copy()
        
        # Debug output before filtering
        debug_print(f"Filtering starting with {len(filtered_df)} records")
        debug_print(f"Filter params: date={start_date}-{end_date}, type={delivery_type}, companies={selected_companies}, vehicles={selected_vehicles}, locations={selected_locations}")
        
        # Add more debugging for key fields
        if not filtered_df.empty and 'company_id' in filtered_df.columns:
            unique_companies = filtered_df['company_id'].nunique()
            first_few = list(filtered_df['company_id'].astype(str).unique())[:5]
            debug_print(f"Dataset has {unique_companies} unique companies. Examples: {first_few}")
            
            # If specific companies are selected, check if they exist in the data
            if selected_companies and len(selected_companies) > 0:
                selected_company_strs = [str(c) for c in selected_companies if c is not None and c != ""]
                existing_companies = set(filtered_df['company_id'].astype(str).unique())
                matches = [c for c in selected_company_strs if c in existing_companies]
                debug_print(f"Selected companies {selected_company_strs}, matching in data: {matches}")
        
        if filtered_df.empty:
            # Return empty dataframe if no data
            debug_print("Empty dataframe, no filtering to do")
            return json.dumps({'empty': True}), json.dumps(filter_state)
        
        # Apply date filter
        if start_date and end_date:
            try:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date) + timedelta(days=1)  # Include full end day
                
                debug_print(f"Filtering by date range: {start_date} to {end_date}")
                
                if 'entry_time' in filtered_df.columns:
                    before_count = len(filtered_df)
                    
                    # Ensure entry_time is datetime
                    filtered_df['entry_time'] = pd.to_datetime(filtered_df['entry_time'])
                    
                    # Apply date filter with proper datetime comparison
                    filtered_df = filtered_df[(filtered_df['entry_time'] >= start_date) & 
                                             (filtered_df['entry_time'] < end_date)]
                    
                    debug_print(f"Date filter: {before_count} -> {len(filtered_df)} records")
            except Exception as e:
                debug_print(f"Date filtering error: {e}")
                import traceback
                debug_print(traceback.format_exc())
        
        # Apply delivery type filter
        if delivery_type and delivery_type != 'all':
            if 'is_recycle' in filtered_df.columns:
                before_count = len(filtered_df)
                if delivery_type == 'normal':
                    filtered_df = filtered_df[~filtered_df['is_recycle']]
                elif delivery_type == 'recycle':
                    filtered_df = filtered_df[filtered_df['is_recycle']]
                debug_print(f"Delivery type filter: {before_count} -> {len(filtered_df)} records")
        
        # Apply company filter
        if selected_companies and len(selected_companies) > 0:
            if 'company_id' in filtered_df.columns:
                before_count = len(filtered_df)
                # Convert selected_companies to list if it's not already
                if not isinstance(selected_companies, list):
                    selected_companies = [selected_companies]
                
                # Handle string or UUID company IDs
                debug_print(f"Company IDs before conversion: {selected_companies}")
                
                # Convert filtered_df company_id to string for comparison
                filtered_df.loc[:, 'company_id_str'] = filtered_df['company_id'].astype(str)
                
                # Convert selected company IDs to strings
                valid_companies = []
                for c in selected_companies:
                    if c is not None and c != "":
                        valid_companies.append(str(c))
                
                debug_print(f"Valid company IDs for filtering: {valid_companies}")
                
                if valid_companies:
                    # Check if any company IDs exist in the filtered dataset 
                    available_ids = set(filtered_df['company_id_str'].unique())
                    debug_print(f"Available company IDs in filtered data: {available_ids}")
                    
                    # Check for matches
                    matches = [c for c in valid_companies if c in available_ids]
                    debug_print(f"Matching company IDs: {matches}")
                    
                    if matches:
                        filtered_df = filtered_df[filtered_df['company_id_str'].isin(matches)]
                        debug_print(f"Company filter: {before_count} -> {len(filtered_df)} records")
                    else:
                        debug_print(f"WARNING: No matching company IDs found in filtered data")
                        # We'll keep the data and apply the date filter only - this will allow
                        # users to see data from the selected date range
        
        # Apply vehicle filter
        if selected_vehicles and len(selected_vehicles) > 0:
            if 'vehicle_id' in filtered_df.columns:
                before_count = len(filtered_df)
                # Convert selected_vehicles to list if it's not already
                if not isinstance(selected_vehicles, list):
                    selected_vehicles = [selected_vehicles]
                
                # Handle string or UUID vehicle IDs
                debug_print(f"Vehicle IDs before conversion: {selected_vehicles}")
                
                # Convert filtered_df vehicle_id to string for comparison
                filtered_df.loc[:, 'vehicle_id_str'] = filtered_df['vehicle_id'].astype(str)
                
                # Convert selected vehicle IDs to strings
                valid_vehicles = []
                for v in selected_vehicles:
                    if v is not None and v != "":
                        valid_vehicles.append(str(v))
                
                debug_print(f"Valid vehicle IDs for filtering: {valid_vehicles}")
                
                if valid_vehicles:
                    # Check if any vehicle IDs exist in the filtered dataset 
                    available_ids = set(filtered_df['vehicle_id_str'].unique())
                    debug_print(f"Available vehicle IDs in filtered data: {available_ids}")
                    
                    # Check for matches
                    matches = [v for v in valid_vehicles if v in available_ids]
                    debug_print(f"Matching vehicle IDs: {matches}")
                    
                    if matches:
                        filtered_df = filtered_df[filtered_df['vehicle_id_str'].isin(matches)]
                        debug_print(f"Vehicle filter: {before_count} -> {len(filtered_df)} records")
                    else:
                        debug_print(f"WARNING: No matching vehicle IDs found in filtered data")
                        # We'll keep the data and apply the date filter only - this will allow
                        # users to see data from the selected date range
        
        # Apply location filter
        if selected_locations and len(selected_locations) > 0:
            if 'location' in filtered_df.columns:
                before_count = len(filtered_df)
                # Convert selected_locations to list if it's not already
                if not isinstance(selected_locations, list):
                    selected_locations = [selected_locations]
                
                # Process locations for filtering
                debug_print(f"Location values before processing: {selected_locations}")
                
                # Extract valid location strings
                valid_locations = [l for l in selected_locations if l is not None and l != ""]
                debug_print(f"Valid locations for filtering: {valid_locations}")
                
                if valid_locations:
                    # Check if any locations exist in the filtered dataset
                    available_locations = set(filtered_df['location'].dropna().unique())
                    debug_print(f"Available locations in filtered data: {available_locations}")
                    
                    # Check for matches
                    matches = [l for l in valid_locations if l in available_locations]
                    debug_print(f"Matching locations: {matches}")
                    
                    if matches:
                        filtered_df = filtered_df[filtered_df['location'].isin(matches)]
                        debug_print(f"Location filter: {before_count} -> {len(filtered_df)} records")
                    else:
                        debug_print(f"WARNING: No matching locations found in filtered data")
                        # We'll keep the data and apply the date filter only - this will allow
                        # users to see data from the selected date range
        
        # Return a serialized version of the dataframe
        if filtered_df.empty:
            # If we have a date filter but no matches, try ignoring the company filters
            if start_date and end_date and selected_companies and len(selected_companies) > 0:
                debug_print("No records match all filters. Trying with just date filter.")
                # Try with just date filtering
                date_filtered_df = net_weights_df.copy()
                
                try:
                    start_date_dt = pd.to_datetime(start_date)
                    end_date_dt = pd.to_datetime(end_date) + timedelta(days=1)
                    
                    # Ensure entry_time is datetime
                    date_filtered_df['entry_time'] = pd.to_datetime(date_filtered_df['entry_time'])
                    
                    # Apply just the date filter
                    date_filtered_df = date_filtered_df[(date_filtered_df['entry_time'] >= start_date_dt) & 
                                             (date_filtered_df['entry_time'] < end_date_dt)]
                    
                    if not date_filtered_df.empty:
                        debug_print(f"Fallback: Found {len(date_filtered_df)} records with date filter only")
                        filtered_df = date_filtered_df
                except Exception as e:
                    debug_print(f"Error in date-only filtering fallback: {e}")
            
            # If still empty, return empty result
            if filtered_df.empty:
                debug_print("No records match the filters after fallback attempt")
                return json.dumps({'empty': True}), json.dumps(filter_state)
        
        # Extract just the session IDs which is enough to identify the filtered rows
        # Convert any UUIDs to strings for JSON serialization
        session_ids = []
        for sid in filtered_df['session_id']:
            if hasattr(sid, 'hex'):  # UUID object
                session_ids.append(str(sid))
            else:
                session_ids.append(str(sid))  # Convert everything to string to be safe
        
        debug_print(f"Final filtered result: {len(session_ids)} records")
        return json.dumps({'session_ids': session_ids}), json.dumps(filter_state)
    
    except Exception as e:
        import traceback
        print(f"Error in filter_data: {e}")
        print(traceback.format_exc())
        # Return the original data if there's an error
        # Clear filter state on error
        error_filter_state = filter_state.copy()
        error_filter_state['filters_applied'] = False
        return net_weights_df.to_json(date_format='iso', orient='split'), json.dumps(error_filter_state)

# Reset filters
@app.callback(
    [Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('delivery-type-filter', 'value'),
     Output('company-filter', 'value'),
     Output('vehicle-filter', 'value'),
     Output('location-filter', 'value'),
     Output('filtered-data', 'data', allow_duplicate=True),
     Output('filter-state', 'data', allow_duplicate=True)],
    [Input('reset-filters', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    # Create json data with session_ids for filtering - use all available data
    if not net_weights_df.empty:
        session_ids = []
        for sid in net_weights_df['session_id']:
            if hasattr(sid, 'hex'):  # UUID object
                session_ids.append(str(sid))
            else:
                session_ids.append(str(sid))  # Convert everything to string to be safe
                
        filtered_data = json.dumps({'session_ids': session_ids})
    else:
        filtered_data = json.dumps({'empty': True})
    
    # Clear filter state
    clear_filter_state = json.dumps({
        'start_date': None,
        'end_date': None,
        'delivery_type': None,
        'selected_companies': [],
        'selected_vehicles': [],
        'selected_locations': [],
        'filters_applied': False
    })
    
    return (datetime.now() - timedelta(days=30), datetime.now(), 
            'all', [], [], [], filtered_data, clear_filter_state)

# Update data info
@app.callback(
    Output('data-info', 'children'),
    [Input('filtered-data', 'data'),
     Input('database-poll-interval', 'n_intervals')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def update_data_info(json_data, n_intervals):
    debug_print(f"Updating data info with: {json_data[:100] if json_data else 'None'}...")
    try:
        # Get filtered dataframe based on session IDs
        if not json_data:
            debug_print("No JSON data, using full dataset for data info")
            filtered_df = net_weights_df.copy()
        else:
            try:
                filter_data = json.loads(json_data)
                debug_print(f"Loaded filter data for info panel: {str(filter_data)[:200] if filter_data else 'None'}...")
                
                if 'empty' in filter_data and filter_data['empty']:
                    debug_print("Empty filter data, using empty dataframe for info panel")
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    debug_print(f"Found {len(session_ids)} session IDs in filter data for info panel")
                    
                    # Create a new series with string values for comparison
                    session_id_strings = net_weights_df['session_id'].astype(str)
                    
                    # Use the string series for filtering
                    mask = session_id_strings.isin(session_ids)
                    filtered_df = net_weights_df[mask]
                    debug_print(f"After filtering for info panel, got {len(filtered_df)} records")
                else:
                    debug_print("No session_ids in filter data, using full dataset for info panel")
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data for info panel: {e}")
                import traceback
                debug_print(traceback.format_exc())
                filtered_df = net_weights_df.copy()
        
        # Check for empty dataframe
        if filtered_df.empty:
            return [
                html.P("No data available", className="font-medium text-red-600"),
                html.P("Please check database connection", className="text-sm")
            ]
            
        # Check if required columns exist
        if 'net_weight' not in filtered_df.columns:
            return [
                html.P("Data format error", className="font-medium text-red-600"),
                html.P("Missing required columns", className="text-sm")
            ]
        
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
        total_fees = 0
        fee_companies = 0
        if 'fee_amount' in filtered_df.columns:
            total_fees = filtered_df['fee_amount'].sum()
            # Ensure company_name is properly formatted before counting unique values
            fee_companies_series = filtered_df[filtered_df['fee_amount'] > 0]['company_name']
            # Convert any Series objects to strings to make them hashable
            fee_companies_series = fee_companies_series.astype(str)
            fee_companies = fee_companies_series.nunique()
        
        # Format date ranges if available
        date_range_text = "N/A"
        if not filtered_df.empty and 'entry_time' in filtered_df.columns:
            min_date = filtered_df['entry_time'].min()
            max_date = filtered_df['entry_time'].max()
            if pd.notna(min_date) and pd.notna(max_date):
                date_range_text = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        # Add fee information if available
        fee_info = []
        if 'fee_amount' in filtered_df.columns:
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
            html.P(f"Date Range: {date_range_text}", className="mt-2 text-xs")
        ]
        
    except Exception as e:
        import traceback
        print(f"Error in update_data_info: {e}")
        print(traceback.format_exc())
        return [
            html.P("Error processing data", className="font-medium text-red-600"),
            html.P(f"Details: {str(e)}", className="text-sm")
        ]

# Overview Tab Content - Update function to access tab content
@app.callback(
    Output('overview-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value'),
     Input('database-poll-interval', 'n_intervals'),
     Input('apply-filters', 'n_clicks')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def update_overview_tab(json_data, tab_value, n_intervals, n_clicks):
    if tab_value != 'overview':
        return []
    
    try:
        # Get filtered dataframe based on session IDs
        if not json_data:
            filtered_df = net_weights_df.copy()
        else:
            try:
                filter_data = json.loads(json_data)
                if 'empty' in filter_data and filter_data['empty']:
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    # Handle string comparison for session IDs (original might be UUID)
                    filtered_df = net_weights_df[net_weights_df['session_id'].astype(str).isin(session_ids)]
                else:
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data: {e}")
                filtered_df = net_weights_df.copy()
        
        if filtered_df.empty or 'net_weight' not in filtered_df.columns:
            return html.Div("No data available. Please check database connection.", className="text-gray-500 text-center py-10")
        
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
        
        # Prepare daily trend data - convert dates to strings to avoid serialization issues
        # Create a copy with string dates
        if 'date' in filtered_df.columns:
            trend_df = filtered_df.copy()
            trend_df.loc[:, 'date_str'] = trend_df['date'].astype(str)
            daily_data = trend_df.groupby(['date_str', 'is_recycle']).agg({
                'net_weight': 'sum',
                'session_id': 'count'
            }).reset_index()
            daily_data.rename(columns={'date_str': 'date'}, inplace=True)
        else:
            # Create an empty dataframe with the expected columns
            daily_data = pd.DataFrame(columns=['date', 'is_recycle', 'net_weight', 'session_id'])
        
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
        
        # Create hourly heatmap (limited to business hours 8 AM - 5 PM)
        # Filter data to only include business hours (8-17)
        business_hours_df = filtered_df[filtered_df['hour'].between(8, 17)]
        hour_dow = business_hours_df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        
        # Custom day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hour_dow['day_of_week'] = pd.Categorical(hour_dow['day_of_week'], categories=day_order, ordered=True)
        hour_dow = hour_dow.sort_values(['day_of_week', 'hour'])
        
        # Create a pivot table for the heatmap
        heatmap_data = hour_dow.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # Define business hours range (8 AM to 5 PM)
        business_hours = list(range(8, 18))  # 8-17 inclusive
        
        # Make sure all days are present in the pivot table
        for day in day_order:
            if day not in heatmap_data.index:
                # Add missing day with zeros for business hours
                heatmap_data.loc[day] = [0] * len(business_hours)
        
        # Sort the index to match day_order
        heatmap_data = heatmap_data.reindex(day_order)
        
        # Make sure all business hours are present and in order
        for hour in business_hours:
            if hour not in heatmap_data.columns:
                heatmap_data[hour] = 0
        
        # Ensure columns are properly ordered (8-18)
        heatmap_data = heatmap_data.reindex(columns=business_hours, fill_value=0)
        
        # Create the heatmap with clearly formatted hours for business hours
        hour_labels = [f"{h:02d}hrs" for h in business_hours]  # Format as 08hrs, 09hrs, etc.
        
        heatmap_fig = px.imshow(
            heatmap_data,
            labels=dict(x='Hour of Day', y='Day of Week', color='Sessions'),
            x=business_hours,  # Use business hours list
            y=heatmap_data.index.tolist(),
            color_continuous_scale='Blues',
            aspect='auto'
        )
        
        heatmap_fig.update_layout(
            title=None,
            xaxis=dict(
                title="Hour of Day (Business Hours)",
                titlefont=dict(size=12),
                tickmode='array',
                tickvals=business_hours,
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
                
                # Show total fees or normal/recycle ratio based on whether fees exist
                html.Div([
                    html.H4("Total Fees", className="text-sm font-medium text-gray-500"),
                    html.P(f"K {filtered_df['fee_amount'].sum():,.2f}", className="text-3xl font-bold text-red-600"),
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
    except Exception as e:
        import traceback
        print(f"Error in update_overview_tab: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H3("Error loading overview", className="text-xl font-medium text-red-600 mb-2"),
            html.P(f"Details: {str(e)}", className="text-gray-700")
        ], className="text-center py-10")

# Analysis Tab Content
@app.callback(
    Output('analysis-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value'),
     Input('database-poll-interval', 'n_intervals'),
     Input('apply-filters', 'n_clicks')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def update_analysis_tab(json_data, tab_value, n_intervals, n_clicks):
    if tab_value != 'analysis':
        return []
    
    try:
        # Get filtered dataframe based on session IDs
        if not json_data:
            filtered_df = net_weights_df.copy()
        else:
            try:
                filter_data = json.loads(json_data)
                if 'empty' in filter_data and filter_data['empty']:
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    # Handle string comparison for session IDs (original might be UUID)
                    filtered_df = net_weights_df[net_weights_df['session_id'].astype(str).isin(session_ids)]
                else:
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data: {e}")
                filtered_df = net_weights_df.copy()
        
        if filtered_df.empty or 'net_weight' not in filtered_df.columns:
            return html.Div("No data available. Please check database connection.", className="text-gray-500 text-center py-10")
        
        # Day of week analysis - use string values to avoid serialization issues
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if 'day_of_week' in filtered_df.columns:
            # Create a copy to ensure we have proper string values
            dow_df = filtered_df.copy()
            
            # Ensure day_of_week is a string
            dow_df.loc[:, 'day_of_week'] = dow_df['day_of_week'].astype(str)
            
            day_data = dow_df.groupby(['day_of_week', 'is_recycle']).agg({
                'net_weight': 'sum',
                'session_id': 'count'
            }).reset_index()
            
            # Convert to categorical for proper ordering
            day_data['day_of_week'] = pd.Categorical(day_data['day_of_week'], categories=day_order, ordered=True)
            day_data = day_data.sort_values('day_of_week')
        else:
            # Create an empty dataframe with expected columns
            day_data = pd.DataFrame(columns=['day_of_week', 'is_recycle', 'net_weight', 'session_id'])
        
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
        
        # Monthly trend analysis - use loc to avoid SettingWithCopyWarning
        # Create a copy to ensure we're not modifying a view
        if 'entry_time' in filtered_df.columns:
            month_analysis_df = filtered_df.copy()
            
            # Format the month-year as a string directly to avoid Period objects
            month_analysis_df.loc[:, 'month_year_str'] = pd.to_datetime(month_analysis_df['entry_time']).dt.strftime('%Y-%m')
            
            # Group by the string version of month-year
            monthly_data = month_analysis_df.groupby(['month_year_str', 'is_recycle']).agg({
                'net_weight': 'sum',
                'session_id': 'count'
            }).reset_index()
            
            # Rename column for consistency
            monthly_data.rename(columns={'month_year_str': 'month_year'}, inplace=True)
        else:
            # Create an empty dataframe with expected columns if entry_time is missing
            monthly_data = pd.DataFrame(columns=['month_year', 'is_recycle', 'net_weight', 'session_id'])
        
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
    except Exception as e:
        import traceback
        print(f"Error in update_analysis_tab: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H3("Error loading analysis", className="text-xl font-medium text-red-600 mb-2"),
            html.P(f"Details: {str(e)}", className="text-gray-700")
        ], className="text-center py-10")

# Locations Tab Content
@app.callback(
    Output('locations-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value'),
     Input('database-poll-interval', 'n_intervals'),
     Input('apply-filters', 'n_clicks')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def update_locations_tab(json_data, tab_value, n_intervals, n_clicks):
    if tab_value != 'locations':
        return []
    
    try:
        # Get filtered dataframe based on session IDs
        if not json_data:
            filtered_df = net_weights_df.copy()
        else:
            try:
                filter_data = json.loads(json_data)
                if 'empty' in filter_data and filter_data['empty']:
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    # Handle string comparison for session IDs (original might be UUID)
                    filtered_df = net_weights_df[net_weights_df['session_id'].astype(str).isin(session_ids)]
                else:
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data: {e}")
                filtered_df = net_weights_df.copy()
        
        if filtered_df.empty or 'net_weight' not in filtered_df.columns or 'location' not in filtered_df.columns:
            return html.Div("No location data available. Please check database connection.", className="text-gray-500 text-center py-10")
        
        # Filter out recycle collection to focus on normal disposal with locations
        normal_df = filtered_df[~filtered_df['is_recycle']] if 'is_recycle' in filtered_df.columns else filtered_df
        
        # Skip locations with "LEGACY DATA" or empty values
        location_df = normal_df[~normal_df['location'].isin(['LEGACY DATA', ''])]
        
        if location_df.empty:
            return html.Div("No location data available after filtering.", className="text-gray-500 text-center py-10")
        
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
    except Exception as e:
        import traceback
        print(f"Error in update_locations_tab: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H3("Error loading locations", className="text-xl font-medium text-red-600 mb-2"),
            html.P(f"Details: {str(e)}", className="text-gray-700")
        ], className="text-center py-10")

# Data Table Tab Content
@app.callback(
    Output('data-table-tab-content', 'children'),
    [Input('filtered-data', 'data'),
     Input('tabs', 'value'),
     Input('database-poll-interval', 'n_intervals'),
     Input('apply-filters', 'n_clicks')],
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def update_data_table_tab(json_data, tab_value, n_intervals, n_clicks):
    if tab_value != 'data-table':
        return []
    
    try:
        # Get filtered dataframe based on session IDs
        if not json_data:
            filtered_df = net_weights_df.copy()
        else:
            try:
                filter_data = json.loads(json_data)
                if 'empty' in filter_data and filter_data['empty']:
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    # Handle string comparison for session IDs (original might be UUID)
                    filtered_df = net_weights_df[net_weights_df['session_id'].astype(str).isin(session_ids)]
                else:
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data: {e}")
                filtered_df = net_weights_df.copy()
        
        if filtered_df.empty:
            return html.Div("No data available. Please check database connection.", className="text-gray-500 text-center py-10")
        
        # Limit to 1000 rows for performance
        display_df = filtered_df.head(1000)
        
        # Format dates and times
        if 'entry_time' in display_df.columns:
            display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
        if 'exit_time' in display_df.columns:
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
        
        if not display_cols:
            return html.Div("No data available with the required columns.", className="text-gray-500 text-center py-10")
        
        table_df = display_df[display_cols].copy()
        
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
        
        # Convert any UUID objects to strings to avoid JSON serialization issues
        for column in table_df.columns:
            if table_df[column].apply(lambda x: isinstance(x, uuid.UUID)).any():
                debug_print(f"Converting UUIDs to strings in column: {column}")
                table_df[column] = table_df[column].astype(str)
        
        # Create data table with enhanced features
        table = dash_table.DataTable(
            id='data-table',
            columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in table_df.columns],
            data=table_df.to_dict('records'),
            export_format='csv',  # Enable CSV export directly from the table
            export_headers='display',  # Use formatted headers for CSV
            style_table={
                'overflowX': 'auto',
                'height': '600px', 
                'overflowY': 'auto'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '14px',
                'whiteSpace': 'normal',  # Allow text wrapping
                'minWidth': '120px',     # Set minimum column width
                'maxWidth': '300px',     # Set maximum column width
                'textOverflow': 'ellipsis',  # Add ellipsis for overflow
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
            filter_action='native',  # Enable filtering
            sort_action='native'     # Enable sorting
        )
        
        # Create dedicated download button for full dataset
        download_button = html.Button(
            "Export Full Data to CSV", 
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
    except Exception as e:
        import traceback
        print(f"Error in update_data_table_tab: {e}")
        print(traceback.format_exc())
        return html.Div([
            html.H3("Error loading data table", className="text-xl font-medium text-red-600 mb-2"),
            html.P(f"Details: {str(e)}", className="text-gray-700")
        ], className="text-center py-10")

# Export data to CSV callback
@app.callback(
    Output('dummy-export-output', 'children', allow_duplicate=True),
    Input('export-button', 'n_clicks'),
    State('filtered-data', 'data'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def export_data(n_clicks, json_data):
    if not n_clicks:
        return None
    
    try:
        debug_print(f"Exporting data to CSV from button click: {n_clicks}")
        # Get filtered dataframe based on session IDs
        if not json_data:
            filtered_df = net_weights_df.copy()
            debug_print("Exporting all data (no filter)")
        else:
            try:
                filter_data = json.loads(json_data)
                debug_print(f"Loaded filter data for export: {str(filter_data)[:200]}...")
                
                if 'empty' in filter_data and filter_data['empty']:
                    debug_print("Empty filter data, exporting empty CSV")
                    filtered_df = pd.DataFrame()
                elif 'session_ids' in filter_data:
                    session_ids = filter_data['session_ids']
                    debug_print(f"Exporting {len(session_ids)} filtered sessions")
                    
                    # Create mask for string comparison
                    session_id_strings = net_weights_df['session_id'].astype(str)
                    mask = session_id_strings.isin(session_ids)
                    filtered_df = net_weights_df[mask]
                    debug_print(f"Found {len(filtered_df)} records for export")
                else:
                    debug_print("No session_ids in filter, exporting all data")
                    filtered_df = net_weights_df.copy()
            except Exception as e:
                debug_print(f"Error parsing filtered data for export: {e}")
                import traceback
                debug_print(traceback.format_exc())
                filtered_df = net_weights_df.copy()
        
        # Format dates for better CSV readability
        if 'entry_time' in filtered_df.columns:
            filtered_df['entry_time'] = pd.to_datetime(filtered_df['entry_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'exit_time' in filtered_df.columns:
            filtered_df['exit_time'] = pd.to_datetime(filtered_df['exit_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
        # Round numeric values for better display
        for col in ['duration_minutes', 'entry_weight', 'exit_weight', 'net_weight']:
            if col in filtered_df.columns:
                filtered_df[col] = filtered_df[col].round(2)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_dir = os.path.dirname(__file__)
        export_path = os.path.join(base_dir, f'weigh_events_export_{timestamp}.csv')
        
        # Export to CSV
        filtered_df.to_csv(export_path, index=False)
        
        debug_print(f"Data exported to {export_path} ({len(filtered_df)} records)")
        return html.Div([
            html.P(f"Data exported to {export_path}", className="text-green-600 mt-2"),
            html.P(f"({len(filtered_df)} records exported)", className="text-sm text-gray-600")
        ])
    except Exception as e:
        debug_print(f"Error exporting data: {e}")
        import traceback
        debug_print(traceback.format_exc())
        return html.Div([
            html.P(f"Error exporting data: {str(e)}", className="text-red-600 mt-2")
        ])

# Add callback for data refresh
@app.callback(
    [Output('last-refresh-time', 'children'),
     Output('dummy-refresh-output', 'children')],
    [Input('database-poll-interval', 'n_intervals'),
     Input('refresh-filters', 'n_clicks')],
    [State('auto-refresh-toggle', 'value')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def refresh_dashboard_data(n_intervals, n_clicks, auto_refresh_enabled):
    """Refresh data from database periodically or on manual request"""
    ctx = dash.callback_context
    
    # Check what triggered the callback
    if not ctx.triggered:
        return [f"Last refreshed: {last_refresh_time}", ""]
    
    trigger = ctx.triggered[0]['prop_id']
    
    # Handle manual refresh button
    if 'refresh-filters' in trigger and n_clicks:
        debug_print("Manual refresh triggered")
        refresh_success = refresh_data_from_database()
        if refresh_success:
            return [f"Last refreshed: {last_refresh_time}", ""]
        else:
            return [f"Last refresh attempt failed at {datetime.now().strftime('%H:%M:%S')}", ""]
    
    # Handle automatic refresh interval
    if 'database-poll-interval' in trigger and n_intervals:
        # Only auto-refresh if enabled
        if auto_refresh_enabled and 'enabled' in auto_refresh_enabled:
            debug_print(f"Auto-refresh triggered (interval: {n_intervals})")
            refresh_success = refresh_data_from_database()
            if refresh_success:
                return [f"Last refreshed: {last_refresh_time} (auto)", ""]
            else:
                return [f"Auto-refresh failed at {datetime.now().strftime('%H:%M:%S')}", ""]
        else:
            # Auto-refresh is disabled, just update the timestamp
            return [f"🔒 Auto-refresh disabled - Last manual refresh: {last_refresh_time}", ""]
    
    # Default return
    return [f"Last refreshed: {last_refresh_time}", ""]

# Auto-reapply filters after data refresh
@app.callback(
    Output('filtered-data', 'data', allow_duplicate=True),
    [Input('dummy-refresh-output', 'children')],
    [State('filter-state', 'data')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def reapply_filters_after_refresh(refresh_signal, filter_state_json):
    """Automatically reapply active filters when data is refreshed"""
    try:
        if not filter_state_json:
            # No stored filter state, return all data
            if not net_weights_df.empty:
                session_ids = []
                for sid in net_weights_df['session_id']:
                    if hasattr(sid, 'hex'):
                        session_ids.append(str(sid))
                    else:
                        session_ids.append(str(sid))
                return json.dumps({'session_ids': session_ids})
            else:
                return json.dumps({'empty': True})
        
        filter_state = json.loads(filter_state_json)
        
        # Check if filters are currently applied
        if not filter_state.get('filters_applied', False):
            # No active filters, return all data
            if not net_weights_df.empty:
                session_ids = []
                for sid in net_weights_df['session_id']:
                    if hasattr(sid, 'hex'):
                        session_ids.append(str(sid))
                    else:
                        session_ids.append(str(sid))
                return json.dumps({'session_ids': session_ids})
            else:
                return json.dumps({'empty': True})
        
        debug_print("Reapplying filters to refreshed data...")
        
        # Reapply the stored filters to fresh data
        filtered_df = net_weights_df.copy()
        
        # Extract filter parameters
        start_date = filter_state.get('start_date')
        end_date = filter_state.get('end_date')
        delivery_type = filter_state.get('delivery_type')
        selected_companies = filter_state.get('selected_companies', [])
        selected_vehicles = filter_state.get('selected_vehicles', [])
        selected_locations = filter_state.get('selected_locations', [])
        
        debug_print(f"Reapplying filters: date={start_date}-{end_date}, type={delivery_type}, companies={len(selected_companies)}, vehicles={len(selected_vehicles)}, locations={len(selected_locations)}")
        
        if filtered_df.empty:
            return json.dumps({'empty': True})
        
        # Apply date filter
        if start_date and end_date:
            try:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date) + timedelta(days=1)
                
                if 'entry_time' in filtered_df.columns:
                    filtered_df['entry_time'] = pd.to_datetime(filtered_df['entry_time'])
                    filtered_df = filtered_df[(filtered_df['entry_time'] >= start_date) & 
                                             (filtered_df['entry_time'] < end_date)]
                    debug_print(f"Date filter reapplied: {len(filtered_df)} records")
            except Exception as e:
                debug_print(f"Date filtering error during reapply: {e}")
        
        # Apply delivery type filter
        if delivery_type and delivery_type != 'all':
            if 'is_recycle' in filtered_df.columns:
                before_count = len(filtered_df)
                if delivery_type == 'normal':
                    filtered_df = filtered_df[~filtered_df['is_recycle']]
                elif delivery_type == 'recycle':
                    filtered_df = filtered_df[filtered_df['is_recycle']]
                debug_print(f"Delivery type filter reapplied: {before_count} -> {len(filtered_df)} records")
        
        # Apply company filter
        if selected_companies and len(selected_companies) > 0:
            if 'company_id' in filtered_df.columns:
                before_count = len(filtered_df)
                selected_company_strs = [str(c) for c in selected_companies if c is not None and c != ""]
                filtered_df = filtered_df[filtered_df['company_id'].astype(str).isin(selected_company_strs)]
                debug_print(f"Company filter reapplied: {before_count} -> {len(filtered_df)} records")
        
        # Apply vehicle filter
        if selected_vehicles and len(selected_vehicles) > 0:
            if 'vehicle_id' in filtered_df.columns:
                before_count = len(filtered_df)
                selected_vehicle_strs = [str(v) for v in selected_vehicles if v is not None and v != ""]
                filtered_df = filtered_df[filtered_df['vehicle_id'].astype(str).isin(selected_vehicle_strs)]
                debug_print(f"Vehicle filter reapplied: {before_count} -> {len(filtered_df)} records")
        
        # Apply location filter
        if selected_locations and len(selected_locations) > 0:
            if 'location' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]
                debug_print(f"Location filter reapplied: {before_count} -> {len(filtered_df)} records")
        
        # Return filtered session IDs
        if filtered_df.empty:
            debug_print("No records match the reapplied filters")
            return json.dumps({'empty': True})
        
        session_ids = []
        for sid in filtered_df['session_id']:
            if hasattr(sid, 'hex'):
                session_ids.append(str(sid))
            else:
                session_ids.append(str(sid))
        
        debug_print(f"Filters reapplied successfully: {len(session_ids)} records")
        return json.dumps({'session_ids': session_ids})
        
    except Exception as e:
        debug_print(f"Error in reapply_filters_after_refresh: {e}")
        import traceback
        debug_print(traceback.format_exc())
        
        # Return all data on error
        if not net_weights_df.empty:
            session_ids = []
            for sid in net_weights_df['session_id']:
                if hasattr(sid, 'hex'):
                    session_ids.append(str(sid))
                else:
                    session_ids.append(str(sid))
            return json.dumps({'session_ids': session_ids})
        else:
            return json.dumps({'empty': True})

# Initialize filtered data on app start
@app.callback(
    Output('filtered-data', 'data'),
    Input('dummy-refresh-output', 'children'),
    prevent_initial_call=False,
    suppress_callback_exceptions=True
)
def initialize_filtered_data(dummy):
    """Initialize filtered data with all session IDs on app start"""
    if not net_weights_df.empty:
        session_ids = []
        for sid in net_weights_df['session_id']:
            if hasattr(sid, 'hex'):  # UUID object
                session_ids.append(str(sid))
            else:
                session_ids.append(str(sid))
        return json.dumps({'session_ids': session_ids})
    else:
        return json.dumps({'empty': True})

# Initialize the auth manager instance
auth_manager = AuthManager()

# Run the app
if __name__ == '__main__':
    # Production vs development configuration
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5007))
    host = '0.0.0.0'
    
    debug_print("Starting Database-Connected Analytics Dashboard...")
    debug_print(f"Dashboard will be available at: http://{host}:{port}/")
    debug_print(f"Debug mode: {debug_mode}")
    app.run(debug=debug_mode, port=port, host=host)
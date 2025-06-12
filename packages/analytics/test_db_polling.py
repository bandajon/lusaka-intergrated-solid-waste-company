#!/usr/bin/env python3
"""
Test script to verify database polling and data refresh
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_database_connection():
    """Test direct database connection and data fetch"""
    try:
        from database.database_connection import read_weigh_events, read_vehicles, read_companies
        
        debug_print("Testing database connection...")
        
        # Read data from database
        weigh_df = read_weigh_events()
        vehicles_df = read_vehicles()
        companies_df = read_companies()
        
        debug_print(f"Successfully read data from database:")
        debug_print(f"  - Weigh events: {len(weigh_df)} records")
        debug_print(f"  - Vehicles: {len(vehicles_df)} records")
        debug_print(f"  - Companies: {len(companies_df)} records")
        
        # Save data to CSV files
        weigh_events_file = 'extracted_weigh_events.csv'
        vehicles_file = 'extracted_vehicles.csv'
        companies_file = 'extracted_companies.csv'
        
        weigh_df.to_csv(weigh_events_file, index=False)
        vehicles_df.to_csv(vehicles_file, index=False)
        companies_df.to_csv(companies_file, index=False)
        
        debug_print(f"Saved data to CSV files:")
        debug_print(f"  - {weigh_events_file}")
        debug_print(f"  - {vehicles_file}")
        debug_print(f"  - {companies_file}")
        
        return True
    except Exception as e:
        debug_print(f"Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_freshness():
    """Check if extracted CSV files are up to date"""
    files_to_check = [
        'extracted_weigh_events.csv',
        'extracted_vehicles.csv', 
        'extracted_companies.csv'
    ]
    
    debug_print("Checking file freshness...")
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            mod_time = os.path.getmtime(file_path)
            mod_datetime = datetime.fromtimestamp(mod_time)
            age_seconds = (datetime.now() - mod_datetime).total_seconds()
            age_minutes = age_seconds / 60
            
            debug_print(f"  - {file_path}: Last modified {mod_datetime.strftime('%Y-%m-%d %H:%M:%S')} ({age_minutes:.1f} minutes ago)")
        else:
            debug_print(f"  - {file_path}: File does not exist")

def check_data_consistency():
    """Check if data extracted from dashboard CSV files matches database"""
    try:
        from database.database_connection import read_weigh_events, read_vehicles, read_companies
        
        debug_print("Checking data consistency between database and CSV files...")
        
        # Read data from database
        db_weigh_df = read_weigh_events()
        db_vehicles_df = read_vehicles()
        db_companies_df = read_companies()
        
        # Read data from CSV files
        csv_weigh_df = pd.read_csv('extracted_weigh_events.csv')
        csv_vehicles_df = pd.read_csv('extracted_vehicles.csv')
        csv_companies_df = pd.read_csv('extracted_companies.csv')
        
        # Compare record counts
        debug_print("Comparing record counts:")
        debug_print(f"  - Weigh events: DB={len(db_weigh_df)}, CSV={len(csv_weigh_df)}, Match={len(db_weigh_df) == len(csv_weigh_df)}")
        debug_print(f"  - Vehicles: DB={len(db_vehicles_df)}, CSV={len(csv_vehicles_df)}, Match={len(db_vehicles_df) == len(csv_vehicles_df)}")
        debug_print(f"  - Companies: DB={len(db_companies_df)}, CSV={len(csv_companies_df)}, Match={len(db_companies_df) == len(csv_companies_df)}")
        
        # Check more details if there's a mismatch
        if len(db_weigh_df) != len(csv_weigh_df):
            debug_print("⚠️ Weigh events count mismatch! Checking session IDs...")
            
            # Compare most recent session IDs to check if new data exists
            if 'session_id' in db_weigh_df.columns and 'session_id' in csv_weigh_df.columns:
                db_sessions = set(db_weigh_df['session_id'].unique())
                csv_sessions = set(csv_weigh_df['session_id'].unique())
                
                # Find sessions in DB that aren't in CSV (new sessions)
                new_sessions = db_sessions - csv_sessions
                
                if new_sessions:
                    debug_print(f"  - Found {len(new_sessions)} new session IDs in database that aren't in CSV")
                    sample_new = list(new_sessions)[:5]
                    debug_print(f"  - Sample new sessions: {sample_new}")
                else:
                    debug_print("  - No new session IDs found, but counts still differ")
        
        return True
    except Exception as e:
        debug_print(f"Error checking data consistency: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_reload_works():
    """Test if reload_from_database function works properly"""
    try:
        # Save current CSV files to backup
        debug_print("Backing up current CSV files...")
        backup_files = {}
        for filename in ['extracted_weigh_events.csv', 'extracted_vehicles.csv', 'extracted_companies.csv']:
            if os.path.exists(filename):
                backup_content = open(filename, 'rb').read()
                backup_files[filename] = backup_content
                debug_print(f"  - Backed up {filename}")
            
        # Delete the files to simulate a clean state
        debug_print("Deleting CSV files to test fresh load...")
        for filename in backup_files:
            if os.path.exists(filename):
                os.remove(filename)
                debug_print(f"  - Deleted {filename}")
        
        # Import the dashboard module and test reload function
        try:
            debug_print("Importing dashboard module...")
            from flask_app.dashboards.weigh_events_dashboard import reload_from_database
            
            debug_print("Testing reload_from_database function...")
            result = reload_from_database()
            
            if result:
                merged_df, weigh_df, vehicles_df, companies_df, net_weights_df = result
                debug_print("✅ reload_from_database function works!")
                debug_print(f"  - Loaded {len(weigh_df)} weigh events")
                debug_print(f"  - Loaded {len(vehicles_df)} vehicles")
                debug_print(f"  - Loaded {len(companies_df)} companies")
                debug_print(f"  - Calculated {len(net_weights_df)} net weights")
                
                # Check if files were re-created
                files_recreated = []
                for filename in backup_files:
                    if os.path.exists(filename):
                        files_recreated.append(filename)
                
                debug_print(f"Files recreated by reload function: {files_recreated}")
                return True
            else:
                debug_print("❌ reload_from_database function returned None")
                return False
        
        except Exception as e:
            debug_print(f"Error testing reload function: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Restore backup files
            debug_print("Restoring backup files...")
            for filename, content in backup_files.items():
                with open(filename, 'wb') as f:
                    f.write(content)
                debug_print(f"  - Restored {filename}")
    
    except Exception as e:
        debug_print(f"Error in check_reload_works: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    debug_print("Starting database polling test script")
    
    # Test database connection and data extraction
    debug_print("\n=== Testing Database Connection ===")
    test_database_connection()
    
    # Check file freshness
    debug_print("\n=== Checking File Freshness ===")
    check_file_freshness()
    
    # Check data consistency
    debug_print("\n=== Checking Data Consistency ===")
    check_data_consistency()
    
    # Test reload function
    debug_print("\n=== Testing Reload Function ===")
    check_reload_works()
    
    debug_print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
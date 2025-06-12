#!/usr/bin/env python3
"""
Test script for the auto-close session functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the analytics directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_dashboard import find_open_sessions, estimate_tare_weight, auto_close_sessions

def create_test_data():
    """Create test data with some open sessions"""
    current_time = datetime.now()
    
    # Create test weigh events
    test_events = []
    
    # Session 1: Completed session (should not be auto-closed)
    test_events.extend([
        {
            'session_id': 'session_001',
            'vehicle_id': 'VEH_001',
            'event_type': 1,  # Entry
            'event_time': current_time - timedelta(hours=1),
            'weight_kg': 5000,
            'license_plate': 'ABC123',
            'company_name': 'Test Company 1',
            'remarks': 'Test entry'
        },
        {
            'session_id': 'session_001',
            'vehicle_id': 'VEH_001',
            'event_type': 2,  # Exit
            'event_time': current_time - timedelta(minutes=30),
            'weight_kg': 2000,
            'license_plate': 'ABC123',
            'company_name': 'Test Company 1',
            'remarks': 'Test exit'
        }
    ])
    
    # Session 2: Open session > 2 hours (should be auto-closed)
    test_events.append({
        'session_id': 'session_002',
        'vehicle_id': 'VEH_002',
        'event_type': 1,  # Entry only
        'event_time': current_time - timedelta(hours=3),
        'weight_kg': 4500,
        'license_plate': 'XYZ789',
        'company_name': 'Test Company 2',
        'remarks': 'Test entry - long session'
    })
    
    # Session 3: Open recycle session > 2 hours (should be auto-closed)
    test_events.append({
        'session_id': 'session_003',
        'vehicle_id': 'VEH_003',
        'event_type': 1,  # Entry only
        'event_time': current_time - timedelta(hours=4),
        'weight_kg': 2500,
        'license_plate': 'REC456',
        'company_name': 'Recycle Company',
        'remarks': 'R - Recycle collection'
    })
    
    # Session 4: Recent open session < 2 hours (should NOT be auto-closed)
    test_events.append({
        'session_id': 'session_004',
        'vehicle_id': 'VEH_004',
        'event_type': 1,  # Entry only
        'event_time': current_time - timedelta(minutes=90),
        'weight_kg': 3500,
        'license_plate': 'NEW999',
        'company_name': 'Test Company 3',
        'remarks': 'Recent entry'
    })
    
    df = pd.DataFrame(test_events)
    df['event_time'] = pd.to_datetime(df['event_time'])
    df['event_type_std'] = df['event_type']
    
    return df

def create_historical_data():
    """Create historical data for tare weight estimation"""
    historical_events = [
        {
            'vehicle_id': 'VEH_001',
            'license_plate': 'ABC123',
            'company_name': 'Test Company 1',
            'entry_weight': 5200,
            'exit_weight': 2100,
            'net_weight': 3100
        },
        {
            'vehicle_id': 'VEH_001',
            'license_plate': 'ABC123',
            'company_name': 'Test Company 1',
            'entry_weight': 4800,
            'exit_weight': 1900,
            'net_weight': 2900
        },
        {
            'vehicle_id': 'VEH_002',
            'license_plate': 'XYZ789',
            'company_name': 'Test Company 2',
            'entry_weight': 4600,
            'exit_weight': 2200,
            'net_weight': 2400
        }
    ]
    
    return pd.DataFrame(historical_events)

def test_find_open_sessions():
    """Test the find_open_sessions function"""
    print("Testing find_open_sessions...")
    
    test_df = create_test_data()
    open_sessions = find_open_sessions(test_df, max_hours=2)
    
    print(f"Found {len(open_sessions)} open sessions")
    if not open_sessions.empty:
        print("Open sessions:")
        for _, session in open_sessions.iterrows():
            print(f"  - Session {session['session_id']}: {session['license_plate']} "
                  f"({session['hours_open']:.1f} hours open)")
    
    # Should find 2 open sessions (session_002 and session_003)
    assert len(open_sessions) == 2, f"Expected 2 open sessions, found {len(open_sessions)}"
    print("✓ find_open_sessions test passed")

def test_estimate_tare_weight():
    """Test the estimate_tare_weight function"""
    print("\nTesting estimate_tare_weight...")
    
    historical_df = create_historical_data()
    
    # Test with known vehicle
    tare_weight, confidence = estimate_tare_weight('VEH_001', 'ABC123', 5000, historical_df)
    print(f"VEH_001 estimated tare: {tare_weight:.0f}kg (confidence: {confidence})")
    assert confidence in ['high', 'medium'], f"Expected high/medium confidence, got {confidence}"
    
    # Test with unknown vehicle
    tare_weight, confidence = estimate_tare_weight('VEH_999', 'UNK999', 6000, historical_df)
    print(f"Unknown vehicle estimated tare: {tare_weight:.0f}kg (confidence: {confidence})")
    assert confidence == 'low', f"Expected low confidence for unknown vehicle, got {confidence}"
    
    # Test recycle vehicle
    tare_weight, confidence = estimate_tare_weight('VEH_REC', 'REC999', 3000, pd.DataFrame(), is_recycle=True)
    print(f"Recycle vehicle estimated tare: {tare_weight:.0f}kg (confidence: {confidence})")
    assert tare_weight <= 3000 * 0.2, "Recycle vehicle tare should be lower"
    
    print("✓ estimate_tare_weight test passed")

def test_auto_close_sessions():
    """Test the complete auto_close_sessions function"""
    print("\nTesting auto_close_sessions...")
    
    test_df = create_test_data()
    historical_df = create_historical_data()
    
    print(f"Original dataframe has {len(test_df)} events")
    
    # Test without persisting to database
    updated_df = auto_close_sessions(test_df, historical_df, max_hours=2, persist_to_db=False)
    
    print(f"Updated dataframe has {len(updated_df)} events")
    
    # Should have added 2 synthetic exit events
    added_events = len(updated_df) - len(test_df)
    assert added_events == 2, f"Expected 2 new events, got {added_events}"
    
    # Check that auto-closed events have proper remarks
    auto_closed_events = updated_df[updated_df['remarks'].str.contains('AUTO-CLOSED', na=False)]
    print(f"Found {len(auto_closed_events)} auto-closed events")
    assert len(auto_closed_events) == 2, f"Expected 2 auto-closed events, got {len(auto_closed_events)}"
    
    # Verify session completion
    for session_id in ['session_002', 'session_003']:
        session_events = updated_df[updated_df['session_id'] == session_id]
        entries = session_events[session_events['event_type'] == 1]
        exits = session_events[session_events['event_type'] == 2]
        assert len(entries) == 1 and len(exits) == 1, f"Session {session_id} should have 1 entry and 1 exit"
    
    print("✓ auto_close_sessions test passed")

def run_all_tests():
    """Run all tests"""
    print("Running auto-close session tests...\n")
    
    try:
        test_find_open_sessions()
        test_estimate_tare_weight()
        test_auto_close_sessions()
        
        print("\n✅ All tests passed successfully!")
        print("\nThe auto-close functionality is working correctly:")
        print("- Sessions open for more than 2 hours are automatically identified")
        print("- Tare weights are estimated based on historical data or vehicle type")
        print("- Synthetic exit events are created with proper notes")
        print("- Recycle vehicles get lower tare weight estimates")
        print("- New vehicles get reasonable weight estimates")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
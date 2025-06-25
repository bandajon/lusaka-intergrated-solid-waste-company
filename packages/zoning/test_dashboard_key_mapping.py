#!/usr/bin/env python3
"""
Test the dashboard key mapping to see exactly what the JavaScript gets
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_key_mapping():
    """Test the exact data structure that goes to JavaScript"""
    print("🔍 TESTING DASHBOARD KEY MAPPING")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test data that matches what the WasteAnalyzer returns
    mock_waste_analysis = {
        'total_waste_kg_day': 308.0,
        'trucks_required': 1,
        'vehicles_required': 1,
        'collection_points': 2,
        'monthly_revenue': 800.8,
        'annual_revenue': 9609.6
    }
    
    print("🔍 Test 1: Dashboard Endpoint Formatting")
    print("-" * 40)
    
    # Simulate the dashboard endpoint formatting
    formatted_data = {
        'zone_id': 'test_zone',
        'zone_name': 'Test Zone',
        'total_waste_kg_day': mock_waste_analysis.get('total_waste_kg_day', 0),  # Fixed mapping
        'daily_waste': mock_waste_analysis.get('total_waste_kg_day', 0),         # Fixed mapping  
        'trucks_needed': mock_waste_analysis.get('trucks_required', 0),         # Correct mapping
        'vehicles_required': mock_waste_analysis.get('trucks_required', 0),     # Correct mapping
        'collection_points': mock_waste_analysis.get('collection_points', 0),
        'monthly_revenue': mock_waste_analysis.get('monthly_revenue', 0),
        'annual_revenue': mock_waste_analysis.get('annual_revenue', 0),
    }
    
    print(f"✅ Formatted data for DashboardCore:")
    for key, value in formatted_data.items():
        if 'waste' in key or 'truck' in key or 'vehicle' in key:
            print(f"   - {key}: {value}")
    
    print("\n🔍 Test 2: DashboardCore Processing")
    print("-" * 40)
    
    try:
        from app.utils.dashboard_core import DashboardCore
        dashboard = DashboardCore()
        
        # Generate dashboard data
        dashboard_data = dashboard.generate_zone_overview_dashboard(formatted_data)
        
        # Extract key metrics
        key_metrics = dashboard_data.get('key_metrics', {})
        
        print(f"✅ Dashboard key_metrics truck-related keys:")
        truck_keys = {k: v for k, v in key_metrics.items() if 'truck' in k or 'vehicle' in k or 'waste' in k}
        for key, value in truck_keys.items():
            print(f"   - {key}: {value}")
        
        # Check nested waste structure
        waste_nested = key_metrics.get('waste', {})
        print(f"✅ Dashboard nested waste structure:")
        for key, value in waste_nested.items():
            print(f"   - waste.{key}: {value}")
        
        # Test what JavaScript would see
        print("\n🔍 Test 3: JavaScript Extraction Simulation")
        print("-" * 40)
        
        # Simulate the JavaScript logic from zone_analyzer.js line 923 and 931
        daily_waste_js = key_metrics.get('daily_waste') or key_metrics.get('total_waste_kg_day', 0)
        trucks_needed_js = key_metrics.get('trucks_needed') or key_metrics.get('vehicles_required') or key_metrics.get('trucks_required', 0)
        
        print(f"🎯 JavaScript would extract:")
        print(f"   - Daily waste: {daily_waste_js} (looking for: daily_waste || total_waste_kg_day)")
        print(f"   - Trucks needed: {trucks_needed_js} (looking for: trucks_needed || vehicles_required || trucks_required)")
        
        if daily_waste_js > 0 and trucks_needed_js > 0:
            print("\n✅ SUCCESS: JavaScript should display non-zero values!")
            return True
        else:
            print(f"\n❌ ISSUE: JavaScript would show zeros")
            print(f"   - Daily waste: {daily_waste_js}")
            print(f"   - Trucks needed: {trucks_needed_js}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 TESTING DASHBOARD KEY MAPPING")
    print("Verifying the exact data structure sent to JavaScript")
    print()
    
    success = test_dashboard_key_mapping()
    
    if success:
        print("\n🎉 SUCCESS: Dashboard key mapping is working!")
        print("The real-time display should show non-zero values")
    else:
        print("\n❌ FAILURE: Dashboard key mapping issues detected")
        print("Need to fix the key mapping between dashboard and JavaScript")
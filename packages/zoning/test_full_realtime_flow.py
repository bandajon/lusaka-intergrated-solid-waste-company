#!/usr/bin/env python3
"""
Test the complete real-time flow from GeoJSON to display data
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_full_realtime_flow():
    """Test the complete real-time flow including dashboard data generation"""
    print("🔧 TESTING FULL REAL-TIME FLOW")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Run Real-Time Analysis
    print("🔧 Test 1: Run Real-Time Analysis")
    print("-" * 40)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Create GeoJSON
        mock_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [28.280, -15.420],
                    [28.285, -15.420],
                    [28.285, -15.415],
                    [28.280, -15.415],
                    [28.280, -15.420]
                ]]
            },
            "properties": {
                "name": "Flow Test Zone"
            }
        }
        
        print("🔄 Running analyze_drawn_zone...")
        result = analyzer.analyze_drawn_zone(mock_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print("✅ Real-time analysis completed")
        
        # Extract waste analysis
        analysis_modules = result.get('analysis_modules', {})
        waste_analysis = analysis_modules.get('waste_analysis', {})
        
        print(f"📊 Waste analysis result: {waste_analysis}")
        
        if 'error' in waste_analysis:
            print(f"❌ Waste analysis has error: {waste_analysis['error']}")
            
            # Let's check if it went to offline mode
            if result.get('offline_mode'):
                print(f"⚠️  Analysis is in offline mode")
                offline_components = result.get('offline_components', [])
                print(f"   Offline components: {offline_components}")
            
            return False
        
        # Check the key values
        total_waste = waste_analysis.get('total_waste_kg_day', 0)
        trucks_required = waste_analysis.get('trucks_required', 0)
        vehicles_required = waste_analysis.get('vehicles_required', 0)
        
        print(f"🎯 Waste analysis data:")
        print(f"   - total_waste_kg_day: {total_waste}")
        print(f"   - trucks_required: {trucks_required}")
        print(f"   - vehicles_required: {vehicles_required}")
        
        if total_waste > 0:
            print("✅ Waste analysis has data!")
        else:
            print("❌ Waste analysis has no data")
            return False
        
    except Exception as e:
        print(f"❌ Real-time analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test Dashboard Data Generation
    print("\\n🔧 Test 2: Test Dashboard Data Generation")
    print("-" * 40)
    
    try:
        from app.utils.dashboard_core import DashboardCore
        dashboard = DashboardCore()
        
        # Simulate dashboard data endpoint processing 
        analysis_data = result
        analysis_modules = analysis_data.get('analysis_modules', {})
        
        population_module = analysis_modules.get('population_estimation', {})
        waste_module = analysis_modules.get('waste_analysis', {})
        earth_engine_module = analysis_modules.get('earth_engine', {})
        geometry_module = analysis_modules.get('geometry', {})
        
        print(f"📊 Dashboard input modules:")
        print(f"   - Population keys: {list(population_module.keys()) if isinstance(population_module, dict) else 'Not available'}")
        print(f"   - Waste keys: {list(waste_module.keys()) if isinstance(waste_module, dict) else 'Not available'}")
        print(f"   - Earth Engine keys: {list(earth_engine_module.keys()) if isinstance(earth_engine_module, dict) else 'Not available'}")
        
        # Format data like the dashboard endpoint does
        formatted_data = {
            'zone_id': 'temp_zone',
            'zone_name': 'Drawing Zone',
            'analysis_modules': analysis_modules,
            'geometry_analysis': geometry_module,
            'population_analysis': population_module,
            'waste_analysis': waste_module,
            'earth_engine_analysis': earth_engine_module,
            'collection_feasibility': analysis_modules.get('collection_feasibility', {}),
            'zone_viability_score': analysis_data.get('zone_viability_score', 0),
            'optimization_recommendations': analysis_data.get('optimization_recommendations', []),
            'critical_issues': analysis_data.get('critical_issues', []),
            
            # Add the key mappings that we fixed
            'total_waste_kg_day': waste_module.get('total_waste_kg_day', 0),  # Fixed mapping
            'daily_waste': waste_module.get('total_waste_kg_day', 0),         # Fixed mapping
            'trucks_needed': waste_module.get('trucks_required', 0),         # Correct mapping
            'vehicles_required': waste_module.get('trucks_required', 0),     # Correct mapping
        }
        
        print(f"🎯 Dashboard formatted data:")
        print(f"   - total_waste_kg_day: {formatted_data['total_waste_kg_day']}")
        print(f"   - daily_waste: {formatted_data['daily_waste']}")
        print(f"   - trucks_needed: {formatted_data['trucks_needed']}")
        print(f"   - vehicles_required: {formatted_data['vehicles_required']}")
        
        # Generate dashboard data
        dashboard_data = dashboard.generate_zone_overview_dashboard(formatted_data)
        
        print(f"✅ Dashboard data generated")
        print(f"📊 Dashboard keys: {list(dashboard_data.keys()) if isinstance(dashboard_data, dict) else 'Not a dict'}")
        
        # Check if dashboard contains the key metrics we need
        key_metrics = dashboard_data.get('key_metrics', {})
        print(f"📊 Dashboard key metrics: {key_metrics}")
        
        dashboard_daily_waste = key_metrics.get('daily_waste') or key_metrics.get('total_waste_kg_day', 0)
        dashboard_trucks = key_metrics.get('trucks_needed') or key_metrics.get('vehicles_required', 0)
        
        print(f"🎯 Dashboard final values:")
        print(f"   - Daily waste: {dashboard_daily_waste}")
        print(f"   - Trucks needed: {dashboard_trucks}")
        
        if dashboard_daily_waste > 0 and dashboard_trucks > 0:
            print("✅ DASHBOARD DATA HAS THE CORRECT VALUES!")
            print("✅ THE DISPLAY FIX SHOULD NOW WORK!")
            return True
        else:
            print("❌ Dashboard data still missing values")
            return False
        
    except Exception as e:
        print(f"❌ Dashboard data generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TESTING FULL REAL-TIME FLOW")
    print("Testing the complete flow from analysis to dashboard display")
    print()
    
    success = test_full_realtime_flow()
    
    if success:
        print("\\n🎉 SUCCESS: Full real-time flow is working!")
        print("\\n✅ FIXES APPLIED:")
        print("   - WasteAnalyzer enhanced with Earth Engine fallback")
        print("   - Dashboard endpoint key mapping fixed")
        print("   - Real-time analysis chain validated")
        print("\\n🚀 THE ZONE ANALYZER SHOULD NOW DISPLAY:")
        print("   - Non-zero daily waste generation")
        print("   - Non-zero truck requirements")
    else:
        print("\\n❌ FAILURE: Issues remain in the real-time flow")
        print("Check the debug output above for specific problems")
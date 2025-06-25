#!/usr/bin/env python3
"""
Test the real-time analyzer to confirm it returns the correct data structure
for the dashboard display with the fixed key mapping
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_realtime_display_data():
    """Test that real-time analyzer returns correct data structure for display"""
    print("🔧 TESTING REAL-TIME DISPLAY DATA STRUCTURE")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Initialize Real-Time Analyzer
    print("🔧 Test 1: Initialize Real-Time Analyzer")
    print("-" * 40)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        print("✅ Real-time analyzer initialized")
        
    except Exception as e:
        print(f"❌ Real-time analyzer initialization failed: {str(e)}")
        return False
    
    # Test 2: Create Mock Zone GeoJSON
    print("\n🔧 Test 2: Create Mock Zone GeoJSON")
    print("-" * 40)
    
    try:
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
                "name": "Test Display Zone"
            }
        }
        
        print("✅ Mock GeoJSON created for real-time analysis")
        
    except Exception as e:
        print(f"❌ Mock GeoJSON creation failed: {str(e)}")
        return False
    
    # Test 3: Run Enhanced Zone Analysis
    print("\n🔧 Test 3: Run Enhanced Zone Analysis")
    print("-" * 40)
    
    try:
        print("🔄 Running analyze_drawn_zone...")
        result = analyzer.analyze_drawn_zone(mock_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print("✅ Enhanced zone analysis completed")
        print(f"📊 Analysis result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Extract the waste analysis module
        analysis_modules = result.get('analysis_modules', {})
        waste_analysis = analysis_modules.get('waste_analysis', {})
        
        print(f"📊 Waste analysis keys: {list(waste_analysis.keys()) if isinstance(waste_analysis, dict) else 'No waste analysis'}")
        
        # Check the specific keys we need for display
        total_waste = waste_analysis.get('total_waste_kg_day', 0)
        trucks_required = waste_analysis.get('trucks_required', 0)
        vehicles_required = waste_analysis.get('vehicles_required', 0)
        
        print(f"🎯 KEY DATA FOR DISPLAY:")
        print(f"   - total_waste_kg_day: {total_waste}")
        print(f"   - trucks_required: {trucks_required}")
        print(f"   - vehicles_required: {vehicles_required}")
        
        if total_waste > 0:
            print("✅ WASTE DATA IS AVAILABLE FOR DISPLAY!")
            
            if trucks_required > 0 or vehicles_required > 0:
                print("✅ TRUCK DATA IS AVAILABLE FOR DISPLAY!")
                return True
            else:
                print("❌ Truck data is missing for display")
                return False
        else:
            print("❌ Waste data is missing for display")
            return False
        
    except Exception as e:
        print(f"❌ Enhanced zone analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TESTING REAL-TIME DISPLAY DATA STRUCTURE")
    print("Verifying that real-time analysis returns the correct data for display")
    print()
    
    success = test_realtime_display_data()
    
    if success:
        print("\n🎉 SUCCESS: Real-time analysis returns correct data structure!")
        print("The dashboard display should now show:")
        print("   - Non-zero daily waste generation")
        print("   - Non-zero truck requirements")
        print("\n✅ DISPLAY FIX SHOULD BE WORKING!")
    else:
        print("\n❌ FAILURE: Data structure issues remain")
        print("Need further investigation of the real-time analysis chain")
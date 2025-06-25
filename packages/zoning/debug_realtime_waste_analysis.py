#!/usr/bin/env python3
"""
Debug the real-time waste analysis to see why it's failing
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_realtime_waste_analysis():
    """Debug the real-time waste analysis failure"""
    print("🔍 DEBUG REAL-TIME WASTE ANALYSIS")
    print("=" * 50)
    print(f"⏰ Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Initialize Real-Time Analyzer and Get Mock Zone
    print("🔍 Test 1: Initialize and Create Mock Zone")
    print("-" * 40)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Create GeoJSON like real-time analysis does
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
                "name": "Debug Zone"
            }
        }
        
        # Create mock zone the same way as in real-time analyzer
        from shapely.geometry import shape
        polygon = shape(mock_geojson['geometry'])
        
        # Create MockZone class similar to real-time analyzer
        class MockZone:
            def __init__(self, geojson):
                self.id = 'debug_realtime_zone'
                self.name = geojson['properties'].get('name', 'Real-Time Zone')
                self.geojson = geojson
                self.geometry = geojson['geometry']
                
                # Calculate area from polygon
                polygon = shape(geojson['geometry'])
                self.area_sqm = polygon.area * 111320 * 111320  # Rough conversion to sqm
                
                # Initialize other required attributes
                self.estimated_population = 0  # Start with 0 to trigger Earth Engine lookup
                self.household_count = 0
                self.business_count = 0
                self.collection_frequency_week = 2
                self.waste_generation_kg_day = 0
                
                # Add zone type
                from app.models import ZoneTypeEnum
                class MockZoneType:
                    def __init__(self, value):
                        self.value = value
                self.zone_type = MockZoneType('mixed')
        
        mock_zone = MockZone(mock_geojson)
        
        print(f"✅ Mock zone created with:")
        print(f"   - ID: {mock_zone.id}")
        print(f"   - Name: {mock_zone.name}")
        print(f"   - Area: {mock_zone.area_sqm} sqm")
        print(f"   - Population: {mock_zone.estimated_population}")
        print(f"   - Zone type: {mock_zone.zone_type.value}")
        
    except Exception as e:
        print(f"❌ Mock zone creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Test Direct WasteAnalyzer Call
    print("\n🔍 Test 2: Test Direct WasteAnalyzer Call")
    print("-" * 40)
    
    try:
        from app.utils.analysis import WasteAnalyzer
        direct_analyzer = WasteAnalyzer()
        
        print("🔄 Calling WasteAnalyzer directly...")
        waste_result = direct_analyzer.analyze_zone(mock_zone, include_advanced=True)
        
        print(f"📊 Direct WasteAnalyzer result keys: {list(waste_result.keys()) if isinstance(waste_result, dict) else 'Not a dict'}")
        
        total_waste = waste_result.get('total_waste_kg_day', 0)
        trucks_required = waste_result.get('trucks_required', 0)
        vehicles_required = waste_result.get('vehicles_required', 0)
        
        print(f"🎯 Direct results:")
        print(f"   - total_waste_kg_day: {total_waste}")
        print(f"   - trucks_required: {trucks_required}")
        print(f"   - vehicles_required: {vehicles_required}")
        
        if total_waste > 0:
            print("✅ Direct WasteAnalyzer working correctly!")
        else:
            print("❌ Direct WasteAnalyzer still returning 0")
        
    except Exception as e:
        print(f"❌ Direct WasteAnalyzer failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test Real-Time Analyzer's _run_enhanced_waste_analysis
    print("\n🔍 Test 3: Test Real-Time Analyzer's _run_enhanced_waste_analysis")
    print("-" * 40)
    
    try:
        print("🔄 Calling _run_enhanced_waste_analysis...")
        
        # Provide empty population estimates and settlement classification
        population_estimates = {'total_population': 0}
        settlement_classification = {'settlement_type': 'mixed'}
        
        waste_result = analyzer._run_enhanced_waste_analysis(
            mock_zone, population_estimates, settlement_classification
        )
        
        print(f"📊 Real-time waste analysis result: {waste_result}")
        
        if 'error' in waste_result:
            print(f"❌ Real-time waste analysis failed: {waste_result['error']}")
            return False
        else:
            total_waste = waste_result.get('total_waste_kg_day', 0)
            trucks_required = waste_result.get('trucks_required', 0)
            vehicles_required = waste_result.get('vehicles_required', 0)
            
            print(f"🎯 Real-time results:")
            print(f"   - total_waste_kg_day: {total_waste}")
            print(f"   - trucks_required: {trucks_required}")
            print(f"   - vehicles_required: {vehicles_required}")
            
            if total_waste > 0:
                print("✅ Real-time waste analysis working correctly!")
                return True
            else:
                print("❌ Real-time waste analysis returning 0")
                return False
        
    except Exception as e:
        print(f"❌ Real-time waste analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 DEBUG REAL-TIME WASTE ANALYSIS")
    print("Investigating why real-time waste analysis is failing")
    print()
    
    success = debug_realtime_waste_analysis()
    
    if success:
        print("\n🎉 SUCCESS: Real-time waste analysis is working!")
        print("The issue might be elsewhere in the data flow")
    else:
        print("\n❌ FAILURE: Real-time waste analysis has issues")
        print("Need to fix the mock zone or analysis chain")
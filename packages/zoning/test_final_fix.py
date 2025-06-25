#!/usr/bin/env python3
"""
Final test to confirm the waste calculation fix is working end-to-end
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_final_fix():
    """Test the complete fix end-to-end"""
    print("🎯 FINAL WASTE CALCULATION FIX TEST")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Clear All Caches
    print("🔧 Test 1: Clear All Caches")
    print("-" * 30)
    
    try:
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Initialize and clear caches
        earth_engine = EarthEngineAnalyzer()
        earth_engine.cache.clear()
        print("🗑️  Cleared Earth Engine cache")
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        if hasattr(analyzer.earth_engine, 'cache'):
            analyzer.earth_engine.cache.clear()
            print("🗑️  Cleared Real-time analyzer cache")
        
    except Exception as e:
        print(f"❌ Cache clearing failed: {str(e)}")
        return False
    
    # Test 2: Test with New Zone ID
    print("\n🔧 Test 2: Test with Fresh Zone")
    print("-" * 30)
    
    try:
        # Create a zone with a unique ID to avoid cache hits
        import time
        unique_id = f"test_zone_fix_{int(time.time())}"
        
        test_zone_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon", 
                "coordinates": [[
                    [28.281, -15.421],  # Slightly different coordinates
                    [28.286, -15.421],
                    [28.286, -15.416],
                    [28.281, -15.416],
                    [28.281, -15.421]
                ]]
            },
            "properties": {
                "name": f"Fix Test Zone {unique_id}",
                "zone_type": "mixed"
            }
        }
        
        print(f"✅ Created test zone with unique ID: {unique_id}")
        
    except Exception as e:
        print(f"❌ Zone creation failed: {str(e)}")
        return False
    
    # Test 3: Run Analysis
    print("\n🔧 Test 3: Run Complete Analysis")
    print("-" * 30)
    
    try:
        print("🔄 Running analysis with cleared cache...")
        result = analyzer.analyze_drawn_zone(test_zone_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        print("✅ Analysis completed successfully")
        
        # Check Earth Engine results
        earth_engine_data = result.get('analysis_modules', {}).get('earth_engine', {})
        if earth_engine_data and 'error' not in earth_engine_data:
            print("✅ Earth Engine data available")
            
            # Check for building features
            building_features = earth_engine_data.get('building_features', {})
            if building_features and 'error' not in building_features:
                print("✅ Building features available")
                
                # Check for waste generation
                waste_gen = building_features.get('waste_generation', {})
                if waste_gen and 'error' not in waste_gen:
                    print("✅ Waste generation data available")
                    
                    # Check daily waste
                    daily_waste = waste_gen.get('daily_waste_generation', {})
                    if daily_waste:
                        avg_daily = daily_waste.get('annual_average_kg_day', 0)
                        if avg_daily > 0:
                            print(f"✅ Daily waste calculated: {avg_daily} kg/day")
                            
                            # Check truck requirements
                            collection_reqs = waste_gen.get('collection_requirements', {})
                            if collection_reqs:
                                vehicles = collection_reqs.get('vehicles_required', {})
                                if vehicles:
                                    trucks_10t = vehicles.get('10_tonne_trucks', 0)
                                    trucks_20t = vehicles.get('20_tonne_trucks', 0)
                                    
                                    print(f"✅ TRUCK REQUIREMENTS CALCULATED:")
                                    print(f"   - 10-tonne trucks: {trucks_10t}")
                                    print(f"   - 20-tonne trucks: {trucks_20t}")
                                    
                                    if trucks_10t > 0 or trucks_20t > 0:
                                        print("\n🎉 SUCCESS: WASTE GENERATION AND TRUCK CALCULATIONS ARE WORKING!")
                                        
                                        # Additional details
                                        frequency = collection_reqs.get('recommended_collection_frequency', 'Unknown')
                                        print(f"   - Collection frequency: {frequency}")
                                        
                                        annual_tonnes = daily_waste.get('annual_total_tonnes', 0)
                                        print(f"   - Annual waste: {annual_tonnes} tonnes/year")
                                        
                                        return True
                                    else:
                                        print("❌ Truck requirements calculated but returned 0")
                                else:
                                    print("❌ No vehicles_required in collection requirements")
                            else:
                                print("❌ No collection_requirements found")
                        else:
                            print("❌ Daily waste is 0")
                    else:
                        print("❌ No daily_waste_generation data")
                else:
                    print(f"❌ Waste generation error: {waste_gen.get('error', 'Unknown error')}")
            else:
                print(f"❌ Building features error: {building_features.get('error', 'No building features')}")
        else:
            print(f"❌ Earth Engine error: {earth_engine_data.get('error', 'No Earth Engine data')}")
        
        return False
        
    except Exception as e:
        print(f"❌ Analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 FINAL WASTE CALCULATION FIX TEST")
    print("Testing the complete fix for waste generation and truck calculations")
    print()
    
    success = test_final_fix()
    
    if success:
        print("\n🏆 MISSION ACCOMPLISHED!")
        print("The zone analyzer is now calculating waste produced and number of trucks needed!")
        print("\n✅ FIXED ISSUES:")
        print("   - Zone analyzer now calculates waste generation")
        print("   - Truck requirements (10-tonne and 20-tonne) are calculated")
        print("   - Collection frequency recommendations are provided")
        print("   - Fallback population estimation is implemented")
        print("   - Enhanced error handling and debugging added")
    else:
        print("\n❌ Still need to investigate further...")
        print("Check the output above for specific error details")
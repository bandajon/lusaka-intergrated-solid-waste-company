#!/usr/bin/env python3
"""
Test the real-time zone analyzer to see if it can calculate waste and trucks
This will test the actual integration point where the issue occurs
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_real_time_analyzer():
    """Test the real-time zone analyzer end-to-end"""
    print("🧪 TESTING REAL-TIME ZONE ANALYZER")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Initialize Real-Time Analyzer
    print("🧪 Test 1: Initialize EnhancedRealTimeZoneAnalyzer")
    print("-" * 50)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        print("✅ Real-time analyzer initialized successfully")
        
        # Check if Earth Engine is available
        if analyzer.earth_engine and hasattr(analyzer.earth_engine, 'initialized'):
            print(f"✅ Earth Engine available: {analyzer.earth_engine.initialized}")
        else:
            print("❌ Earth Engine not available in analyzer")
            
    except Exception as e:
        print(f"❌ Real-time analyzer initialization failed: {str(e)}")
        return False
    
    # Test 2: Create Test Zone GeoJSON
    print("\n🧪 Test 2: Create Test Zone in Central Lusaka")
    print("-" * 50)
    
    try:
        # Create a realistic zone in central Lusaka (near Cairo Road area)
        test_zone_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [28.280, -15.420],  # Southwest
                    [28.285, -15.420],  # Southeast
                    [28.285, -15.415],  # Northeast
                    [28.280, -15.415],  # Northwest
                    [28.280, -15.420]   # Close polygon
                ]]
            },
            "properties": {
                "name": "Test Zone - Central Lusaka",
                "zone_type": "mixed",
                "description": "Test zone for waste calculation debugging"
            }
        }
        
        print("✅ Test zone GeoJSON created")
        print(f"   Zone area: ~0.5 km² in central Lusaka")
        print(f"   Coordinates: {test_zone_geojson['geometry']['coordinates'][0]}")
        
    except Exception as e:
        print(f"❌ Test zone creation failed: {str(e)}")
        return False
    
    # Test 3: Analyze Zone for Waste and Trucks
    print("\n🧪 Test 3: Analyze Zone for Waste Generation and Truck Requirements")
    print("-" * 50)
    
    try:
        # Optional metadata
        zone_metadata = {
            "zone_type": "mixed",
            "priority": "high",
            "expected_population": 3000
        }
        
        print("🔄 Running comprehensive zone analysis...")
        analysis_result = analyzer.analyze_drawn_zone(test_zone_geojson, zone_metadata)
        
        if 'error' in analysis_result:
            print(f"❌ Zone analysis failed: {analysis_result['error']}")
            return False
        
        print("✅ Zone analysis completed successfully")
        print()
        
        # Check waste generation results
        print("📊 WASTE GENERATION RESULTS:")
        print("-" * 30)
        
        waste_data = analysis_result.get('analysis_modules', {}).get('earth_engine', {})
        if waste_data and 'error' not in waste_data:
            # Look for waste generation in the results
            building_features = waste_data.get('building_features', {})
            if building_features and 'error' not in building_features:
                waste_gen = building_features.get('waste_generation', {})
                if waste_gen and 'error' not in waste_gen:
                    daily_waste = waste_gen.get('daily_waste_generation', {})
                    if daily_waste:
                        avg_daily = daily_waste.get('annual_average_kg_day', 0)
                        print(f"✅ Daily waste generation: {avg_daily} kg/day")
                        
                        annual_tonnes = daily_waste.get('annual_total_tonnes', 0)
                        print(f"✅ Annual waste: {annual_tonnes} tonnes/year")
                        
                        # Check truck requirements
                        collection_reqs = waste_gen.get('collection_requirements', {})
                        if collection_reqs:
                            vehicles = collection_reqs.get('vehicles_required', {})
                            if vehicles:
                                trucks_10t = vehicles.get('10_tonne_trucks', 0)
                                trucks_20t = vehicles.get('20_tonne_trucks', 0)
                                print(f"✅ Truck requirements:")
                                print(f"   - 10-tonne trucks: {trucks_10t}")
                                print(f"   - 20-tonne trucks: {trucks_20t}")
                            else:
                                print("❌ No truck requirements calculated")
                        else:
                            print("❌ No collection requirements found")
                    else:
                        print("❌ No daily waste generation data")
                else:
                    print("❌ No waste generation data found")
                    if 'error' in waste_gen:
                        print(f"   Error: {waste_gen['error']}")
            else:
                print("❌ No building features found")
                if 'error' in building_features:
                    print(f"   Error: {building_features['error']}")
        else:
            print("❌ No Earth Engine data found")
            if 'error' in waste_data:
                print(f"   Error: {waste_data['error']}")
        
        # Check population data
        print("\n📊 POPULATION DATA:")
        print("-" * 20)
        
        population_data = analysis_result.get('analysis_modules', {}).get('population_estimation', {})
        if population_data and 'error' not in population_data:
            total_pop = population_data.get('estimated_population', 0)
            print(f"✅ Estimated population: {total_pop}")
        else:
            print("❌ No population estimation found")
            if 'error' in population_data:
                print(f"   Error: {population_data['error']}")
        
        # Check if we have offline mode components
        offline_components = analysis_result.get('offline_components', [])
        if offline_components:
            print(f"\n⚠️  OFFLINE MODE: {len(offline_components)} components using fallback")
            for component in offline_components:
                print(f"   - {component}")
        
        # Overall zone viability score
        viability_score = analysis_result.get('zone_viability_score', 0)
        print(f"\n📈 Zone viability score: {viability_score}/100")
        
        # Critical issues
        critical_issues = analysis_result.get('critical_issues', [])
        if critical_issues:
            print(f"\n⚠️  Critical issues found:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
    except Exception as e:
        print(f"❌ Zone analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    # Determine if waste and truck calculations worked
    waste_calculated = False
    trucks_calculated = False
    
    try:
        earth_engine_data = analysis_result.get('analysis_modules', {}).get('earth_engine', {})
        if earth_engine_data and 'error' not in earth_engine_data:
            building_features = earth_engine_data.get('building_features', {})
            if building_features and 'error' not in building_features:
                waste_gen = building_features.get('waste_generation', {})
                if waste_gen and 'error' not in waste_gen:
                    daily_waste = waste_gen.get('daily_waste_generation', {})
                    if daily_waste and daily_waste.get('annual_average_kg_day', 0) > 0:
                        waste_calculated = True
                    
                    collection_reqs = waste_gen.get('collection_requirements', {})
                    if collection_reqs:
                        vehicles = collection_reqs.get('vehicles_required', {})
                        if vehicles and (vehicles.get('10_tonne_trucks', 0) > 0 or vehicles.get('20_tonne_trucks', 0) > 0):
                            trucks_calculated = True
    except:
        pass
    
    print(f"✅ Waste generation calculated: {'YES' if waste_calculated else 'NO'}")
    print(f"✅ Truck requirements calculated: {'YES' if trucks_calculated else 'NO'}")
    
    if waste_calculated and trucks_calculated:
        print("\n🎉 SUCCESS: Both waste generation and truck calculations are working!")
        print("💡 The zone analyzer is functioning correctly")
    elif waste_calculated:
        print("\n⚠️  PARTIAL SUCCESS: Waste calculated but truck requirements missing")
        print("💡 Check truck calculation logic")
    else:
        print("\n❌ FAILURE: Waste generation calculations not working")
        print("💡 Check Earth Engine integration and population data")
    
    return waste_calculated and trucks_calculated

if __name__ == "__main__":
    print("🧪 REAL-TIME ZONE ANALYZER TEST")
    print("Testing waste generation and truck calculation functionality")
    print()
    
    success = test_real_time_analyzer()
    
    if success:
        print("\n🏁 Test completed successfully - system is working!")
    else:
        print("\n❌ Test identified issues that need fixing")
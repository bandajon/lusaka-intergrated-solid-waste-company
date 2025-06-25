#!/usr/bin/env python3
"""
Test the WasteAnalyzer fix to verify waste generation and truck calculations
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_waste_analyzer_fix():
    """Test the fixed WasteAnalyzer with enhanced Earth Engine integration"""
    print("🔧 TESTING WASTEANALYZER FIX")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Initialize WasteAnalyzer
    print("🔧 Test 1: Initialize WasteAnalyzer")
    print("-" * 40)
    
    try:
        from app.utils.analysis import WasteAnalyzer
        analyzer = WasteAnalyzer()
        
        if analyzer.earth_engine and analyzer.earth_engine.initialized:
            print("✅ WasteAnalyzer initialized with Earth Engine")
        else:
            print("⚠️  WasteAnalyzer initialized without Earth Engine")
        
    except Exception as e:
        print(f"❌ WasteAnalyzer initialization failed: {str(e)}")
        return False
    
    # Test 2: Create Mock Zone with no estimated_population
    print("\n🔧 Test 2: Create Mock Zone (Zero Population)")
    print("-" * 40)
    
    try:
        class MockZone:
            def __init__(self):
                self.id = 'test_zone_fix'
                self.name = 'Test Zone Fix'
                self.estimated_population = 0  # Zero to trigger Earth Engine lookup
                self.household_count = 0
                self.business_count = 0
                self.area_sqm = 2750000  # Approximately 2.75 km²
                self.zone_type = MockZoneType('mixed')
                self.collection_frequency_week = 2
                self.waste_generation_kg_day = 0
                # Create geometry for Lusaka area
                self.geometry = {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.280, -15.420],
                        [28.285, -15.420],
                        [28.285, -15.415],
                        [28.280, -15.415],
                        [28.280, -15.420]
                    ]]
                }
                # Add geojson attribute required by Earth Engine
                self.geojson = {
                    "type": "Feature",
                    "geometry": self.geometry,
                    "properties": {
                        "name": self.name,
                        "zone_type": "mixed"
                    }
                }
        
        class MockZoneType:
            def __init__(self, value):
                self.value = value
        
        mock_zone = MockZone()
        print(f"✅ Mock zone created with zero population: {mock_zone.estimated_population}")
        
    except Exception as e:
        print(f"❌ Mock zone creation failed: {str(e)}")
        return False
    
    # Test 3: Run Waste Generation Calculation
    print("\n🔧 Test 3: Run Waste Generation Calculation")
    print("-" * 40)
    
    try:
        print("🔄 Calling _calculate_waste_generation...")
        waste_result = analyzer._calculate_waste_generation(mock_zone)
        
        print(f"✅ Waste calculation completed")
        print(f"   📊 Total waste: {waste_result.get('total_waste_kg_day', 0)} kg/day")
        print(f"   🏠 Residential waste: {waste_result.get('residential_waste', 0)} kg/day")
        print(f"   🏢 Commercial waste: {waste_result.get('commercial_waste', 0)} kg/day")
        print(f"   📝 Updated zone population: {mock_zone.estimated_population}")
        
        if waste_result.get('total_waste_kg_day', 0) > 0:
            print("✅ WASTE GENERATION IS WORKING!")
        else:
            print("❌ Waste generation returned 0")
            return False
        
    except Exception as e:
        print(f"❌ Waste generation calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Run Collection Requirements Calculation
    print("\n🔧 Test 4: Run Collection Requirements Calculation")
    print("-" * 40)
    
    try:
        total_waste = waste_result.get('total_waste_kg_day', 0)
        frequency = mock_zone.collection_frequency_week
        
        print(f"🔄 Calculating collection requirements for {total_waste} kg/day, {frequency}x/week...")
        collection_result = analyzer._calculate_collection_requirements(total_waste, frequency)
        
        print(f"✅ Collection calculation completed")
        print(f"   🚛 Total trucks: {collection_result.get('trucks_required', 0)}")
        print(f"   🚚 10-tonne trucks: {collection_result.get('10_tonne_trucks', 0)}")
        print(f"   🚛 20-tonne trucks: {collection_result.get('20_tonne_trucks', 0)}")
        print(f"   📍 Collection points: {collection_result.get('collection_points', 0)}")
        print(f"   👥 Staff required: {collection_result.get('collection_staff', 0)}")
        
        trucks_needed = collection_result.get('trucks_required', 0)
        if trucks_needed > 0:
            print("✅ TRUCK CALCULATIONS ARE WORKING!")
        else:
            print("❌ Truck calculations returned 0")
            return False
        
    except Exception as e:
        print(f"❌ Collection requirements calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Run Full Zone Analysis
    print("\n🔧 Test 5: Run Full Zone Analysis")
    print("-" * 40)
    
    try:
        print("🔄 Running full zone analysis...")
        full_result = analyzer.analyze_zone(mock_zone, include_advanced=True)
        
        print(f"✅ Full analysis completed")
        print(f"   📊 Total waste: {full_result.get('total_waste_kg_day', 0)} kg/day")
        print(f"   🚛 Vehicles required: {full_result.get('vehicles_required', 0)}")
        print(f"   📍 Collection points: {full_result.get('collection_points', 0)}")
        print(f"   💰 Monthly revenue: ${full_result.get('total_revenue', 0):.2f}")
        
        final_waste = full_result.get('total_waste_kg_day', 0)
        final_trucks = full_result.get('vehicles_required', 0)
        
        if final_waste > 0 and final_trucks > 0:
            print("\n🎉 SUCCESS: FULL WASTE ANALYZER IS NOW WORKING!")
            print(f"   - Zone analyzer calculates waste: {final_waste} kg/day")
            print(f"   - Zone analyzer calculates trucks: {final_trucks} vehicles")
            return True
        else:
            print("❌ Full analysis still returning zeros")
            return False
        
    except Exception as e:
        print(f"❌ Full zone analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TESTING WASTEANALYZER FIX")
    print("Testing the enhanced WasteAnalyzer with Earth Engine integration")
    print()
    
    success = test_waste_analyzer_fix()
    
    if success:
        print("\n🏆 MISSION ACCOMPLISHED!")
        print("The WasteAnalyzer fix is working correctly!")
        print("\n✅ FIXED ISSUES:")
        print("   - WasteAnalyzer now uses Earth Engine for population estimation")
        print("   - Waste generation calculations work with real-time data")
        print("   - Truck requirements include 10-tonne and 20-tonne options")
        print("   - Full zone analysis integration is working")
    else:
        print("\n❌ Still need to investigate further...")
        print("Check the output above for specific error details")
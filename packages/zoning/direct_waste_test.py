#!/usr/bin/env python3
"""
Direct test of the waste generation calculation to pinpoint the exact issue
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_waste_calculation():
    """Test waste calculation directly without caching"""
    print("🧪 DIRECT WASTE CALCULATION TEST")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Initialize Earth Engine Analyzer
    print("🔧 Test 1: Initialize Earth Engine Analyzer")
    print("-" * 40)
    
    try:
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        earth_engine = EarthEngineAnalyzer()
        
        if not earth_engine.initialized:
            print("❌ Earth Engine not initialized - aborting test")
            return False
        
        print("✅ Earth Engine initialized successfully")
        
    except Exception as e:
        print(f"❌ Earth Engine initialization failed: {str(e)}")
        return False
    
    # Test 2: Create Mock Zone
    print("\n🔧 Test 2: Create Mock Zone")
    print("-" * 40)
    
    try:
        class MockZone:
            def __init__(self):
                self.id = 'direct_test_zone'
                self.name = 'Direct Test Zone'
                self.geojson = {
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
                        "name": "Direct Test Zone"
                    }
                }
                self.area_sqm = 2750000  # Approximately 2.75 km²
        
        mock_zone = MockZone()
        print("✅ Mock zone created successfully")
        
    except Exception as e:
        print(f"❌ Mock zone creation failed: {str(e)}")
        return False
    
    # Test 3: Clear Cache and Test GHSL Population Extraction
    print("\n🔧 Test 3: GHSL Population Extraction (Fresh)")
    print("-" * 40)
    
    try:
        # Clear any existing cache
        earth_engine.cache.clear()
        print("🗑️  Cleared Earth Engine cache")
        
        # Test GHSL population extraction directly
        ghsl_result = earth_engine.extract_ghsl_population_for_zone(mock_zone, 2025)
        
        if 'error' in ghsl_result:
            print(f"❌ GHSL extraction failed: {ghsl_result['error']}")
            return False
        
        population = ghsl_result.get('total_population', 0)
        print(f"✅ GHSL population extracted: {population} people")
        
        if population == 0:
            print("⚠️  Population is 0 - this will trigger fallback logic")
        
    except Exception as e:
        print(f"❌ GHSL extraction failed with exception: {str(e)}")
        return False
    
    # Test 4: Test Building Density Metrics
    print("\n🔧 Test 4: Building Density Metrics")
    print("-" * 40)
    
    try:
        # Create mock building data
        mock_buildings_data = {
            'building_count': 50,
            'building_footprints': [{'area': 100, 'perimeter': 40} for _ in range(50)]
        }
        
        density_features = earth_engine.calculate_building_density_metrics(mock_zone, mock_buildings_data)
        
        if 'error' in density_features:
            print(f"❌ Density calculation failed: {density_features['error']}")
            density_features = {'building_count': 50}  # Fallback
        else:
            print("✅ Building density features calculated")
        
    except Exception as e:
        print(f"❌ Density calculation failed: {str(e)}")
        density_features = {'building_count': 50}  # Fallback
    
    # Test 5: Test Building Area Features
    print("\n🔧 Test 5: Building Area Features")
    print("-" * 40)
    
    try:
        area_features = earth_engine.calculate_detailed_building_areas(mock_zone, mock_buildings_data)
        
        if 'error' in area_features:
            print(f"❌ Area calculation failed: {area_features['error']}")
            area_features = {'total_area_sqkm': 2.75}  # Fallback
        else:
            print("✅ Building area features calculated")
        
    except Exception as e:
        print(f"❌ Area calculation failed: {str(e)}")
        area_features = {'total_area_sqkm': 2.75}  # Fallback
    
    # Test 6: Direct Waste Generation Calculation
    print("\n🔧 Test 6: Direct Waste Generation Calculation")
    print("-" * 40)
    
    try:
        print(f"🔄 Calling waste generation with:")
        print(f"   - Population: {ghsl_result.get('total_population', 0)}")
        print(f"   - Density features: {density_features}")
        print(f"   - Area features: {area_features}")
        
        waste_result = earth_engine.calculate_comprehensive_waste_generation(
            ghsl_result, density_features, area_features, mock_zone
        )
        
        if 'error' in waste_result:
            print(f"❌ Waste calculation failed: {waste_result['error']}")
            return False
        
        print("✅ Waste generation calculated successfully!")
        
        # Extract results
        daily_waste = waste_result.get('daily_waste_generation', {})
        if daily_waste:
            avg_daily = daily_waste.get('annual_average_kg_day', 0)
            annual_tonnes = daily_waste.get('annual_total_tonnes', 0)
            print(f"   📊 Daily waste: {avg_daily} kg/day")
            print(f"   📊 Annual waste: {annual_tonnes} tonnes/year")
        
        # Check collection requirements
        collection_reqs = waste_result.get('collection_requirements', {})
        if collection_reqs:
            vehicles = collection_reqs.get('vehicles_required', {})
            if vehicles:
                trucks_10t = vehicles.get('10_tonne_trucks', 0)
                trucks_20t = vehicles.get('20_tonne_trucks', 0)
                print(f"   🚛 Truck requirements:")
                print(f"      - 10-tonne trucks: {trucks_10t}")
                print(f"      - 20-tonne trucks: {trucks_20t}")
                
                if trucks_10t > 0 or trucks_20t > 0:
                    print("✅ TRUCK CALCULATIONS WORKING!")
                    return True
                else:
                    print("❌ Truck calculations returned 0")
            else:
                print("❌ No vehicle requirements in collection requirements")
        else:
            print("❌ No collection requirements calculated")
        
        return False
        
    except Exception as e:
        print(f"❌ Waste generation calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 DIRECT WASTE CALCULATION TEST")
    print("Testing waste generation and truck calculations directly")
    print()
    
    success = test_direct_waste_calculation()
    
    if success:
        print("\n🎉 SUCCESS: Direct waste and truck calculations are working!")
    else:
        print("\n❌ FAILURE: Direct calculations still not working correctly")
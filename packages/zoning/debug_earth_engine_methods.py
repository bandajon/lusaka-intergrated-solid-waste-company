#!/usr/bin/env python3
"""
Debug Earth Engine methods to understand why population estimation fails
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_earth_engine_methods():
    """Debug each Earth Engine method individually"""
    print("🔬 DEBUG EARTH ENGINE METHODS")
    print("=" * 50)
    print(f"⏰ Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize Earth Engine
    try:
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        earth_engine = EarthEngineAnalyzer()
        
        if not earth_engine.initialized:
            print("❌ Earth Engine not initialized - aborting debug")
            return False
        
        print("✅ Earth Engine initialized successfully")
        
    except Exception as e:
        print(f"❌ Earth Engine initialization failed: {str(e)}")
        return False
    
    # Create Mock Zone
    try:
        class MockZone:
            def __init__(self):
                self.id = 'debug_zone'
                self.name = 'Debug Zone'
                self.area_sqm = 2750000  # Approximately 2.75 km²
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
                self.geojson = {
                    "type": "Feature",
                    "geometry": self.geometry,
                    "properties": {"name": self.name}
                }
        
        mock_zone = MockZone()
        print(f"✅ Mock zone created with area: {mock_zone.area_sqm} sqm")
        
    except Exception as e:
        print(f"❌ Mock zone creation failed: {str(e)}")
        return False
    
    # Test 1: GHSL Population Extraction
    print("\n🔬 Test 1: GHSL Population Extraction")
    print("-" * 40)
    
    try:
        print("🔄 Testing extract_ghsl_population_for_zone...")
        ghsl_result = earth_engine.extract_ghsl_population_for_zone(mock_zone, 2025)
        
        print(f"📊 GHSL Result: {ghsl_result}")
        
        if 'error' in ghsl_result:
            print(f"❌ GHSL extraction failed: {ghsl_result['error']}")
        else:
            population = ghsl_result.get('total_population', 0)
            print(f"✅ GHSL population: {population} people")
            if population > 0:
                print("🎉 GHSL population extraction is working!")
            else:
                print("⚠️  GHSL returned 0 population")
        
    except Exception as e:
        print(f"❌ GHSL extraction error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Building Extraction  
    print("\n🔬 Test 2: Building Extraction")
    print("-" * 40)
    
    try:
        print("🔄 Testing extract_buildings_for_zone...")
        buildings_result = earth_engine.extract_buildings_for_zone(mock_zone)
        
        print(f"📊 Buildings Result keys: {list(buildings_result.keys()) if isinstance(buildings_result, dict) else 'Not a dict'}")
        
        if 'error' in buildings_result:
            print(f"❌ Building extraction failed: {buildings_result['error']}")
        else:
            building_count = buildings_result.get('building_count', 0)
            print(f"✅ Building count: {building_count} buildings")
            if building_count > 0:
                print("🎉 Building extraction is working!")
                print(f"   📊 Buildings data: {buildings_result}")
            else:
                print("⚠️  Building extraction returned 0 buildings")
        
    except Exception as e:
        print(f"❌ Building extraction error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Comprehensive Building Features
    print("\n🔬 Test 3: Comprehensive Building Features")
    print("-" * 40)
    
    try:
        print("🔄 Testing extract_comprehensive_building_features...")
        comp_result = earth_engine.extract_comprehensive_building_features(mock_zone)
        
        print(f"📊 Comprehensive Result keys: {list(comp_result.keys()) if isinstance(comp_result, dict) else 'Not a dict'}")
        
        if 'error' in comp_result:
            print(f"❌ Comprehensive building failed: {comp_result['error']}")
        else:
            print(f"✅ Comprehensive building features extracted")
            print(f"   📊 Data: {comp_result}")
        
    except Exception as e:
        print(f"❌ Comprehensive building error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Alternative Population Methods
    print("\n🔬 Test 4: Alternative Population Methods")
    print("-" * 40)
    
    try:
        # Check if there are other population methods
        methods = [method for method in dir(earth_engine) if 'population' in method.lower()]
        print(f"📋 Available population methods: {methods}")
        
        for method_name in methods:
            if method_name.startswith('_'):
                continue
            print(f"🔄 Testing {method_name}...")
            
            try:
                method = getattr(earth_engine, method_name)
                if callable(method):
                    # Try calling with zone parameter
                    if 'worldpop' in method_name.lower():
                        result = method(mock_zone, year=2020)
                    else:
                        result = method(mock_zone)
                    print(f"   ✅ {method_name}: {result}")
                    
                    if isinstance(result, dict) and not result.get('error'):
                        pop = result.get('estimated_population') or result.get('total_population', 0)
                        if pop > 0:
                            print(f"   🎉 {method_name} found {pop} people!")
            except Exception as method_error:
                print(f"   ⚠️  {method_name} failed: {str(method_error)}")
        
    except Exception as e:
        print(f"❌ Alternative methods test failed: {str(e)}")
    
    print("\n📝 DEBUG COMPLETE")
    return True

if __name__ == "__main__":
    print("🔬 DEBUG EARTH ENGINE METHODS")
    print("Testing individual Earth Engine methods to find population data")
    print()
    
    debug_earth_engine_methods()
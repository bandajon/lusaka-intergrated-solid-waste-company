#!/usr/bin/env python3
"""
Test Earth Engine Population Data Retrieval
Checks authentication and data source availability
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.earth_engine_analysis import EarthEngineAnalyzer
import json
import traceback

def test_earth_engine_status():
    """Test Earth Engine authentication and initialization"""
    print("🔍 Testing Earth Engine Authentication Status")
    print("=" * 60)
    
    try:
        analyzer = EarthEngineAnalyzer()
        status = analyzer.get_auth_status()
        
        print(f"✅ Initialized: {status['initialized']}")
        print(f"📊 Can Provide Estimates: {status['can_provide_estimates']}")
        
        if status['error_details']:
            print(f"❌ Error Details: {status['error_details']}")
        
        return analyzer, status['initialized']
        
    except Exception as e:
        print(f"❌ Failed to initialize Earth Engine: {str(e)}")
        traceback.print_exc()
        return None, False

def test_worldpop_data(analyzer):
    """Test WorldPop data retrieval"""
    print("\n🌍 Testing WorldPop Data Retrieval")
    print("=" * 60)
    
    if not analyzer or not analyzer.initialized:
        print("❌ Earth Engine not initialized - cannot test WorldPop")
        return None
    
    try:
        # Test WorldPop connection
        worldpop_result = analyzer.connect_to_worldpop()
        print("WorldPop Connection Result:")
        print(json.dumps(worldpop_result, indent=2))
        
        if not worldpop_result.get('error'):
            print("✅ WorldPop connection successful")
            
            # Test Lusaka data fetch
            print("\n📍 Testing Lusaka WorldPop Data Fetch...")
            lusaka_data = analyzer.fetch_worldpop_lusaka(year=2020)
            print("Lusaka WorldPop Data:")
            print(json.dumps(lusaka_data, indent=2))
            
            return lusaka_data
        else:
            print(f"❌ WorldPop connection failed: {worldpop_result['error']}")
            return None
            
    except Exception as e:
        print(f"❌ WorldPop test failed: {str(e)}")
        traceback.print_exc()
        return None

def test_zone_population_estimation(analyzer):
    """Test population estimation with a mock zone"""
    print("\n🏘️ Testing Zone Population Estimation")
    print("=" * 60)
    
    # Create a mock zone for testing (small area in Lusaka)
    mock_zone_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.2800, -15.4200],
                [28.2850, -15.4200],
                [28.2850, -15.4150],
                [28.2800, -15.4150],
                [28.2800, -15.4200]
            ]]
        },
        "properties": {
            "name": "Test Zone Lusaka Central"
        }
    }
    
    class MockZone:
        def __init__(self, geojson):
            self.geojson = geojson
            self.id = "test_zone_001"
            # Calculate approximate area (rough estimation)
            self.area_sqm = 0.005 * 0.005 * 111320 * 111320  # ~0.31 km²
    
    mock_zone = MockZone(mock_zone_geojson)
    
    print(f"📏 Test Zone Area: ~{mock_zone.area_sqm/1000000:.2f} km²")
    
    # Test different population estimation methods
    results = {}
    
    # 1. Test Earth Engine population estimation
    if analyzer and analyzer.initialized:
        try:
            print("\n1️⃣ Testing Earth Engine Population Estimation...")
            ee_result = analyzer.get_population_estimate(mock_zone)
            results['earth_engine'] = ee_result
            print("Earth Engine Result:")
            print(json.dumps(ee_result, indent=2))
            
            if not ee_result.get('error'):
                print(f"✅ Earth Engine Estimate: {ee_result.get('estimated_population', 0)} people")
                print(f"📊 Data Source: {ee_result.get('data_source', 'Unknown')}")
            else:
                print(f"❌ Earth Engine Error: {ee_result['error']}")
                
        except Exception as e:
            print(f"❌ Earth Engine population test failed: {str(e)}")
            results['earth_engine'] = {'error': str(e)}
    else:
        print("❌ Earth Engine not available for population testing")
        results['earth_engine'] = {'error': 'Earth Engine not initialized'}
    
    # 2. Test enhanced fallback method
    print("\n2️⃣ Testing Enhanced Fallback Population Estimation...")
    try:
        # This should trigger the fallback we implemented
        if analyzer:
            fallback_result = analyzer.get_population_estimate(mock_zone)
            results['fallback'] = fallback_result
            print("Fallback Result:")
            print(json.dumps(fallback_result, indent=2))
        else:
            # Manual fallback calculation
            area_km2 = mock_zone.area_sqm / 1000000
            building_coverage = 0.30
            people_per_sqm = 0.11
            
            building_area_sqm = mock_zone.area_sqm * building_coverage
            building_estimate = building_area_sqm * people_per_sqm
            area_estimate = area_km2 * 5000
            final_estimate = max(building_estimate, area_estimate)
            
            fallback_result = {
                'estimated_population': int(final_estimate),
                'method': 'manual_fallback',
                'building_estimate': int(building_estimate),
                'area_estimate': int(area_estimate),
                'data_source': 'Manual Analysis.md Methodology'
            }
            results['manual_fallback'] = fallback_result
            print("Manual Fallback Result:")
            print(json.dumps(fallback_result, indent=2))
            
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        results['fallback'] = {'error': str(e)}
    
    return results

def main():
    """Main test function"""
    print("🚀 Earth Engine Population Data Test Suite")
    print("=" * 80)
    
    # 1. Test Earth Engine authentication
    analyzer, ee_initialized = test_earth_engine_status()
    
    # 2. Test WorldPop data if Earth Engine is available
    worldpop_data = None
    if ee_initialized:
        worldpop_data = test_worldpop_data(analyzer)
    
    # 3. Test zone population estimation
    population_results = test_zone_population_estimation(analyzer)
    
    # 4. Summary
    print("\n📋 SUMMARY")
    print("=" * 60)
    print(f"🔐 Earth Engine Initialized: {ee_initialized}")
    
    if worldpop_data:
        print(f"🌍 WorldPop Available: {not worldpop_data.get('error', True)}")
        if not worldpop_data.get('error'):
            print(f"📊 WorldPop Data Years: {worldpop_data.get('available_years', [])}")
    else:
        print("🌍 WorldPop Available: False")
    
    print("\n🏘️ Population Estimation Results:")
    for method, result in population_results.items():
        if not result.get('error'):
            pop = result.get('estimated_population', 0)
            source = result.get('data_source', 'Unknown')
            print(f"   {method}: {pop} people (Source: {source})")
        else:
            print(f"   {method}: Error - {result['error']}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if not ee_initialized:
        print("   • Earth Engine authentication needed for full functionality")
        print("   • System will use enhanced fallback methods (analysis.md)")
        print("   • Consider running 'earthengine authenticate' or setting up service account")
    
    if ee_initialized and (not worldpop_data or worldpop_data.get('error')):
        print("   • Earth Engine authenticated but WorldPop data not accessible")
        print("   • Check network connectivity and Earth Engine permissions")
    
    if ee_initialized and worldpop_data and not worldpop_data.get('error'):
        print("   • ✅ Full Earth Engine functionality available")
        print("   • Population data should come from WorldPop with high confidence")

if __name__ == "__main__":
    main()
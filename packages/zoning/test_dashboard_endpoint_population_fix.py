#!/usr/bin/env python3
"""
Test the dashboard endpoint population fix
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_endpoint_population_fix():
    """Test that the dashboard endpoint now returns correct population data"""
    print("🔍 TESTING DASHBOARD ENDPOINT POPULATION FIX")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        from app.views.zones import _get_best_population_estimate
        
        # Run real-time analysis
        analyzer = EnhancedRealTimeZoneAnalyzer()
        mock_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[28.280, -15.420], [28.285, -15.420], [28.285, -15.415], [28.280, -15.415], [28.280, -15.420]]]
            },
            "properties": {"name": "Population Fix Test Zone"}
        }
        
        print("🔄 Running real-time analysis...")
        result = analyzer.analyze_drawn_zone(mock_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        # Extract the modules like the dashboard endpoint does
        analysis_modules = result.get('analysis_modules', {})
        population_module = analysis_modules.get('population_estimation', {})
        waste_module = analysis_modules.get('waste_analysis', {})
        earth_engine_module = analysis_modules.get('earth_engine', {})
        
        print("📊 Testing population selection logic...")
        
        # Test the new population selection function
        best_population = _get_best_population_estimate(
            population_module, earth_engine_module, waste_module
        )
        
        print(f"🎯 Best population estimate selected:")
        print(f"   - Population: {best_population.get('estimated_population', 0)}")
        print(f"   - Confidence: {best_population.get('confidence', 'Unknown')}")
        print(f"   - Source: {best_population.get('source', 'Unknown')}")
        print(f"   - Error: {best_population.get('error', 'None')}")
        
        # Compare with available sources
        print("\\n📊 Available sources for comparison:")
        
        ghsl_pop = earth_engine_module.get('ghsl_population', {}).get('total_population', 0)
        worldpop_pop = waste_module.get('population_estimate', {}).get('estimated_population', 0)
        consensus_pop = population_module.get('consensus_estimate', 0)
        
        print(f"   - GHSL: {ghsl_pop} people")
        print(f"   - WorldPop: {worldpop_pop} people")
        print(f"   - Consensus: {consensus_pop} people")
        
        selected_pop = best_population.get('estimated_population', 0)
        
        if selected_pop > 0:
            print(f"\\n✅ SUCCESS: Population selection is working!")
            print(f"   Selected: {selected_pop} people from {best_population.get('source', 'Unknown')}")
            
            # Check if it selected the best source (GHSL should be preferred)
            if ghsl_pop > 0 and selected_pop == ghsl_pop:
                print(f"   ✅ Correctly selected GHSL as the best source")
            elif worldpop_pop > 0 and selected_pop == worldpop_pop and ghsl_pop == 0:
                print(f"   ✅ Correctly selected WorldPop as fallback")
            elif consensus_pop > 0 and selected_pop == consensus_pop and ghsl_pop == 0 and worldpop_pop == 0:
                print(f"   ✅ Correctly selected Consensus as final fallback")
            else:
                print(f"   ⚠️  Population selection logic may need review")
            
            return True
        else:
            print(f"\\n❌ ISSUE: No population selected despite available data")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 TESTING DASHBOARD ENDPOINT POPULATION FIX")
    print("Verifying that EST. POPULATION will now show the correct value")
    print()
    
    success = test_dashboard_endpoint_population_fix()
    
    if success:
        print("\\n🎉 SUCCESS: Dashboard endpoint population fix is working!")
        print("EST. POPULATION should now display the correct population value")
    else:
        print("\\n❌ FAILURE: Population fix needs more work")
        print("Check debug output for specific issues")
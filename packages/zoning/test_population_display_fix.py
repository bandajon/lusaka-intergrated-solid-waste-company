#!/usr/bin/env python3
"""
Test population display fix - verify that population data shows up correctly
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_population_display_fix():
    """Test that population data displays correctly in the dashboard"""
    print("🔍 TESTING POPULATION DISPLAY FIX")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        from app.utils.dashboard_core import DashboardCore
        
        # Run real-time analysis
        analyzer = EnhancedRealTimeZoneAnalyzer()
        mock_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[28.280, -15.420], [28.285, -15.420], [28.285, -15.415], [28.280, -15.415], [28.280, -15.420]]]
            },
            "properties": {"name": "Population Test Zone"}
        }
        
        print("🔄 Running real-time analysis...")
        result = analyzer.analyze_drawn_zone(mock_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        # Check available population sources
        analysis_modules = result.get('analysis_modules', {})
        print("📊 Available population data sources:")
        
        # GHSL from Earth Engine
        earth_engine = analysis_modules.get('earth_engine', {})
        ghsl_pop = earth_engine.get('ghsl_population', {})
        if not ghsl_pop.get('error') and ghsl_pop.get('total_population', 0) > 0:
            print(f"   ✅ GHSL Population: {ghsl_pop.get('total_population', 0)} people")
        else:
            print(f"   ❌ GHSL Population: Not available")
        
        # WorldPop from waste analysis
        waste_analysis = analysis_modules.get('waste_analysis', {})
        worldpop = waste_analysis.get('population_estimate', {})
        if not worldpop.get('error') and worldpop.get('estimated_population', 0) > 0:
            print(f"   ✅ WorldPop Estimate: {worldpop.get('estimated_population', 0)} people")
        else:
            print(f"   ❌ WorldPop Estimate: Not available")
        
        # Population estimation module
        pop_estimation = analysis_modules.get('population_estimation', {})
        if isinstance(pop_estimation, dict) and pop_estimation.get('consensus_estimate', 0) > 0:
            print(f"   ✅ Consensus Estimate: {pop_estimation.get('consensus_estimate', 0)} people")
        else:
            print(f"   ❌ Consensus Estimate: Not available")
        
        print()
        
        # Test dashboard population extraction
        print("🔧 Testing dashboard population extraction...")
        dashboard = DashboardCore()
        
        # Format data like the dashboard endpoint does
        formatted_data = {
            'zone_id': 'population_test_zone',
            'zone_name': 'Population Test Zone',
            'analysis_modules': analysis_modules,
            'enhanced_population_estimate': waste_analysis.get('enhanced_population_estimate', {}),
        }
        
        dashboard_data = dashboard.generate_zone_overview_dashboard(formatted_data)
        key_metrics = dashboard_data.get('key_metrics', {})
        
        estimated_population = key_metrics.get('estimated_population', 0)
        population_confidence = key_metrics.get('population_confidence', 'Unknown')
        
        print(f"🎯 Dashboard results:")
        print(f"   - Estimated Population: {estimated_population}")
        print(f"   - Population Confidence: {population_confidence}")
        
        if estimated_population > 0:
            print(f"\\n✅ SUCCESS: Population display fix is working!")
            print(f"   Dashboard will show: {estimated_population} people")
            return True
        else:
            print(f"\\n❌ ISSUE: Population still showing as 0")
            print("   Debug: Available data sources didn't populate dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 TESTING POPULATION DISPLAY FIX")
    print("Verifying that EST. POPULATION shows actual values instead of 0")
    print()
    
    success = test_population_display_fix()
    
    if success:
        print("\\n🎉 SUCCESS: Population display fix is working!")
        print("EST. POPULATION will now show actual population numbers")
    else:
        print("\\n❌ FAILURE: Population display still needs work")
        print("Check debug output for specific issues")
#!/usr/bin/env python3
"""
Test the dashboard endpoint with real data to see what's actually being sent
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_endpoint_data():
    """Test what data is actually sent to the dashboard endpoint"""
    print("🔍 TESTING DASHBOARD ENDPOINT DATA")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Run real-time analysis
        analyzer = EnhancedRealTimeZoneAnalyzer()
        mock_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[28.280, -15.420], [28.285, -15.420], [28.285, -15.415], [28.280, -15.415], [28.280, -15.420]]]
            },
            "properties": {"name": "Dashboard Test Zone"}
        }
        
        print("🔄 Running real-time analysis...")
        result = analyzer.analyze_drawn_zone(mock_geojson)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return False
        
        # Extract the data that would be sent to dashboard endpoint
        analysis_modules = result.get('analysis_modules', {})
        
        population_module = analysis_modules.get('population_estimation', {})
        waste_module = analysis_modules.get('waste_analysis', {})
        earth_engine_module = analysis_modules.get('earth_engine', {})
        
        print("📊 Population Module Data:")
        print(f"   - Type: {type(population_module)}")
        if isinstance(population_module, dict):
            print(f"   - Keys: {list(population_module.keys())}")
            print(f"   - consensus_estimate: {population_module.get('consensus_estimate', 'NOT FOUND')}")
            print(f"   - confidence_level: {population_module.get('confidence_level', 'NOT FOUND')}")
        
        print("\\n📊 Earth Engine Module Data:")
        print(f"   - Type: {type(earth_engine_module)}")
        if isinstance(earth_engine_module, dict):
            print(f"   - Keys: {list(earth_engine_module.keys())}")
            ghsl_pop = earth_engine_module.get('ghsl_population', {})
            print(f"   - ghsl_population.total_population: {ghsl_pop.get('total_population', 'NOT FOUND')}")
            print(f"   - estimated_population: {earth_engine_module.get('estimated_population', 'NOT FOUND')}")
        
        print("\\n📊 Waste Module Data:")
        print(f"   - Type: {type(waste_module)}")
        if isinstance(waste_module, dict):
            print(f"   - Keys: {list(waste_module.keys())}")
            pop_estimate = waste_module.get('population_estimate', {})
            print(f"   - population_estimate.estimated_population: {pop_estimate.get('estimated_population', 'NOT FOUND')}")
        
        # Test the dashboard endpoint logic
        print("\\n🔧 Testing Dashboard Endpoint Logic:")
        print("-" * 40)
        
        # Simulate what the dashboard endpoint does
        enhanced_population_estimate = {
            'estimated_population': population_module.get('consensus_estimate', 0),
            'confidence': population_module.get('confidence_level', 'Medium'),
            'error': population_module.get('error')
        }
        
        print(f"🎯 Dashboard endpoint would create:")
        print(f"   - enhanced_population_estimate: {enhanced_population_estimate}")
        
        # Check if we have better data sources
        print("\\n🔍 Available Population Sources:")
        
        # GHSL population
        ghsl_pop = earth_engine_module.get('ghsl_population', {})
        ghsl_total = ghsl_pop.get('total_population', 0)
        print(f"   - GHSL: {ghsl_total} people")
        
        # WorldPop population
        worldpop = waste_module.get('population_estimate', {})
        worldpop_total = worldpop.get('estimated_population', 0)
        print(f"   - WorldPop: {worldpop_total} people")
        
        # Consensus estimate
        consensus = population_module.get('consensus_estimate', 0)
        print(f"   - Consensus: {consensus} people")
        
        print("\\n💡 RECOMMENDATION:")
        if ghsl_total > 0:
            print(f"   Use GHSL population: {ghsl_total} people")
        elif worldpop_total > 0:
            print(f"   Use WorldPop population: {worldpop_total} people")  
        elif consensus > 0:
            print(f"   Use consensus estimate: {consensus} people")
        else:
            print("   No population data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 TESTING DASHBOARD ENDPOINT DATA")
    print("Checking what population data is sent to dashboard endpoint")
    print()
    
    success = test_dashboard_endpoint_data()
    
    if success:
        print("\\n✅ Data analysis complete!")
        print("Check the output above to see what data sources are available")
    else:
        print("\\n❌ Test failed - check error messages above")
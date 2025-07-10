#!/usr/bin/env python3
"""
Test the fixed waste analysis system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType

# Test geometry - realistic size for Lusaka residential area
test_geometry = {
    "type": "Polygon",
    "coordinates": [[
        [28.2816, -15.3875],
        [28.2860, -15.3875],
        [28.2860, -15.3840],
        [28.2816, -15.3840],
        [28.2816, -15.3875]
    ]]
}

def test_waste_analysis_fix():
    """Test waste analysis with fixed geometry and data mapping"""
    print("🗑️ Waste Analysis Fix Test")
    print("=" * 40)
    
    # Calculate expected area
    from shapely.geometry import shape
    geom = shape(test_geometry)
    area_km2 = (geom.area * 111320 ** 2) / 1_000_000
    print(f"📍 Test area: {area_km2:.3f} km² ({area_km2 * 1000000:.0f} sqm)")
    
    # Initialize analyzer
    analyzer = UnifiedAnalyzer()
    
    print("\n🔧 Testing Complete Analysis with Waste Focus")
    print("-" * 30)
    
    # Create analysis request
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=test_geometry,
        zone_name="Test Waste Zone",
        zone_type="residential",
        options={
            'confidence_threshold': 0.95,
            'use_fallback': False,
            'include_buildings': True,
            'include_population': True,
            'include_waste': True
        }
    )
    
    try:
        # Perform analysis
        result = analyzer.analyze(analysis_request)
        result_dict = result.to_dict()
        
        print(f"✅ Analysis Success: {result.success}")
        print(f"🏠 Building Count: {result_dict.get('building_count', 0)}")
        print(f"👥 Population: {result_dict.get('population_estimate', 0)}")
        print(f"🗑️ Waste (kg/day): {result_dict.get('waste_generation_kg_per_day', 0)}")
        print(f"📊 Confidence: {result_dict.get('confidence_level', 0):.2f}")
        
        # Test waste calculations specifically
        building_count = result_dict.get('building_count', 0)
        population = result_dict.get('population_estimate', 0)
        waste_kg_day = result_dict.get('waste_generation_kg_per_day', 0)
        
        if population > 0 and waste_kg_day > 0:
            waste_rate = waste_kg_day / population
            print(f"📈 Waste rate: {waste_rate:.2f} kg/person/day")
            
            # Check if waste rate is reasonable (0.3-0.8 kg/person/day for Lusaka)
            if 0.3 <= waste_rate <= 0.8:
                print("✅ Waste rate looks realistic for Lusaka")
            else:
                print(f"⚠️ Waste rate ({waste_rate:.2f}) seems unusual")
        
        # Test collection requirements
        collection_req = result_dict.get('collection_requirements', {})
        if collection_req:
            print(f"\n🚛 Collection Requirements:")
            print(f"  Frequency: {collection_req.get('frequency_per_week', 0)} times/week")
            
            vehicle_req = collection_req.get('vehicle_requirements', {})
            if vehicle_req:
                print(f"  Vehicles needed: {vehicle_req.get('vehicles_needed', 0)}")
                print(f"  Primary vehicle: {vehicle_req.get('primary_vehicle', 'unknown')}")
        
        # Test weekly and monthly calculations
        weekly_waste = waste_kg_day * 7
        weekly_tonnes = weekly_waste / 1000
        print(f"\n📊 Waste Projections:")
        print(f"  Weekly: {weekly_waste:.1f} kg ({weekly_tonnes:.2f} tonnes)")
        print(f"  Monthly: {waste_kg_day * 30:.1f} kg ({waste_kg_day * 30 / 1000:.2f} tonnes)")
        
        # Check data sources
        data_sources = result_dict.get('data_sources', [])
        if any('Google' in source or 'Earth Engine' in source for source in data_sources):
            print("✅ Using Google Earth Engine data for building analysis")
        else:
            print("⚠️ Using fallback estimation")
        
        return {
            'success': True,
            'population': population,
            'waste_kg_day': waste_kg_day,
            'waste_rate': waste_rate if population > 0 else 0,
            'building_count': building_count,
            'collection_requirements': collection_req
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_geometry_validation():
    """Test geometry validation fixes"""
    print("\n🔍 Geometry Validation Test")
    print("-" * 30)
    
    # Test with Feature wrapper (this was causing the GeoJSON error)
    feature_geometry = {
        "type": "Feature",
        "geometry": test_geometry,
        "properties": {}
    }
    
    analyzer = UnifiedAnalyzer()
    
    # This should now work without geometry errors
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.BUILDINGS,
        geometry=feature_geometry,
        options={'confidence_threshold': 0.95}
    )
    
    try:
        result = analyzer.analyze(analysis_request)
        print("✅ Feature geometry handled correctly")
        return True
    except Exception as e:
        print(f"❌ Geometry validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test main waste analysis
    main_result = test_waste_analysis_fix()
    
    # Test geometry validation
    geom_result = test_geometry_validation()
    
    print("\n📋 Test Summary:")
    print("-" * 20)
    if main_result.get('success'):
        population = main_result.get('population', 0)
        waste_kg_day = main_result.get('waste_kg_day', 0)
        waste_rate = main_result.get('waste_rate', 0)
        building_count = main_result.get('building_count', 0)
        
        print(f"✅ Waste analysis working: {waste_kg_day:.1f} kg/day for {population} people")
        print(f"📊 Waste rate: {waste_rate:.2f} kg/person/day")
        print(f"🏠 Buildings analyzed: {building_count}")
        print(f"🔍 Geometry validation: {'✅ Working' if geom_result else '❌ Failed'}")
        
        if waste_kg_day > 0 and population > 0 and 0.3 <= waste_rate <= 0.8:
            print("🎯 All waste calculations look good!")
        else:
            print("⚠️ Some calculations need review")
    else:
        print("❌ Waste analysis test failed")
    
    print("\n✅ Test complete!")
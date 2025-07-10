"""
Test the analytics display fixes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType
from app.views.zones import _calculate_area_from_geometry

# Test geometry (larger area for more realistic results)
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

def test_area_calculation():
    """Test the area calculation function"""
    print("🔍 Testing Area Calculation...")
    
    # Test with plain geometry
    area_km2 = _calculate_area_from_geometry(test_geometry)
    print(f"✅ Calculated area: {area_km2:.4f} km²")
    
    # Test with Feature object
    feature_geometry = {
        "type": "Feature",
        "geometry": test_geometry,
        "properties": {}
    }
    area_km2_feature = _calculate_area_from_geometry(feature_geometry)
    print(f"✅ Calculated area from feature: {area_km2_feature:.4f} km²")
    
    return area_km2

def test_analytics_result_structure():
    """Test that analytics results have correct structure for database storage"""
    print("\n🔍 Testing Analytics Result Structure...")
    
    analyzer = UnifiedAnalyzer()
    
    # Test comprehensive analysis
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=test_geometry,
        zone_name="Test Zone",
        zone_type="residential",
        options={'use_fallback': True}
    )
    
    try:
        result = analyzer.analyze(analysis_request)
        result_dict = result.to_dict()
        
        print(f"✅ Analysis success: {result.success}")
        
        # Check key fields that need to be stored in database
        print("\n📊 Key Database Fields:")
        print(f"  population_estimate: {result_dict.get('population_estimate')}")
        print(f"  waste_generation_kg_per_day: {result_dict.get('waste_generation_kg_per_day')}")
        print(f"  building_count: {result_dict.get('building_count')}")
        print(f"  confidence_level: {result_dict.get('confidence_level')}")
        
        # Check if all required fields are present and non-zero
        required_fields = ['population_estimate', 'waste_generation_kg_per_day', 'building_count']
        missing_fields = []
        zero_fields = []
        
        for field in required_fields:
            value = result_dict.get(field)
            if value is None:
                missing_fields.append(field)
            elif value == 0:
                zero_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        if zero_fields:
            print(f"⚠️ Zero value fields: {zero_fields}")
        
        if not missing_fields and not zero_fields:
            print("✅ All required fields present with non-zero values!")
        
        return result_dict
        
    except Exception as e:
        print(f"❌ Analytics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_building_engine_directly():
    """Test building engine directly to check for errors"""
    print("\n🔍 Testing Building Engine Directly...")
    
    try:
        from app.utils.building_engine import BuildingEngine
        
        engine = BuildingEngine()
        result = engine.analyze_buildings(test_geometry, {'use_fallback': True})
        
        print(f"✅ Building engine success")
        print(f"🏠 Building count: {result.get('building_count')}")
        print(f"🏘️ Settlement type: {result.get('settlement_classification')}")
        print(f"📊 Confidence: {result.get('confidence_level')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Building engine test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Analytics Display Fixes Test")
    print("=" * 40)
    
    # Test area calculation
    area = test_area_calculation()
    
    # Test analytics structure
    analytics_result = test_analytics_result_structure()
    
    # Test building engine
    building_success = test_building_engine_directly()
    
    print("\n📋 Test Summary:")
    print(f"  Area calculation: {'✅' if area > 0 else '❌'} ({area:.4f} km²)")
    print(f"  Analytics results: {'✅' if analytics_result else '❌'}")
    print(f"  Building engine: {'✅' if building_success else '❌'}")
    
    if analytics_result:
        pop = analytics_result.get('population_estimate', 0)
        waste = analytics_result.get('waste_generation_kg_per_day', 0)
        buildings = analytics_result.get('building_count', 0)
        
        print(f"\n🎯 Expected Database Values:")
        print(f"  estimated_population: {pop}")
        print(f"  total_waste_kg_day: {waste}")
        print(f"  area_sqkm: {area}")
        print(f"  building_count: {buildings}")
    
    print("\n✅ Test complete!")
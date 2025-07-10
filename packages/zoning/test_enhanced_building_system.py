#!/usr/bin/env python3
"""
Test the enhanced building detection system with Google Earth Engine
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

def test_enhanced_building_detection():
    """Test enhanced building detection with Earth Engine"""
    print("🏗️ Enhanced Building Detection System Test")
    print("=" * 50)
    
    # Calculate expected area
    from shapely.geometry import shape
    geom = shape(test_geometry)
    area_km2 = (geom.area * 111320 ** 2) / 1_000_000
    print(f"📍 Test area: {area_km2:.3f} km² ({area_km2 * 1000000:.0f} sqm)")
    
    # Initialize analyzer
    analyzer = UnifiedAnalyzer()
    
    print("\n🔧 Testing with Earth Engine Analysis (95% confidence)")
    print("-" * 30)
    
    # Create analysis request with Earth Engine enabled
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=test_geometry,
        zone_name="Test Enhanced Zone",
        zone_type="residential",
        options={
            'confidence_threshold': 0.95,
            'use_fallback': False,  # Force Earth Engine analysis
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
        print(f"🏘️ Settlement Type: {result_dict.get('settlement_classification', 'unknown')}")
        print(f"📚 Data Sources: {result_dict.get('data_sources', [])}")
        
        if result_dict.get('warnings'):
            print(f"⚠️ Warnings: {result_dict.get('warnings')}")
        
        # Check if Earth Engine was used successfully
        data_sources = result_dict.get('data_sources', [])
        if any('Google' in source or 'Earth Engine' in source for source in data_sources):
            print("✅ Successfully used Google Earth Engine data!")
        elif any('Enhanced fallback' in source for source in data_sources):
            print("⚠️ Used enhanced fallback estimation (Earth Engine may have failed)")
        elif any('Fallback' in source for source in data_sources):
            print("❌ Used basic fallback estimation")
        
        # Validate results make sense
        building_count = result_dict.get('building_count', 0)
        population = result_dict.get('population_estimate', 0)
        
        if building_count > 0:
            people_per_building = population / building_count if building_count > 0 else 0
            print(f"📈 People per building: {people_per_building:.1f}")
            
            # Check if ratios make sense
            if 2.0 <= people_per_building <= 6.0:
                print("✅ People per building ratio looks realistic")
            else:
                print(f"⚠️ People per building ratio ({people_per_building:.1f}) seems unusual")
        
        # Expected building density check
        expected_buildings_min = area_km2 * 60   # Low density
        expected_buildings_max = area_km2 * 200  # High density
        
        print(f"\n📊 Expected Range Analysis:")
        print(f"  Expected buildings: {expected_buildings_min:.0f} - {expected_buildings_max:.0f}")
        print(f"  Actual buildings: {building_count}")
        
        if expected_buildings_min <= building_count <= expected_buildings_max:
            print("✅ Building count within expected range")
        else:
            print("⚠️ Building count outside expected range")
        
        return result_dict
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_fallback_comparison():
    """Compare enhanced fallback vs basic fallback"""
    print("\n🔄 Fallback Methods Comparison")
    print("=" * 40)
    
    analyzer = UnifiedAnalyzer()
    
    # Test enhanced fallback
    enhanced_buildings = analyzer._enhanced_fallback_building_count(test_geometry)
    basic_buildings = analyzer._fallback_building_count(test_geometry)
    
    print(f"🏗️ Enhanced fallback: {enhanced_buildings} buildings")
    print(f"📊 Basic fallback: {basic_buildings} buildings")
    print(f"📈 Difference: {enhanced_buildings - basic_buildings} buildings")
    
    return enhanced_buildings, basic_buildings

if __name__ == "__main__":
    # Test main system
    main_result = test_enhanced_building_detection()
    
    # Test fallback comparison
    enhanced_fb, basic_fb = test_fallback_comparison()
    
    print("\n📋 Test Summary:")
    print("-" * 20)
    if main_result:
        building_count = main_result.get('building_count', 0)
        population = main_result.get('population_estimate', 0)
        confidence = main_result.get('confidence_level', 0)
        
        print(f"✅ Enhanced system working: {building_count} buildings, {population} people")
        print(f"📊 Confidence level: {confidence:.2f}")
        print(f"🏗️ Enhanced fallback: {enhanced_fb} buildings")
        print(f"📊 Basic fallback: {basic_fb} buildings")
        
        if building_count > 0 and population > 0:
            print("🎯 Ready for production use!")
        else:
            print("⚠️ Needs further investigation")
    else:
        print("❌ System test failed")
    
    print("\n✅ Test complete!")
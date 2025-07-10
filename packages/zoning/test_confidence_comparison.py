#!/usr/bin/env python3
"""
Test different confidence thresholds to find optimal balance
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType

# Test geometry
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

def test_confidence_threshold(threshold):
    """Test a specific confidence threshold"""
    analyzer = UnifiedAnalyzer()
    
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=test_geometry,
        zone_name=f"Test {int(threshold*100)}% Zone",
        zone_type="residential",
        options={
            'confidence_threshold': threshold,
            'use_fallback': False,
            'include_buildings': True,
            'include_population': True,
            'include_waste': True
        }
    )
    
    try:
        result = analyzer.analyze(analysis_request)
        result_dict = result.to_dict()
        
        building_count = result_dict.get('building_count', 0)
        population = result_dict.get('population_estimate', 0)
        waste_kg_day = result_dict.get('waste_generation_kg_per_day', 0)
        confidence = result_dict.get('confidence_level', 0)
        data_sources = result_dict.get('data_sources', [])
        
        using_earth_engine = any('Google' in source or 'Earth Engine' in source for source in data_sources)
        
        return {
            'threshold': threshold,
            'buildings': building_count,
            'population': population,
            'waste_kg_day': waste_kg_day,
            'confidence': confidence,
            'using_earth_engine': using_earth_engine,
            'people_per_building': population / building_count if building_count > 0 else 0
        }
        
    except Exception as e:
        return {
            'threshold': threshold,
            'error': str(e),
            'buildings': 0,
            'population': 0,
            'using_earth_engine': False
        }

if __name__ == "__main__":
    print("🏗️ Building Confidence Threshold Comparison")
    print("=" * 50)
    
    # Test different thresholds
    thresholds = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    
    results = []
    for threshold in thresholds:
        print(f"\\n🔍 Testing {int(threshold*100)}% confidence threshold...")
        result = test_confidence_threshold(threshold)
        results.append(result)
        
        if 'error' not in result:
            print(f"  Buildings: {result['buildings']}")
            print(f"  Population: {result['population']}")
            print(f"  Earth Engine: {'✅' if result['using_earth_engine'] else '❌'}")
            if result['buildings'] > 0:
                print(f"  People/building: {result['people_per_building']:.1f}")
        else:
            print(f"  Error: {result['error']}")
    
    print("\\n📊 Summary Comparison:")
    print("-" * 40)
    print("Threshold | Buildings | Population | EE | People/Bldg")
    print("-" * 40)
    
    for result in results:
        if 'error' not in result:
            threshold = int(result['threshold'] * 100)
            buildings = result['buildings']
            population = result['population']
            ee_symbol = "✅" if result['using_earth_engine'] else "❌"
            people_per_building = result['people_per_building']
            
            print(f"   {threshold:2d}%    |    {buildings:3d}    |    {population:4d}    | {ee_symbol} |    {people_per_building:4.1f}")
    
    print("\\n💡 Recommendations:")
    print("-" * 20)
    
    # Find the optimal threshold
    earth_engine_results = [r for r in results if r.get('using_earth_engine') and r.get('buildings', 0) > 0]
    
    if earth_engine_results:
        # Look for reasonable people per building ratio (2-6 people/building for Lusaka)
        good_ratios = [r for r in earth_engine_results if 2.0 <= r.get('people_per_building', 0) <= 6.0]
        
        if good_ratios:
            optimal = min(good_ratios, key=lambda x: abs(x['people_per_building'] - 4.0))  # Target ~4 people/building
            print(f"✅ Optimal threshold: {int(optimal['threshold']*100)}% confidence")
            print(f"   - {optimal['buildings']} buildings")
            print(f"   - {optimal['population']} people")
            print(f"   - {optimal['people_per_building']:.1f} people per building")
            print(f"   - Filters out unfinished buildings while keeping genuine structures")
        else:
            print("⚠️  No thresholds found with ideal people/building ratios")
            if earth_engine_results:
                highest_confidence = max(earth_engine_results, key=lambda x: x['threshold'])
                print(f"🔄 Highest working threshold: {int(highest_confidence['threshold']*100)}%")
    else:
        print("❌ No thresholds successfully used Earth Engine data")
        print("🔄 Consider using fallback methods or checking Earth Engine connectivity")
    
    print("\\n✅ Comparison complete!")
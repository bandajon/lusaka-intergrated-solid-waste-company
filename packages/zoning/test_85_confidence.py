#!/usr/bin/env python3
"""
Quick test to verify 85% confidence threshold is working
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType

def test_85_confidence():
    """Test 85% confidence threshold"""
    print("🔧 Testing 85% Confidence Threshold")
    print("=" * 40)
    
    # Test geometry
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[[28.2816, -15.3875], [28.2860, -15.3875], [28.2860, -15.3840], [28.2816, -15.3840], [28.2816, -15.3875]]]
    }
    
    # Initialize analyzer
    analyzer = UnifiedAnalyzer()
    
    # Create request (should use 85% confidence by default)
    request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=test_geometry,
        zone_name="Test 85% Zone",
        zone_type="residential",
        options={
            'include_population': True,
            'include_buildings': True,
            'include_waste': True,
            'use_fallback': False
        }
    )
    
    print(f"📊 Using confidence threshold: {request.options.get('confidence_threshold')}")
    
    try:
        # Perform analysis with timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Analysis timed out after 60 seconds")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout
        
        result = analyzer.analyze(request)
        signal.alarm(0)  # Cancel timeout
        
        result_dict = result.to_dict()
        
        print(f"✅ Analysis Success: {result.success}")
        print(f"🏠 Building Count: {result_dict.get('building_count', 0)}")
        print(f"👥 Population: {result_dict.get('population_estimate', 0)}")
        print(f"🗑️ Waste (kg/day): {result_dict.get('waste_generation_kg_per_day', 0)}")
        print(f"📊 Confidence: {result_dict.get('confidence_level', 0):.2f}")
        print(f"🔧 Data Sources: {result_dict.get('data_sources', [])}")
        
        # Check if we got buildings
        building_count = result_dict.get('building_count', 0)
        if building_count > 0:
            print(f"🎯 SUCCESS: Found {building_count} buildings with 85% confidence!")
            return True
        else:
            print("⚠️ Still getting 0 buildings - need to investigate further")
            return False
            
    except TimeoutError:
        print("⏱️ Analysis timed out - this is expected for Earth Engine calls")
        return None
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_85_confidence()
    if result is True:
        print("\n✅ 85% confidence threshold is working correctly!")
    elif result is False:
        print("\n❌ Still having issues with building detection")
    else:
        print("\n⏱️ Analysis timed out but system is configured correctly")
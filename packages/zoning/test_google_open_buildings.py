#!/usr/bin/env python3
"""
Test Google Open Buildings integration with Earth Engine
Validates building detection, feature extraction, and settlement classification
"""
import sys
import os
import time
import json

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.earth_engine_analysis import EarthEngineAnalyzer
from config.config import Config


class MockZone:
    """Mock zone object for testing"""
    def __init__(self, zone_id, geojson):
        self.id = zone_id
        self.geojson = geojson


def test_google_open_buildings_integration():
    """Test the complete Google Open Buildings integration workflow"""
    print("="*70)
    print("Google Open Buildings Integration Test")
    print("="*70)
    
    # Initialize analyzer
    print("\n1. Initializing Earth Engine Analyzer...")
    analyzer = EarthEngineAnalyzer()
    
    if not analyzer.initialized:
        print("❌ Earth Engine not initialized. Please check configuration.")
        return False
    
    print("✅ Earth Engine initialized successfully!")
    
    # Create test zone geometry (Lusaka city center area)
    test_zone_geojson = {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [28.280, -15.410],
                [28.285, -15.410],
                [28.285, -15.415],
                [28.280, -15.415],
                [28.280, -15.410]
            ]]
        }
    }
    
    test_zone = MockZone("test_zone_1", test_zone_geojson)
    
    # Test building extraction
    print("\n2. Testing building extraction for Lusaka test area...")
    print("   Area coordinates: [28.280, -15.410] to [28.285, -15.415]")
    
    start_time = time.time()
    
    try:
        # Extract buildings with 75% confidence threshold
        buildings_result = analyzer.extract_buildings_for_zone(test_zone, confidence_threshold=0.75)
        
        extraction_time = time.time() - start_time
        
        if 'error' in buildings_result:
            print(f"❌ Building extraction failed: {buildings_result['error']}")
            return False
        
        print(f"✅ Building extraction completed in {extraction_time:.2f} seconds")
        print(f"   Buildings found: {buildings_result.get('building_count', 0)}")
        print(f"   Data source: {buildings_result.get('data_source', 'N/A')}")
        
        # Display building statistics
        features = buildings_result.get('features', {})
        if features and not features.get('error'):
            area_stats = features.get('area_statistics', {})
            density = features.get('building_density_per_sqkm', 0)
            
            print(f"   Building density: {density:.1f} buildings/km²")
            print(f"   Average building size: {area_stats.get('mean', 0):.1f} m²")
            print(f"   Largest building: {area_stats.get('max', 0):.1f} m²")
            print(f"   Smallest building: {area_stats.get('min', 0):.1f} m²")
        
        # Display height statistics
        height_stats = buildings_result.get('height_stats', {})
        if height_stats and not height_stats.get('error'):
            print(f"   Average building height: {height_stats.get('building_height_mean', 0):.1f} m")
            print(f"   Max building height: {height_stats.get('building_height_max', 0):.1f} m")
        
    except Exception as e:
        print(f"❌ Error during building extraction: {str(e)}")
        return False
    
    # Test caching mechanism
    print("\n3. Testing caching mechanism...")
    
    # Second extraction should use cache
    cache_start_time = time.time()
    cached_result = analyzer.extract_buildings_for_zone(test_zone, confidence_threshold=0.75)
    cache_time = time.time() - cache_start_time
    
    print(f"✅ Cache test completed in {cache_time:.2f} seconds")
    
    if cache_time < extraction_time * 0.5:  # Should be much faster
        print("✅ Caching working correctly (significant speed improvement)")
    else:
        print("⚠️  Caching may not be working optimally")
    
    # Display cache info
    cache_info = analyzer.get_cache_info()
    print(f"   Cache size: {cache_info['cache_size']} entries")
    
    # Test settlement classification
    print("\n4. Testing settlement classification...")
    
    try:
        classification = analyzer.classify_buildings_by_context(test_zone, buildings_result)
        
        if 'error' in classification:
            print(f"❌ Classification failed: {classification['error']}")
        else:
            print(f"✅ Settlement classification completed")
            print(f"   Settlement type: {classification.get('settlement_type', 'unknown')}")
            print(f"   Confidence: {classification.get('confidence', 0):.2f}")
            print(f"   Building density: {classification.get('building_density', 0):.1f} buildings/km²")
            print(f"   Average building size: {classification.get('average_building_size_sqm', 0):.1f} m²")
            
            factors = classification.get('classification_factors', {})
            print("   Classification factors:")
            print(f"     - Density-based: {factors.get('density_based', False)}")
            print(f"     - Size-based: {factors.get('size_based', False)}")
            print(f"     - Variability-based: {factors.get('variability_based', False)}")
    
    except Exception as e:
        print(f"❌ Error during classification: {str(e)}")
        return False
    
    # Test different confidence thresholds
    print("\n5. Testing different confidence thresholds...")
    
    thresholds = [0.5, 0.75, 0.9]
    for threshold in thresholds:
        try:
            result = analyzer.extract_buildings_for_zone(test_zone, confidence_threshold=threshold, use_cache=False)
            building_count = result.get('building_count', 0)
            print(f"   Confidence >= {threshold}: {building_count} buildings")
        except Exception as e:
            print(f"   ❌ Error with threshold {threshold}: {str(e)}")
    
    # Test error handling and quota management
    print("\n6. Testing error handling...")
    
    # Test with invalid geometry
    invalid_zone_geojson = {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [200, 200],  # Invalid coordinates
                [201, 200],
                [201, 201],
                [200, 201],
                [200, 200]
            ]]
        }
    }
    
    invalid_zone = MockZone("invalid_zone", invalid_zone_geojson)
    
    try:
        invalid_result = analyzer.extract_buildings_for_zone(invalid_zone)
        if 'error' in invalid_result:
            print("✅ Error handling working correctly for invalid geometry")
        else:
            print("⚠️  Expected error for invalid geometry, but got result")
    except Exception as e:
        print(f"✅ Error handling working correctly: {str(e)}")
    
    # Clear cache for cleanup
    print("\n7. Cleaning up...")
    analyzer.clear_cache()
    final_cache_info = analyzer.get_cache_info()
    print(f"✅ Cache cleared (size: {final_cache_info['cache_size']})")
    
    print("\n" + "="*70)
    print("✅ Google Open Buildings Integration Test COMPLETED")
    print("="*70)
    
    return True


def test_individual_components():
    """Test individual components of the integration"""
    print("\n" + "="*70)
    print("Individual Component Tests")
    print("="*70)
    
    analyzer = EarthEngineAnalyzer()
    
    if not analyzer.initialized:
        print("❌ Earth Engine not initialized")
        return False
    
    # Test basic dataset loading
    print("\n1. Testing basic dataset loading...")
    
    try:
        import ee
        
        # Test loading Google Open Buildings
        lusaka_bounds = ee.Geometry.Rectangle([28.2, -15.5, 28.4, -15.3])
        buildings = analyzer.load_google_open_buildings(lusaka_bounds, 0.75)
        
        # Get a small sample
        sample = buildings.limit(10)
        count = sample.size().getInfo()
        
        print(f"✅ Loaded Google Open Buildings dataset")
        print(f"   Sample count: {count} buildings")
        
        # Test temporal data loading
        temporal_data = analyzer.load_open_buildings_temporal(lusaka_bounds, 2023)
        
        # Check if temporal data has expected bands
        band_names = temporal_data.bandNames().getInfo()
        print(f"✅ Loaded temporal building data")
        print(f"   Available bands: {band_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("Starting Google Open Buildings Integration Tests...\n")
    
    # Run main integration test
    success = test_google_open_buildings_integration()
    
    if success:
        # Run individual component tests
        component_success = test_individual_components()
        
        if component_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("Google Open Buildings integration is working correctly.")
        else:
            print("\n⚠️  Main test passed but some components failed.")
    else:
        print("\n❌ TESTS FAILED!")
        print("Please check Earth Engine configuration and network connectivity.")
    
    print("\nTest complete!") 
#!/usr/bin/env python3
"""
Test script to verify polygon centroid calculation and Google Maps distance accuracy
This will help identify why distances are always showing 10.5 km regardless of location
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer

def test_centroid_calculation():
    """Test that polygon centroids are being calculated correctly from different zone geometries"""
    analyzer = EnhancedRealTimeZoneAnalyzer()
    
    print("🧪 Testing Polygon Centroid Calculation & Distance Accuracy")
    print("=" * 70)
    
    # Test Case 1: Zone near city center (should be ~10-12 km from Chunga)
    lusaka_center_zone = {
        "type": "Polygon",
        "coordinates": [[
            [28.2833, -15.4166],  # Lusaka center area
            [28.2900, -15.4166],
            [28.2900, -15.4100],
            [28.2833, -15.4100],
            [28.2833, -15.4166]
        ]]
    }
    
    # Test Case 2: Zone closer to Chunga (should be ~5-7 km from Chunga)  
    near_chunga_zone = {
        "type": "Polygon", 
        "coordinates": [[
            [28.2750, -15.3600],  # Closer to Chunga area
            [28.2800, -15.3600],
            [28.2800, -15.3550], 
            [28.2750, -15.3550],
            [28.2750, -15.3600]
        ]]
    }
    
    # Test Case 3: Zone farther from Chunga (should be ~15-20 km from Chunga)
    far_from_chunga_zone = {
        "type": "Polygon",
        "coordinates": [[
            [28.3200, -15.4800],  # Farther from Chunga area
            [28.3300, -15.4800],
            [28.3300, -15.4700],
            [28.3200, -15.4700],
            [28.3200, -15.4800]
        ]]
    }
    
    test_zones = [
        ("Lusaka Center Zone", lusaka_center_zone, "~10-12 km expected"),
        ("Near Chunga Zone", near_chunga_zone, "~5-7 km expected"),
        ("Far from Chunga Zone", far_from_chunga_zone, "~15-20 km expected")
    ]
    
    chunga_lat, chunga_lon = -15.350004, 28.270069
    print(f"📍 Chunga Dumpsite: [{chunga_lat}, {chunga_lon}]")
    print()
    
    results = []
    
    for zone_name, zone_geojson, expected_range in test_zones:
        print(f"🔍 Testing: {zone_name} ({expected_range})")
        print("-" * 50)
        
        # Create mock zone and get centroid
        mock_zone = analyzer._create_mock_zone(zone_geojson)
        
        # Check if centroid was calculated
        if hasattr(mock_zone, 'centroid') and mock_zone.centroid:
            centroid_lon, centroid_lat = mock_zone.centroid[0], mock_zone.centroid[1]
            print(f"✅ Centroid calculated: [{centroid_lon:.6f}, {centroid_lat:.6f}]")
            
            # Calculate distances using both methods
            google_distance = analyzer._calculate_distance_google_maps(centroid_lat, centroid_lon, chunga_lat, chunga_lon)
            haversine_distance = analyzer._calculate_distance_haversine(centroid_lat, centroid_lon, chunga_lat, chunga_lon)
            
            print(f"🚗 Google Maps distance: {google_distance} km")
            print(f"📏 Haversine distance: {haversine_distance} km")
            print(f"🎯 Expected range: {expected_range}")
            
            results.append({
                'zone_name': zone_name,
                'centroid': [centroid_lon, centroid_lat],
                'google_distance': google_distance,
                'haversine_distance': haversine_distance,
                'expected_range': expected_range
            })
            
        else:
            print("❌ No centroid calculated - using fallback coordinates")
            # This would mean using default Lusaka center: [28.2833, -15.4166]
            fallback_lat, fallback_lon = -15.4166, 28.2833
            google_distance = analyzer._calculate_distance_google_maps(fallback_lat, fallback_lon, chunga_lat, chunga_lon)
            print(f"🚗 Google Maps distance (fallback): {google_distance} km")
            
            results.append({
                'zone_name': zone_name,
                'centroid': 'FALLBACK',
                'google_distance': google_distance,
                'haversine_distance': 0,
                'expected_range': expected_range
            })
        
        print()
    
    # Analysis of results
    print("=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    
    distances = [r['google_distance'] for r in results if r['google_distance'] > 0]
    
    if len(set(distances)) == 1:
        print("❌ ISSUE FOUND: All distances are the same!")
        print(f"   All zones showing: {distances[0]} km")
        print("   This confirms the bug - centroid calculation or coordinate passing issue")
        
        # Check if all centroids are the same (fallback issue)
        centroids = [r['centroid'] for r in results if r['centroid'] != 'FALLBACK']
        if len(set(str(c) for c in centroids)) <= 1:
            print("   🔧 ROOT CAUSE: All zones using same centroid (likely fallback coordinates)")
        else:
            print("   🔧 ROOT CAUSE: Centroids different but distance calculation issue")
            
    else:
        print("✅ SUCCESS: Different distances calculated for different zones!")
        for result in results:
            print(f"   {result['zone_name']}: {result['google_distance']} km")
    
    print("\n" + "=" * 70)
    print("🔧 RECOMMENDED FIXES:")
    print("1. Verify polygon centroid calculation in _create_mock_zone method")
    print("2. Check coordinate format consistency (lat,lon vs lon,lat)")
    print("3. Ensure Google Maps API receives actual polygon centroid, not fallback")
    print("4. Add debug logging to trace coordinate flow")
    
    return results

def test_mock_zone_creation():
    """Test the mock zone creation process specifically"""
    analyzer = EnhancedRealTimeZoneAnalyzer()
    
    print("\n🧪 Testing Mock Zone Creation Process")
    print("=" * 50)
    
    # Simple test polygon
    test_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [28.2800, -15.4000],
            [28.2850, -15.4000], 
            [28.2850, -15.3950],
            [28.2800, -15.3950],
            [28.2800, -15.4000]
        ]]
    }
    
    print("Creating mock zone from test polygon...")
    mock_zone = analyzer._create_mock_zone(test_polygon)
    
    print("\n📋 Mock Zone Attributes:")
    print(f"  - ID: {mock_zone.id}")
    print(f"  - Name: {mock_zone.name}")
    print(f"  - Zone Type: {mock_zone.zone_type}")
    print(f"  - Area (sqm): {mock_zone.area_sqm}")
    
    if hasattr(mock_zone, 'centroid'):
        print(f"  - Centroid: {mock_zone.centroid}")
        print(f"  - Centroid type: {type(mock_zone.centroid)}")
        if mock_zone.centroid and len(mock_zone.centroid) == 2:
            print(f"  - Longitude: {mock_zone.centroid[0]}")
            print(f"  - Latitude: {mock_zone.centroid[1]}")
    else:
        print("  - ❌ No centroid attribute found!")
    
    return mock_zone

if __name__ == "__main__":
    print("🔍 POLYGON CENTROID & DISTANCE CALCULATION TEST")
    print("=" * 70)
    print("Testing why all zones show the same distance to Chunga dumpsite...")
    print()
    
    # Test 1: Mock zone creation
    mock_zone = test_mock_zone_creation()
    
    # Test 2: Centroid calculation and distance accuracy
    results = test_centroid_calculation()
    
    # Test 3: Manual verification
    print("\n🧪 Manual Verification")
    print("=" * 30)
    print("Expected behavior:")
    print("- Different polygon locations should show different distances")
    print("- Zones closer to Chunga should show shorter distances")
    print("- Current bug: All zones showing same distance (likely 10.5 km)")
    
    if results:
        all_same = len(set(r['google_distance'] for r in results)) == 1
        if all_same:
            print(f"\n❌ BUG CONFIRMED: All distances = {results[0]['google_distance']} km")
        else:
            print("\n✅ BUG APPEARS FIXED: Different distances calculated!")
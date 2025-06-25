#!/usr/bin/env python3
"""
Isolated test to identify the exact distance calculation bug
Focus only on the truck requirements calculation which includes distance
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_isolated_distance_bug():
    """Test just the distance calculation part without full analysis"""
    print("🔍 ISOLATED DISTANCE BUG TEST")
    print("=" * 50)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Test zones at different locations
        test_zones = [
            {
                "name": "Zone A (Lusaka Center)", 
                "coords": [28.2833, -15.4166],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2833, -15.4166],
                        [28.2900, -15.4166], 
                        [28.2900, -15.4100],
                        [28.2833, -15.4100],
                        [28.2833, -15.4166]
                    ]]
                }
            },
            {
                "name": "Zone B (Near Chunga)",
                "coords": [28.2750, -15.3600],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2750, -15.3600],
                        [28.2800, -15.3600],
                        [28.2800, -15.3550],
                        [28.2750, -15.3550],
                        [28.2750, -15.3600]
                    ]]
                }
            },
            {
                "name": "Zone C (Far from Chunga)",
                "coords": [28.3200, -15.4800],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.3200, -15.4800],
                        [28.3300, -15.4800],
                        [28.3300, -15.4700],
                        [28.3200, -15.4700],
                        [28.3200, -15.4800]
                    ]]
                }
            }
        ]
        
        chunga_lat, chunga_lon = -15.350004, 28.270069
        print(f"📍 Chunga Dumpsite: [{chunga_lat}, {chunga_lon}]")
        print()
        
        results = []
        
        for zone in test_zones:
            print(f"🔍 Testing: {zone['name']}")
            print(f"   Expected centroid: {zone['coords']}")
            
            # Step 1: Create mock zone
            mock_zone = analyzer._create_mock_zone(zone['geometry'])
            
            # Check centroid
            if hasattr(mock_zone, 'centroid') and mock_zone.centroid:
                actual_centroid = mock_zone.centroid
                print(f"   ✅ Actual centroid: [{actual_centroid[0]:.6f}, {actual_centroid[1]:.6f}]")
                
                # Step 2: Calculate distance directly
                zone_lat, zone_lon = actual_centroid[1], actual_centroid[0]  # [lon, lat] -> lat, lon
                
                # Manual Google Maps distance calculation
                google_distance = analyzer._calculate_distance_google_maps(zone_lat, zone_lon, chunga_lat, chunga_lon)
                haversine_distance = analyzer._calculate_distance_haversine(zone_lat, zone_lon, chunga_lat, chunga_lon)
                
                print(f"   🚗 Google Maps distance: {google_distance} km")
                print(f"   📏 Haversine distance: {haversine_distance} km")
                
                # Step 3: Test truck requirements calculation (the actual method used in analysis)
                print("   🚛 Testing truck requirements method...")
                truck_requirements = analyzer._calculate_truck_requirements(mock_zone)
                
                if truck_requirements and not truck_requirements.get('error'):
                    # Distance is stored in dumpsite_logistics section
                    dumpsite_logistics = truck_requirements.get('dumpsite_logistics', {})
                    truck_distance = dumpsite_logistics.get('chunga_dumpsite_distance_km', 'Not found')
                    print(f"   🎯 Truck requirements distance: {truck_distance} km")  
                    
                    # This is the key comparison!
                    if truck_distance == google_distance:
                        print("   ✅ MATCH: Truck calculation uses correct centroid")
                    else:
                        print("   ❌ MISMATCH: Truck calculation differs from direct calculation")
                        print("       This indicates the bug is in truck requirements method!")
                else:
                    print(f"   ❌ Truck requirements failed: {truck_requirements.get('error', 'Unknown')}")
                    truck_distance = 'Error'
                
                results.append({
                    'name': zone['name'],
                    'expected_coords': zone['coords'],
                    'actual_centroid': actual_centroid,
                    'google_distance': google_distance,
                    'truck_distance': truck_distance,
                    'haversine_distance': haversine_distance
                })
                
            else:
                print("   ❌ No centroid calculated!")
                results.append({
                    'name': zone['name'],
                    'expected_coords': zone['coords'],
                    'actual_centroid': None,
                    'google_distance': 'No centroid',
                    'truck_distance': 'No centroid',
                    'haversine_distance': 'No centroid'
                })
            
            print()
        
        # Analyze results
        print("=" * 50)
        print("📊 BUG ANALYSIS")
        print("=" * 50)
        
        # Check if truck distances are all the same
        truck_distances = [r['truck_distance'] for r in results if isinstance(r['truck_distance'], (int, float))]
        google_distances = [r['google_distance'] for r in results if isinstance(r['google_distance'], (int, float))]
        
        print("Truck requirements distances:", truck_distances)
        print("Direct Google Maps distances:", google_distances)
        
        if truck_distances and len(set(truck_distances)) == 1:
            print(f"\n❌ BUG CONFIRMED: All truck distances = {truck_distances[0]} km")
            print("   The issue is in the _calculate_truck_requirements method")
            
            if google_distances and len(set(google_distances)) > 1:
                print("   Direct calculation works correctly")
                print("   🔧 FIX NEEDED: Check centroid usage in truck requirements")
            else:
                print("   Both methods show same issue")
                
        elif truck_distances and len(set(truck_distances)) > 1:
            print("✅ NO BUG: Truck distances vary correctly")
            for result in results:
                print(f"   {result['name']}: {result['truck_distance']} km")
        else:
            print("❓ INCONCLUSIVE: Some calculations failed")
        
        return results
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_isolated_distance_bug()
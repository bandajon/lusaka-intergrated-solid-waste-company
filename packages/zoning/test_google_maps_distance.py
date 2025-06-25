#!/usr/bin/env python3
"""
Test script for Google Maps Distance Matrix API integration
Tests accurate driving distance calculation to Chunga dumpsite
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer

def test_google_maps_distance():
    """Test Google Maps distance calculation vs Haversine"""
    analyzer = EnhancedRealTimeZoneAnalyzer()
    
    # Test coordinates
    zone_lat, zone_lon = -15.4166, 28.2833  # Lusaka center
    chunga_lat, chunga_lon = -15.350004, 28.270069  # Chunga dumpsite
    
    print("Testing distance calculations to Chunga dumpsite:")
    print(f"Zone location: {zone_lat}, {zone_lon}")
    print(f"Chunga dumpsite: {chunga_lat}, {chunga_lon}")
    print()
    
    # Test Google Maps distance
    print("=== Google Maps Distance Matrix API ===")
    google_distance = analyzer._calculate_distance_google_maps(zone_lat, zone_lon, chunga_lat, chunga_lon)
    print(f"Google Maps driving distance: {google_distance} km")
    print()
    
    # Test Haversine distance for comparison
    print("=== Haversine Formula (straight-line) ===")
    haversine_distance = analyzer._calculate_distance_haversine(zone_lat, zone_lon, chunga_lat, chunga_lon)
    print(f"Haversine straight-line distance: {haversine_distance} km")
    print()
    
    # Compare results
    print("=== Comparison ===")
    difference = abs(google_distance - haversine_distance)
    print(f"Difference: {difference:.2f} km")
    
    if google_distance > haversine_distance:
        print(f"Google Maps route is {difference:.2f} km longer (more accurate for actual driving)")
    else:
        print(f"Google Maps route is {difference:.2f} km shorter")
    
    print("\n✅ Google Maps integration test completed")
    return google_distance, haversine_distance

if __name__ == "__main__":
    test_google_maps_distance()
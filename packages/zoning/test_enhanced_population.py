#!/usr/bin/env python3
"""
Test script for enhanced population estimation with Earth Engine integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.zone import Zone
from app.views.zones import _estimate_population_for_zone
import json

def test_population_estimation():
    """Test the enhanced population estimation function"""
    
    app = create_app()
    
    with app.app_context():
        print("Testing Enhanced Population Estimation")
        print("=" * 50)
        
        # Create a test zone
        test_geometry = {
            "type": "Polygon",
            "coordinates": [[[
                [28.3293, -15.4067],  # Southwest corner
                [28.3293, -15.4037],  # Northwest corner  
                [28.3323, -15.4037],  # Northeast corner
                [28.3323, -15.4067],  # Southeast corner
                [28.3293, -15.4067]   # Close polygon
            ]]]
        }
        
        # Calculate area using pyproj (similar to what the create function does)
        from shapely.geometry import shape, mapping
        from shapely.ops import transform
        import pyproj
        
        polygon = shape(test_geometry)
        
        # Convert to UTM for accurate area calculation
        wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (lat/lng)
        utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S
        
        transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
        utm_polygon = transform(transformer.transform, polygon)
        
        area_sqm = utm_polygon.area
        perimeter_m = utm_polygon.length
        
        print(f"Test Zone Area: {area_sqm:,.2f} m² ({area_sqm/1000000:.3f} km²)")
        print(f"Test Zone Perimeter: {perimeter_m:,.2f} m")
        print()
        
        # Create a mock zone object for testing
        class MockZone:
            def __init__(self):
                self.area_sqm = area_sqm
                self.perimeter_m = perimeter_m
                self.zone_type = 'RESIDENTIAL'
                self.geometry = test_geometry
                
        mock_zone = MockZone()
        
        # Test the population estimation
        print("Running Population Estimation...")
        result = _estimate_population_for_zone(mock_zone)
        
        print("\nPopulation Estimation Results:")
        print("-" * 30)
        
        if isinstance(result, dict):
            print(f"Estimated Population: {result.get('estimated_population', 0):,}")
            print(f"Primary Method: {result.get('primary_method', 'Unknown')}")
            print(f"Confidence: {result.get('confidence', 'Unknown')}")
            print(f"Methods Used: {', '.join(result.get('methods_used', []))}")
            
            if result.get('earth_engine_population', 0) > 0:
                print(f"Earth Engine WorldPop: {result['earth_engine_population']:,}")
            
            if result.get('building_based_population', 0) > 0:
                print(f"Building-based Estimate: {result['building_based_population']:,}")
            
            if result.get('simple_area_estimate', 0) > 0:
                print(f"Simple Area-based: {result['simple_area_estimate']:,}")
            
            if result.get('comparison'):
                comp = result['comparison']
                print(f"\nComparison Analysis:")
                print(f"  Agreement Level: {comp.get('agreement_level', 'Unknown')}")
                if comp.get('max_difference_pct'):
                    print(f"  Max Difference: {comp['max_difference_pct']:.1f}%")
                
                if comp.get('estimates'):
                    print("  All Estimates:")
                    for method, estimate in comp['estimates'].items():
                        print(f"    {method}: {estimate:,}")
            
            if result.get('error'):
                print(f"Errors: {result['error']}")
                
        else:
            print(f"Simple Estimate: {result:,}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")

if __name__ == "__main__":
    test_population_estimation() 
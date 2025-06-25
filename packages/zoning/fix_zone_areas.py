#!/usr/bin/env python3
"""
Script to fix zone areas that are 0 or incorrect.
This will recalculate the area for all zones using proper UTM projection.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Zone
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj
import json

def fix_zone_areas():
    """Fix area calculations for all zones"""
    app = create_app()
    
    with app.app_context():
        zones = Zone.query.all()
        print(f"Found {len(zones)} zones to check...")
        
        fixed_count = 0
        error_count = 0
        
        for zone in zones:
            print(f"\nProcessing Zone {zone.id}: {zone.name}")
            print(f"Current area: {zone.area_sqm} m²")
            print(f"Current perimeter: {zone.perimeter_m} m")
            
            if not zone.geometry:
                print("  ❌ No geometry data - skipping")
                error_count += 1
                continue
            
            try:
                # Create polygon from stored geometry
                polygon = shape(zone.geometry)
                
                if not polygon.is_valid:
                    print("  ❌ Invalid polygon geometry - skipping")
                    error_count += 1
                    continue
                
                print(f"  📍 Polygon bounds: {polygon.bounds}")
                print(f"  📐 Polygon area (WGS84): {polygon.area}")
                
                # Convert to UTM for accurate area/perimeter calculation
                # Lusaka is in UTM Zone 35S
                wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (lat/lng)
                utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S
                
                # Transform to UTM for area calculation
                transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
                utm_polygon = transform(transformer.transform, polygon)
                
                # Calculate area and perimeter in meters
                new_area = utm_polygon.area
                new_perimeter = utm_polygon.length
                
                print(f"  🔧 UTM area: {new_area:.2f} m²")
                print(f"  🔧 UTM perimeter: {new_perimeter:.2f} m")
                
                # Update if different (with some tolerance for floating point differences)
                if abs(zone.area_sqm - new_area) > 1.0 or abs(zone.perimeter_m - new_perimeter) > 1.0:
                    old_area = zone.area_sqm
                    old_perimeter = zone.perimeter_m
                    
                    zone.area_sqm = new_area
                    zone.perimeter_m = new_perimeter
                    
                    # Also update centroid if needed
                    centroid = polygon.centroid
                    zone.centroid = mapping(centroid)
                    
                    print(f"  ✅ Updated: {old_area:.2f} → {new_area:.2f} m²")
                    print(f"  ✅ Updated: {old_perimeter:.2f} → {new_perimeter:.2f} m")
                    fixed_count += 1
                else:
                    print("  ✓ Area and perimeter are correct")
                
            except Exception as e:
                print(f"  ❌ Error processing zone: {e}")
                error_count += 1
                continue
        
        if fixed_count > 0:
            print(f"\n💾 Committing changes for {fixed_count} zones...")
            db.session.commit()
            print("✅ Changes committed successfully!")
        else:
            print("\n✓ No changes needed")
        
        print(f"\n📊 Summary:")
        print(f"  Total zones: {len(zones)}")
        print(f"  Fixed: {fixed_count}")
        print(f"  Errors: {error_count}")
        print(f"  Unchanged: {len(zones) - fixed_count - error_count}")

if __name__ == '__main__':
    fix_zone_areas()
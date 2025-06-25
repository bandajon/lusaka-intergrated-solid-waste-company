#!/usr/bin/env python3
"""
Test zone creation process to reproduce the "0.00 m²" issue
"""

import sys
import os
import json

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Zone, ZoneTypeEnum, ZoneStatusEnum
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj

def test_zone_creation_geometry():
    """Test the zone creation geometry processing"""
    app = create_app()
    
    with app.app_context():
        # Example geometry data that might come from the frontend
        # This is a simple square polygon around Lusaka
        test_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.2800, -15.3870],  # Southwest corner
                [28.2850, -15.3870],  # Southeast corner
                [28.2850, -15.3820],  # Northeast corner
                [28.2800, -15.3820],  # Northwest corner
                [28.2800, -15.3870]   # Close polygon
            ]]
        }
        
        print("Testing zone creation geometry processing...")
        print(f"Test geometry: {test_geometry}")
        
        # Test the geometry processing logic from zones.py
        try:
            # Validate geometry structure
            if not test_geometry or 'type' not in test_geometry or 'coordinates' not in test_geometry:
                raise ValueError("Invalid geometry structure: missing type or coordinates")
            
            if test_geometry['type'] != 'Polygon':
                raise ValueError(f"Expected Polygon geometry, got {test_geometry['type']}")
            
            if not test_geometry['coordinates'] or not test_geometry['coordinates'][0] or len(test_geometry['coordinates'][0]) < 4:
                raise ValueError("Polygon must have at least 4 coordinate points")
            
            print("✅ Geometry structure validation passed")
            
            # Create shapely polygon
            polygon = shape(test_geometry)
            print(f"✅ Shapely polygon created: {polygon}")
            
            if not polygon.is_valid:
                # Try to fix invalid geometry
                polygon = polygon.buffer(0)
                if not polygon.is_valid:
                    raise ValueError("Cannot create valid polygon from provided coordinates")
            
            print(f"✅ Polygon is valid: {polygon.is_valid}")
            print(f"Polygon bounds: {polygon.bounds}")
            print(f"Polygon area (WGS84): {polygon.area}")
            
            # Convert to UTM for accurate area/perimeter calculation
            # Lusaka is in UTM Zone 35S
            wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (lat/lng)
            utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S
            
            # Transform to UTM for area calculation
            transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
            utm_polygon = transform(transformer.transform, polygon)
            
            print(f"UTM polygon bounds: {utm_polygon.bounds}")
            print(f"UTM polygon area: {utm_polygon.area}")
            print(f"UTM polygon length: {utm_polygon.length}")
            
            # Calculate area and perimeter in meters
            area_sqm = utm_polygon.area
            perimeter_m = utm_polygon.length
            
            print(f"✅ Final area_sqm: {area_sqm:.2f}")
            print(f"✅ Final perimeter_m: {perimeter_m:.2f}")
            
            # Test creating a zone with this geometry
            print("\nTesting zone creation...")
            
            zone = Zone(
                name="Test Zone Creation",
                code="TEST001",
                description="Test zone for geometry processing",
                zone_type=ZoneTypeEnum.RESIDENTIAL,
                status=ZoneStatusEnum.DRAFT,
                estimated_population=1000,
                household_count=250,
                business_count=5,
                collection_frequency_week=2,
                created_by=1,
                import_source='test'
            )
            
            # Store geometry as GeoJSON (for SQLite)
            zone.geometry = mapping(polygon)
            zone.area_sqm = area_sqm
            zone.perimeter_m = perimeter_m
            
            # Store centroid as GeoJSON point
            centroid = polygon.centroid
            zone.centroid = mapping(centroid)
            
            print(f"Zone geometry stored: {zone.geometry}")
            print(f"Zone area_sqm: {zone.area_sqm}")
            print(f"Zone perimeter_m: {zone.perimeter_m}")
            print(f"Zone centroid: {zone.centroid}")
            
            # Add and commit to database
            db.session.add(zone)
            db.session.commit()
            
            print(f"✅ Zone created successfully with ID: {zone.id}")
            
            # Read back from database to verify
            retrieved_zone = Zone.query.get(zone.id)
            print(f"Retrieved zone area: {retrieved_zone.area_sqm}")
            print(f"Retrieved zone perimeter: {retrieved_zone.perimeter_m}")
            
            if retrieved_zone.area_sqm and retrieved_zone.area_sqm > 0:
                print("✅ SUCCESS: Zone area was stored and retrieved correctly!")
            else:
                print("❌ FAILURE: Zone area is zero or null after storage!")
                
            # Clean up
            db.session.delete(retrieved_zone)
            db.session.commit()
            print("✅ Test zone cleaned up")
            
        except Exception as e:
            print(f"❌ Error in geometry processing: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_zone_creation_geometry()
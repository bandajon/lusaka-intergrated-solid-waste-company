#!/usr/bin/env python3
"""
Check for zones with zero or null areas
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Zone

def check_zero_areas():
    """Check for zones with zero or null areas"""
    app = create_app()
    
    with app.app_context():
        zones = Zone.query.all()
        print(f"Checking {len(zones)} zones for zero or null areas...")
        
        zero_areas = []
        null_areas = []
        
        for zone in zones:
            print(f"\nZone {zone.id}: {zone.name}")
            print(f"  Area: {zone.area_sqm}")
            print(f"  Perimeter: {zone.perimeter_m}")
            print(f"  Has geometry: {'Yes' if zone.geometry else 'No'}")
            
            if zone.area_sqm is None:
                null_areas.append(zone)
                print("  ❌ NULL AREA")
            elif zone.area_sqm == 0:
                zero_areas.append(zone)
                print("  ❌ ZERO AREA")
            else:
                print(f"  ✅ Area: {zone.area_sqm:,.2f} m² ({zone.area_sqm/10000:.2f} hectares)")
        
        print(f"\n📊 Summary:")
        print(f"  Total zones: {len(zones)}")
        print(f"  Zones with NULL area: {len(null_areas)}")
        print(f"  Zones with ZERO area: {len(zero_areas)}")
        print(f"  Zones with valid area: {len(zones) - len(null_areas) - len(zero_areas)}")
        
        if null_areas:
            print(f"\n❌ Zones with NULL areas:")
            for zone in null_areas:
                print(f"  - Zone {zone.id}: {zone.name}")
        
        if zero_areas:
            print(f"\n❌ Zones with ZERO areas:")
            for zone in zero_areas:
                print(f"  - Zone {zone.id}: {zone.name}")

if __name__ == '__main__':
    check_zero_areas()
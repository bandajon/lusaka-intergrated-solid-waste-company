#!/usr/bin/env python3
"""
Test real zones from database to identify population extraction issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.zone import Zone
from app.utils.earth_engine_analysis import EarthEngineAnalyzer

def test_real_zones():
    """Test GHSL and WorldPop population extraction on real zones"""
    print("🔍 TESTING REAL ZONES FROM DATABASE")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # Get some real zones from the database
        zones = Zone.query.limit(3).all()
        
        if not zones:
            print("❌ No zones found in database")
            return
        
        # Initialize Earth Engine
        earth_engine = EarthEngineAnalyzer()
        
        for zone in zones:
            print(f"\n🧪 Testing Zone: {zone.name} (ID: {zone.id})")
            print("-" * 40)
            
            # Check zone geometry
            if not hasattr(zone, 'geojson') or not zone.geojson:
                print("❌ Zone has no geojson geometry")
                continue
                
            geom = zone.geojson.get('geometry', {})
            coords = geom.get('coordinates', [])
            if not coords:
                print("❌ Zone has no coordinates")
                continue
                
            print(f"✅ Zone has geometry: {geom.get('type', 'Unknown')} with {len(coords[0]) if coords else 0} points")
            if coords and coords[0]:
                print(f"   First coordinate: {coords[0][0]}")
                
            # Test GHSL extraction
            print("🧪 Testing GHSL extraction...")
            try:
                ghsl_result = earth_engine.extract_ghsl_population_for_zone(zone, 2020)
                if 'error' in ghsl_result:
                    print(f"❌ GHSL failed: {ghsl_result['error']}")
                else:
                    population = ghsl_result.get('total_population', 0)
                    print(f"✅ GHSL result: {population:,} people")
                    if population == 0:
                        print("⚠️  Zero population detected - investigating...")
                        # Show more details
                        pixel_count = ghsl_result.get('population_statistics', {}).get('populated_pixels', 0)
                        area = ghsl_result.get('zone_area_sqkm', 0)
                        print(f"   Zone area: {area:.4f} km²")
                        print(f"   Populated pixels: {pixel_count}")
                        print(f"   Data source: {ghsl_result.get('data_source', 'Unknown')}")
                        print(f"   Year: {ghsl_result.get('year', 'Unknown')}")
            except Exception as e:
                print(f"❌ GHSL extraction failed with exception: {str(e)}")
            
            # Test WorldPop extraction  
            print("🧪 Testing WorldPop extraction...")
            try:
                worldpop_result = earth_engine.extract_population_for_zone(zone, 2020)
                if 'error' in worldpop_result:
                    print(f"❌ WorldPop failed: {worldpop_result['error']}")
                else:
                    population = worldpop_result.get('total_population', 0)
                    print(f"✅ WorldPop result: {population:,} people")
                    if population == 0:
                        print("⚠️  Zero population detected in WorldPop too")
            except Exception as e:
                print(f"❌ WorldPop extraction failed with exception: {str(e)}")
                
            print()
    
    print("🏁 Real zone testing completed")
    print("=" * 60)

if __name__ == "__main__":
    test_real_zones()
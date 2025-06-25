#!/usr/bin/env python3
"""
Debug script to see the actual structure of truck_requirements output
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer

def debug_truck_requirements():
    """Debug the truck requirements output structure"""
    print("🔍 DEBUGGING TRUCK REQUIREMENTS OUTPUT")
    print("=" * 50)
    
    try:
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Simple test geometry
        test_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.2800, -15.4000],
                [28.2850, -15.4000],
                [28.2850, -15.3950],
                [28.2800, -15.3950],
                [28.2800, -15.4000]
            ]]
        }
        
        print("Creating mock zone...")
        mock_zone = analyzer._create_mock_zone(test_geometry)
        
        print(f"Mock zone centroid: {getattr(mock_zone, 'centroid', 'None')}")
        print(f"Mock zone estimated_population: {getattr(mock_zone, 'estimated_population', 'None')}")
        print(f"Mock zone area_sqm: {getattr(mock_zone, 'area_sqm', 'None')}")
        print()
        
        print("Calculating truck requirements...")
        truck_requirements = analyzer._calculate_truck_requirements(mock_zone)
        
        print("📋 TRUCK REQUIREMENTS OUTPUT:")
        print("=" * 30)
        print(json.dumps(truck_requirements, indent=2, default=str))
        
        print("\n🔍 AVAILABLE KEYS:")
        if isinstance(truck_requirements, dict):
            for key in truck_requirements.keys():
                value = truck_requirements[key]
                if isinstance(value, dict):
                    print(f"  📁 {key}: (dict with {len(value)} keys)")
                    for subkey in value.keys():
                        print(f"    - {subkey}")
                else:
                    print(f"  📄 {key}: {type(value).__name__}")
        
        # Look specifically for distance-related keys
        print("\n🎯 DISTANCE-RELATED KEYS:")
        def find_distance_keys(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if 'distance' in key.lower() or 'chunga' in key.lower():
                        print(f"  🎯 {full_key}: {value}")
                    if isinstance(value, dict):
                        find_distance_keys(value, full_key)
        
        find_distance_keys(truck_requirements)
        
        return truck_requirements
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_truck_requirements()
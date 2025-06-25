#!/usr/bin/env python3
"""
Test Earth Engine initialization within the Flask app context
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.earth_engine_analysis import EarthEngineAnalyzer

# Create app context
app = create_app('development')

with app.app_context():
    print("Testing Earth Engine in Flask app context...")
    
    # Initialize analyzer
    analyzer = EarthEngineAnalyzer()
    
    if analyzer.initialized:
        print("✓ Earth Engine initialized successfully in Flask app!")
        
        # Test with a simple zone
        class MockZone:
            def __init__(self):
                self.geojson = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [28.27, -15.41],
                            [28.28, -15.41],
                            [28.28, -15.42],
                            [28.27, -15.42],
                            [28.27, -15.41]
                        ]]
                    }
                }
        
        zone = MockZone()
        result = analyzer.analyze_zone_land_use(zone)
        
        if 'error' not in result:
            print("✓ Zone analysis working!")
            print(f"  Vegetation index: {result.get('vegetation_index', 'N/A')}")
            print(f"  Built-up index: {result.get('built_up_index', 'N/A')}")
        else:
            print(f"✗ Analysis failed: {result['error']}")
    else:
        print("✗ Earth Engine failed to initialize")
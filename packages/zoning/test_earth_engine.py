#!/usr/bin/env python3
"""
Test Google Earth Engine initialization and basic functionality
"""
import ee
import os
import sys

# Add the parent directory to the path so we can import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config

def test_earth_engine_initialization():
    """Test if Earth Engine can be initialized with the service account"""
    print("Testing Google Earth Engine initialization...")
    print(f"Service Account: {Config.GEE_SERVICE_ACCOUNT}")
    print(f"Key File: {Config.GEE_KEY_FILE}")
    
    # Check if the key file exists
    if not os.path.exists(Config.GEE_KEY_FILE):
        print(f"ERROR: Key file not found at {Config.GEE_KEY_FILE}")
        return False
    
    print("Key file found!")
    
    try:
        # Initialize with service account
        credentials = ee.ServiceAccountCredentials(
            Config.GEE_SERVICE_ACCOUNT, 
            Config.GEE_KEY_FILE
        )
        ee.Initialize(credentials)
        print("✓ Earth Engine initialized successfully!")
        
        # Test basic functionality
        print("\nTesting basic Earth Engine functionality...")
        
        # Create a simple geometry (Lusaka coordinates)
        point = ee.Geometry.Point([28.2833, -15.4166])
        
        # Try to fetch some data
        image = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(point) \
            .filterDate('2023-01-01', '2023-01-31') \
            .first()
        
        # Get image info
        info = image.getInfo()
        
        if info:
            print("✓ Successfully accessed Sentinel-2 imagery!")
            print(f"  Image ID: {info['id']}")
            print(f"  Bands: {len(info['bands'])}")
            return True
        else:
            print("✗ Could not fetch imagery data")
            return False
            
    except Exception as e:
        print(f"✗ Earth Engine initialization failed: {str(e)}")
        print(f"  Error type: {type(e).__name__}")
        return False

def test_earth_engine_analyzer():
    """Test the EarthEngineAnalyzer class"""
    print("\n\nTesting EarthEngineAnalyzer class...")
    
    try:
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        
        analyzer = EarthEngineAnalyzer()
        
        if analyzer.initialized:
            print("✓ EarthEngineAnalyzer initialized successfully!")
            
            # Create a test zone geometry (small area in Lusaka)
            test_zone = {
                'geojson': {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [28.27, -15.41],
                            [28.29, -15.41],
                            [28.29, -15.42],
                            [28.27, -15.42],
                            [28.27, -15.41]
                        ]]
                    }
                }
            }
            
            # Create a mock zone object
            class MockZone:
                def __init__(self, geojson):
                    self.geojson = geojson
            
            mock_zone = MockZone(test_zone['geojson'])
            
            print("\nTesting land use analysis...")
            result = analyzer.analyze_zone_land_use(mock_zone)
            
            if 'error' not in result:
                print("✓ Land use analysis completed!")
                print(f"  Vegetation index: {result.get('vegetation_index', 'N/A')}")
                print(f"  Built-up index: {result.get('built_up_index', 'N/A')}")
                print(f"  Vegetation coverage: {result.get('vegetation_coverage_percent', 'N/A')}%")
            else:
                print(f"✗ Land use analysis failed: {result['error']}")
                
        else:
            print("✗ EarthEngineAnalyzer failed to initialize")
            
    except Exception as e:
        print(f"✗ Error testing EarthEngineAnalyzer: {str(e)}")

if __name__ == "__main__":
    print("="*60)
    print("Google Earth Engine Configuration Test")
    print("="*60)
    
    # Test basic initialization
    if test_earth_engine_initialization():
        # Test the analyzer class
        test_earth_engine_analyzer()
    
    print("\n" + "="*60)
    print("Test complete!")
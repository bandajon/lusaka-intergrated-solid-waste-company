#!/usr/bin/env python3
"""
Test both Earth Engine authentication methods
"""
import ee
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config

def test_service_account():
    """Test service account authentication"""
    print("Testing Service Account Authentication...")
    print(f"Service Account: {Config.GEE_SERVICE_ACCOUNT}")
    print(f"Key File: {Config.GEE_KEY_FILE}")
    
    try:
        credentials = ee.ServiceAccountCredentials(
            Config.GEE_SERVICE_ACCOUNT, 
            Config.GEE_KEY_FILE
        )
        ee.Initialize(credentials)
        print("✓ Service account authentication successful!")
        
        # Test with a simple query
        point = ee.Geometry.Point([28.2833, -15.4166])
        image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(point) \
            .filterDate('2023-01-01', '2023-01-31') \
            .first()
        
        info = image.getInfo()
        if info:
            print(f"  Successfully accessed data: {info['id']}")
        
        return True
    except Exception as e:
        print(f"✗ Service account authentication failed: {str(e)}")
        return False

def test_default_auth():
    """Test default authentication"""
    print("\nTesting Default Authentication...")
    
    # Reset Earth Engine to test default auth
    ee.Reset()
    
    try:
        ee.Initialize()
        print("✓ Default authentication successful!")
        
        # Test with a simple query
        point = ee.Geometry.Point([28.2833, -15.4166])
        image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(point) \
            .filterDate('2023-01-01', '2023-01-31') \
            .first()
        
        info = image.getInfo()
        if info:
            print(f"  Successfully accessed data: {info['id']}")
        
        return True
    except Exception as e:
        print(f"✗ Default authentication failed: {str(e)}")
        print("  Run 'earthengine authenticate' to set up default authentication")
        return False

def test_earth_engine_analyzer():
    """Test the EarthEngineAnalyzer with both methods"""
    print("\nTesting EarthEngineAnalyzer class...")
    
    # Reset Earth Engine
    ee.Reset()
    
    from app.utils.earth_engine_analysis import EarthEngineAnalyzer
    
    analyzer = EarthEngineAnalyzer()
    
    if analyzer.initialized:
        print("✓ EarthEngineAnalyzer initialized successfully!")
        return True
    else:
        print("✗ EarthEngineAnalyzer failed to initialize")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Earth Engine Authentication Test")
    print("="*60)
    
    # Test service account (should work)
    service_account_works = test_service_account()
    
    # Test default auth (may fail if not authenticated)
    default_auth_works = test_default_auth()
    
    # Test the analyzer (should use service account)
    analyzer_works = test_earth_engine_analyzer()
    
    print("\n" + "="*60)
    print("Summary:")
    print(f"Service Account Authentication: {'✓ Working' if service_account_works else '✗ Not working'}")
    print(f"Default Authentication: {'✓ Working' if default_auth_works else '✗ Not set up (run earthengine authenticate)'}")
    print(f"EarthEngineAnalyzer: {'✓ Working' if analyzer_works else '✗ Not working'}")
    
    if service_account_works or default_auth_works:
        print("\n✓ Your Earth Engine configuration is working!")
        print("The zoning tool can now analyze zones using satellite data.")
    else:
        print("\n✗ Earth Engine is not properly configured.")
        print("Please check the setup guide in EARTH_ENGINE_SETUP.md")
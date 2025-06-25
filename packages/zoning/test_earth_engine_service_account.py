#!/usr/bin/env python3
"""
Test Earth Engine authentication with service account credentials
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from config.config import Config
from app.utils.earth_engine_analysis import EarthEngineAnalyzer

def test_earth_engine_authentication():
    """Test Earth Engine service account authentication"""
    print("Testing Earth Engine Service Account Authentication")
    print("=" * 50)
    
    # Show configuration
    print(f"Service Account: {Config.GEE_SERVICE_ACCOUNT}")
    print(f"Key File: {Config.GEE_KEY_FILE}")
    print(f"Key File Exists: {os.path.exists(Config.GEE_KEY_FILE)}")
    print()
    
    # Initialize analyzer
    analyzer = EarthEngineAnalyzer()
    
    # Check authentication status
    auth_status = analyzer.get_auth_status()
    print("Authentication Status:")
    print(f"  Initialized: {auth_status['initialized']}")
    print(f"  Error Details: {auth_status['error_details']}")
    print(f"  Can Provide Estimates: {auth_status['can_provide_estimates']}")
    print()
    
    if analyzer.initialized:
        print("✅ Earth Engine initialized successfully!")
        
        try:
            # Test a simple Earth Engine operation
            import ee
            
            # Test accessing a basic dataset
            dataset = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').first()
            info = dataset.getInfo()
            
            print("✅ Earth Engine API access confirmed!")
            print(f"Test dataset info: {info['id']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Earth Engine API test failed: {str(e)}")
            return False
    else:
        print("❌ Earth Engine initialization failed")
        return False

if __name__ == "__main__":
    success = test_earth_engine_authentication()
    if success:
        print("\n🎉 Earth Engine service account authentication successful!")
    else:
        print("\n💥 Earth Engine service account authentication failed!")
    
    exit(0 if success else 1)
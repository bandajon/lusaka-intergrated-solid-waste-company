#!/usr/bin/env python3
"""
Test Google Earth Engine with default authentication
Similar to your working example
"""
import ee
import datetime

# Initialize Earth Engine with default authentication
print("Initializing Earth Engine with default authentication...")
try:
    ee.Initialize()
    print("✓ Earth Engine initialized successfully!")
except Exception as e:
    print(f"✗ Initialization failed: {str(e)}")
    print("\nPlease run 'earthengine authenticate' in your terminal first")
    exit(1)

# Test with a simple analysis
def test_earth_engine():
    """Test Earth Engine functionality"""
    # Define a test area in Lusaka
    lusaka_point = ee.Geometry.Point([28.2833, -15.4166])
    
    # Calculate dates (last 30 days)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\nFetching Sentinel-2 data from {start_date_str} to {end_date_str}...")
    
    # Get Sentinel-2 imagery
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(lusaka_point) \
        .filterDate(start_date_str, end_date_str) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    
    # Get collection size
    count = sentinel2.size()
    print(f"Found {count.getInfo()} images")
    
    # Get the first image
    first_image = sentinel2.first()
    image_info = first_image.getInfo()
    
    if image_info:
        print(f"✓ Successfully accessed imagery!")
        print(f"  Image ID: {image_info['id']}")
        print(f"  Date: {image_info['properties']['system:time_start']}")
        
        # Calculate NDVI for the area
        buffer_zone = lusaka_point.buffer(1000)  # 1km buffer
        ndvi = first_image.normalizedDifference(['B8', 'B4'])
        
        ndvi_stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=buffer_zone,
            scale=10,
            maxPixels=1e9
        )
        
        ndvi_value = ndvi_stats.getInfo()
        print(f"  NDVI (vegetation index): {ndvi_value.get('nd', 0):.3f}")
        
        return True
    else:
        print("✗ No imagery found")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Testing Earth Engine with Default Authentication")
    print("="*60)
    
    if test_earth_engine():
        print("\n✓ Earth Engine is working correctly!")
        print("\nThe zoning tool will now work with either:")
        print("1. Default authentication (after running 'earthengine authenticate')")
        print("2. Service account authentication (using the JSON file)")
    else:
        print("\n✗ Test failed")
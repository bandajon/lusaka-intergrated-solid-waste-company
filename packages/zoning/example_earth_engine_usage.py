#!/usr/bin/env python3
"""
Example of using Google Earth Engine with the zoning tool
This demonstrates how to analyze zones using satellite data
"""
import ee
from config.config import Config

# Initialize Earth Engine with your credentials
credentials = ee.ServiceAccountCredentials(
    Config.GEE_SERVICE_ACCOUNT, 
    Config.GEE_KEY_FILE
)
ee.Initialize(credentials)

print("✓ Google Earth Engine initialized successfully!")

# Example 1: Analyze a specific area in Lusaka
def analyze_lusaka_area():
    """Analyze a sample area in Lusaka"""
    # Define a polygon for a sample zone in Lusaka
    lusaka_zone = ee.Geometry.Polygon([[
        [28.27, -15.41],
        [28.29, -15.41],
        [28.29, -15.42],
        [28.27, -15.42],
        [28.27, -15.41]
    ]])
    
    print("\nAnalyzing sample zone in Lusaka...")
    
    # Get Sentinel-2 imagery
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(lusaka_zone) \
        .filterDate('2023-01-01', '2024-01-01') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .median()
    
    # Calculate NDVI (vegetation index)
    ndvi = sentinel2.normalizedDifference(['B8', 'B4']).rename('ndvi')
    
    # Get statistics
    stats = ndvi.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.minMax(), '', True
        ),
        geometry=lusaka_zone,
        scale=10,
        maxPixels=1e9
    )
    
    result = stats.getInfo()
    print(f"Vegetation Index (NDVI):")
    print(f"  Mean: {result.get('ndvi_mean', 0):.3f}")
    print(f"  Min: {result.get('ndvi_min', 0):.3f}")
    print(f"  Max: {result.get('ndvi_max', 0):.3f}")
    
    return result

# Example 2: Get population data for a zone
def get_population_data():
    """Get population estimate for a zone"""
    # Define a larger area for population analysis
    zone = ee.Geometry.Rectangle([28.25, -15.45, 28.30, -15.40])
    
    print("\nGetting population data...")
    
    # WorldPop data for Zambia
    worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
        .filter(ee.Filter.eq('country', 'ZMB')) \
        .filter(ee.Filter.eq('year', 2020)) \
        .first()
    
    # Calculate total population
    pop_sum = worldpop.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=zone,
        scale=100,
        maxPixels=1e9
    )
    
    result = pop_sum.getInfo()
    total_pop = result.get('population', 0)
    
    print(f"Estimated population in zone: {int(total_pop):,}")
    
    return total_pop

# Example 3: Climate data analysis
def analyze_climate():
    """Analyze climate data for waste management planning"""
    # Point location in Lusaka
    location = ee.Geometry.Point([28.2833, -15.4166])
    
    print("\nAnalyzing climate data...")
    
    # Get temperature data
    climate = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY') \
        .filterBounds(location) \
        .filterDate('2023-01-01', '2024-01-01') \
        .select(['temperature_2m'])
    
    # Calculate annual average
    annual_temp = climate.mean()
    
    # Get value at point
    temp_value = annual_temp.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=location,
        scale=1000
    ).getInfo()
    
    # Convert from Kelvin to Celsius
    temp_celsius = temp_value.get('temperature_2m', 273.15) - 273.15
    
    print(f"Average temperature: {temp_celsius:.1f}°C")
    
    # Recommend collection frequency based on temperature
    if temp_celsius > 30:
        recommendation = "Daily collection recommended"
    elif temp_celsius > 25:
        recommendation = "3-4 times per week"
    elif temp_celsius > 20:
        recommendation = "2-3 times per week"
    else:
        recommendation = "2 times per week"
    
    print(f"Waste collection recommendation: {recommendation}")
    
    return temp_celsius, recommendation

if __name__ == "__main__":
    print("="*60)
    print("Google Earth Engine Analysis Examples")
    print("="*60)
    
    try:
        # Run examples
        analyze_lusaka_area()
        get_population_data()
        analyze_climate()
        
        print("\n✓ All analyses completed successfully!")
        print("\nYour Earth Engine configuration is working correctly!")
        print("The zoning tool can now use satellite data for:")
        print("- Land use classification")
        print("- Population estimation")
        print("- Environmental monitoring")
        print("- Climate-based waste collection planning")
        
    except Exception as e:
        print(f"\n✗ Error during analysis: {str(e)}")
        print("Please check your Earth Engine credentials and permissions.")
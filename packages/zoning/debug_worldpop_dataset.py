#!/usr/bin/env python3
"""
Debug WorldPop dataset to understand why it's returning 0 population
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.earth_engine_analysis import EarthEngineAnalyzer
import ee

def debug_worldpop_dataset():
    """Debug WorldPop dataset access to identify issues"""
    print("🔍 DEBUGGING WORLDPOP DATASET ACCESS")
    print("=" * 60)
    
    # Initialize Earth Engine
    earth_engine = EarthEngineAnalyzer()
    
    if not earth_engine.initialized:
        print("❌ Earth Engine not initialized")
        return
    
    print("✅ Earth Engine initialized")
    
    # Test 1: Check WorldPop collection availability
    print("\n🧪 Test 1: WorldPop Collection Availability")
    print("-" * 40)
    
    try:
        worldpop_collection = ee.ImageCollection('WorldPop/GP/100m/pop')
        print("✅ WorldPop collection accessible")
        
        # Get collection info
        collection_info = worldpop_collection.getInfo()
        print(f"   Collection ID: WorldPop/GP/100m/pop")
        print(f"   Collection type: {collection_info.get('type', 'Unknown')}")
        
        # Get available years
        years = worldpop_collection.aggregate_array('year').distinct().sort().getInfo()
        print(f"   Available years: {years}")
        
    except Exception as e:
        print(f"❌ WorldPop collection access failed: {str(e)}")
        return
    
    # Test 2: Check specific year availability  
    print("\n🧪 Test 2: Check 2020 Data Availability")
    print("-" * 40)
    
    try:
        worldpop_2020 = worldpop_collection.filter(ee.Filter.eq('year', 2020))
        count = worldpop_2020.size().getInfo()
        print(f"✅ Images for 2020: {count}")
        
        if count > 0:
            first_image = worldpop_2020.first()
            image_info = first_image.getInfo()
            print(f"   First image ID: {image_info.get('id', 'Unknown')}")
            
            # Check bands
            bands = first_image.bandNames().getInfo()
            print(f"   Bands: {bands}")
            
            # Check properties
            properties = image_info.get('properties', {})
            print(f"   Year property: {properties.get('year', 'Missing')}")
            print(f"   Country property: {properties.get('country', 'Missing')}")
            
        else:
            print("❌ No images found for 2020")
            
    except Exception as e:
        print(f"❌ 2020 data check failed: {str(e)}")
        return
    
    # Test 3: Test data extraction for Lusaka area
    print("\n🧪 Test 3: Test Data Extraction for Lusaka")
    print("-" * 40)
    
    try:
        # Create a simple Lusaka test point/area
        lusaka_point = ee.Geometry.Point([28.284, -15.417])  # Central Lusaka
        lusaka_area = lusaka_point.buffer(1000)  # 1km buffer
        
        print(f"✅ Test geometry created around Lusaka center")
        
        # Try to get WorldPop data for this area
        worldpop_2020 = worldpop_collection.filter(ee.Filter.eq('year', 2020)).first()
        
        # Check if the image exists
        if worldpop_2020:
            print("✅ 2020 image exists")
            
            # Clip to test area
            clipped = worldpop_2020.clip(lusaka_area)
            
            # Get reduction statistics
            stats = clipped.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.count(), '', True
                    ), '', True
                ),
                geometry=lusaka_area,
                scale=100,
                maxPixels=1e6
            ).getInfo()
            
            print(f"   Population sum: {stats.get('population_sum', 'Missing')}")
            print(f"   Population mean: {stats.get('population_mean', 'Missing')}")
            print(f"   Pixel count: {stats.get('population_count', 'Missing')}")
            
            # Check for different band names
            print(f"   All stats keys: {list(stats.keys())}")
            
        else:
            print("❌ No 2020 image found")
            
    except Exception as e:
        print(f"❌ Lusaka area test failed: {str(e)}")
    
    # Test 4: Alternative WorldPop datasets
    print("\n🧪 Test 4: Alternative WorldPop Datasets")
    print("-" * 40)
    
    alternative_datasets = [
        'WorldPop/GP/100m/pop_age_sex_cons_unadj',
        'WorldPop/POP',
        'WorldPop/GP/100m/pop_age_sex'
    ]
    
    for dataset in alternative_datasets:
        try:
            alt_collection = ee.ImageCollection(dataset)
            # Try to get basic info
            size = alt_collection.size().getInfo()
            print(f"✅ {dataset}: {size} images")
        except Exception as e:
            print(f"❌ {dataset}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔍 WORLDPOP DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    debug_worldpop_dataset()
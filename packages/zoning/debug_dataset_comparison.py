#!/usr/bin/env python3
"""
Compare GHSL (working) vs WorldPop (not working) dataset access patterns
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ee
from app.utils.earth_engine_analysis import EarthEngineAnalyzer

def compare_datasets():
    """Compare GHSL vs WorldPop dataset access"""
    print("🔍 COMPARING GHSL (WORKING) VS WORLDPOP (NOT WORKING)")
    print("=" * 60)
    
    # Initialize Earth Engine
    earth_engine = EarthEngineAnalyzer()
    
    if not earth_engine.initialized:
        print("❌ Earth Engine not initialized")
        return
    
    # Test area in Lusaka
    lusaka_point = ee.Geometry.Point([28.284, -15.417])
    lusaka_area = lusaka_point.buffer(1000)
    
    # Test 1: GHSL Dataset (GPWv4.11) - This works
    print("\n🧪 Test 1: GHSL/GPWv4.11 Dataset (Working)")
    print("-" * 50)
    
    try:
        gpw_collection = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Count")
        print("✅ GPWv4.11 collection accessible")
        
        # Filter to 2020 (same as GHSL function)
        gpw_2020 = gpw_collection.filter(ee.Filter.date('2020-01-01', '2020-12-31')).first()
        
        if gpw_2020:
            print("✅ 2020 GPWv4.11 image found")
            
            # Test extraction (same as GHSL function)
            population_band = gpw_2020.select('population_count')
            population_band = population_band.updateMask(population_band.gt(0))
            zone_population = population_band.clip(lusaka_area)
            
            stats = zone_population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.count(), '', True
                    ), '', True
                ),
                geometry=lusaka_area,
                scale=927.67,  # GPWv4.11 scale
                maxPixels=1e9
            ).getInfo()
            
            print(f"   Population sum: {stats.get('population_count_sum', 'Missing')}")
            print(f"   Population mean: {stats.get('population_count_mean', 'Missing')}")
            print(f"   Pixel count: {stats.get('population_count_count', 'Missing')}")
        else:
            print("❌ No 2020 GPWv4.11 image found")
            
    except Exception as e:
        print(f"❌ GPWv4.11 test failed: {str(e)}")
    
    # Test 2: WorldPop Dataset - This doesn't work  
    print("\n🧪 Test 2: WorldPop Dataset (Not Working)")
    print("-" * 50)
    
    try:
        # Use the same filter approach as the WorldPop function
        worldpop = ee.ImageCollection('WorldPop/GP/100m/pop').filter(ee.Filter.eq('year', 2020)).first()
        
        if worldpop:
            print("✅ 2020 WorldPop image found")
            
            # Test extraction (same as WorldPop function)
            zone_population = worldpop.clip(lusaka_area)
            
            stats = zone_population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.count(), '', True
                    ), '', True
                ),
                geometry=lusaka_area,
                scale=100,  # WorldPop scale
                maxPixels=1e9
            ).getInfo()
            
            print(f"   Population sum: {stats.get('population_sum', 'Missing')}")
            print(f"   Population mean: {stats.get('population_mean', 'Missing')}")
            print(f"   Pixel count: {stats.get('population_count', 'Missing')}")
            print(f"   All keys: {list(stats.keys())}")
            
        else:
            print("❌ No 2020 WorldPop image found")
            
    except Exception as e:
        print(f"❌ WorldPop test failed: {str(e)}")
    
    # Test 3: Check WorldPop band names
    print("\n🧪 Test 3: WorldPop Band Investigation")
    print("-" * 50)
    
    try:
        # Try to get a WorldPop image and check its bands
        worldpop = ee.ImageCollection('WorldPop/GP/100m/pop').limit(1).first()
        
        if worldpop:
            bands = worldpop.bandNames().getInfo()
            print(f"✅ WorldPop bands: {bands}")
            
            # Check image properties
            properties = worldpop.getInfo().get('properties', {})
            print(f"   Year: {properties.get('year', 'Missing')}")
            print(f"   Country: {properties.get('country', 'Missing')}")
            print(f"   UNadj: {properties.get('UNadj', 'Missing')}")
            
        else:
            print("❌ Could not get WorldPop image")
            
    except Exception as e:
        print(f"❌ WorldPop band investigation failed: {str(e)}")
    
    # Test 4: Alternative WorldPop filter approaches
    print("\n🧪 Test 4: Alternative WorldPop Filtering")
    print("-" * 50)
    
    try:
        # Try different filtering approaches
        
        # Approach 1: Filter by date range instead of year property
        print("🔍 Trying date range filter...")
        worldpop_date = ee.ImageCollection('WorldPop/GP/100m/pop').filter(
            ee.Filter.date('2020-01-01', '2020-12-31')
        ).first()
        
        if worldpop_date:
            print("✅ Date range filter found image")
        else:
            print("❌ Date range filter found no images")
        
        # Approach 2: Get most recent image
        print("🔍 Trying most recent image...")
        worldpop_recent = ee.ImageCollection('WorldPop/GP/100m/pop').sort('system:time_start', False).first()
        
        if worldpop_recent:
            recent_props = worldpop_recent.getInfo().get('properties', {})
            print(f"✅ Most recent image year: {recent_props.get('year', 'Unknown')}")
        else:
            print("❌ Could not get recent image")
        
    except Exception as e:
        print(f"❌ Alternative filtering failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔍 DATASET COMPARISON COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    compare_datasets()
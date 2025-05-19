"""
Test script to verify Google Earth Engine road datasets for Lusaka, Zambia
"""

import ee

# Initialize Earth Engine
ee.Initialize()

# Lusaka, Zambia coordinates
lusaka = ee.Geometry.Point([28.2826, -15.4067])
lusaka_area = lusaka.buffer(50000)  # 50km buffer

# Example 1: TIGER Roads
try:
    tiger_roads = ee.FeatureCollection('TIGER/2016/Roads')
    lusaka_tiger = tiger_roads.filterBounds(lusaka_area)
    print("TIGER/2016/Roads is available")
    print("Sample code:")
    print("""
    // TIGER Roads 2016
    var tiger = ee.FeatureCollection('TIGER/2016/Roads');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    var lusakaArea = lusaka.buffer(50000);
    var lusakaRoads = tiger.filterBounds(lusakaArea);
    Map.addLayer(lusakaRoads, {color: 'red'}, 'Lusaka Roads');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"TIGER/2016/Roads error: {str(e)}")

# Example 2: Updated TIGER Roads
try:
    tiger_roads_2018 = ee.FeatureCollection('projects/earthengine-legacy/assets/TIGER/2018/Roads')
    lusaka_tiger_2018 = tiger_roads_2018.filterBounds(lusaka_area)
    print("projects/earthengine-legacy/assets/TIGER/2018/Roads is available")
    print("Sample code:")
    print("""
    // TIGER Roads 2018
    var tiger2018 = ee.FeatureCollection('projects/earthengine-legacy/assets/TIGER/2018/Roads');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    var lusakaArea = lusaka.buffer(50000);
    var lusakaRoads = tiger2018.filterBounds(lusakaArea);
    Map.addLayer(lusakaRoads, {color: 'blue'}, 'Lusaka Roads 2018');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"TIGER/2018/Roads error: {str(e)}")

# Example 3: OpenStreetMap 
try:
    osm_roads = ee.FeatureCollection('ft:1LieStBARqOSo5oWwrqfHVH9Z9V0SEC1jXsQOIiQb')
    lusaka_osm = osm_roads.filterBounds(lusaka_area)
    print("ft:1LieStBARqOSo5oWwrqfHVH9Z9V0SEC1jXsQOIiQb (OpenStreetMap) is available")
    print("Sample code:")
    print("""
    // OpenStreetMap Roads
    var osm = ee.FeatureCollection('ft:1LieStBARqOSo5oWwrqfHVH9Z9V0SEC1jXsQOIiQb');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    var lusakaArea = lusaka.buffer(50000);
    var lusakaRoads = osm.filterBounds(lusakaArea);
    Map.addLayer(lusakaRoads, {color: 'green'}, 'Lusaka OSM Roads');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"OpenStreetMap error: {str(e)}")

# Example 4: GLAD Roads
try:
    glad_roads = ee.FeatureCollection('projects/glad/GLCLU2020/Roads_2020')
    lusaka_glad = glad_roads.filterBounds(lusaka_area)
    print("projects/glad/GLCLU2020/Roads_2020 is available")
    print("Sample code:")
    print("""
    // GLAD Roads 2020
    var glad = ee.FeatureCollection('projects/glad/GLCLU2020/Roads_2020');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    var lusakaArea = lusaka.buffer(50000);
    var lusakaRoads = glad.filterBounds(lusakaArea);
    Map.addLayer(lusakaRoads, {color: 'yellow'}, 'Lusaka GLAD Roads');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"GLAD Roads error: {str(e)}")

# Example 5: JRC Global Surface Water - Occurrence used as potential proxy for identifying roads
try:
    water = ee.Image('JRC/GSW1_3/GlobalSurfaceWater')
    print("JRC/GSW1_3/GlobalSurfaceWater is available (can be used to mask roads)")
    print("Sample code:")
    print("""
    // JRC Surface Water (inverse can help identify roads)
    var water = ee.Image('JRC/GSW1_3/GlobalSurfaceWater');
    var occurrence = water.select('occurrence');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    // Roads typically have 0 water occurrence
    var potentialRoads = occurrence.eq(0);
    Map.addLayer(potentialRoads.clip(lusaka.buffer(50000)), {min: 0, max: 1, palette: ['black', 'white']}, 'Potential Roads');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"JRC Surface Water error: {str(e)}")

# Example 6: USGS NLCD Land Cover (can be used to extract roads)
try:
    nlcd = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD')
    print("USGS/NLCD_RELEASES/2019_REL/NLCD is available")
    print("Sample code:")
    print("""
    // USGS NLCD Land Cover (road class is typically highlighted)
    var nlcd = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD');
    var landcover = nlcd.first().select('landcover');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    Map.addLayer(landcover.clip(lusaka.buffer(50000)), {}, 'Land Cover (roads)');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"USGS NLCD error: {str(e)}")

# Example 7: ESA WorldCover (can identify urban areas including roads)
try:
    worldcover = ee.ImageCollection('ESA/WorldCover/v100')
    print("ESA/WorldCover/v100 is available")
    print("Sample code:")
    print("""
    // ESA WorldCover (urban class includes roads)
    var worldcover = ee.ImageCollection('ESA/WorldCover/v100').first();
    var urban = worldcover.select('Map').eq(50); // 50 is urban class
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    Map.addLayer(urban.clip(lusaka.buffer(50000)), {min: 0, max: 1, palette: ['black', 'gray']}, 'Urban (including roads)');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"ESA WorldCover error: {str(e)}")

# Example 8: VIIRS Night Lights (can be used to identify roads in urban areas)
try:
    viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
    print("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG is available")
    print("Sample code:")
    print("""
    // VIIRS Night Lights (can show roads in urban areas)
    var viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
                  .filterDate('2022-01-01', '2022-12-31')
                  .mean()
                  .select('avg_rad');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    // Threshold to highlight brighter areas (including roads)
    var roads = viirs.gt(1);
    Map.addLayer(roads.clip(lusaka.buffer(50000)), {min: 0, max: 1, palette: ['black', 'yellow']}, 'Potential Roads from Night Lights');
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"VIIRS Night Lights error: {str(e)}")

# Example 9: Google Earth Engine Open Buildings
try:
    buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
    print("GOOGLE/Research/open-buildings/v3/polygons is available (can be used to infer roads)")
    print("Sample code:")
    print("""
    // Google Open Buildings (can be used to infer roads between buildings)
    var buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons');
    var lusaka = ee.Geometry.Point([28.2826, -15.4067]);
    var lusakaArea = lusaka.buffer(50000);
    var lusakaBuildings = buildings.filterBounds(lusakaArea);
    Map.addLayer(lusakaBuildings, {color: 'red'}, 'Lusaka Buildings');
    // Buildings often line roads, so this dataset can help infer road networks
    Map.centerObject(lusaka, 10);
    """)
except Exception as e:
    print(f"Google Open Buildings error: {str(e)}")

print("\nIf no datasets are available with direct EE authentication, try these confirmed road datasets in the Earth Engine Code Editor:")
print("1. TIGER/2016/Roads (US only, won't have data for Zambia)")
print("2. projects/sat-io/open-datasets/africaroads - Africa Roads")
print("3. GOOGLE/Research/open-buildings/v3/polygons - Buildings can be used to infer roads")
print("4. ESA/WorldCover/v100 - Urban class (50) includes roads")
print("5. NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG - Night lights can highlight major roads")
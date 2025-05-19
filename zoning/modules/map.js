// Map handling module

var ui = require('ui');
var ee = require('ee');
var config = require('./config');

// Create and configure the main map
exports.createMap = function() {
  // Create a map centered on Lusaka and surrounding areas
  var map = ui.Map();
  map.setCenter(
    config.LUSAKA_CENTER[0], 
    config.LUSAKA_CENTER[1], 
    config.DEFAULT_ZOOM
  );
  
  // Add base layers
  addBaseLayers(map);
  
  // Configure map options
  map.setControlVisibility({
    all: true,
    zoomControl: true,
    layerList: true,
    drawingToolsControl: false // We'll handle drawing via our custom UI
  });
  
  return map;
};

// Add base layers to the map
function addBaseLayers(map) {
  // Add district boundaries
  var districts = ee.FeatureCollection(config.ADMIN_BOUNDARIES)
    .filter(ee.Filter.eq('ADM0_NAME', 'Zambia'))
    .filterBounds(config.REGION_BOUNDARY);
  
  var districtsLayer = ui.Map.Layer(districts, {
    color: '#3f569e',
    fillColor: '#00000000', // Transparent fill
    width: 2
  }, 'District Boundaries');
  map.add(districtsLayer);
  
  // Add Urban Areas (includes roads) from WorldCover
  print("Loading urban areas from WorldCover");
  try {
    // Load WorldCover data
    var worldcover = ee.ImageCollection(config.WORLDCOVER_DATASET).first();
    
    // Extract urban class (50) - this includes roads and built-up areas
    var urban = worldcover.select('Map').eq(50);
    
    // Create visualization - just show urban areas which include roads
    var urbanLayer = ui.Map.Layer(
      urban.clip(config.REGION_BOUNDARY), 
      {min: 0, max: 1, palette: ['#00000000', '#666666']}, 
      'Urban Areas (includes roads)'
    );
    
    // Add layer
    map.add(urbanLayer);
    
    print("Urban areas loaded successfully");
  } catch(e) {
    print("Error loading urban areas:", e);
  }
  
  // Add buildings as a base layer (initially hidden)
  print("Loading building data");
  try {
    var buildings = ee.FeatureCollection(config.BUILDINGS_DATASET)
      .filterBounds(config.REGION_BOUNDARY);
    
    var buildingsLayer = ui.Map.Layer(buildings, {color: '#FF0000'}, 'Buildings', false);
    map.add(buildingsLayer);
    print("Buildings loaded successfully");
  } catch(e) {
    print("Error loading buildings:", e);
  }
  
  // Add population density layer (initially hidden)
  print("Loading population data");
  try {
    var population = ee.ImageCollection(config.POPULATION_DATASET)
      .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
      .first() 
      .clip(config.REGION_BOUNDARY);
    
    var populationViz = {
      min: 0,
      max: 100,
      palette: ['blue', 'yellow', 'red']
    };
    
    var populationLayer = ui.Map.Layer(population, populationViz, 'Population Density', false);
    map.add(populationLayer);
    print("Population data loaded successfully");
  } catch(e) {
    print("Error loading population data:", e);
  }
  
  // Add land cover layer (initially hidden)
  print("Loading land cover data");
  try {
    var landcover = ee.Image(config.LAND_COVER)
      .select('discrete_classification')
      .clip(config.REGION_BOUNDARY);
    
    // Define visualization parameters for Copernicus Land Cover
    var landcoverViz = {
      bands: ['discrete_classification'],
      min: 0, 
      max: 200,
      palette: [
        '#282828', '#FFBB22', '#FFFF4C', '#10D22C', '#53A01D', 
        '#02D8E9', '#0F47FF', '#FFFFFF', '#FF00FF'
      ]
    };
    
    var landcoverLayer = ui.Map.Layer(landcover, landcoverViz, 'Land Cover', false);
    map.add(landcoverLayer);
    print("Land cover data loaded successfully");
  } catch(e) {
    print("Error loading land cover:", e);
  }
  
  return map;
}

// Helper function to clear all drawn features
exports.clearDrawings = function(map) {
  map.drawingTools().layers().reset();
};

// Helper function to add a zone to the map
exports.addZoneToMap = function(map, zone, name, color, selected) {
  var zoneLayer = ui.Map.Layer(zone, {color: color}, name);
  map.layers().add(zoneLayer);
  return zoneLayer;
};

// Helper function to highlight buildings by class
exports.highlightBuildingsByClass = function(map, buildings, isVisible) {
  // Remove existing building layers first
  map.layers().forEach(function(layer) {
    if (layer.getName().indexOf('Buildings - ') === 0) {
      map.remove(layer);
    }
  });
  
  if (!isVisible) return;
  
  // Add a layer for each building class
  Object.keys(config.BUILDING_CLASSES).forEach(function(classKey) {
    var classInfo = config.BUILDING_CLASSES[classKey];
    var classColor = config.COLORS.BUILDINGS[classKey];
    var classLabel = classInfo.label;
    
    var classBuildings = buildings.filter(function(feature) {
      var area = feature.geometry().area();
      if (classInfo.min && classInfo.max) {
        return area.gte(classInfo.min).and(area.lt(classInfo.max));
      } else if (classInfo.min) {
        return area.gte(classInfo.min);
      } else if (classInfo.max) {
        return area.lt(classInfo.max);
      }
      return ee.Filter.eq('dummy', 'dummy'); // Should never happen
    });
    
    var layer = ui.Map.Layer(
      classBuildings,
      {color: classColor},
      'Buildings - ' + classLabel
    );
    
    map.layers().add(layer);
  });
};
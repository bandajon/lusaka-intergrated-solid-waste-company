/**
 * Lusaka Integrated Waste Management Zone Planning Tool
 * Standalone version with all modules combined in a single file
 */

// Configuration parameters
var CONFIG = {
  // Geographic constants
  LUSAKA_CENTER: [28.2816, -15.3875], // Longitude, Latitude for central Lusaka
  DEFAULT_ZOOM: 11, // Zoomed out to show greater Lusaka area
  REGION_BOUNDARY: ee.Geometry.Polygon([
    // Expanded boundary to include Lusaka and surrounding areas (Chongwe, Chilanga, Chibombo)
    [27.9500, -15.7000], // Southwest
    [28.6500, -15.7000], // Southeast
    [28.6500, -15.1000], // Northeast
    [27.9500, -15.1000]  // Northwest
  ]), // Greater Lusaka area including surrounding districts

  // Data sources
  BUILDINGS_DATASET: 'GOOGLE/Research/open-buildings/v3/polygons', // Google Open Buildings dataset with confidence scores
  POPULATION_DATASET: 'WorldPop/GP/100m/pop',
  WORLDCOVER_DATASET: 'ESA/WorldCover/v100', // ESA WorldCover (urban class includes roads)
  LAND_COVER: 'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019', // Copernicus Global Land Cover
  ADMIN_BOUNDARIES: 'FAO/GAUL/2015/level2', // Admin level 2 boundaries (districts)

  // Building classification thresholds (sq meters of footprint area)
  BUILDING_CLASSES: {
    RESIDENTIAL_PERI_URBAN: { max: 80, label: 'Residential Peri-Urban' }, // Small homes - under 80 sq m footprint
    RESIDENTIAL_URBAN: { min: 80, max: 150, label: 'Residential Urban' }, // Medium homes - 80-150 sq m footprint
    COMMERCIAL_SMALL: { min: 150, max: 300, label: 'Commercial Small' }, // Small businesses - 150-300 sq m
    COMMERCIAL_MEDIUM: { min: 300, max: 800, label: 'Commercial Medium' }, // Medium businesses - 300-800 sq m
    COMMERCIAL_LARGE: { min: 800, label: 'Commercial Large' } // Large businesses - over 800 sq m
  },
  
  // Building analysis constants
  BUILDING_ANALYSIS: {
    AREA_ADJUSTMENT_FACTOR: 0.9, // Adjustment factor for building areas (compensate for outlining errors)
    COUNT_ADJUSTMENT_FACTOR: 0.98, // Adjustment factor for building counts (prevent potential double counting)
    USE_CENTROID_FILTER: true, // Whether to filter buildings based on centroid containment
    MIN_CONFIDENCE_SCORE: 0.75, // Minimum confidence score (0-1) for Google's Open Buildings dataset (set to 0.75)
    MIN_BUILDING_SIZE: 10, // Minimum size in square meters (much less strict, just to filter extremely small objects)
    MAX_BUILDING_SIZE: 30000 // Maximum size in square meters (very permissive, only filters extreme outliers)
  },

  // Pricing tiers (Kwacha/month)
  PRICING: {
    RESIDENTIAL_PERI_URBAN: 30,
    RESIDENTIAL_URBAN: 40,
    COMMERCIAL_SMALL: 100,
    COMMERCIAL_MEDIUM: 250,
    COMMERCIAL_LARGE: 500
  },

  // Waste generation parameters
  WASTE_GENERATION: {
    // kg per person/business per day
    RESIDENTIAL_PER_PERSON: 0.5,
    COMMERCIAL_SMALL: 5,
    COMMERCIAL_MEDIUM: 20,
    COMMERCIAL_LARGE: 50,
    // Cost in Kwacha per ton
    DISPOSAL_COST: 100
  },

  // UI constants
  PANEL_WIDTH: '350px',
  COLORS: {
    MAIN_ZONE: '#FF5733',
    SUB_ZONE: '#33A1FF',
    SELECTED_ZONE: '#33FF57',
    BUILDINGS: {
      RESIDENTIAL_PERI_URBAN: '#FFC300',
      RESIDENTIAL_URBAN: '#DAF7A6',
      COMMERCIAL_SMALL: '#C70039',
      COMMERCIAL_MEDIUM: '#900C3F',
      COMMERCIAL_LARGE: '#581845'
    }
  },

  // Common districts in the study area
  DISTRICTS: [
    {name: 'Lusaka', center: [28.2816, -15.3875], zoom: 12},
    {name: 'Chongwe', center: [28.6820, -15.3278], zoom: 12},
    {name: 'Chilanga', center: [28.2790, -15.5621], zoom: 12},
    {name: 'Kafue', center: [28.1814, -15.7607], zoom: 12},
    {name: 'Chibombo', center: [28.0731, -14.6543], zoom: 11}
  ],

  // Operational expenses (simplified model)
  EXPENSES: {
    FIXED_MONTHLY: 5000, // Base monthly expenses
    PER_TON_COLLECTION: 200 // Cost per ton to collect waste
  },

  // Export configuration
  EXPORT_OPTIONS: {
    FORMATS: ['CSV', 'GeoJSON', 'KML'],
    DEFAULT_FORMAT: 'GeoJSON'
  }
};

// Map handling module
var MAP = {
  // Create and configure the main map
  createMap: function() {
    // Create a map centered on Lusaka and surrounding areas
    var map = ui.Map();
    map.setCenter(
      CONFIG.LUSAKA_CENTER[0], 
      CONFIG.LUSAKA_CENTER[1], 
      CONFIG.DEFAULT_ZOOM
    );
    
    // Add base layers
    MAP.addBaseLayers(map);
    
    // Configure map options
    map.setControlVisibility({
      all: true,
      zoomControl: true,
      layerList: true,
      drawingToolsControl: false // We'll handle drawing via our custom UI
    });
    
    return map;
  },

  // Add base layers to the map
  addBaseLayers: function(map) {
    // Add district boundaries
    var districts = ee.FeatureCollection(CONFIG.ADMIN_BOUNDARIES)
      .filter(ee.Filter.eq('ADM0_NAME', 'Zambia'))
      .filterBounds(CONFIG.REGION_BOUNDARY);
    
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
      var worldcover = ee.ImageCollection(CONFIG.WORLDCOVER_DATASET).first();
      
      // Extract urban class (50) - this includes roads and built-up areas
      var urban = worldcover.select('Map').eq(50);
      
      // Create visualization - just show urban areas which include roads
      var urbanLayer = ui.Map.Layer(
        urban.clip(CONFIG.REGION_BOUNDARY), 
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
      var buildings = ee.FeatureCollection(CONFIG.BUILDINGS_DATASET)
        .filterBounds(CONFIG.REGION_BOUNDARY);
      
      var buildingsLayer = ui.Map.Layer(buildings, {color: '#FF0000'}, 'Buildings', false);
      map.add(buildingsLayer);
      print("Buildings loaded successfully");
    } catch(e) {
      print("Error loading buildings:", e);
    }
    
    // Add population density layer (initially hidden)
    print("Loading population data");
    try {
      var population = ee.ImageCollection(CONFIG.POPULATION_DATASET)
        .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
        .first() 
        .clip(CONFIG.REGION_BOUNDARY);
      
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
      var landcover = ee.Image(CONFIG.LAND_COVER)
        .select('discrete_classification')
        .clip(CONFIG.REGION_BOUNDARY);
      
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
  },

  // Helper function to clear all drawn features
  clearDrawings: function(map) {
    map.drawingTools().layers().reset();
  },

  // Helper function to add a zone to the map
  addZoneToMap: function(map, zone, name, color, selected) {
    var zoneLayer = ui.Map.Layer(zone, {color: color}, name);
    map.layers().add(zoneLayer);
    return zoneLayer;
  },

  // Helper function to highlight buildings by class - simplified to avoid encoding errors
  highlightBuildingsByClass: function(map, buildings, isVisible) {
    try {
      print("Building highlighting function called but using the simplified approach");
      
      // Note: We're not using this function anymore - 
      // This is kept as a stub for API compatibility
      // Actual implementation is in ANALYSIS.toggleBuildingsDisplay
      
      // Remove existing building layers
      try {
        map.layers().forEach(function(layer) {
          if (layer.getName().indexOf('Buildings - ') === 0 ||
              layer.getName() === 'Building classification area center') {
            map.layers().remove(layer);
          }
        });
      } catch(e) {
        print("Error removing building layers:", e.message);
      }
      
      // Don't attempt to add new building layers to avoid encoding errors
      if (!isVisible) return;
      
      print("Building classification display is disabled to prevent encoding errors");
      print("Please see console for building class information");
    } catch(error) {
      print("ERROR in highlightBuildingsByClass:", error.message);
    }
  }
};

// Drawing module for creating and managing zones
var DRAWING = {
  // Store state for zones
  zones: {},
  activeZone: null,
  drawingMode: false,
  mapInstance: null,
  mainAppPanel: null,

  // Initialize the drawing module
  initialize: function(map, appPanel) {
    DRAWING.mapInstance = map;
    DRAWING.mainAppPanel = appPanel;
    
    // Set up drawing tools
    DRAWING.setupDrawingTools(map);
    
    // Initialize the zones storage
    DRAWING.initializeZonesStorage();
  },

  // Set up the drawing tools on the map
  setupDrawingTools: function(map) {
    map.drawingTools().setShown(false);
    
    // Set up drawing tools event listeners with error handling
    try {
      map.drawingTools().onDraw(function(geometry) {
        try {
          if (!DRAWING.drawingMode) return;
          
          print('Geometry drawing completed.');
          
          // Store the drawn geometry temporarily
          DRAWING.activeZone = geometry;
          
          // Disable drawing mode after a polygon is completed
          DRAWING.drawingMode = false;
          
          // Show the save panel
          // This could be a signal to the UI to show the save options
          try {
            ui.root.widgets().get(1).widgets().get(1).widgets().get(1).widgets().get(0).widgets().get(5).style().set('border', '1px solid #3182CE');
          } catch(e) {
            print('Non-critical UI error:', e.message);
            // Continue even if UI update fails
          }
          
          print('Zone drawing complete. Ready to save.');
        } catch(e) {
          print('Error in draw callback:', e.message);
        }
      });
      
      print('Drawing tools setup complete.');
    } catch(err) {
      print('Error setting up drawing tools:', err.message);
    }
  },

  // Initialize the zones storage
  initializeZonesStorage: function() {
    // In a real application, you would load saved zones from a database or file
    // For this demo, we'll just initialize an empty object
    DRAWING.zones = {};
  },

  // Start drawing a new zone
  startDrawing: function() {
    // Clear any existing geometry
    DRAWING.mapInstance.drawingTools().layers().reset();
    
    // Enter drawing mode
    DRAWING.drawingMode = true;
    DRAWING.mapInstance.drawingTools().setShape('polygon');
    DRAWING.mapInstance.drawingTools().setLinked(true);
    DRAWING.mapInstance.drawingTools().setDrawModes(['polygon']);
    DRAWING.mapInstance.drawingTools().setShown(true);
    
    // Show the save panel (will be completed when the user finishes drawing)
    ui.root.widgets().get(1).widgets().get(1).widgets().get(1).widgets().get(0).widgets().get(5).style().set('border', '1px solid #dddddd');
  },

  // Clear the current drawing
  clearDrawing: function() {
    DRAWING.mapInstance.drawingTools().layers().reset();
    DRAWING.activeZone = null;
    DRAWING.drawingMode = false;
  },

  // Save the current zone
  saveZone: function(zoneName, parentZoneName) {
    if (!DRAWING.activeZone) {
      // Safe alert approach
      print("ALERT: No zone has been drawn. Please draw a zone first.");
      print("⚠️ ==================================== ⚠️");
      print("⚠️              ALERT                  ⚠️");
      print("⚠️ ==================================== ⚠️");
      return;
    }
    
    // Create a new zone object
    var zone = {
      name: zoneName,
      geometry: DRAWING.activeZone,
      parentZone: parentZoneName || null,
      subZones: [],
      dateCreated: new Date().toISOString(),
      id: 'zone_' + Date.now()
    };
    
    // Add to zones collection
    DRAWING.zones[zoneName] = zone;
    
    // If this is a sub-zone, add it to its parent
    if (parentZoneName && DRAWING.zones[parentZoneName]) {
      DRAWING.zones[parentZoneName].subZones.push(zoneName);
    }
    
    // Add the zone to the map
    var color = parentZoneName ? CONFIG.COLORS.SUB_ZONE : CONFIG.COLORS.MAIN_ZONE;
    DRAWING.addZoneToMap(zone, color);
    
    // Clear the active zone and drawing tools
    DRAWING.mapInstance.drawingTools().layers().reset();
    DRAWING.activeZone = null;
    
    // Safe alert approach
  print("ALERT: Zone \"" + zoneName + "\" has been saved.");
  print("⚠️ ==================================== ⚠️");
  print("⚠️              ALERT                  ⚠️");
  print("⚠️ ==================================== ⚠️");
    
    return zone;
  },

  // Add a zone to the map
  addZoneToMap: function(zone, color) {
    var geoFeature = ee.Feature(zone.geometry, {
      name: zone.name,
      zoneId: zone.id
    });
    
    var zoneLayer = ui.Map.Layer(geoFeature, {color: color}, zone.name);
    DRAWING.mapInstance.layers().add(zoneLayer);
    
    return zoneLayer;
  },

  // Get all zones as a list of names
  getZonesList: function() {
    return Object.keys(DRAWING.zones);
  },

  // Get a specific zone by name
  getZone: function(zoneName) {
    return DRAWING.zones[zoneName] || null;
  },

  // Get all zones
  getAllZones: function() {
    return DRAWING.zones;
  },

  // Highlight a specific zone on the map
  highlightZone: function(zoneName) {
    // First remove any existing highlight
    DRAWING.removeZoneHighlight();
    
    // Then highlight the requested zone
    var zone = DRAWING.zones[zoneName];
    if (!zone) return;
    
    var geoFeature = ee.Feature(zone.geometry, {
      name: zone.name,
      zoneId: zone.id,
      highlighted: true
    });
    
    var highlightLayer = ui.Map.Layer(
      geoFeature, 
      {color: CONFIG.COLORS.SELECTED_ZONE}, 
      zone.name + ' (selected)'
    );
    
    DRAWING.mapInstance.layers().add(highlightLayer);
    
    // Center map on the zone
    DRAWING.mapInstance.centerObject(geoFeature, 15);
  },

  // Remove zone highlight
  removeZoneHighlight: function() {
    DRAWING.mapInstance.layers().forEach(function(layer) {
      if (layer.getName().indexOf('(selected)') !== -1) {
        DRAWING.mapInstance.layers().remove(layer);
      }
    });
  },

  // Rename a zone
  renameZone: function(oldName, newName) {
    if (!DRAWING.zones[oldName]) {
      print('Zone "' + oldName + '" does not exist.');
      safeAlert('Zone "' + oldName + '" does not exist.');
      return;
    }
    
    if (DRAWING.zones[newName]) {
      print('Zone "' + newName + '" already exists. Please choose a different name.');
      safeAlert('Zone "' + newName + '" already exists. Please choose a different name.');
      return;
    }
    
    // Update the zone name
    var zone = DRAWING.zones[oldName];
    zone.name = newName;
    
    // Add to zones collection with new name
    DRAWING.zones[newName] = zone;
    
    // Remove old entry
    delete DRAWING.zones[oldName];
    
    // Update parent references if this is a sub-zone
    Object.keys(DRAWING.zones).forEach(function(zoneName) {
      var parentZone = DRAWING.zones[zoneName];
      var subZones = parentZone.subZones;
      
      for (var i = 0; i < subZones.length; i++) {
        if (subZones[i] === oldName) {
          subZones[i] = newName;
        }
      }
    });
    
    // Update map layer
    DRAWING.mapInstance.layers().forEach(function(layer) {
      if (layer.getName() === oldName) {
        // Remove the old layer
        DRAWING.mapInstance.layers().remove(layer);
        
        // Add a new layer with the updated name
        var color = zone.parentZone ? CONFIG.COLORS.SUB_ZONE : CONFIG.COLORS.MAIN_ZONE;
        DRAWING.addZoneToMap(zone, color);
      }
    });
    
    print('Zone renamed from "' + oldName + '" to "' + newName + '".');
    safeAlert('Zone renamed from "' + oldName + '" to "' + newName + '".');
  },

  // Delete a zone
  deleteZone: function(zoneName) {
    if (!DRAWING.zones[zoneName]) {
      print('Zone "' + zoneName + '" does not exist.');
      safeAlert('Zone "' + zoneName + '" does not exist.');
      return;
    }
    
    // Check if this zone has sub-zones
    var zone = DRAWING.zones[zoneName];
    if (zone.subZones && zone.subZones.length > 0) {
      print('Cannot delete zone "' + zoneName + '" because it has sub-zones. Delete the sub-zones first.');
      safeAlert('Cannot delete zone "' + zoneName + '" because it has sub-zones. Delete the sub-zones first.');
      return;
    }
    
    // Remove from parent's sub-zones list
    if (zone.parentZone && DRAWING.zones[zone.parentZone]) {
      var parentZone = DRAWING.zones[zone.parentZone];
      var subZones = parentZone.subZones;
      var index = subZones.indexOf(zoneName);
      if (index !== -1) {
        subZones.splice(index, 1);
      }
    }
    
    // Remove from map
    DRAWING.mapInstance.layers().forEach(function(layer) {
      if (layer.getName() === zoneName || layer.getName() === zoneName + ' (selected)') {
        DRAWING.mapInstance.layers().remove(layer);
      }
    });
    
    // Remove from zones collection
    delete DRAWING.zones[zoneName];
    
    print('Zone "' + zoneName + '" has been deleted.');
    safeAlert('Zone "' + zoneName + '" has been deleted.');
  },

  // Edit zone geometry
  editZoneGeometry: function(zoneName) {
    if (!DRAWING.zones[zoneName]) {
      print('Zone "' + zoneName + '" does not exist.');
      safeAlert('Zone "' + zoneName + '" does not exist.');
      return;
    }
    
    var zone = DRAWING.zones[zoneName];
    
    // Clear drawing tools
    DRAWING.mapInstance.drawingTools().layers().reset();
    
    // Add the geometry to the drawing tools
    DRAWING.mapInstance.drawingTools().addLayer(ee.FeatureCollection([ee.Feature(zone.geometry)]));
    
    // Activate drawing tools for editing
    DRAWING.mapInstance.drawingTools().setShape('polygon');
    DRAWING.mapInstance.drawingTools().setLinked(true);
    DRAWING.mapInstance.drawingTools().setDrawModes(['polygon']);
    DRAWING.mapInstance.drawingTools().setShown(true);
    
    // Set up listener for edit completion - safer implementation
    try {
      // Use a safer approach without trying to manage the listener explicitly
      // Earth Engine's event model handles this automatically
      DRAWING.mapInstance.drawingTools().onEdit(function(geometry) {
        try {
          print('Geometry edit completed. Updating zone...');
          
          // Update the zone geometry
          zone.geometry = geometry;
          
          // Update the map layer
          DRAWING.mapInstance.layers().forEach(function(layer) {
            if (layer.getName() === zoneName || layer.getName() === zoneName + ' (selected)') {
              DRAWING.mapInstance.layers().remove(layer);
            }
          });
          
          var color = zone.parentZone ? CONFIG.COLORS.SUB_ZONE : CONFIG.COLORS.MAIN_ZONE;
          DRAWING.addZoneToMap(zone, color);
          
          // Clear the drawing tools
          DRAWING.mapInstance.drawingTools().layers().reset();
          DRAWING.mapInstance.drawingTools().setShown(false);
          
          print('Zone "' + zoneName + '" geometry has been updated.');
          safeAlert('Zone "' + zoneName + '" geometry has been updated.');
        } catch(e) {
          print('Error updating zone geometry:', e.message);
          safeAlert('Error updating zone: ' + e.message + '. See console for details.');
        }
      });
      
      print('Edit listener set up successfully for zone: ' + zoneName);
    } catch(err) {
      print('Failed to set up edit listener:', err.message);
      safeAlert('Could not enable geometry editing. Please try again.');
    }
  }
};

// Analysis module for processing zone data
var ANALYSIS = {
  // Analyze a zone and return detailed metrics
  analyzeZone: function(zoneName) {
    return new Promise(function(resolve, reject) {
      try {
        print("Beginning analysis for zone: " + zoneName);
        
        var zone = DRAWING.getZone(zoneName);
        if (!zone) {
          print("ERROR: Zone '" + zoneName + "' not found");
          reject(new Error('Zone "' + zoneName + '" not found.'));
          return;
        }
        
        print("Processing zone geometry...");
        
        // Create an Earth Engine geometry from the zone
        var zoneGeometry = zone.geometry;
        var zoneFeature = ee.Feature(zoneGeometry, { 'name': zoneName });
        
        // Calculate zone area in square kilometers
        var area = zoneFeature.geometry().area().divide(1000000); // Convert to sq km
        
        print("Analyzing buildings...");
        // Get buildings within the zone
        var buildingsAnalysis = ANALYSIS.analyzeBuildings(zoneFeature);
        
        print("Analyzing population data...");
        // Get population within the zone
        var populationAnalysis = ANALYSIS.analyzePopulation(zoneFeature, area);
        
        print("Calculating waste generation...");
        // Calculate waste generation
        var wasteAnalysis = ANALYSIS.calculateWasteGeneration(buildingsAnalysis, populationAnalysis);
        
        print("Performing financial analysis...");
        // Financial analysis
        var financialAnalysis = ANALYSIS.calculateFinancials(buildingsAnalysis, wasteAnalysis);
        
        // Combine all results
        var results = {
          zoneName: zoneName,
          parentZone: zone.parentZone,
          area: area.getInfo(),
          buildings: buildingsAnalysis,
          population: populationAnalysis,
          waste: wasteAnalysis,
          financial: financialAnalysis
        };
        
        print("Analysis complete for zone: " + zoneName);
        resolve(results);
      } catch (error) {
        print("ERROR in analysis: " + error.message);
        print("Stack trace: " + error.stack);
        reject(error);
      }
    });
  },

  // Analyze buildings within a zone
  analyzeBuildings: function(zoneFeature) {
    try {
      print("Getting buildings dataset...");
      
      // First check the building dataset source to understand what kind of data we're working with
      print("Building dataset source:", CONFIG.BUILDINGS_DATASET);
      
      // Get buildings dataset - first just get a sample to examine what we're dealing with
      var sampleBuildings = ee.FeatureCollection(CONFIG.BUILDINGS_DATASET)
        .filterBounds(zoneFeature.geometry())
        .limit(5);
      
      // Try to print sample buildings to examine their properties
      try {
        print("Sample building properties:", sampleBuildings.first().toDictionary().getInfo());
      } catch(e) {
        print("Could not examine building properties:", e.message);
      }
      
      // Use Google's Open Buildings confidence score for more accurate building detection
      print("Using Google Open Buildings dataset with confidence score filtering");
      print("Minimum confidence score:", CONFIG.BUILDING_ANALYSIS.MIN_CONFIDENCE_SCORE);
      
      // First get all buildings in the bounding box of the zone for analysis
      var allNearbyBuildings = ee.FeatureCollection(CONFIG.BUILDINGS_DATASET)
        .filterBounds(zoneFeature.geometry());
      
      // Get the total count first to understand data volume
      try {
        var nearbyCount = allNearbyBuildings.size().getInfo();
        print("All buildings near zone:", nearbyCount);
      } catch(e) {
        print("Could not count nearby buildings:", e.message);
      }
      
      // Examine properties including confidence score if available
      try {
        var sampleBuilding = allNearbyBuildings.first();
        var properties = sampleBuilding.toDictionary().getInfo();
        print("Sample building properties:", properties);
        
        // Check if confidence property exists and report
        var confidenceProp = 'confidence' in properties ? 'confidence' : 
                          'confidence_score' in properties ? 'confidence_score' : 
                          'score' in properties ? 'score' : null;
                          
        if (confidenceProp) {
          print("Using confidence property:", confidenceProp);
        } else {
          print("WARNING: No confidence property found. Using size-based filtering only.");
          // Add properties about confidence score attempts
          for (var key in properties) {
            if (key.toLowerCase().includes('conf')) {
              print("Potential confidence-related property:", key);
            }
          }
        }
      } catch(e) {
        print("Could not examine building properties:", e.message);
      }
      
      // Apply more intelligent filtering based on what properties are available
      var buildings = allNearbyBuildings
        .map(function(feature) {
          // Calculate area
          var area = feature.geometry().area();
          var adjustedArea = area.multiply(CONFIG.BUILDING_ANALYSIS.AREA_ADJUSTMENT_FACTOR);
          
          // Use centroid to determine if building is inside the zone
          var centroid = feature.geometry().centroid();
          var insideZone = centroid.containedIn(zoneFeature.geometry());
          
          // Check basic size thresholds (very permissive now)
          var meetsMinSize = adjustedArea.gte(CONFIG.BUILDING_ANALYSIS.MIN_BUILDING_SIZE);
          var meetsMaxSize = adjustedArea.lte(CONFIG.BUILDING_ANALYSIS.MAX_BUILDING_SIZE);
          
          // Check confidence score if the property exists
          // Google Open Buildings v3 uses 'confidence' property
          // This handles different versions of the dataset with different property names
          var confidenceScore = ee.Algorithms.If(
            feature.propertyNames().contains('confidence'),
            feature.get('confidence'),
            ee.Algorithms.If(
              feature.propertyNames().contains('confidence_score'),
              feature.get('confidence_score'),
              ee.Algorithms.If(
                feature.propertyNames().contains('score'),
                feature.get('score'),
                1.0  // Default to 1.0 if no confidence score is found
              )
            )
          );
          
          var meetsConfidence = ee.Number(confidenceScore).gte(CONFIG.BUILDING_ANALYSIS.MIN_CONFIDENCE_SCORE);
          
          // Add all filters as properties
          return feature
            .set('area', adjustedArea)
            .set('insideZone', insideZone)
            .set('meetsMinSize', meetsMinSize)
            .set('meetsMaxSize', meetsMaxSize)
            .set('confidenceScore', confidenceScore)
            .set('meetsConfidence', meetsConfidence);
        });
        
      // Count buildings that meet each criterion separately
      try {
        var insideCount = buildings.filter(ee.Filter.eq('insideZone', true)).size().getInfo();
        var confFilteredCount = buildings
          .filter(ee.Filter.and(
            ee.Filter.eq('insideZone', true),
            ee.Filter.eq('meetsConfidence', true)
          )).size().getInfo();
        
        print("Buildings inside zone boundary:", insideCount);
        print("Buildings meeting confidence threshold:", confFilteredCount);
      } catch(e) {
        print("Error counting filtered buildings:", e.message);
      }
      
      // Now apply all filters for the final dataset
      buildings = buildings
        .filter(ee.Filter.and(
          ee.Filter.eq('insideZone', true),
          ee.Filter.eq('meetsMinSize', true),
          ee.Filter.eq('meetsMaxSize', true),
          ee.Filter.eq('meetsConfidence', true)
        ));
        
      print("Minimum building size threshold:", CONFIG.BUILDING_ANALYSIS.MIN_BUILDING_SIZE, "sq meters");
      
      // Report on filtering impact - now using confidence scores and size together
      try {
        // Get count of buildings by different filter combinations
        var totalInsideZone = buildings
          .filter(ee.Filter.eq('insideZone', true))
          .size().getInfo();
          
        var confidenceFiltered = buildings
          .filter(ee.Filter.and(
            ee.Filter.eq('insideZone', true),
            ee.Filter.eq('meetsConfidence', false)
          ))
          .size().getInfo();
          
        var sizeFiltered = buildings
          .filter(ee.Filter.and(
            ee.Filter.eq('insideZone', true),
            ee.Filter.or(
              ee.Filter.eq('meetsMinSize', false),
              ee.Filter.eq('meetsMaxSize', false)
            )
          ))
          .size().getInfo();
          
        print("Buildings filtered by confidence score:", confidenceFiltered);
        print("Buildings filtered by size thresholds:", sizeFiltered);
        
        // Calculate what percentage of buildings are filtered by each criterion
        if (totalInsideZone > 0) {
          var confidencePercent = (confidenceFiltered / totalInsideZone * 100).toFixed(1);
          var sizePercent = (sizeFiltered / totalInsideZone * 100).toFixed(1);
          
          print("Confidence score filtered out: " + confidencePercent + "% of buildings");
          print("Size thresholds filtered out: " + sizePercent + "% of buildings");
        }
      } catch(e) {
        print("Could not calculate filter statistics:", e.message);
      }
      
      print("Counting total buildings (after all filters)...");
      // Get total number of buildings - with better error handling
      var totalBuildings = 0;
      try {
        // Get raw building count (already filtered by size)
        var rawBuildingCount = buildings.size().getInfo();
        
        // Apply adjustment factor to avoid potential double-counting
        totalBuildings = Math.round(rawBuildingCount * CONFIG.BUILDING_ANALYSIS.COUNT_ADJUSTMENT_FACTOR);
        
        print("Raw building count (after filters): " + rawBuildingCount);
        print("Adjusted building count: " + totalBuildings + 
             " (using " + (CONFIG.BUILDING_ANALYSIS.COUNT_ADJUSTMENT_FACTOR * 100) + "% adjustment factor)");
        
        // Report on filtered buildings
        try {
          if (typeof preFilterCount !== 'undefined') {
            var filteredOutCount = preFilterCount - rawBuildingCount;
            var percentageFiltered = (filteredOutCount / preFilterCount * 100).toFixed(1);
            print("Buildings filtered out by size thresholds:", filteredOutCount, 
                 "(" + percentageFiltered + "% of total)");
            
            // More detailed guidance based on filter percentage
            if (percentageFiltered > 70) {
              print("WARNING: Over 70% of buildings were filtered out. Size threshold is likely too high.");
              print("Consider reducing MIN_BUILDING_SIZE in CONFIG.BUILDING_ANALYSIS.");
            } else if (percentageFiltered > 50) {
              print("NOTE: 50-70% of buildings filtered out. This may be appropriate in some areas,");
              print("but you may want to check if the threshold is filtering legitimate buildings.");
            } else if (percentageFiltered < 5 && totalBuildings > 0) {
              print("NOTE: Less than 5% of buildings were filtered out. Size threshold might need to");
              print("be increased if you're still seeing small structures counted as buildings.");
            } else if (totalBuildings === 0) {
              print("WARNING: No buildings detected after filtering. Your filters may be too strict.");
              print("Try reducing MIN_BUILDING_SIZE in CONFIG.BUILDING_ANALYSIS or check if the zone");
              print("actually contains buildings.");
            } else {
              print("Filter settings appear reasonable - " + percentageFiltered + "% of buildings filtered out.");
            }
          }
        } catch(e) {
          print("Error calculating filter statistics:", e.message);
        }
        
        // Warn if building count seems exceptionally high for the area
        var areaInSqKm = 0;
        try {
          areaInSqKm = zoneFeature.geometry().area().divide(1000000).getInfo();
          var buildingDensity = totalBuildings / areaInSqKm;
          print("Zone area: " + areaInSqKm.toFixed(2) + " sq km, Building density: " + 
                buildingDensity.toFixed(0) + " buildings/sq km");
          
          if (buildingDensity > 3000) {
            print("WARNING: Building density exceeds 3000 buildings/sq km, which is unusually high.");
            print("Consider manual verification of building counts in this zone.");
          }
        } catch(e) {
          print("Error calculating building density:", e.message);
        }
      } catch(e) {
        print("Error counting buildings:", e.message);
        print("Using default value of 0 for total buildings");
      }
      
      // Analyze buildings by type based on area
      var buildingsByType = {};
      
      // Initialize all building types with zero to avoid missing keys
      Object.keys(CONFIG.BUILDING_CLASSES).forEach(function(classKey) {
        buildingsByType[classKey] = 0;
      });
      
      // Using safer approach to filter buildings
      print("Classifying buildings by type...");
      
      // Using a simplified, more robust approach
      try {
        // For each building class
        Object.keys(CONFIG.BUILDING_CLASSES).forEach(function(classKey) {
          try {
            var classInfo = CONFIG.BUILDING_CLASSES[classKey];
            print("Processing building class: " + classKey);
            
            // Create filter expressions based on area
            var areaFilter;
            if (classInfo.min && classInfo.max) {
              areaFilter = ee.Filter.and(
                ee.Filter.gte('area', classInfo.min),
                ee.Filter.lt('area', classInfo.max)
              );
            } else if (classInfo.min) {
              areaFilter = ee.Filter.gte('area', classInfo.min);
            } else if (classInfo.max) {
              areaFilter = ee.Filter.lt('area', classInfo.max);
            } else {
              areaFilter = ee.Filter.eq('dummy', 'dummy'); // Should never happen
            }
            
            // Try an alternative approach using calculated areas
            // First, let's check the area distribution for better understanding
            if (classKey === 'RESIDENTIAL_PERI_URBAN') {
              try {
                // Sample a few buildings to check areas
                var sampleBuildings = buildings.limit(5);
                print("Sample building areas (in sq meters):");
                var sampleAreas = sampleBuildings.map(function(feature) {
                  return feature.geometry().area();
                }).getInfo();
                print("Sample areas:", sampleAreas);
              } catch(e) {
                print("Error sampling building areas:", e.message);
              }
            }
            
            // The buildings collection already has the adjusted area calculated,
            // so we don't need to recalculate it here
            var areaBuildings = buildings; // Area is already set with 'area' property
            
            // Apply appropriate filtering with additional validation
            var filteredBuildings = areaBuildings.filter(areaFilter);
            var count = filteredBuildings.size().getInfo();
            buildingsByType[classKey] = count;
            
            // Report results with better detail
            print("Found " + count + " buildings of type: " + classKey + 
                 " (" + (count / totalBuildings * 100).toFixed(1) + "% of total)");
              
            // If this class dominates, provide a warning for verification
            if (count > totalBuildings * 0.7) {
              print("WARNING: " + classKey + " buildings account for over 70% of all buildings.");
              print("This may indicate an issue with area calculations or thresholds.");
            }
          } catch(e) {
            print("Error counting buildings for class " + classKey + ":", e.message);
            // Keep the default 0 value
          }
        });
      } catch(e) {
        print("Error in building classification:", e.message);
      }
      
      print("Building analysis complete");
      return {
        total: totalBuildings,
        byType: buildingsByType
      };
    } catch (error) {
      print("FATAL ERROR in analyzeBuildings:", error.message);
      // Return default values
      var defaultBuildingsByType = {};
      Object.keys(CONFIG.BUILDING_CLASSES).forEach(function(classKey) {
        defaultBuildingsByType[classKey] = 0;
      });
      
      return {
        total: 0,
        byType: defaultBuildingsByType
      };
    }
  },

  // Analyze population within a zone
  analyzePopulation: function(zoneFeature, area) {
    try {
      print("Loading population dataset...");
      
      // For WorldPop dataset, print available collections
      try {
        var collections = ee.data.getList({id: CONFIG.POPULATION_DATASET.split('/').slice(0, -1).join('/')});
        print("Available WorldPop collections:", collections);
      } catch(e) {
        print("Could not list WorldPop collections:", e.message);
      }
      
      // Modified approach for WorldPop dataset
      // First try latest year available (2020)
      var populationImage = null;
      
      // Skip dataset loading attempt - go directly to estimation
      print("Using area-based population estimation directly");
      populationImage = null;
      
      /* 
      // We're skipping these attempts since they've been failing
      // If you want to try dataset loading in the future, uncomment this code
      
      try {
        print("Trying CIESIN/GPWv411/GPW_Population_Density format...");
        populationImage = ee.Image('CIESIN/GPWv411/GPW_Population_Density/2020');
        print("Found CIESIN GPW global population density dataset for 2020");
      } catch(e1) {
        print("CIESIN dataset not found:", e1.message);
        
        try {
          print("Trying JRC/GHSL/P2016/POP_GPW_GLOBE_V1 format...");
          populationImage = ee.Image('JRC/GHSL/P2016/POP_GPW_GLOBE_V1');
          print("Found JRC GHSL global population dataset");
        } catch(e2) {
          print("JRC GHSL dataset not found:", e2.message);
          
          try {
            print("Trying WorldPop collection as image...");
            // This gets the most recent image from the collection
            var worldPopCollection = ee.ImageCollection('WorldPop/GP/100m/pop');
            if (worldPopCollection.size().getInfo() > 0) {
              populationImage = worldPopCollection.first();
              print("Found WorldPop image from collection");
            } else {
              throw new Error("WorldPop collection is empty");
            }
          } catch(e3) {
            print("All dataset attempts failed. Using area-based estimation only.");
            populationImage = null;
          }
        }
      }
      */
      
      // Handle both cases: when we have a population image or need to use fallback
      var totalPopulation = 0;
      
      if (populationImage !== null) {
        try {
          print("Population image acquired. Examining bands...");
          var bandNames = populationImage.bandNames().getInfo();
          print("Available bands:", bandNames);
          
          // Determine which band to use
          var populationBand = null;
          
          // Common band names in different population datasets
          if (bandNames.includes('population')) {
            populationBand = 'population';
          } else if (bandNames.includes('Population')) {
            populationBand = 'Population';
          } else if (bandNames.includes('pop')) {
            populationBand = 'pop';
          } else if (bandNames.includes('population_count')) {
            populationBand = 'population_count';  // CIESIN dataset
          } else if (bandNames.includes('b1')) {
            populationBand = 'b1';  // Some WorldPop datasets
          } else if (bandNames.length > 0) {
            // Use the first available band as fallback
            populationBand = bandNames[0];
            print("Using first available band:", populationBand);
          } else {
            throw new Error("No bands found in population data");
          }
          
          print("Using population band:", populationBand);
          
          print("Calculating population statistics...");
          var populationStats = populationImage.select(populationBand).reduceRegion({
            reducer: ee.Reducer.sum(),
            geometry: zoneFeature.geometry(),
            scale: 100, 
            maxPixels: 1e12  // Increased max pixels further
          });
          
          // Get the population total
          var statsInfo = populationStats.getInfo();
          print("Population stats result:", statsInfo);
          
          if (statsInfo && statsInfo[populationBand] !== undefined) {
            totalPopulation = statsInfo[populationBand];
            print("Successfully calculated population:", totalPopulation);
          } else {
            throw new Error("Population calculation returned no value");
          }
        } catch(e) {
          print("Error in population calculation:", e.message);
          print("Falling back to area-based estimation");
          // Will use area-based fallback below
          totalPopulation = 0;
        }
      }
      
      // Since we're going straight to area-based estimation, simplify this section
      print("Calculating population based on area and average density");
      
      // Get area in square kilometers
      var areaInSqKm = 1; // Default to 1 sq km if area calculation fails
      try {
        areaInSqKm = area.getInfo() || 1;
        print("Zone area:", areaInSqKm, "sq km");
      } catch(e) {
        print("Error getting area:", e.message);
      }
      
      // Set Lusaka average population density
      var populationDensity = 4800; // people per sq km (average for Lusaka)
      
      // Calculate population
      totalPopulation = areaInSqKm * populationDensity;
      print("Area-based population estimate:", totalPopulation, 
            "(based on density of", populationDensity, "people per sq km)");
      
      // Adjust for very large areas (over 10 sq km) to account for non-residential areas
      if (areaInSqKm > 10) {
        // For large areas, reduce density by 20% to account for parks, roads, etc.
        totalPopulation = areaInSqKm * (populationDensity * 0.8);
        print("Large area adjustment applied. Adjusted population:", totalPopulation);
      }
      
      var areaValue = 1; // Default to avoid division by zero
      try {
        areaValue = area.getInfo() || 1;
      } catch(e) {
        print("Error getting area value:", e.message);
      }
      
      // Calculate population density (people per sq km)
      var density = totalPopulation / areaValue;
      
      print("Population analysis complete. Total:", totalPopulation, "Density:", density);
      return {
        total: totalPopulation,
        density: density
      };
    } catch(error) {
      print("FATAL ERROR in analyzePopulation:", error.message);
      print("Stack trace:", error.stack);
      return {
        total: 0,
        density: 0
      };
    }
  },

  // Calculate waste generation based on buildings and population
  calculateWasteGeneration: function(buildings, population) {
    try {
      print("Calculating waste generation...");
      // Default values to prevent NaN/undefined issues
      var popTotal = 0;
      var buildingCounts = {
        COMMERCIAL_SMALL: 0,
        COMMERCIAL_MEDIUM: 0,
        COMMERCIAL_LARGE: 0
      };
      
      // Safely get population data
      if (population && typeof population.total === 'number') {
        popTotal = population.total;
      } else {
        print("Warning: Invalid population data, using default 0");
      }
      
      // Safely get building counts
      if (buildings && buildings.byType) {
        if (typeof buildings.byType.COMMERCIAL_SMALL === 'number') {
          buildingCounts.COMMERCIAL_SMALL = buildings.byType.COMMERCIAL_SMALL;
        }
        if (typeof buildings.byType.COMMERCIAL_MEDIUM === 'number') {
          buildingCounts.COMMERCIAL_MEDIUM = buildings.byType.COMMERCIAL_MEDIUM;
        }
        if (typeof buildings.byType.COMMERCIAL_LARGE === 'number') {
          buildingCounts.COMMERCIAL_LARGE = buildings.byType.COMMERCIAL_LARGE;
        }
      } else {
        print("Warning: Invalid building data, using defaults");
      }
      
      // Calculate daily waste generation in kg
      
      // Residential waste based on population
      var residentialWaste = popTotal * CONFIG.WASTE_GENERATION.RESIDENTIAL_PER_PERSON;
      
      // Commercial waste based on building counts
      var commercialSmallWaste = buildingCounts.COMMERCIAL_SMALL * CONFIG.WASTE_GENERATION.COMMERCIAL_SMALL;
      var commercialMediumWaste = buildingCounts.COMMERCIAL_MEDIUM * CONFIG.WASTE_GENERATION.COMMERCIAL_MEDIUM;
      var commercialLargeWaste = buildingCounts.COMMERCIAL_LARGE * CONFIG.WASTE_GENERATION.COMMERCIAL_LARGE;
      
      // Total daily waste in kg
      var dailyWaste = residentialWaste + commercialSmallWaste + commercialMediumWaste + commercialLargeWaste;
      
      // Calculate monthly waste (30 days) in kg
      var monthlyWaste = dailyWaste * 30;
      
      print("Waste calculation complete. Daily:", dailyWaste, "kg, Monthly:", monthlyWaste, "kg");
      return {
        daily: dailyWaste,
        monthly: monthlyWaste,
        residential: residentialWaste,
        commercial: commercialSmallWaste + commercialMediumWaste + commercialLargeWaste
      };
    } catch(error) {
      print("ERROR in waste calculation:", error.message);
      return {
        daily: 0,
        monthly: 0,
        residential: 0,
        commercial: 0
      };
    }
  },

  // Calculate financial metrics based on building counts and waste generation
  calculateFinancials: function(buildings, waste) {
    try {
      print("Calculating financial metrics...");
      // Calculate monthly revenue based on building counts and pricing tiers
      var revenueByType = {};
      var totalRevenue = 0;
      
      // Default building counts to prevent NaN issues
      var buildingCounts = {
        RESIDENTIAL_PERI_URBAN: 0,
        RESIDENTIAL_URBAN: 0,
        COMMERCIAL_SMALL: 0,
        COMMERCIAL_MEDIUM: 0,
        COMMERCIAL_LARGE: 0
      };
      
      // Safely get building counts
      if (buildings && buildings.byType) {
        Object.keys(buildingCounts).forEach(function(type) {
          if (typeof buildings.byType[type] === 'number') {
            buildingCounts[type] = buildings.byType[type];
          } else {
            print("Warning: Invalid building count for " + type + ", using default 0");
          }
        });
      } else {
        print("Warning: Invalid building data, using defaults for financial calculations");
      }
      
      // Default waste to prevent NaN issues
      var wasteData = {
        monthly: 0
      };
      
      // Safely get waste data
      if (waste && typeof waste.monthly === 'number') {
        wasteData.monthly = waste.monthly;
      } else {
        print("Warning: Invalid waste data, using default 0 for financial calculations");
      }
      
      // Residential revenue
      revenueByType.RESIDENTIAL_PERI_URBAN = buildingCounts.RESIDENTIAL_PERI_URBAN * CONFIG.PRICING.RESIDENTIAL_PERI_URBAN;
      revenueByType.RESIDENTIAL_URBAN = buildingCounts.RESIDENTIAL_URBAN * CONFIG.PRICING.RESIDENTIAL_URBAN;
      
      // Commercial revenue
      revenueByType.COMMERCIAL_SMALL = buildingCounts.COMMERCIAL_SMALL * CONFIG.PRICING.COMMERCIAL_SMALL;
      revenueByType.COMMERCIAL_MEDIUM = buildingCounts.COMMERCIAL_MEDIUM * CONFIG.PRICING.COMMERCIAL_MEDIUM;
      revenueByType.COMMERCIAL_LARGE = buildingCounts.COMMERCIAL_LARGE * CONFIG.PRICING.COMMERCIAL_LARGE;
      
      // Total revenue
      Object.keys(revenueByType).forEach(function(type) {
        totalRevenue += revenueByType[type];
      });
      
      // Calculate expenses
      var disposalCost = (wasteData.monthly / 1000) * CONFIG.WASTE_GENERATION.DISPOSAL_COST; // Convert kg to tons
      var collectionCost = (wasteData.monthly / 1000) * CONFIG.EXPENSES.PER_TON_COLLECTION; // Cost per ton
      var fixedExpenses = CONFIG.EXPENSES.FIXED_MONTHLY;
      
      var totalExpenses = fixedExpenses + collectionCost + disposalCost;
      
      // Calculate profit/loss
      var profit = totalRevenue - totalExpenses;
      
      print("Financial calculation complete. Revenue:", totalRevenue, "Expenses:", totalExpenses, "Profit:", profit);
      return {
        revenue: {
          byType: revenueByType,
          total: totalRevenue
        },
        expenses: {
          fixed: fixedExpenses,
          collection: collectionCost,
          disposal: disposalCost,
          total: totalExpenses
        },
        profit: profit
      };
    } catch(error) {
      print("ERROR in financial calculation:", error.message);
      // Return sensible defaults
      return {
        revenue: {
          byType: {
            RESIDENTIAL_PERI_URBAN: 0,
            RESIDENTIAL_URBAN: 0,
            COMMERCIAL_SMALL: 0,
            COMMERCIAL_MEDIUM: 0,
            COMMERCIAL_LARGE: 0
          },
          total: 0
        },
        expenses: {
          fixed: CONFIG.EXPENSES.FIXED_MONTHLY,
          collection: 0,
          disposal: 0,
          total: CONFIG.EXPENSES.FIXED_MONTHLY
        },
        profit: -CONFIG.EXPENSES.FIXED_MONTHLY
      };
    }
  },

  // Toggle display of buildings classified by confidence score
  toggleBuildingsDisplay: function(zoneName, show) {
    try {
      print("Toggling building visualization by confidence score:", show ? "show" : "hide");
      
      var zone = DRAWING.getZone(zoneName);
      if (!zone) {
        print("Zone not found:", zoneName);
        return;
      }
      
      // Get the map instance directly rather than through a complex path
      var mapInstance = ui.root.widgets().get(0);
      
      if (show) {
        // Show buildings colored by confidence score
        try {
          print("Adding building visualization layers - classified by confidence score");
          
          // Get buildings within the zone's bounding box
          var zoneBuildings = ee.FeatureCollection(CONFIG.BUILDINGS_DATASET)
            .filterBounds(zone.geometry);
          
          // Create layers for different confidence score ranges
          var lowConfidenceBuildings = zoneBuildings.filter('confidence >= 0.6 && confidence < 0.7');
          var mediumConfidenceBuildings = zoneBuildings.filter('confidence >= 0.7 && confidence < 0.8');
          var highConfidenceBuildings = zoneBuildings.filter('confidence >= 0.8');
          
          // Add building layers to map
          var lowConfidenceLayer = ui.Map.Layer(
            lowConfidenceBuildings, 
            {color: '#FF0000'}, // Red
            'Buildings with low confidence (0.6-0.7)'
          );
          
          var mediumConfidenceLayer = ui.Map.Layer(
            mediumConfidenceBuildings, 
            {color: '#FFAA00'}, // Orange
            'Buildings with medium confidence (0.7-0.8)'
          );
          
          var highConfidenceLayer = ui.Map.Layer(
            highConfidenceBuildings, 
            {color: '#00AA00'}, // Green
            'Buildings with high confidence (0.8+)'
          );
          
          // Add layers to map in order (low confidence first, then higher confidence on top)
          mapInstance.layers().add(lowConfidenceLayer);
          mapInstance.layers().add(mediumConfidenceLayer);
          mapInstance.layers().add(highConfidenceLayer);
          
          // Add zone boundary for context
          var zoneLayer = ui.Map.Layer(
            ee.Feature(zone.geometry), 
            {color: '#3366FF', fillColor: '#00000000'}, // Blue outline, transparent fill
            'Zone boundary'
          );
          mapInstance.layers().add(zoneLayer);
          
          // Center map on zone
          mapInstance.centerObject(ee.Feature(zone.geometry), 15);
          
          print("Building confidence visualization added to map");
          print("Building colors by confidence score:");
          print("- Red: Low confidence (0.6-0.7)");
          print("- Orange: Medium confidence (0.7-0.8)");
          print("- Green: High confidence (0.8+)");
          print("Note: Only buildings with confidence ≥ 0.75 are used in analysis calculations");
        } catch(e) {
          print("Error showing building visualization:", e.message);
          
          // Fallback to simple marker if visualization fails
          try {
            var centerPoint = ee.Geometry.Point(zone.geometry.centroid().coordinates());
            var messageLayer = ui.Map.Layer(
              centerPoint, 
              {color: '#FF0000'}, 
              'Zone center'
            );
            mapInstance.layers().add(messageLayer);
            print("Added zone center marker (visualization failed)");
          } catch(e2) {
            print("Even fallback visualization failed:", e2.message);
          }
        }
      } else {
        // Hide all building and zone layers
        try {
          mapInstance.layers().forEach(function(layer) {
            var layerName = layer.getName();
            if (layerName.indexOf('Buildings with') !== -1 || 
                layerName === 'Zone boundary' ||
                layerName === 'Zone center') {
              mapInstance.layers().remove(layer);
            }
          });
          print("Removed building visualization layers");
        } catch(e) {
          print("Error hiding building layers:", e.message);
        }
      }
    } catch(error) {
      print("ERROR in toggleBuildingsDisplay:", error.message);
    }
  }
};

// Export module for exporting zone data
var EXPORT = {
  // Export data for a specific zone
  exportZoneData: function(zoneName, format) {
    var zone = DRAWING.getZone(zoneName);
    if (!zone) {
      print('Zone "' + zoneName + '" not found.');
      safeAlert('Zone "' + zoneName + '" not found.');
      return;
    }
    
    // Show loading message in console
    print('Preparing export for zone "' + zoneName + '"...');
    
    // Analyze the zone to get all metrics
    ANALYSIS.analyzeZone(zoneName)
      .then(function(results) {
        // Create a feature with zone geometry and all analysis results as properties
        var properties = {
          zone_name: results.zoneName,
          parent_zone: results.parentZone || 'None',
          area_sq_km: results.area,
          total_buildings: results.buildings.total,
          residential_peri_urban: results.buildings.byType.RESIDENTIAL_PERI_URBAN,
          residential_urban: results.buildings.byType.RESIDENTIAL_URBAN,
          commercial_small: results.buildings.byType.COMMERCIAL_SMALL,
          commercial_medium: results.buildings.byType.COMMERCIAL_MEDIUM,
          commercial_large: results.buildings.byType.COMMERCIAL_LARGE,
          estimated_population: results.population.total,
          population_density: results.population.density,
          daily_waste_kg: results.waste.daily,
          monthly_waste_kg: results.waste.monthly,
          monthly_waste_tons: results.waste.monthly / 1000,
          monthly_revenue: results.financial.revenue.total,
          monthly_expenses: results.financial.expenses.total,
          monthly_profit: results.financial.profit,
          export_date: new Date().toISOString()
        };
        
        var zoneFeature = ee.Feature(zone.geometry, properties);
        var featureCollection = ee.FeatureCollection([zoneFeature]);
        
        // Create export task based on format
        var exportTask;
        var description = 'Zone_' + zoneName.replace(/\s+/g, '_') + '_' + 
                         new Date().toISOString().substring(0, 10);
        
        if (format === 'CSV') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'CSV'
          });
        } else if (format === 'GeoJSON') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'GeoJSON'
          });
        } else if (format === 'KML') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'KML'
          });
        }
        
        // Start the export task
        exportTask.start();
        
        // Show success message with instructions to check Tasks tab
        var successMsg = 'Export started for zone "' + zoneName + '".\n' +
                        'Check the Tasks tab in Google Earth Engine to download your file. ' +
                        'The export may take a few minutes to complete.';
        print(successMsg);
        safeAlert(successMsg);
      })
      .catch(function(error) {
        // Show error in console and with alert
        var errorMsg = 'Error exporting zone: ' + error.message;
        print(errorMsg);
        safeAlert(errorMsg);
      });
  },

  // Export data for all zones
  exportAllZones: function(format) {
    var allZones = DRAWING.getAllZones();
    var zoneNames = Object.keys(allZones);
    
    if (zoneNames.length === 0) {
      print('No zones to export.');
      safeAlert('No zones to export.');
      return;
    }
    
    // Show loading message in console
    print('Preparing export for all zones...');
    
    // Create promises for all zone analyses
    var analysisPromises = zoneNames.map(function(zoneName) {
      return ANALYSIS.analyzeZone(zoneName);
    });
    
    // Wait for all analyses to complete
    Promise.all(analysisPromises)
      .then(function(resultsArray) {
        // Create features for each zone with analysis results
        var features = resultsArray.map(function(results) {
          var zone = DRAWING.getZone(results.zoneName);
          
          var properties = {
            zone_name: results.zoneName,
            parent_zone: results.parentZone || 'None',
            area_sq_km: results.area,
            total_buildings: results.buildings.total,
            residential_peri_urban: results.buildings.byType.RESIDENTIAL_PERI_URBAN,
            residential_urban: results.buildings.byType.RESIDENTIAL_URBAN,
            commercial_small: results.buildings.byType.COMMERCIAL_SMALL,
            commercial_medium: results.buildings.byType.COMMERCIAL_MEDIUM,
            commercial_large: results.buildings.byType.COMMERCIAL_LARGE,
            estimated_population: results.population.total,
            population_density: results.population.density,
            daily_waste_kg: results.waste.daily,
            monthly_waste_kg: results.waste.monthly,
            monthly_waste_tons: results.waste.monthly / 1000,
            monthly_revenue: results.financial.revenue.total,
            monthly_expenses: results.financial.expenses.total,
            monthly_profit: results.financial.profit,
            export_date: new Date().toISOString()
          };
          
          return ee.Feature(zone.geometry, properties);
        });
        
        var featureCollection = ee.FeatureCollection(features);
        
        // Create export task based on format
        var exportTask;
        var description = 'All_Zones_' + new Date().toISOString().substring(0, 10);
        
        if (format === 'CSV') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'CSV'
          });
        } else if (format === 'GeoJSON') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'GeoJSON'
          });
        } else if (format === 'KML') {
          exportTask = ee.batch.Export.table.toDrive({
            collection: featureCollection,
            description: description,
            fileFormat: 'KML'
          });
        }
        
        // Start the export task
        exportTask.start();
        
        // Show success message with instructions to check Tasks tab
        var successMsg = 'Export started for all zones.\n' +
                        'Check the Tasks tab in Google Earth Engine to download your file. ' +
                        'The export may take a few minutes to complete.';
        print(successMsg);
        safeAlert(successMsg);
      })
      .catch(function(error) {
        // Show error in console and with alert
        var errorMsg = 'Error exporting zones: ' + error.message;
        print(errorMsg);
        safeAlert(errorMsg);
      });
  }
};

// UI components module
var UI = {
  // Create the main application panel
  createMainPanel: function() {
    var panel = ui.Panel({
      style: {
        width: CONFIG.PANEL_WIDTH,
        padding: '8px'
      }
    });
    
    // Add title
    var title = ui.Label({
      value: 'Lusaka Integrated Waste Management Zone Planner',
      style: {
        fontSize: '18px',
        fontWeight: 'bold',
        margin: '10px 0'
      }
    });
    panel.add(title);
    
    // Create tabs for different sections
    var tabs = UI.createTabPanel(panel);
    panel.add(tabs);
    
    return panel;
  },

  // Create the tabbed interface
  createTabPanel: function(mainPanel) {
    var tabPanel = ui.Panel();
    
    // Tab buttons panel
    var buttonPanel = ui.Panel({
      layout: ui.Panel.Layout.flow('horizontal'),
      style: {margin: '0 0 10px 0'}
    });
    
    // Content panel (where tab contents will be displayed)
    var contentPanel = ui.Panel({
      style: {
        margin: '0px',
        padding: '0px'
      }
    });
    
    // Add the tab buttons and content panel to the tab panel
    tabPanel.add(buttonPanel);
    tabPanel.add(contentPanel);
    
    // Define tabs
    var tabs = {
      welcome: {
        label: 'Welcome',
        panel: UI.createWelcomePanel()
      },
      draw: {
        label: 'Draw Zone',
        panel: UI.createDrawingPanel()
      },
      analyze: {
        label: 'Analysis',
        panel: UI.createAnalysisPanel()
      },
      edit: {
        label: 'Edit Zones',
        panel: UI.createEditPanel()
      },
      export: {
        label: 'Export',
        panel: UI.createExportPanel()
      }
    };
    
    // Create a button for each tab
    Object.keys(tabs).forEach(function(tabId) {
      var tab = tabs[tabId];
      
      var button = ui.Button({
        label: tab.label,
        style: {
          padding: '5px',
          margin: '0 3px'
        },
        onClick: function() {
          // Clear the content panel
          contentPanel.clear();
          
          // Add the selected tab's panel
          contentPanel.add(tab.panel);
          
          // Update button styling
          buttonPanel.widgets().reset();
          Object.keys(tabs).forEach(function(id) {
            var btn = ui.Button({
              label: tabs[id].label,
              style: {
                padding: '5px',
                margin: '0 3px',
                backgroundColor: id === tabId ? '#3182CE' : '#E2E8F0',
                color: id === tabId ? 'white' : 'black'
              },
              onClick: tabs[id].onClick
            });
            buttonPanel.add(btn);
          });
        }
      });
      
      tab.onClick = button.onClick;
      buttonPanel.add(button);
    });
    
    // Set default tab - use direct approach to avoid onClick() method issues
    contentPanel.clear();
    contentPanel.add(tabs.welcome.panel);
    
    return tabPanel;
  },

  // Create welcome panel
  createWelcomePanel: function() {
    var panel = ui.Panel();
    
    var welcomeText = ui.Label({
      value: 'Welcome to the Lusaka Integrated Waste Management Zone Planner',
      style: {fontSize: '16px', fontWeight: 'bold', margin: '10px 0'}
    });
    panel.add(welcomeText);
    
    var instructions = ui.Label({
      value: 'This tool helps you plan waste management zones across Lusaka and surrounding areas ' +
             '(including parts of Chongwe, Chilanga, and Chibombo). ' +
             'You can draw zones, analyze building types and population, and calculate ' +
             'waste generation and revenue potential.',
      style: {margin: '10px 0'}
    });
    panel.add(instructions);
    
    var steps = ui.Label({
      value: 'How to use this tool:\n' +
             '1. Go to the "Draw Zone" tab to create your first zone\n' +
             '2. Select a district to navigate to that area\n' + 
             '3. Click points on the map to draw a polygon\n' +
             '4. Name and save your zone\n' +
             '5. View analysis results in the "Analysis" tab\n' +
             '6. Create sub-zones or edit existing zones in the "Edit Zones" tab\n' +
             '7. Export your data in the "Export" tab',
      style: {whiteSpace: 'pre', margin: '10px 0'}
    });
    panel.add(steps);
    
    // Quick district navigation
    var quickNavLabel = ui.Label({
      value: 'Quick Navigation:',
      style: {margin: '15px 0 5px 0', fontWeight: 'bold'}
    });
    panel.add(quickNavLabel);
    
    var districtButtonPanel = ui.Panel({
      layout: ui.Panel.Layout.flow('horizontal', true),
      style: {margin: '0 0 10px 0'}
    });
    
    // Add a button for each district
    CONFIG.DISTRICTS.forEach(function(district) {
      var districtButton = ui.Button({
        label: district.name,
        onClick: function() {
          ui.root.widgets().get(0).setCenter(
            district.center[0],
            district.center[1],
            district.zoom
          );
        },
        style: {margin: '0 5px 5px 0'}
      });
      districtButtonPanel.add(districtButton);
    });
    
    panel.add(districtButtonPanel);
    
    var startButton = ui.Button({
      label: 'Start Drawing a Zone',
      onClick: function() {
        // Find the main tabPanel through document structure
        var mainPanel = ui.root.widgets().get(1);  // App panel
        var tabPanel = mainPanel.widgets().get(1);  // Tab panel
        var contentPanel = tabPanel.widgets().get(1);  // Content panel
        
        // Clear content panel and show drawing panel
        contentPanel.clear();
        contentPanel.add(UI.createDrawingPanel());
        
        // Update tab buttons to highlight Draw Zone tab
        var buttonPanel = tabPanel.widgets().get(0);  // Button panel
        
        // Reset all buttons styling
        buttonPanel.widgets().reset();
        
        // Recreate buttons with correct styling
        buttonPanel.add(ui.Button({
          label: 'Welcome',
          style: { 
            padding: '5px', 
            margin: '0 3px',
            backgroundColor: '#E2E8F0',
            color: 'black'
          },
          onClick: function() {
            contentPanel.clear();
            contentPanel.add(UI.createWelcomePanel());
          }
        }));
        
        buttonPanel.add(ui.Button({
          label: 'Draw Zone',
          style: { 
            padding: '5px', 
            margin: '0 3px',
            backgroundColor: '#3182CE',
            color: 'white'
          },
          onClick: function() {
            contentPanel.clear();
            contentPanel.add(UI.createDrawingPanel());
          }
        }));
        
        // Add other tab buttons
        buttonPanel.add(ui.Button({
          label: 'Analysis',
          style: { padding: '5px', margin: '0 3px' },
          onClick: function() {
            contentPanel.clear();
            contentPanel.add(UI.createAnalysisPanel());
          }
        }));
        
        buttonPanel.add(ui.Button({
          label: 'Edit Zones',
          style: { padding: '5px', margin: '0 3px' },
          onClick: function() {
            contentPanel.clear();
            contentPanel.add(UI.createEditPanel());
          }
        }));
        
        buttonPanel.add(ui.Button({
          label: 'Export',
          style: { padding: '5px', margin: '0 3px' },
          onClick: function() {
            contentPanel.clear();
            contentPanel.add(UI.createExportPanel());
          }
        }));
      },
      style: {
        padding: '10px',
        margin: '10px 0'
      }
    });
    panel.add(startButton);
    
    return panel;
  },

  // Create drawing panel
  createDrawingPanel: function() {
    var panel = ui.Panel();
    
    var drawingInstructions = ui.Label({
      value: 'Draw a Zone',
      style: {fontSize: '16px', fontWeight: 'bold', margin: '10px 0'}
    });
    panel.add(drawingInstructions);
    
    var instructions = ui.Label({
      value: 'Click on the map to draw a polygon. Complete the polygon by clicking on the first point.',
      style: {margin: '10px 0'}
    });
    panel.add(instructions);
    
    // District selector
    var districtLabel = ui.Label({
      value: 'Navigate to District:',
      style: {margin: '10px 0 5px 0', fontWeight: 'bold'}
    });
    panel.add(districtLabel);
    
    var districtNames = CONFIG.DISTRICTS.map(function(district) {
      return district.name;
    });
    
    var districtSelect = ui.Select({
      items: districtNames,
      placeholder: 'Select a district',
      onChange: function(selected) {
        if (!selected) return;
        
        // Find the district data 
        var district = null;
        
        // Debug what we have
        print("Selected district:", selected);
        print("Available districts:", CONFIG.DISTRICTS);
        
        // Manual lookup since Array.find isn't reliable in GEE
        for (var i = 0; i < CONFIG.DISTRICTS.length; i++) {
          print("Checking district:", CONFIG.DISTRICTS[i].name);
          if (CONFIG.DISTRICTS[i].name === selected) {
            district = CONFIG.DISTRICTS[i];
            break;
          }
        }
        
        // If district is still null, use default center
        if (district === null) {
          print("Warning: District not found, using default center");
          district = {
            center: CONFIG.LUSAKA_CENTER,
            zoom: CONFIG.DEFAULT_ZOOM
          };
        }
        
        // Center the map on the selected district
        ui.root.widgets().get(0).setCenter(
          district.center[0],
          district.center[1],
          district.zoom
        );
      },
      style: {margin: '0 0 10px 0'}
    });
    panel.add(districtSelect);
    
    // Draw button
    var drawButton = ui.Button({
      label: 'Start Drawing',
      onClick: function() {
        DRAWING.startDrawing();
      },
      style: {margin: '5px 0'}
    });
    panel.add(drawButton);
    
    // Clear button
    var clearButton = ui.Button({
      label: 'Clear Drawing',
      onClick: function() {
        DRAWING.clearDrawing();
      },
      style: {margin: '5px 0'}
    });
    panel.add(clearButton);
    
    // Save zone section
    var saveSection = ui.Panel({
      style: {
        padding: '10px',
        margin: '10px 0',
        border: '1px solid #ddd'
      }
    });
    
    var saveLabel = ui.Label({
      value: 'Save Zone',
      style: {fontWeight: 'bold', margin: '0 0 5px 0'}
    });
    saveSection.add(saveLabel);
    
    var nameInput = ui.Textbox({
      placeholder: 'Enter zone name',
      onChange: function(text) {
        // Store the name for later use
        panel.zoneName = text;
      }
    });
    saveSection.add(ui.Label('Zone Name:'));
    saveSection.add(nameInput);
    
    var parentZoneSelect = ui.Select({
      placeholder: 'None (Main Zone)',
      onChange: function(value) {
        panel.parentZone = value;
      }
    });
    saveSection.add(ui.Label('Parent Zone (for sub-zones):'));
    saveSection.add(parentZoneSelect);
    
    // Save button
    var saveButton = ui.Button({
      label: 'Save Zone',
      onClick: function() {
        var zoneName = panel.zoneName;
        if (!zoneName) {
          alert('Please enter a zone name');
          return;
        }
        
        DRAWING.saveZone(zoneName, panel.parentZone);
        
        // Update parent zone dropdown
        UI.updateParentZoneDropdown(parentZoneSelect);
        
        // Clear the name input
        nameInput.setValue('');
      },
      style: {margin: '10px 0 0 0'}
    });
    saveSection.add(saveButton);
    
    panel.add(saveSection);
    
    // Store references to UI elements that need to be accessed later
    panel.nameInput = nameInput;
    panel.parentZoneSelect = parentZoneSelect;
    
    return panel;
  },

  // Create analysis panel
  createAnalysisPanel: function() {
    var panel = ui.Panel();
    
    var analysisTitle = ui.Label({
      value: 'Zone Analysis',
      style: {fontSize: '16px', fontWeight: 'bold', margin: '10px 0'}
    });
    panel.add(analysisTitle);
    
    // Zone selection dropdown
    var zoneSelect = ui.Select({
      placeholder: 'Select a zone to analyze',
      onChange: function(zoneName) {
        if (!zoneName) return;
        
        // Clear previous results
        resultsPanel.clear();
        
        // Add loading indicator
        var loadingLabel = ui.Label({
          value: 'Analyzing zone...',
          style: {margin: '10px 0'}
        });
        resultsPanel.add(loadingLabel);
        
        // Request analysis
        try {
          // Always log to console first - this ensures information is captured
          print("Starting analysis for zone: " + zoneName);
          
          ANALYSIS.analyzeZone(zoneName)
            .then(function(results) {
              try {
                UI.displayAnalysisResults(resultsPanel, results);
                print("Analysis complete for zone: " + zoneName);
              } catch(e) {
                // If UI display fails, at least show results in console
                print("Error displaying analysis results: " + e.message);
                print("Analysis results: " + JSON.stringify(results));
                
                // Try a basic display approach that's less likely to fail
                resultsPanel.clear();
                resultsPanel.add(ui.Label('Analysis complete. See results in console.'));
              }
            })
            .catch(function(error) {
              print("Error in analysis: " + error.message);
              resultsPanel.clear();
              resultsPanel.add(ui.Label('Error: ' + error.message + '. See console for details.'));
            });
        } catch(e) {
          print("Fatal error starting analysis: " + e.message);
          resultsPanel.clear();
          resultsPanel.add(ui.Label('Error starting analysis. See console for details.'));
        }
      }
    });
    
    panel.add(ui.Label('Select Zone:'));
    panel.add(zoneSelect);
    
    // Add a button to refresh zone list
    var refreshButton = ui.Button({
      label: 'Refresh Zone List',
      onClick: function() {
        UI.updateZoneDropdown(zoneSelect);
      }
    });
    panel.add(refreshButton);
    
    // Panel to hold analysis results
    var resultsPanel = ui.Panel({
      style: {
        margin: '10px 0',
        padding: '10px',
        border: '1px solid #ddd'
      }
    });
    panel.add(resultsPanel);
    
    // Store a reference to the zone dropdown
    panel.zoneSelect = zoneSelect;
    
    // Initialize the zone dropdown
    UI.updateZoneDropdown(zoneSelect);
    
    return panel;
  },

  // Create edit panel
  createEditPanel: function() {
    var panel = ui.Panel();
    
    var editTitle = ui.Label({
      value: 'Edit Zones',
      style: {fontSize: '16px', fontWeight: 'bold', margin: '10px 0'}
    });
    panel.add(editTitle);
    
    // Zone selection dropdown
    var zoneSelect = ui.Select({
      placeholder: 'Select a zone to edit',
      onChange: function(zoneName) {
        if (!zoneName) return;
        
        // Enable edit buttons
        editButtonsPanel.style().set('color', '#000000');
        
        // Highlight the selected zone on the map
        DRAWING.highlightZone(zoneName);
      }
    });
    
    panel.add(ui.Label('Select Zone:'));
    panel.add(zoneSelect);
    
    // Add a button to refresh zone list
    var refreshButton = ui.Button({
      label: 'Refresh Zone List',
      onClick: function() {
        UI.updateZoneDropdown(zoneSelect);
      }
    });
    panel.add(refreshButton);
    
    // Edit buttons panel
    var editButtonsPanel = ui.Panel({
      layout: ui.Panel.Layout.flow('vertical'),
      style: {
        margin: '10px 0',
        padding: '10px',
        border: '1px solid #ddd',
        color: '#999999' // Start with gray text to indicate disabled
      }
    });
    
    // Rename button
    var renameButton = ui.Button({
      label: 'Rename Zone',
      onClick: function() {
        var zoneName = zoneSelect.getValue();
        if (!zoneName) return;
        
        var newName = prompt('Enter new name for zone "' + zoneName + '"');
        if (newName) {
          DRAWING.renameZone(zoneName, newName);
          UI.updateZoneDropdown(zoneSelect);
        }
      }
    });
    editButtonsPanel.add(renameButton);
    
    // Delete button
    var deleteButton = ui.Button({
      label: 'Delete Zone',
      onClick: function() {
        var zoneName = zoneSelect.getValue();
        if (!zoneName) return;
        
        var confirmed = confirm('Are you sure you want to delete zone "' + zoneName + '"?');
        if (confirmed) {
          DRAWING.deleteZone(zoneName);
          UI.updateZoneDropdown(zoneSelect);
          // Disable edit buttons
          editButtonsPanel.style().set('color', '#999999');
        }
      },
      style: {
        margin: '5px 0'
      }
    });
    editButtonsPanel.add(deleteButton);
    
    // Edit geometry button
    var editGeometryButton = ui.Button({
      label: 'Edit Zone Boundary',
      onClick: function() {
        var zoneName = zoneSelect.getValue();
        if (!zoneName) return;
        
        DRAWING.editZoneGeometry(zoneName);
      },
      style: {
        margin: '5px 0'
      }
    });
    editButtonsPanel.add(editGeometryButton);
    
    // Add to panel
    panel.add(editButtonsPanel);
    
    // Store a reference to the zone dropdown
    panel.zoneSelect = zoneSelect;
    
    // Initialize the zone dropdown
    UI.updateZoneDropdown(zoneSelect);
    
    return panel;
  },

  // Create export panel
  createExportPanel: function() {
    var panel = ui.Panel();
    
    var exportTitle = ui.Label({
      value: 'Export Data',
      style: {fontSize: '16px', fontWeight: 'bold', margin: '10px 0'}
    });
    panel.add(exportTitle);
    
    // Zone selection dropdown
    var zoneSelect = ui.Select({
      placeholder: 'Select a zone to export',
      onChange: function(zoneName) {
        if (!zoneName) {
          // Disable export button
          exportButton.setDisabled(true);
          return;
        }
        
        // Enable export button
        exportButton.setDisabled(false);
      }
    });
    
    panel.add(ui.Label('Select Zone:'));
    panel.add(zoneSelect);
    
    // Export format selection
    var formatSelect = ui.Select({
      items: CONFIG.EXPORT_OPTIONS.FORMATS,
      placeholder: CONFIG.EXPORT_OPTIONS.DEFAULT_FORMAT,
      onChange: function(format) {
        // Store selected format
        panel.exportFormat = format;
      }
    });
    
    panel.add(ui.Label('Export Format:'));
    panel.add(formatSelect);
    
    // Export button
    var exportButton = ui.Button({
      label: 'Export Data',
      onClick: function() {
        var zoneName = zoneSelect.getValue();
        var format = panel.exportFormat || CONFIG.EXPORT_OPTIONS.DEFAULT_FORMAT;
        
        if (!zoneName) return;
        
        EXPORT.exportZoneData(zoneName, format);
      },
      style: {
        margin: '10px 0'
      },
      disabled: true
    });
    panel.add(exportButton);
    
    // Export all zones button
    var exportAllButton = ui.Button({
      label: 'Export All Zones',
      onClick: function() {
        var format = panel.exportFormat || CONFIG.EXPORT_OPTIONS.DEFAULT_FORMAT;
        EXPORT.exportAllZones(format);
      },
      style: {
        margin: '5px 0'
      }
    });
    panel.add(exportAllButton);
    
    // Store references to UI elements
    panel.zoneSelect = zoneSelect;
    panel.exportButton = exportButton;
    
    // Initialize the zone dropdown
    UI.updateZoneDropdown(zoneSelect);
    
    return panel;
  },

  // Helper function to update zone dropdown options
  updateZoneDropdown: function(dropdown) {
    var zones = DRAWING.getZonesList();
    dropdown.items().reset(zones);
    if (zones.length > 0) {
      dropdown.setPlaceholder('Select a zone');
    } else {
      dropdown.setPlaceholder('No zones available');
    }
  },

  // Helper function to update parent zone dropdown options
  updateParentZoneDropdown: function(dropdown) {
    var zones = DRAWING.getZonesList();
    dropdown.items().reset(zones);
    dropdown.setPlaceholder('None (Main Zone)');
  },

  // Display analysis results
  displayAnalysisResults: function(panel, results) {
    try {
      panel.clear();
      print("Displaying analysis results for zone:", results.zoneName);
    
    // Zone info
    var zoneInfoPanel = ui.Panel({
      style: {padding: '0 0 10px 0', margin: '0 0 10px 0'}
    });
    
    zoneInfoPanel.add(ui.Label({
      value: 'Zone: ' + results.zoneName,
      style: {fontWeight: 'bold', fontSize: '14px'}
    }));
    
    zoneInfoPanel.add(ui.Label('Area: ' + results.area.toFixed(2) + ' sq km'));
    
    if (results.parentZone) {
      zoneInfoPanel.add(ui.Label('Parent Zone: ' + results.parentZone));
    }
    
    panel.add(zoneInfoPanel);
    
    // Buildings summary
    var buildingsPanel = ui.Panel({
      style: {padding: '10px 0', margin: '0 0 10px 0'}
    });
    
    buildingsPanel.add(ui.Label({
      value: 'Buildings',
      style: {fontWeight: 'bold'}
    }));
    
    buildingsPanel.add(ui.Label('Total Buildings: ' + results.buildings.total));
    
    // Add building counts by type
    Object.keys(results.buildings.byType).forEach(function(type) {
      var count = results.buildings.byType[type];
      var label = CONFIG.BUILDING_CLASSES[type].label;
      buildingsPanel.add(ui.Label(label + ': ' + count));
    });
    
    panel.add(buildingsPanel);
    
    // Population summary
    var populationPanel = ui.Panel({
      style: {padding: '10px 0', margin: '0 0 10px 0'}
    });
    
    populationPanel.add(ui.Label({
      value: 'Population',
      style: {fontWeight: 'bold'}
    }));
    
    populationPanel.add(ui.Label('Estimated Population: ' + Math.round(results.population.total)));
    populationPanel.add(ui.Label('Population Density: ' + Math.round(results.population.density) + ' people/sq km'));
    
    panel.add(populationPanel);
    
    // Waste generation
    var wastePanel = ui.Panel({
      style: {padding: '10px 0', margin: '0 0 10px 0'}
    });
    
    wastePanel.add(ui.Label({
      value: 'Waste Generation',
      style: {fontWeight: 'bold'}
    }));
    
    wastePanel.add(ui.Label('Daily Waste: ' + results.waste.daily.toFixed(2) + ' kg/day'));
    wastePanel.add(ui.Label('Monthly Waste: ' + results.waste.monthly.toFixed(2) + ' kg/month'));
    wastePanel.add(ui.Label('Monthly Waste (tons): ' + (results.waste.monthly / 1000).toFixed(2) + ' tons/month'));
    
    panel.add(wastePanel);
    
    // Financial analysis
    var financialPanel = ui.Panel({
      style: {padding: '10px 0'}
    });
    
    financialPanel.add(ui.Label({
      value: 'Financial Analysis (Monthly)',
      style: {fontWeight: 'bold'}
    }));
    
    // Revenue details
    financialPanel.add(ui.Label('Total Revenue: ' + results.financial.revenue.total.toFixed(2) + ' Kwacha'));
    
    var revenueDetails = ui.Panel();
    Object.keys(results.financial.revenue.byType).forEach(function(type) {
      var amount = results.financial.revenue.byType[type];
      var label = CONFIG.BUILDING_CLASSES[type].label;
      revenueDetails.add(ui.Label('- ' + label + ': ' + amount.toFixed(2) + ' Kwacha'));
    });
    
    financialPanel.add(revenueDetails);
    
    // Expenses
    financialPanel.add(ui.Label('Total Expenses: ' + results.financial.expenses.total.toFixed(2) + ' Kwacha'));
    
    var expensesDetails = ui.Panel();
    expensesDetails.add(ui.Label('- Fixed Expenses: ' + results.financial.expenses.fixed.toFixed(2) + ' Kwacha'));
    expensesDetails.add(ui.Label('- Collection Costs: ' + results.financial.expenses.collection.toFixed(2) + ' Kwacha'));
    expensesDetails.add(ui.Label('- Disposal Costs: ' + results.financial.expenses.disposal.toFixed(2) + ' Kwacha'));
    
    financialPanel.add(expensesDetails);
    
    // Profit/Loss
    var profit = results.financial.profit;
    var profitLabel = ui.Label({
      value: 'Net Profit/Loss: ' + profit.toFixed(2) + ' Kwacha',
      style: {
        fontWeight: 'bold',
        color: profit >= 0 ? 'green' : 'red'
      }
    });
    financialPanel.add(profitLabel);
    
    panel.add(financialPanel);
    
    // Show/hide buildings button for confidence visualization
    var showBuildingsButton = ui.Button({
      label: 'Show Buildings by Confidence Score',
      onClick: function() {
        try {
          var showing = showBuildingsButton.getLabel() === 'Show Buildings by Confidence Score';
          showBuildingsButton.setLabel(showing ? 'Hide Building Visualization' : 'Show Buildings by Confidence Score');
          ANALYSIS.toggleBuildingsDisplay(results.zoneName, showing);
        } catch(e) {
          print("Error toggling building display:", e.message);
        }
      }
    });
    panel.add(showBuildingsButton);
    
    print("Analysis results displayed successfully");
    } catch(error) {
      // Handle any UI rendering errors
      print("ERROR displaying analysis results:", error.message);
      
      // Create a simple error panel
      panel.clear();
      panel.add(ui.Label("Error displaying detailed results. See console for data."));
      
      // Add a text representation of basic results
      try {
        var basicResultsText = "Zone: " + results.zoneName + 
                             "\nArea: " + results.area.toFixed(2) + " sq km" +
                             "\nEstimated Population: " + Math.round(results.population.total) +
                             "\nMonthly Waste: " + results.waste.monthly.toFixed(2) + " kg" +
                             "\nEstimated Monthly Revenue: " + results.financial.revenue.total.toFixed(2) + " Kwacha";
        
        panel.add(ui.Label(basicResultsText, {whiteSpace: 'pre'}));
      } catch(e) {
        print("Could not even display basic text results:", e.message);
      }
    }
  },

  // Helper function: alert - console-only approach to avoid errors
  alert: function(message) {
    // Always print to console for logging
    print("ALERT MESSAGE:", message);
    
    // Add visually distinct markers to make alerts stand out in the console
    print("⚠️ ==================================== ⚠️");
    print("⚠️              ALERT                  ⚠️");
    print("⚠️ ==================================== ⚠️");
    
    // DO NOT try to use UI components for alerts at all
    // Instead, rely exclusively on console logging for stability
  },

  // Helper function: prompt
  prompt: function(message, defaultValue) {
    return window.prompt(message, defaultValue || '');
  },

  // Helper function: confirm
  confirm: function(message) {
    return window.confirm(message);
  }
};

// Safe alert function that will work even if ui.Modal is not defined
function safeAlert(message) {
  // Always print to console first
  print("ALERT:", message);
  
  // Add visually distinct markers to make alerts stand out in the console
  print("⚠️ ==================================== ⚠️");
  print("⚠️              ALERT                  ⚠️");
  print("⚠️ ==================================== ⚠️");
  
  // AVOID using UI components for alerts entirely
  // Since they're causing errors, we'll rely exclusively on console logging
  
  // DO NOT try to use ui components directly - this is safer
  /*
  try {
    // Try ui.alert first
    if (typeof ui !== 'undefined' && typeof ui.alert === 'function') {
      ui.alert(message);
      return;
    }
    
    // Fall back to UI object's alert if defined
    if (typeof UI !== 'undefined' && typeof UI.alert === 'function') {
      UI.alert(message);
      return;
    }
  } catch(e) {
    print("Error showing alert:", e);
  }
  */
}

// Initialize the application
function initialize() {
  // Set up the map centered on Lusaka and surrounding areas
  var mapPanel = MAP.createMap();
  
  // Create UI components
  var appPanel = UI.createMainPanel();
  
  // Add the map and panels to the UI
  ui.root.clear();
  ui.root.add(mapPanel);
  ui.root.add(appPanel);
  
  // Initialize drawing tools
  DRAWING.initialize(mapPanel, appPanel);
  
  // Add a logo or credit in the bottom corner
  var creditLabel = ui.Label({
    value: 'Lusaka Integrated Solid Waste Management Company',
    style: {
      position: 'bottom-left',
      backgroundColor: 'rgba(255, 255, 255, 0.7)',
      padding: '4px 8px',
      fontSize: '10px',
      border: '1px solid #ddd',
      borderRadius: '3px'
    }
  });
  mapPanel.add(creditLabel);
}

// Start the application
initialize();
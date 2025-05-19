// Drawing module for creating and managing zones

var ee = require('ee');
var ui = require('ui');
var config = require('./config');
var uiModule = require('./ui');

// Safe alert function that doesn't rely on UI
function safeAlert(message) {
  // Always print to console
  print("ALERT:", message);
  
  // Try to use the custom alert from ui.js if available
  if (uiModule && typeof uiModule.alert === 'function') {
    try {
      uiModule.alert(message);
      return;
    } catch(e) {
      print("Failed to use ui module alert:", e);
    }
  }
  
  // Fallback to direct ui.alert if available
  try {
    if (ui && typeof ui.alert === 'function') {
      ui.alert(message);
    }
  } catch(e) {
    print("Failed to use ui.alert:", e);
    // At this point, at least the message is printed to console
  }
}

// Store state for zones
var zones = {};
var activeZone = null;
var drawingMode = false;
var mapInstance = null;
var mainAppPanel = null;

// Initialize the drawing module
exports.initialize = function(map, appPanel) {
  mapInstance = map;
  mainAppPanel = appPanel;
  
  // Set up drawing tools
  setupDrawingTools(map);
  
  // Initialize the zones storage
  initializeZonesStorage();
};

// Set up the drawing tools on the map
function setupDrawingTools(map) {
  map.drawingTools().setShown(false);
  
  // Set up drawing tools event listeners
  map.drawingTools().onDraw(function(geometry) {
    if (!drawingMode) return;
    
    // Store the drawn geometry temporarily
    activeZone = geometry;
    
    // Disable drawing mode after a polygon is completed
    drawingMode = false;
    
    // Show the save panel
    // This could be a signal to the UI to show the save options
    ui.root.widgets().get(1).widgets().get(1).widgets().get(1).widgets().get(0).widgets().get(5).style().set('border', '1px solid #3182CE');
  });
}

// Initialize the zones storage
function initializeZonesStorage() {
  // In a real application, you would load saved zones from a database or file
  // For this demo, we'll just initialize an empty object
  zones = {};
}

// Start drawing a new zone
exports.startDrawing = function() {
  // Clear any existing geometry
  mapInstance.drawingTools().layers().reset();
  
  // Enter drawing mode
  drawingMode = true;
  mapInstance.drawingTools().setShape('polygon');
  mapInstance.drawingTools().setLinked(true);
  mapInstance.drawingTools().setDrawModes(['polygon']);
  mapInstance.drawingTools().setShown(true);
  
  // Show the save panel (will be completed when the user finishes drawing)
  ui.root.widgets().get(1).widgets().get(1).widgets().get(1).widgets().get(0).widgets().get(5).style().set('border', '1px solid #dddddd');
};

// Clear the current drawing
exports.clearDrawing = function() {
  mapInstance.drawingTools().layers().reset();
  activeZone = null;
  drawingMode = false;
};

// Save the current zone
exports.saveZone = function(zoneName, parentZoneName) {
  if (!activeZone) {
    print('No zone has been drawn. Please draw a zone first.');
    safeAlert('No zone has been drawn. Please draw a zone first.');
    return;
  }
  
  // Create a new zone object
  var zone = {
    name: zoneName,
    geometry: activeZone,
    parentZone: parentZoneName || null,
    subZones: [],
    dateCreated: new Date().toISOString(),
    id: 'zone_' + Date.now()
  };
  
  // Add to zones collection
  zones[zoneName] = zone;
  
  // If this is a sub-zone, add it to its parent
  if (parentZoneName && zones[parentZoneName]) {
    zones[parentZoneName].subZones.push(zoneName);
  }
  
  // Add the zone to the map
  var color = parentZoneName ? config.COLORS.SUB_ZONE : config.COLORS.MAIN_ZONE;
  addZoneToMap(zone, color);
  
  // Clear the active zone and drawing tools
  mapInstance.drawingTools().layers().reset();
  activeZone = null;
  
  print('Zone "' + zoneName + '" has been saved.');
  safeAlert('Zone "' + zoneName + '" has been saved.');
  
  return zone;
};

// Add a zone to the map
function addZoneToMap(zone, color) {
  var geoFeature = ee.Feature(zone.geometry, {
    name: zone.name,
    zoneId: zone.id
  });
  
  var zoneLayer = ui.Map.Layer(geoFeature, {color: color}, zone.name);
  mapInstance.layers().add(zoneLayer);
  
  return zoneLayer;
}

// Get all zones as a list of names
exports.getZonesList = function() {
  return Object.keys(zones);
};

// Get a specific zone by name
exports.getZone = function(zoneName) {
  return zones[zoneName] || null;
};

// Get all zones
exports.getAllZones = function() {
  return zones;
};

// Highlight a specific zone on the map
exports.highlightZone = function(zoneName) {
  // First remove any existing highlight
  removeZoneHighlight();
  
  // Then highlight the requested zone
  var zone = zones[zoneName];
  if (!zone) return;
  
  var geoFeature = ee.Feature(zone.geometry, {
    name: zone.name,
    zoneId: zone.id,
    highlighted: true
  });
  
  var highlightLayer = ui.Map.Layer(
    geoFeature, 
    {color: config.COLORS.SELECTED_ZONE}, 
    zone.name + ' (selected)'
  );
  
  mapInstance.layers().add(highlightLayer);
  
  // Center map on the zone
  mapInstance.centerObject(geoFeature, 15);
};

// Remove zone highlight
function removeZoneHighlight() {
  mapInstance.layers().forEach(function(layer) {
    if (layer.getName().indexOf('(selected)') !== -1) {
      mapInstance.layers().remove(layer);
    }
  });
}

// Rename a zone
exports.renameZone = function(oldName, newName) {
  if (!zones[oldName]) {
    print('Zone "' + oldName + '" does not exist.');
    safeAlert('Zone "' + oldName + '" does not exist.');
    return;
  }
  
  if (zones[newName]) {
    print('Zone "' + newName + '" already exists. Please choose a different name.');
    safeAlert('Zone "' + newName + '" already exists. Please choose a different name.');
    return;
  }
  
  // Update the zone name
  var zone = zones[oldName];
  zone.name = newName;
  
  // Add to zones collection with new name
  zones[newName] = zone;
  
  // Remove old entry
  delete zones[oldName];
  
  // Update parent references if this is a sub-zone
  Object.keys(zones).forEach(function(zoneName) {
    var parentZone = zones[zoneName];
    var subZones = parentZone.subZones;
    
    for (var i = 0; i < subZones.length; i++) {
      if (subZones[i] === oldName) {
        subZones[i] = newName;
      }
    }
  });
  
  // Update map layer
  mapInstance.layers().forEach(function(layer) {
    if (layer.getName() === oldName) {
      // Remove the old layer
      mapInstance.layers().remove(layer);
      
      // Add a new layer with the updated name
      var color = zone.parentZone ? config.COLORS.SUB_ZONE : config.COLORS.MAIN_ZONE;
      addZoneToMap(zone, color);
    }
  });
  
  print('Zone renamed from "' + oldName + '" to "' + newName + '".');
  safeAlert('Zone renamed from "' + oldName + '" to "' + newName + '".');
};

// Delete a zone
exports.deleteZone = function(zoneName) {
  if (!zones[zoneName]) {
    print('Zone "' + zoneName + '" does not exist.');
    safeAlert('Zone "' + zoneName + '" does not exist.');
    return;
  }
  
  // Check if this zone has sub-zones
  var zone = zones[zoneName];
  if (zone.subZones && zone.subZones.length > 0) {
    print('Cannot delete zone "' + zoneName + '" because it has sub-zones. Delete the sub-zones first.');
    safeAlert('Cannot delete zone "' + zoneName + '" because it has sub-zones. Delete the sub-zones first.');
    return;
  }
  
  // Remove from parent's sub-zones list
  if (zone.parentZone && zones[zone.parentZone]) {
    var parentZone = zones[zone.parentZone];
    var subZones = parentZone.subZones;
    var index = subZones.indexOf(zoneName);
    if (index !== -1) {
      subZones.splice(index, 1);
    }
  }
  
  // Remove from map
  mapInstance.layers().forEach(function(layer) {
    if (layer.getName() === zoneName || layer.getName() === zoneName + ' (selected)') {
      mapInstance.layers().remove(layer);
    }
  });
  
  // Remove from zones collection
  delete zones[zoneName];
  
  print('Zone "' + zoneName + '" has been deleted.');
  safeAlert('Zone "' + zoneName + '" has been deleted.');
};

// Edit zone geometry
exports.editZoneGeometry = function(zoneName) {
  if (!zones[zoneName]) {
    print('Zone "' + zoneName + '" does not exist.');
    safeAlert('Zone "' + zoneName + '" does not exist.');
    return;
  }
  
  var zone = zones[zoneName];
  
  // Clear drawing tools
  mapInstance.drawingTools().layers().reset();
  
  // Add the geometry to the drawing tools
  mapInstance.drawingTools().addLayer(ee.FeatureCollection([ee.Feature(zone.geometry)]));
  
  // Activate drawing tools for editing
  mapInstance.drawingTools().setShape('polygon');
  mapInstance.drawingTools().setLinked(true);
  mapInstance.drawingTools().setDrawModes(['polygon']);
  mapInstance.drawingTools().setShown(true);
  
  // Set up listener for edit completion
  var editListener = mapInstance.drawingTools().onEdit(function(geometry) {
    // Update the zone geometry
    zone.geometry = geometry;
    
    // Update the map layer
    mapInstance.layers().forEach(function(layer) {
      if (layer.getName() === zoneName || layer.getName() === zoneName + ' (selected)') {
        mapInstance.layers().remove(layer);
      }
    });
    
    var color = zone.parentZone ? config.COLORS.SUB_ZONE : config.COLORS.MAIN_ZONE;
    addZoneToMap(zone, color);
    
    // Clear the drawing tools
    mapInstance.drawingTools().layers().reset();
    mapInstance.drawingTools().setShown(false);
    
    // Remove the listener
    mapInstance.drawingTools().onEdit(null);
    
    print('Zone "' + zoneName + '" geometry has been updated.');
    safeAlert('Zone "' + zoneName + '" geometry has been updated.');
  });
};
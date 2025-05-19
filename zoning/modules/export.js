// Export module for exporting zone data

var ee = require('ee');
var ui = require('ui');
var drawing = require('./drawing');
var analysis = require('./analysis');
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

// Export data for a specific zone
exports.exportZoneData = function(zoneName, format) {
  var zone = drawing.getZone(zoneName);
  if (!zone) {
    print('Zone "' + zoneName + '" not found.');
    safeAlert('Zone "' + zoneName + '" not found.');
    return;
  }
  
  // Show loading message in console
  print('Preparing export for zone "' + zoneName + '"...');
  
  // Try to show a UI message, but don't rely on it
  try {
    ui.Label({
      value: 'Preparing export for zone "' + zoneName + '"...',
      style: {fontWeight: 'bold', position: 'bottom-center'}
    }).style().set('shown', true);
  } catch(e) {
    print('Error showing export status:', e);
  }
  
  // Analyze the zone to get all metrics
  analysis.analyzeZone(zoneName)
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
      var errorMsg = 'Error exporting zone: ' + error.message;
      print(errorMsg);
      
      safeAlert(errorMsg);
    });
};

// Export data for all zones
exports.exportAllZones = function(format) {
  var allZones = drawing.getAllZones();
  var zoneNames = Object.keys(allZones);
  
  if (zoneNames.length === 0) {
    print('No zones to export.');
    safeAlert('No zones to export.');
    return;
  }
  
  // Show loading message in console
  print('Preparing export for all zones...');
  
  // Try to show a UI message, but don't rely on it
  try {
    ui.Label({
      value: 'Preparing export for all zones...',
      style: {fontWeight: 'bold', position: 'bottom-center'}
    }).style().set('shown', true);
  } catch(e) {
    print('Error showing export status:', e);
  }
  
  // Create promises for all zone analyses
  var analysisPromises = zoneNames.map(function(zoneName) {
    return analysis.analyzeZone(zoneName);
  });
  
  // Wait for all analyses to complete
  Promise.all(analysisPromises)
    .then(function(resultsArray) {
      // Create features for each zone with analysis results
      var features = resultsArray.map(function(results) {
        var zone = drawing.getZone(results.zoneName);
        
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
      var errorMsg = 'Error exporting zones: ' + error.message;
      print(errorMsg);
      
      safeAlert(errorMsg);
    });
};
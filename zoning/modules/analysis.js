// Analysis module for processing zone data

var ee = require('ee');
var ui = require('ui');
var config = require('./config');
var drawing = require('./drawing');
var map = require('./map');

// Analyze a zone and return detailed metrics
exports.analyzeZone = function(zoneName) {
  return new Promise(function(resolve, reject) {
    try {
      var zone = drawing.getZone(zoneName);
      if (!zone) {
        reject(new Error('Zone "' + zoneName + '" not found.'));
        return;
      }
      
      // Create an Earth Engine geometry from the zone
      var zoneGeometry = zone.geometry;
      var zoneFeature = ee.Feature(zoneGeometry, { 'name': zoneName });
      
      // Calculate zone area in square kilometers
      var area = zoneFeature.geometry().area().divide(1000000); // Convert to sq km
      
      // Get buildings within the zone
      var buildingsAnalysis = analyzeBuildings(zoneFeature);
      
      // Get population within the zone
      var populationAnalysis = analyzePopulation(zoneFeature, area);
      
      // Calculate waste generation
      var wasteAnalysis = calculateWasteGeneration(buildingsAnalysis, populationAnalysis);
      
      // Financial analysis
      var financialAnalysis = calculateFinancials(buildingsAnalysis, wasteAnalysis);
      
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
      
      resolve(results);
    } catch (error) {
      reject(error);
    }
  });
};

// Analyze buildings within a zone
function analyzeBuildings(zoneFeature) {
  // Get buildings dataset
  var buildings = ee.FeatureCollection(config.BUILDINGS_DATASET)
    .filterBounds(zoneFeature.geometry());
  
  // Get total number of buildings
  var totalBuildings = buildings.size().getInfo();
  
  // Analyze buildings by type based on area
  var buildingsByType = {};
  
  // Count buildings by class
  Object.keys(config.BUILDING_CLASSES).forEach(function(classKey) {
    var classInfo = config.BUILDING_CLASSES[classKey];
    var filteredBuildings = buildings.filter(function(feature) {
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
    
    buildingsByType[classKey] = filteredBuildings.size().getInfo();
  });
  
  return {
    total: totalBuildings,
    byType: buildingsByType
  };
}

// Analyze population within a zone
function analyzePopulation(zoneFeature, area) {
  // Get population dataset
  var populationDataset = ee.ImageCollection(config.POPULATION_DATASET)
    .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
    .first();
  
  // Calculate total population
  var populationStats = populationDataset
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: zoneFeature.geometry(),
      scale: 100,
      maxPixels: 1e9
    });
  
  var totalPopulation = populationStats.get('population').getInfo();
  
  // Calculate population density (people per sq km)
  var density = totalPopulation / area.getInfo();
  
  return {
    total: totalPopulation,
    density: density
  };
}

// Calculate waste generation based on buildings and population
function calculateWasteGeneration(buildings, population) {
  // Calculate daily waste generation in kg
  
  // Residential waste based on population
  var residentialWaste = population.total * config.WASTE_GENERATION.RESIDENTIAL_PER_PERSON;
  
  // Commercial waste based on building counts
  var commercialSmallWaste = buildings.byType.COMMERCIAL_SMALL * config.WASTE_GENERATION.COMMERCIAL_SMALL;
  var commercialMediumWaste = buildings.byType.COMMERCIAL_MEDIUM * config.WASTE_GENERATION.COMMERCIAL_MEDIUM;
  var commercialLargeWaste = buildings.byType.COMMERCIAL_LARGE * config.WASTE_GENERATION.COMMERCIAL_LARGE;
  
  // Total daily waste in kg
  var dailyWaste = residentialWaste + commercialSmallWaste + commercialMediumWaste + commercialLargeWaste;
  
  // Calculate monthly waste (30 days) in kg
  var monthlyWaste = dailyWaste * 30;
  
  return {
    daily: dailyWaste,
    monthly: monthlyWaste,
    residential: residentialWaste,
    commercial: commercialSmallWaste + commercialMediumWaste + commercialLargeWaste
  };
}

// Calculate financial metrics based on building counts and waste generation
function calculateFinancials(buildings, waste) {
  // Calculate monthly revenue based on building counts and pricing tiers
  var revenueByType = {};
  var totalRevenue = 0;
  
  // Residential revenue
  revenueByType.RESIDENTIAL_PERI_URBAN = buildings.byType.RESIDENTIAL_PERI_URBAN * config.PRICING.RESIDENTIAL_PERI_URBAN;
  revenueByType.RESIDENTIAL_URBAN = buildings.byType.RESIDENTIAL_URBAN * config.PRICING.RESIDENTIAL_URBAN;
  
  // Commercial revenue
  revenueByType.COMMERCIAL_SMALL = buildings.byType.COMMERCIAL_SMALL * config.PRICING.COMMERCIAL_SMALL;
  revenueByType.COMMERCIAL_MEDIUM = buildings.byType.COMMERCIAL_MEDIUM * config.PRICING.COMMERCIAL_MEDIUM;
  revenueByType.COMMERCIAL_LARGE = buildings.byType.COMMERCIAL_LARGE * config.PRICING.COMMERCIAL_LARGE;
  
  // Total revenue
  Object.keys(revenueByType).forEach(function(type) {
    totalRevenue += revenueByType[type];
  });
  
  // Calculate expenses
  var disposalCost = (waste.monthly / 1000) * config.WASTE_GENERATION.DISPOSAL_COST; // Convert kg to tons
  var collectionCost = (waste.monthly / 1000) * config.EXPENSES.PER_TON_COLLECTION; // Cost per ton
  var fixedExpenses = config.EXPENSES.FIXED_MONTHLY;
  
  var totalExpenses = fixedExpenses + collectionCost + disposalCost;
  
  // Calculate profit/loss
  var profit = totalRevenue - totalExpenses;
  
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
}

// Toggle display of buildings classified by type
exports.toggleBuildingsDisplay = function(zoneName, show) {
  var zone = drawing.getZone(zoneName);
  if (!zone) return;
  
  var zoneGeometry = zone.geometry;
  
  if (show) {
    // Get buildings within the zone
    var buildings = ee.FeatureCollection(config.BUILDINGS_DATASET)
      .filterBounds(zoneGeometry);
    
    // Display buildings on the map, colored by type
    map.highlightBuildingsByClass(ui.root.widgets().get(0), buildings, true);
  } else {
    // Hide building classification
    map.highlightBuildingsByClass(ui.root.widgets().get(0), null, false);
  }
};
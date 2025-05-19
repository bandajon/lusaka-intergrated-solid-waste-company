// Lusaka Integrated Solid Waste Management Zone Planning Tool
// Main application entry point

// Import modules
var ui = require('./modules/ui');
var map = require('./modules/map');
var analysis = require('./modules/analysis');
var drawing = require('./modules/drawing');
var dataExport = require('./modules/export');
var config = require('./modules/config');

// Initialize the application
function initialize() {
  // Set up the map centered on Lusaka and surrounding areas
  var mapPanel = map.createMap();
  
  // Create UI components
  var appPanel = ui.createMainPanel();
  
  // Add the map and panels to the UI
  ui.App.clear();
  ui.App.add(mapPanel);
  ui.App.add(appPanel);
  
  // Initialize drawing tools
  drawing.initialize(mapPanel, appPanel);
}

// Start the application
initialize();
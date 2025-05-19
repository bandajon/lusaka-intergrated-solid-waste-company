// UI components module

var ui = require('ui');
var config = require('./config');

// Add safer module loading with availability checks
var analysis, drawing, dataExport;

// Function to safely load modules with error handling
function safeRequire(modulePath) {
  try {
    return require(modulePath);
  } catch (e) {
    print('Error loading module ' + modulePath + ': ' + e.message);
    return {}; // Return empty object as fallback
  }
}

// Safe module loading
try {
  analysis = safeRequire('./analysis');
  print('Analysis module loaded');
} catch (e) {
  print('Failed to load analysis module: ' + e.message);
  analysis = {};
}

try {
  drawing = safeRequire('./drawing');
  print('Drawing module loaded');
} catch (e) {
  print('Failed to load drawing module: ' + e.message);
  drawing = {};
}

try {
  dataExport = safeRequire('./export');
  print('Export module loaded');
} catch (e) {
  print('Failed to load export module: ' + e.message);
  dataExport = {};
}

// Create the main application panel
exports.createMainPanel = function() {
  var panel = ui.Panel({
    style: {
      width: config.PANEL_WIDTH,
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
  var tabs = createTabPanel(panel);
  panel.add(tabs);
  
  return panel;
};

// Create the tabbed interface
function createTabPanel(mainPanel) {
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
      panel: createWelcomePanel()
    },
    draw: {
      label: 'Draw Zone',
      panel: createDrawingPanel()
    },
    analyze: {
      label: 'Analysis',
      panel: createAnalysisPanel()
    },
    edit: {
      label: 'Edit Zones',
      panel: createEditPanel()
    },
    export: {
      label: 'Export',
      panel: createExportPanel()
    }
  };
  
  // Create a button for each tab and store them
  var tabButtons = {};
  
  // Function to switch to a tab
  function switchToTab(tabId) {
    // Clear the content panel
    contentPanel.clear();
    
    // Add the selected tab's panel
    contentPanel.add(tabs[tabId].panel);
    
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
        onClick: function() { switchToTab(id); }
      });
      buttonPanel.add(btn);
      tabButtons[id] = btn;
    });
  }
  
  // Create initial buttons
  Object.keys(tabs).forEach(function(tabId) {
    var button = ui.Button({
      label: tabs[tabId].label,
      style: {
        padding: '5px',
        margin: '0 3px'
      },
      onClick: function() { 
        switchToTab(tabId); 
      }
    });
    
    buttonPanel.add(button);
    tabButtons[tabId] = button;
  });
  
  // Set default tab
  switchToTab('welcome');
  
  return tabPanel;
}

// Create welcome panel
function createWelcomePanel() {
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
  config.DISTRICTS.forEach(function(district) {
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
      contentPanel.add(createDrawingPanel());
      
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
          contentPanel.add(createWelcomePanel());
          
          // Update button styling
          buttonPanel.widgets().get(0).style().set({
            backgroundColor: '#3182CE',
            color: 'white'
          });
          buttonPanel.widgets().get(1).style().set({
            backgroundColor: '#E2E8F0',
            color: 'black'
          });
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
          contentPanel.add(createDrawingPanel());
          
          // Update button styling
          buttonPanel.widgets().get(0).style().set({
            backgroundColor: '#E2E8F0',
            color: 'black'
          });
          buttonPanel.widgets().get(1).style().set({
            backgroundColor: '#3182CE',
            color: 'white'
          });
        }
      }));
      
      // Add other tab buttons
      buttonPanel.add(ui.Button({
        label: 'Analysis',
        style: { padding: '5px', margin: '0 3px' },
        onClick: function() {
          contentPanel.clear();
          contentPanel.add(createAnalysisPanel());
        }
      }));
      
      buttonPanel.add(ui.Button({
        label: 'Edit Zones',
        style: { padding: '5px', margin: '0 3px' },
        onClick: function() {
          contentPanel.clear();
          contentPanel.add(createEditPanel());
        }
      }));
      
      buttonPanel.add(ui.Button({
        label: 'Export',
        style: { padding: '5px', margin: '0 3px' },
        onClick: function() {
          contentPanel.clear();
          contentPanel.add(createExportPanel());
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
}

// Create drawing panel
function createDrawingPanel() {
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
  
  var districtNames = config.DISTRICTS.map(function(district) {
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
      print("Available districts:", config.DISTRICTS);
      
      // Manual lookup since Array.find isn't reliable in GEE
      for (var i = 0; i < config.DISTRICTS.length; i++) {
        print("Checking district:", config.DISTRICTS[i].name);
        if (config.DISTRICTS[i].name === selected) {
          district = config.DISTRICTS[i];
          break;
        }
      }
      
      // If district is still null, use default center
      if (district === null) {
        print("Warning: District not found, using default center");
        district = {
          center: config.LUSAKA_CENTER,
          zoom: config.DEFAULT_ZOOM
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
      // Safety check before calling drawing functions
      if (drawing && typeof drawing.startDrawing === 'function') {
        try {
          drawing.startDrawing();
          print('Drawing started successfully');
        } catch (e) {
          print('Error starting drawing: ' + e.message);
          // Fallback notification
          alert('Could not start drawing tools. Please check the console for errors.');
        }
      } else {
        print('WARNING: drawing.startDrawing is not a function');
        alert('Drawing tools not available. Please check the console for errors.');
      }
    },
    style: {margin: '5px 0'}
  });
  panel.add(drawButton);
  
  // Clear button
  var clearButton = ui.Button({
    label: 'Clear Drawing',
    onClick: function() {
      // Safety check before calling drawing functions
      if (drawing && typeof drawing.clearDrawing === 'function') {
        try {
          drawing.clearDrawing();
          print('Drawing cleared successfully');
        } catch (e) {
          print('Error clearing drawing: ' + e.message);
          alert('Could not clear drawing. Please check the console for errors.');
        }
      } else {
        print('WARNING: drawing.clearDrawing is not a function');
        alert('Drawing tools not available. Please check the console for errors.');
      }
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
        print('Please enter a zone name');
        try {
          alert('Please enter a zone name');
        } catch(e) {
          print('Error showing alert:', e);
        }
        return;
      }
      
      // Safety check before calling drawing functions
      if (drawing && typeof drawing.saveZone === 'function') {
        try {
          drawing.saveZone(zoneName, panel.parentZone);
          print('Zone "' + zoneName + '" saved successfully');
        } catch (e) {
          print('Error saving zone: ' + e.message);
          alert('Could not save zone. Please check the console for errors.');
        }
      } else {
        print('WARNING: drawing.saveZone is not a function');
        alert('Zone saving not available. Please check the console for errors.');
      }
      
      // Update parent zone dropdown
      updateParentZoneDropdown(parentZoneSelect);
      
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
}

// Create analysis panel
function createAnalysisPanel() {
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
      analysis.analyzeZone(zoneName)
        .then(function(results) {
          displayAnalysisResults(resultsPanel, results);
        })
        .catch(function(error) {
          resultsPanel.clear();
          resultsPanel.add(ui.Label('Error: ' + error.message));
        });
    }
  });
  
  panel.add(ui.Label('Select Zone:'));
  panel.add(zoneSelect);
  
  // Add a button to refresh zone list
  var refreshButton = ui.Button({
    label: 'Refresh Zone List',
    onClick: function() {
      updateZoneDropdown(zoneSelect);
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
  updateZoneDropdown(zoneSelect);
  
  return panel;
}

// Create edit panel
function createEditPanel() {
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
      drawing.highlightZone(zoneName);
    }
  });
  
  panel.add(ui.Label('Select Zone:'));
  panel.add(zoneSelect);
  
  // Add a button to refresh zone list
  var refreshButton = ui.Button({
    label: 'Refresh Zone List',
    onClick: function() {
      updateZoneDropdown(zoneSelect);
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
        drawing.renameZone(zoneName, newName);
        updateZoneDropdown(zoneSelect);
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
        drawing.deleteZone(zoneName);
        updateZoneDropdown(zoneSelect);
        // Disable edit buttons
        editButtonsPanel.style().set('opacity', '0.5');
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
      
      drawing.editZoneGeometry(zoneName);
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
  updateZoneDropdown(zoneSelect);
  
  return panel;
}

// Create export panel
function createExportPanel() {
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
    items: config.EXPORT_OPTIONS.FORMATS,
    placeholder: config.EXPORT_OPTIONS.DEFAULT_FORMAT,
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
      var format = panel.exportFormat || config.EXPORT_OPTIONS.DEFAULT_FORMAT;
      
      if (!zoneName) return;
      
      dataExport.exportZoneData(zoneName, format);
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
      var format = panel.exportFormat || config.EXPORT_OPTIONS.DEFAULT_FORMAT;
      dataExport.exportAllZones(format);
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
  updateZoneDropdown(zoneSelect);
  
  return panel;
}

// Helper function to update zone dropdown options
function updateZoneDropdown(dropdown) {
  if (!dropdown) {
    print('WARNING: dropdown is not defined in updateZoneDropdown');
    return;
  }

  try {
    var zones = [];
    if (drawing && typeof drawing.getZonesList === 'function') {
      zones = drawing.getZonesList();
    } else {
      print('WARNING: drawing.getZonesList is not a function');
    }
    
    if (typeof dropdown.items === 'function' && typeof dropdown.items().reset === 'function') {
      dropdown.items().reset(zones);
    }
    
    if (typeof dropdown.setPlaceholder === 'function') {
      if (zones.length > 0) {
        dropdown.setPlaceholder('Select a zone');
      } else {
        dropdown.setPlaceholder('No zones available');
      }
    }
  } catch (e) {
    print('Error in updateZoneDropdown: ' + e.message);
  }
}

// Helper function to update parent zone dropdown options
function updateParentZoneDropdown(dropdown) {
  if (!dropdown) {
    print('WARNING: dropdown is not defined in updateParentZoneDropdown');
    return;
  }
  
  try {
    var zones = [];
    if (drawing && typeof drawing.getZonesList === 'function') {
      zones = drawing.getZonesList();
    } else {
      print('WARNING: drawing.getZonesList is not a function');
    }
    
    if (typeof dropdown.items === 'function' && typeof dropdown.items().reset === 'function') {
      dropdown.items().reset(zones);
    }
    
    if (typeof dropdown.setPlaceholder === 'function') {
      dropdown.setPlaceholder('None (Main Zone)');
    }
  } catch (e) {
    print('Error in updateParentZoneDropdown: ' + e.message);
  }
}

// Display analysis results
function displayAnalysisResults(panel, results) {
  panel.clear();
  
  // Zone info
  var zoneInfoPanel = ui.Panel({
    style: {padding: '0 0 10px 0', border: '0 0 1px 0 solid #ddd'}
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
    style: {padding: '10px 0', borderBottom: '1px solid #ddd'}
  });
  
  buildingsPanel.add(ui.Label({
    value: 'Buildings',
    style: {fontWeight: 'bold'}
  }));
  
  buildingsPanel.add(ui.Label('Total Buildings: ' + results.buildings.total));
  
  // Add building counts by type
  Object.keys(results.buildings.byType).forEach(function(type) {
    var count = results.buildings.byType[type];
    var label = config.BUILDING_CLASSES[type].label;
    buildingsPanel.add(ui.Label(label + ': ' + count));
  });
  
  panel.add(buildingsPanel);
  
  // Population summary
  var populationPanel = ui.Panel({
    style: {padding: '10px 0', borderBottom: '1px solid #ddd'}
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
    style: {padding: '10px 0', borderBottom: '1px solid #ddd'}
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
    var label = config.BUILDING_CLASSES[type].label;
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
  
  // Show/hide buildings button
  var showBuildingsButton = ui.Button({
    label: 'Show Building Classification',
    onClick: function() {
      var showing = showBuildingsButton.getLabel() === 'Show Building Classification';
      showBuildingsButton.setLabel(showing ? 'Hide Building Classification' : 'Show Building Classification');
      analysis.toggleBuildingsDisplay(results.zoneName, showing);
    }
  });
  panel.add(showBuildingsButton);
}

// Alert function - expose it for other modules to use
exports.alert = alert;
// Safe alert function that works even if ui is undefined
function alert(message) {
  // Always print to console for logging
  print("ALERT MESSAGE:", message);
  
  // IMPORTANT: In Earth Engine, just use console logging for alerts
  // Don't try to use UI components for alerts
  // This approach ensures messages are always visible and won't cause errors
  
  // Add visually distinct markers to make alerts stand out in the console
  print("⚠️ ==================================== ⚠️");
  print("⚠️              ALERT                  ⚠️");
  print("⚠️ ==================================== ⚠️");
  
  // Don't try to use UI components for alerts as they may not be available
  // or may behave differently in Earth Engine environments
  
  // If you absolutely must try to show a UI alert, uncomment this section:
  /*
  // Check if ui exists at all before trying to use it
  if (typeof ui === 'undefined') {
    print("UI is not defined, cannot show alert dialog");
    return;
  }
  
  // Try the simplest possible alert if available
  try {
    if (typeof ui.alert === 'function') {
      ui.alert(message);
      return;
    } else {
      print("ui.alert is not a function");
    }
  } catch(e) {
    print("Error using ui.alert:", e);
  }
  */
}
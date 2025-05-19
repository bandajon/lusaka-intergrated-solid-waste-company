// Configuration parameters for the application

// Geographic constants
exports.LUSAKA_CENTER = [28.2816, -15.3875]; // Longitude, Latitude for central Lusaka
exports.DEFAULT_ZOOM = 11; // Zoomed out to show greater Lusaka area
exports.REGION_BOUNDARY = ee.Geometry.Polygon([
  // Expanded boundary to include Lusaka and surrounding areas (Chongwe, Chilanga, Chibombo)
  [27.9500, -15.7000], // Southwest
  [28.6500, -15.7000], // Southeast
  [28.6500, -15.1000], // Northeast
  [27.9500, -15.1000]  // Northwest
]); // Greater Lusaka area including surrounding districts

// Data sources
exports.BUILDINGS_DATASET = 'GOOGLE/Research/open-buildings/v3/polygons';
exports.POPULATION_DATASET = 'WorldPop/GP/100m/pop';
exports.WORLDCOVER_DATASET = 'ESA/WorldCover/v100'; // ESA WorldCover (urban class includes roads)
exports.LAND_COVER = 'COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019'; // Copernicus Global Land Cover
exports.ADMIN_BOUNDARIES = 'FAO/GAUL/2015/level2'; // Admin level 2 boundaries (districts)

// Print for debugging
print("Loading config datasources");

// Building classification thresholds (sq meters)
exports.BUILDING_CLASSES = {
  RESIDENTIAL_PERI_URBAN: { max: 50, label: 'Residential Peri-Urban' },
  RESIDENTIAL_URBAN: { min: 50, max: 150, label: 'Residential Urban' },
  COMMERCIAL_SMALL: { min: 150, max: 300, label: 'Commercial Small' },
  COMMERCIAL_MEDIUM: { min: 300, max: 1000, label: 'Commercial Medium' },
  COMMERCIAL_LARGE: { min: 1000, label: 'Commercial Large' }
};

// Pricing tiers (Kwacha/month)
exports.PRICING = {
  RESIDENTIAL_PERI_URBAN: 30,
  RESIDENTIAL_URBAN: 40,
  COMMERCIAL_SMALL: 100,
  COMMERCIAL_MEDIUM: 250,
  COMMERCIAL_LARGE: 500
};

// Waste generation parameters
exports.WASTE_GENERATION = {
  // kg per person/business per day
  RESIDENTIAL_PER_PERSON: 0.5,
  COMMERCIAL_SMALL: 5,
  COMMERCIAL_MEDIUM: 20,
  COMMERCIAL_LARGE: 50,
  // Cost in Kwacha per ton
  DISPOSAL_COST: 100
};

// UI constants
exports.PANEL_WIDTH = '350px';
exports.COLORS = {
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
};

// Common districts in the study area
exports.DISTRICTS = [
  {name: 'Lusaka', center: [28.2816, -15.3875], zoom: 12},
  {name: 'Chongwe', center: [28.6820, -15.3278], zoom: 12},
  {name: 'Chilanga', center: [28.2790, -15.5621], zoom: 12},
  {name: 'Kafue', center: [28.1814, -15.7607], zoom: 12},
  {name: 'Chibombo', center: [28.0731, -14.6543], zoom: 11}
];

// Operational expenses (simplified model)
exports.EXPENSES = {
  FIXED_MONTHLY: 5000, // Base monthly expenses
  PER_TON_COLLECTION: 200 // Cost per ton to collect waste
};

// Export configuration
exports.EXPORT_OPTIONS = {
  FORMATS: ['CSV', 'GeoJSON', 'KML'],
  DEFAULT_FORMAT: 'GeoJSON'
};
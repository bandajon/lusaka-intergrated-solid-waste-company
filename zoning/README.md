# Lusaka Integrated Waste Management Zone Planning Tool

An interactive Google Earth Engine application for waste management zone planning across Lusaka, Zambia and surrounding areas (including parts of Chongwe, Chilanga, and Chibombo). This tool allows users to draw custom waste collection zones, analyze building and population data, and calculate waste management metrics including revenue potential and profitability.

## Features

- Draw polygonal zones on a map of Lusaka and surrounding areas
- Create sub-zones within larger zones
- Classify buildings as residential (urban/peri-urban) or commercial (small/medium/large)
- Calculate waste generation based on population and building counts
- Calculate revenue potential based on different pricing tiers
- Provide financial analysis including revenue, expenses, and profitability
- Name, save, and export zones

## Data Sources

- Google Open Buildings v3 (GOOGLE/Research/open-buildings/v3/polygons)
- WorldPop population data (WorldPop/GP/100m/pop)
- OSM roads (projects/sat-io/open-datasets/OSM/osm_features)
- ESA WorldCover for land cover (ESA/WorldCover/v100)

## Building Classification Logic

Buildings are classified based on footprint area:
- <50 sq meters: Residential Peri-Urban
- 50-150 sq meters: Residential Urban
- 150-300 sq meters: Commercial Small
- 300-1000 sq meters: Commercial Medium
- >1000 sq meters: Commercial Large

## Waste Generation Parameters

- Residential: 0.5 kg/person/day
- Commercial Small: 5 kg/business/day
- Commercial Medium: 20 kg/business/day
- Commercial Large: 50 kg/business/day
- Disposal cost: 100 Kwacha/ton

## Pricing Tiers

- Residential Urban: 40 Kwacha/month
- Residential Peri-Urban: 30 Kwacha/month
- Commercial Small: 100 Kwacha/month
- Commercial Medium: 250 Kwacha/month
- Commercial Large: 500 Kwacha/month

## User Workflow

1. View welcome screen with instructions
2. Start drawing a zone anywhere in the Greater Lusaka area
3. System shows natural boundaries (roads, terrain) as drawing guides
4. After completing a zone, name and configure it
5. System analyzes buildings and population within the zone
6. System presents waste generation and financial metrics
7. Create sub-zones or edit existing zones
8. Export data for external use

## Technical Implementation

This application is built as a modular Google Earth Engine application using:
- Google Earth Engine JavaScript API
- Earth Engine's UI components
- Earth Engine's geospatial analysis capabilities

The codebase is organized into modules:
- `index.js`: Main application entry point
- `modules/config.js`: Configuration parameters
- `modules/map.js`: Map and layer handling
- `modules/ui.js`: User interface components
- `modules/drawing.js`: Zone drawing and management
- `modules/analysis.js`: Geospatial analysis and metrics calculation
- `modules/export.js`: Data export functionality

## Running the Application

1. Open the [Google Earth Engine Code Editor](https://code.earthengine.google.com/)
2. Copy the contents of these files into new files in your Earth Engine project
3. Run the application by executing `index.js`

## Notes

- This tool is designed for planning purposes
- The accuracy of building classification depends on the quality of Google Open Buildings data
- Population estimates are based on WorldPop data and may have limitations in accuracy
- Financial calculations are simplified models and should be validated with local data
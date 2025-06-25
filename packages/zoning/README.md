# Lusaka Garbage Collection Zoning Platform - Updated Architecture with CSV Upload

## Additional Components for CSV Zone Upload

### 1. CSV Upload Module

**File Upload Handler:**
- Secure file upload with validation
- Support for CSV format with lon/lat coordinates
- File size limits and virus scanning
- Temporary storage for processing

**CSV Processing Engine:**
- Pandas-based CSV parsing and validation
- Coordinate system validation (WGS84 expected)
- Polygon/zone boundary creation from point coordinates
- Data cleaning and error detection
- Support for various CSV formats:
  - Simple lon/lat point list
  - Boundary coordinates (polygon vertices)
  - Zone metadata columns

**Geometry Creation:**
- Convert CSV coordinates to PostGIS geometries
- Polygon validation (closed boundaries, no self-intersections)
- Coordinate projection handling
- Area calculation and validation

### 2. Updated Zone Creation Workflows

#### Method 1: Manual Drawing (Existing)
1. User draws zone on Leaflet map
2. Zone geometry captured in real-time
3. Metadata entry and submission

#### Method 2: CSV Upload (New)
1. User selects "Upload CSV Zone" option
2. File upload interface with format instructions
3. CSV validation and preview
4. Geometry preview on map
5. Metadata entry and zone naming
6. Submission for approval

#### Method 3: Hybrid Approach
1. Upload CSV as starting point
2. Edit/refine boundaries using map tools
3. Combine imported and drawn elements

### 3. Enhanced Database Schema

#### Updated Zones Table
```sql
ALTER TABLE zones ADD COLUMN import_source VARCHAR(50);
ALTER TABLE zones ADD COLUMN import_metadata JSONB;
ALTER TABLE zones ADD COLUMN original_csv_data TEXT;
```

#### New CSVImports Table
```sql
CREATE TABLE csv_imports (
    import_id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    uploaded_by INTEGER REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    rows_processed INTEGER,
    zones_created INTEGER,
    import_status VARCHAR(50),
    error_log TEXT,
    file_path VARCHAR(500)
);
```

### 4. CSV Format Specifications

#### Format 1: Simple Boundary Points
```csv
longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
28.2825,-15.3875
28.2820,-15.3880
28.2816,-15.3875
```

#### Format 2: Zone with Metadata
```csv
longitude,latitude,zone_name,zone_type,description
28.2816,-15.3875,Lusaka_Central_Zone_1,commercial,Main business district
28.2820,-15.3870,Lusaka_Central_Zone_1,commercial,Main business district
...
```

#### Format 3: Multiple Zones in One File
```csv
zone_id,longitude,latitude,zone_name,zone_type
zone_1,28.2816,-15.3875,Residential_A,residential
zone_1,28.2820,-15.3870,Residential_A,residential
zone_2,28.3000,-15.4000,Commercial_B,commercial
zone_2,28.3005,-15.3995,Commercial_B,commercial
```

### 5. Updated API Endpoints

```
POST /api/zones/upload-csv
  - Upload CSV file
  - Returns validation results and preview data

POST /api/zones/create-from-csv
  - Create zones from validated CSV data
  - Includes metadata and geometry

GET /api/zones/csv-templates
  - Download CSV template files

GET /api/imports/{import_id}
  - Get import status and results

GET /api/imports/history
  - List of previous imports by user
```

### 6. Enhanced User Interface

#### CSV Upload Interface
- Drag-and-drop file upload area
- Real-time validation feedback
- Interactive preview map showing imported boundaries
- Format helper with examples
- Error highlighting and correction suggestions

#### Import Management Dashboard
- History of CSV imports
- Import status tracking
- Error logs and resolution guides
- Re-import capabilities for failed uploads

### 7. Validation and Error Handling

#### Coordinate Validation
```python
def validate_coordinates(df):
    """Validate CSV coordinates"""
    errors = []
    
    # Check longitude range (-180 to 180)
    invalid_lon = df[(df['longitude'] < -180) | (df['longitude'] > 180)]
    if not invalid_lon.empty:
        errors.append(f"Invalid longitude values: {invalid_lon.index.tolist()}")
    
    # Check latitude range (-90 to 90)
    invalid_lat = df[(df['latitude'] < -90) | (df['latitude'] > 90)]
    if not invalid_lat.empty:
        errors.append(f"Invalid latitude values: {invalid_lat.index.tolist()}")
    
    # Check for Lusaka region bounds (approximate)
    lusaka_bounds = {
        'min_lon': 27.5, 'max_lon': 29.0,
        'min_lat': -16.0, 'max_lat': -14.5
    }
    
    outside_lusaka = df[
        (df['longitude'] < lusaka_bounds['min_lon']) |
        (df['longitude'] > lusaka_bounds['max_lon']) |
        (df['latitude'] < lusaka_bounds['min_lat']) |
        (df['latitude'] > lusaka_bounds['max_lat'])
    ]
    
    if not outside_lusaka.empty:
        errors.append(f"Coordinates outside Lusaka region: {outside_lusaka.index.tolist()}")
    
    return errors
```

#### Geometry Validation
```python
def create_polygon_from_csv(coordinates):
    """Create and validate polygon from CSV coordinates"""
    from shapely.geometry import Polygon
    
    try:
        # Ensure polygon is closed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        polygon = Polygon(coordinates)
        
        # Validate polygon
        if not polygon.is_valid:
            return None, "Invalid polygon geometry"
        
        if polygon.area == 0:
            return None, "Polygon has zero area"
        
        return polygon, None
        
    except Exception as e:
        return None, f"Error creating polygon: {str(e)}"
```

### 8. Analysis Integration

The uploaded CSV zones will integrate seamlessly with the existing analysis engine:

#### Automated Analysis Post-Upload
```python
def process_csv_zone_upload(csv_data, user_id):
    """Process CSV upload and run initial analysis"""
    
    # 1. Validate and create geometry
    geometry, errors = create_polygon_from_csv(csv_data)
    
    # 2. Create zone record
    zone = create_zone_from_geometry(geometry, user_id)
    
    # 3. Run preliminary analysis
    analysis_results = run_zone_analysis(zone.id)
    
    # 4. Store results
    store_analysis_results(zone.id, analysis_results)
    
    return zone, analysis_results
```

### 9. Enhanced Reporting

#### CSV Import Reports
- Summary of imported zones
- Validation results and warnings
- Analysis results comparison
- Success/failure statistics

#### Batch Analysis Capabilities
- Analyze multiple uploaded zones simultaneously
- Comparative analysis across imported zones
- Bulk export of analysis results

### 10. Updated Claude Code Prompt

```
I need you to help me build a Flask-based web application for garbage collection zone planning in Lusaka, Zambia. The system will allow users to draw zones on a map, upload CSV files with coordinates to create zones, and analyze waste management metrics.

Key requirements:
1. User authentication with role-based access (admin, planner, view-only)
2. Interactive map with Leaflet.js for zone drawing
3. CSV upload functionality for zone creation from longitude/latitude coordinates
4. Support for hierarchical zones (parent zones containing child zones)
5. Integration with Google Earth Engine Python API
6. Implementation of waste management formulas for:
   - Population-based waste generation
   - Building classification and waste estimation
   - Collection frequency calculation
   - Revenue projection
7. Visualization of results with infographics
8. Historical storage of zone plans and CSV imports

CSV Upload Features:
- Support multiple CSV formats (simple coordinates, zones with metadata, multiple zones)
- Real-time validation and preview
- Geometry creation from coordinate points
- Error handling and user feedback
- Integration with existing analysis engine

Technology stack:
- Python 3.9+ with Flask web framework
- PostgreSQL with PostGIS for spatial data
- Leaflet.js for mapping
- D3.js for visualizations
- Earth Engine Python API
- Pandas for CSV processing and data analysis

Please start by creating:
1. Basic Flask application setup
2. Database models for users, zones, and CSV imports
3. Authentication system
4. Map interface with Leaflet.js
5. Zone drawing functionality
6. CSV upload and processing system
7. Zone creation from CSV coordinates

The application should follow modern web development practices and be designed for cloud deployment.
```

## Benefits of CSV Upload Feature

1. **Flexibility**: Users can create zones from various data sources (GPS surveys, GIS exports, field data)
2. **Efficiency**: Bulk zone creation instead of manual drawing
3. **Accuracy**: Precise coordinate input from surveying equipment
4. **Integration**: Easy import from other planning tools and systems
5. **Collaboration**: Teams can share zone data across different platforms
6. **Validation**: Automated checking of coordinate accuracy and geometry validity

This enhancement significantly expands the platform's capabilities while maintaining the core architecture and user experience.
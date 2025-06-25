# Lusaka Waste Management Zoning Platform

A comprehensive Flask-based web application for garbage collection zone planning in Lusaka, Zambia. This system enables urban planners to efficiently manage waste collection zones through interactive mapping, CSV data imports, and advanced analytics.

## Key Features

### 🗺️ Interactive Zone Management
- **Draw zones directly on map** using Leaflet.js
- **Edit existing zones** with real-time updates
- **Hierarchical zone support** for parent-child relationships
- **Multiple zone types**: Residential, Commercial, Industrial, Institutional, Mixed-use, Green spaces

### 📊 CSV Data Import
- **Flexible format support**:
  - Simple coordinate lists
  - Zones with metadata
  - Multiple zones in single file
- **Real-time validation** with error reporting
- **Coordinate validation** ensuring data within Lusaka bounds
- **Batch processing** for efficient zone creation

### 👥 User Management
- **Role-based access control**:
  - Admin: Full system access
  - Planner: Create and edit zones
  - Viewer: Read-only access
- **Secure authentication** with password hashing
- **Activity tracking** and audit logs

### 📈 Waste Analysis Engine
- **Population-based calculations**:
  - 0.5 kg/person/day for residential
  - Scaled rates for commercial/industrial
- **Collection optimization**:
  - Vehicle requirements
  - Collection point placement
  - Route optimization
- **Revenue projections** based on zone types

### 🌍 Earth Engine Integration (Optional)
- Building detection and classification
- Land use analysis
- Vegetation coverage assessment
- Real-time satellite imagery analysis

## Technology Stack

- **Backend**: Python 3.9+, Flask
- **Database**: PostgreSQL with PostGIS
- **Frontend**: Bootstrap 5, Leaflet.js, D3.js
- **Authentication**: Flask-Login with role-based access
- **Data Processing**: Pandas, NumPy, Shapely
- **Spatial Analysis**: GeoAlchemy2, PostGIS

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
flask init-db

# Run application
python run.py
```

Default login credentials:
- Admin: `admin` / `admin123`
- Planner: `planner` / `planner123`
- Viewer: `viewer` / `viewer123`

## API Endpoints

### Zones
- `GET /api/zones` - List all zones with filtering
- `POST /api/zones` - Create new zone
- `GET /api/zones/{id}` - Get zone details
- `PUT /api/zones/{id}` - Update zone
- `DELETE /api/zones/{id}` - Delete zone
- `POST /api/zones/{id}/analyze` - Run waste analysis

### CSV Import
- `POST /api/zones/upload-csv` - Upload and validate CSV
- `GET /api/imports` - Import history
- `GET /api/imports/{id}` - Import details

### Statistics
- `GET /api/stats/dashboard` - Dashboard metrics
- `GET /api/geojson/zones` - All zones as GeoJSON

## CSV Format Examples

### Simple Boundary Points
```csv
longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
28.2825,-15.3875
```

### With Zone Metadata
```csv
longitude,latitude,zone_name,zone_type
28.2816,-15.3875,Lusaka_Central,commercial
28.2820,-15.3870,Lusaka_Central,commercial
```

## Waste Calculation Formulas

### Residential Zones
```
Daily Waste = Population × 0.5 kg/person/day
OR
Daily Waste = Households × 2.5 kg/household/day
```

### Commercial Zones
```
Small Business: 10 kg/day
Medium Business: 50 kg/day
Large Business: 200 kg/day
```

### Collection Requirements
```
Collection Points = Waste per Collection / 1000 kg
Vehicles Required = Waste / (5000 kg × 0.85 efficiency)
Staff Required = (Vehicles × 2) + Supervisors
```

## Security Features

- CSRF protection on all forms
- SQL injection prevention via ORM
- XSS protection with template escaping
- Secure password hashing (bcrypt)
- Session management with timeout
- File upload validation and sanitization

## Performance Optimization

- Database indexing on frequently queried fields
- Pagination for large datasets
- Spatial indexing for geographic queries
- Caching for repeated calculations
- Asynchronous processing for large CSV imports

## Deployment

The application is designed for cloud deployment with support for:
- Environment variable configuration
- PostgreSQL connection pooling
- Gunicorn WSGI server
- Static file serving via CDN
- Horizontal scaling capability

## Contributing

Please ensure all contributions:
1. Include appropriate tests
2. Follow PEP 8 style guidelines
3. Update documentation
4. Pass existing test suite

## License

Proprietary - Lusaka Integrated Solid Waste Management Company

## Support

For technical support or questions, contact the development team.
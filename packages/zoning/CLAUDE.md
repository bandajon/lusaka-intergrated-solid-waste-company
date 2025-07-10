# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application for garbage collection zone planning in Lusaka, Zambia. The system allows users to create waste management zones through interactive map drawing or CSV file uploads, and provides advanced analytics using satellite imagery and AI-powered analysis. This application is part of the LISWMC (Lusaka Integrated Solid Waste Management Company) monorepo.

## Quick Start Commands

```bash
# Quick development setup
./start.sh

# Manual development setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server (SQLite) - Default port 5001
python run_dev.py

# Run development server on specific port
python run_dev.py --port 5002

# Run production server (PostgreSQL) - Default port 5001
python run.py

# Database operations
flask db init
flask db migrate -m "description"
flask db upgrade
flask init-db
flask seed-demo-data
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest test_earth_engine.py

# Run with coverage
pytest --cov=app

# Run specific test function
pytest test_phase6_complete.py::test_comprehensive_analysis

# Run phase-specific tests
pytest test_phase6_complete.py
pytest test_phase7_ui.py
pytest test_real_time_zone_analyzer.py
```

## Technology Stack

- **Backend**: Flask 3.0.0, SQLAlchemy 2.0.23, PostgreSQL with PostGIS
- **Frontend**: Leaflet.js (mapping), Bootstrap (UI), D3.js (visualizations)
- **Spatial**: GeoAlchemy2, Shapely, PostGIS
- **External APIs**: Google Earth Engine, OpenAI, Anthropic Claude
- **Authentication**: Flask-Login with bcrypt
- **File Processing**: Pandas for CSV handling
- **WebSocket**: Flask-SocketIO for real-time updates

## Architecture

### Monorepo Structure
This application is part of a larger monorepo:
- `packages/zoning/`: Zone planning and management (this application)
- `packages/analytics/`: Waste collection analytics and dashboards
- `packages/shared/`: Shared components (database, auth, utilities)

### Application Factory Pattern
The app uses Flask's application factory pattern with blueprints:
- `app/__init__.py`: Application factory and extension initialization
- `config/config.py`: Environment-based configuration classes
- `app/views/`: Route handlers organized by functionality (auth, main, zones, api)
- `app/models/`: Database models with SQLAlchemy

### Database Models
- **User**: Authentication with role-based access (admin, planner, view-only)
- **Zone**: Spatial zones with PostGIS geometry, hierarchical relationships
- **CSVImport**: Import tracking and metadata storage

### Key Modules
- `app/utils/csv_processor.py`: CSV file validation and geometry creation
- `app/utils/earth_engine_analysis.py`: Satellite imagery analysis
- `app/utils/real_time_zone_analyzer.py`: WebSocket-based real-time analytics
- `app/utils/population_estimation.py`: Population density calculations
- `app/utils/websocket_manager.py`: WebSocket connection management
- `app/utils/validation_framework.py`: Data validation and quality checks
- `app/utils/visualization_engine.py`: Chart and visualization generation

## Configuration

### Environment Variables
Key environment variables (set in `.env` file):
- `DATABASE_URL`: PostgreSQL connection string
- `GEE_SERVICE_ACCOUNT`: Google Earth Engine service account
- `OPENAI_API_KEY`: OpenAI API key
- `CLAUDE_API_KEY`: Anthropic Claude API key
- `GOOGLE_MAPS_API_KEY`: Google Maps API key

### Database Configuration
- **Development**: SQLite database in `instance/` directory
- **Production**: PostgreSQL with PostGIS extension
- **Testing**: In-memory SQLite

## CSV Upload System

The application supports multiple CSV formats for zone creation:

### Format 1: Simple Boundary Points
```csv
longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
```

### Format 2: Zone with Metadata
```csv
longitude,latitude,zone_name,zone_type,description
28.2816,-15.3875,Lusaka_Central_Zone_1,commercial,Main business district
```

### CSV Processing Flow
1. File upload with validation (`app/utils/csv_processor.py`)
2. Coordinate validation for Lusaka region bounds
3. Polygon geometry creation using Shapely
4. Zone record creation with metadata
5. Automatic analysis integration

## Spatial Data Handling

### Coordinate System
- **Input**: WGS84 (EPSG:4326) longitude/latitude
- **Storage**: PostGIS geometry columns
- **Validation**: Lusaka region bounds (approximately 27.5-29.0°E, 14.5-16.0°S)

### Geometry Operations
- Polygon creation and validation using Shapely
- Area calculations and centroid determination
- Coordinate projection handling with pyproj
- Parent-child zone relationships

## External API Integration

### Google Earth Engine
- Service account authentication with JSON key file
- Satellite imagery analysis for building detection
- Population density estimation using WorldPop data
- Land use classification algorithms

### AI Analysis
- OpenAI GPT for text analysis and insights
- Anthropic Claude for advanced reasoning
- Integrated analysis caching system

## Real-time Features

### WebSocket Implementation
- Flask-SocketIO for real-time updates
- Zone analysis progress tracking
- Live dashboard updates
- Multi-user collaboration support
- Real-time zone analysis during drawing

### Analytics Engine
- Population-based waste generation calculations
- Collection frequency optimization
- Revenue projections and cost analysis
- Building classification and density mapping
- Google Earth Engine integration for satellite imagery analysis
- AI-powered waste analysis using OpenAI and Anthropic Claude

## File Structure

```
app/
├── models/          # SQLAlchemy database models
├── views/           # Flask blueprints for routes
├── templates/       # Jinja2 HTML templates
├── static/          # CSS, JS, and image assets
├── utils/           # Business logic and analysis modules
└── forms/           # WTForms for input validation

config/
├── config.py        # Environment-based configuration
└── *.json          # Service account credentials

uploads/
├── temp/           # Temporary CSV files
└── processed/      # Processed import files
```

## Development Workflow

1. **Setup**: Use `./start.sh` for quick development environment
2. **Database**: Migrations handled with Flask-Migrate
3. **Testing**: Comprehensive test suite with pytest (40+ specialized test files)
4. **Credentials**: Service account JSON files in `config/` directory
5. **Deployment**: Gunicorn-ready with production configuration
6. **Analytics Integration**: Connects to shared analytics package for data insights

## Common Development Tasks

### Working with Earth Engine
- Service account authentication required
- Credentials stored in `config/earth-engine-service-account.json`
- Test with `pytest test_earth_engine.py`

### Real-time Analysis Testing
- WebSocket functionality: `pytest test_websocket_real_time.py`
- Zone analysis: `pytest test_real_time_zone_analyzer.py`
- Full integration: `pytest test_phase6_complete.py`

### CSV Upload Development
- Test CSV processing: `pytest test_csv_upload_flow.py`
- Debug uploads: `pytest test_csv_upload_debug.py`
- Validation testing: Use sample CSVs in `uploads/temp/`

## Security Considerations

- Role-based access control with Flask-Login
- Input validation using WTForms
- File upload security with type and size restrictions
- Coordinate bounds validation for Lusaka region
- Service account credentials for external APIs

## Default Credentials

Development server default login:
- Username: `admin`
- Password: `admin123`

## Map Configuration

- **Default Center**: Lusaka, Zambia (-15.4166, 28.2833)
- **Default Zoom**: Level 11
- **Bounds**: Lusaka metropolitan area
- **Tile Layer**: OpenStreetMap with Leaflet.js

## Monorepo Integration

### Cross-Package Dependencies
- **Analytics Package**: Located at `../analytics/`
- **Shared Package**: Located at `../shared/`
- **Authentication Bridge**: `analytics_auth_middleware.py` for cross-package auth

### Running Multiple Services
```bash
# Start all services from root
python packages/analytics/start_analytics.py --all

# Start zoning service only
python packages/zoning/run_dev.py

# Start analytics dashboard
python packages/analytics/start_analytics.py --dashboard
```

### Port Configuration
- **Zoning Service**: 5001 (default)
- **Analytics Dashboard**: 5007
- **Analytics Portal**: 5000
- **Flask Data Management**: 5002

### Database Integration
- Development: SQLite (`lusaka_zoning_dev.db`)
- Production: PostgreSQL with PostGIS
- Analytics: Separate database with bridge connections
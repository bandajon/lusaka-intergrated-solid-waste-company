# Lusaka Zoning Platform - Setup Instructions

## Prerequisites

- Python 3.9 or higher
- PostgreSQL with PostGIS extension
- Git

## Installation Steps

### 1. Clone the Repository

```bash
cd /path/to/lusaka-intergrated-solid-waste-management-company/packages/zoning
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL Database

First, ensure PostgreSQL is installed and running. Then create the database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and enable PostGIS
CREATE DATABASE lusaka_zoning;
\c lusaka_zoning
CREATE EXTENSION postgis;
\q
```

### 5. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` and update:
- `DATABASE_URL` with your PostgreSQL connection string
- `SECRET_KEY` with a secure random key
- Other optional settings

### 6. Initialize Database

```bash
flask init-db
```

This will:
- Create all database tables
- Create default users (admin/admin123, planner/planner123, viewer/viewer123)

### 7. (Optional) Seed Demo Data

```bash
flask seed-demo-data
```

This creates sample zones for testing.

### 8. Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Environment Variables for Production

Set these in your production environment:

```bash
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export SECRET_KEY=your-secure-secret-key
export JWT_SECRET_KEY=your-jwt-secret
```

### Database Migrations

For database schema changes:

```bash
flask db init  # First time only
flask db migrate -m "Description of changes"
flask db upgrade
```

## Features Overview

### 1. User Authentication
- Role-based access control (Admin, Planner, View-Only)
- Secure password hashing
- Session management

### 2. Zone Management
- Draw zones on interactive map
- Edit zone properties
- View zone details and analysis

### 3. CSV Upload
- Upload CSV files with coordinates
- Support for multiple formats
- Automatic zone creation
- Validation and error reporting

### 4. Analysis
- Waste generation calculations
- Collection requirements
- Revenue projections
- Population density mapping

### 5. API Endpoints
- RESTful API for zone operations
- GeoJSON export
- Analysis results

## CSV Format Examples

### Simple Format
```csv
longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
28.2825,-15.3875
28.2820,-15.3880
28.2816,-15.3875
```

### With Metadata
```csv
longitude,latitude,zone_name,zone_type,description
28.2816,-15.3875,Central_Zone,commercial,Main business area
28.2820,-15.3870,Central_Zone,commercial,Main business area
...
```

### Multiple Zones
```csv
zone_id,longitude,latitude,zone_name,zone_type
1,28.2816,-15.3875,Zone_A,residential
1,28.2820,-15.3870,Zone_A,residential
2,28.3000,-15.4000,Zone_B,commercial
2,28.3005,-15.3995,Zone_B,commercial
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL format
- Verify PostGIS is installed

### Import Errors
- Check Python version (3.9+)
- Ensure all dependencies installed
- Check for conflicting package versions

### Map Not Loading
- Verify internet connection (for tile layers)
- Check browser console for errors
- Ensure JavaScript is enabled

## Support

For issues or questions:
- Check the logs in the application
- Review error messages
- Contact system administrator
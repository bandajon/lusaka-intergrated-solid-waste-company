# Lusaka Zoning Platform - Quick Start Guide

## 🚀 Quick Start (Development Mode)

### Option 1: Using the start script (Recommended)
```bash
./start.sh
```

### Option 2: Manual start
```bash
# Activate virtual environment
source venv/bin/activate

# Run development server with SQLite
python run_dev.py
```

## 🔑 Default Login Credentials

- **Admin User**: `admin` / `admin123`
- **URL**: http://localhost:5000

## 🎯 Key Features Available

### 1. User Authentication
- ✅ Login/Logout
- ✅ Role-based access control
- ✅ Change password
- ✅ User profile

### 2. Zone Management
- ✅ Draw zones on interactive map
- ✅ Edit zone properties
- ✅ List and filter zones
- ✅ Zone details view

### 3. CSV Upload
- ✅ Upload CSV files with coordinates
- ✅ Support for multiple formats:
  - Simple (lon, lat)
  - With metadata (lon, lat, name, type)
  - Multiple zones (zone_id, lon, lat)
- ✅ Validation and error reporting

### 4. Analysis
- ✅ Waste generation calculations
- ✅ Collection requirements
- ✅ Revenue projections
- ✅ Zone statistics

### 5. API Endpoints
- ✅ RESTful API for all operations
- ✅ GeoJSON export
- ✅ Zone CRUD operations

## 📋 Testing the Application

### 1. Login
Navigate to http://localhost:5000 and login with `admin`/`admin123`

### 2. Create a Zone (Manual)
- Click "Create Zone" from dashboard
- Draw polygon on map
- Fill in zone details
- Save

### 3. Upload CSV
- Click "Upload CSV" from menu
- Select CSV format type
- Upload file with coordinates
- Review created zones

### 4. View Analysis
- Go to Analysis section
- View waste generation metrics
- Check collection requirements

## 🗄️ Database

### Development (SQLite)
The development server uses SQLite for easy setup. The database file is created automatically at `lusaka_zoning_dev.db`.

### Production (PostgreSQL)
For production, install PostgreSQL and PostGIS:

```bash
# Update .env file
DATABASE_URL=postgresql://user:password@localhost:5432/lusaka_zoning

# Initialize PostgreSQL database
flask init-db
```

## 📁 Sample CSV Files

### Simple Format (simple.csv)
```csv
longitude,latitude
28.2816,-15.3875
28.2820,-15.3870
28.2825,-15.3875
28.2820,-15.3880
28.2816,-15.3875
```

### With Metadata (metadata.csv)
```csv
longitude,latitude,zone_name,zone_type,description
28.2816,-15.3875,Central_Business,commercial,Main shopping area
28.2820,-15.3870,Central_Business,commercial,Main shopping area
28.2825,-15.3875,Central_Business,commercial,Main shopping area
28.2820,-15.3880,Central_Business,commercial,Main shopping area
28.2816,-15.3875,Central_Business,commercial,Main shopping area
```

## 🛠️ Common Issues

### Port Already in Use
```bash
# Kill existing Flask process
pkill -f "python run"
```

### Database Issues
```bash
# Reset database
rm lusaka_zoning_dev.db
python run_dev.py
```

### Missing Dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///lusaka_zoning_dev.db
```

### Map Settings
Default center: Lusaka (-15.4166, 28.2833)
Default zoom: 11

## 📊 API Examples

### Get All Zones
```bash
curl -H "Cookie: session=..." http://localhost:5000/api/zones
```

### Create Zone via API
```bash
curl -X POST http://localhost:5000/api/zones \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "name": "Test Zone",
    "code": "TEST001",
    "zone_type": "residential",
    "geometry": {...}
  }'
```

## 🚢 Next Steps

1. **Production Setup**
   - Install PostgreSQL with PostGIS
   - Configure production environment
   - Set up proper secret keys

2. **Advanced Features**
   - Enable Google Earth Engine integration
   - Configure email notifications
   - Set up background task processing

3. **Deployment**
   - Use Gunicorn for production
   - Set up Nginx reverse proxy
   - Configure SSL certificates

## 📞 Support

For issues or questions:
- Check application logs
- Review error messages in browser console
- Refer to main documentation
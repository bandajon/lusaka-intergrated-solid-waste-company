# LISWMC Analytics Quick Start Guide

## 🚀 Unified Startup Script

Use the `start_analytics.py` script for easy access to all analytics components:

```bash
# Show all available options
python start_analytics.py

# Start the Dash analytics dashboard (port 5007)
python start_analytics.py --dashboard

# Start the Flask data management app (port 5001)
python start_analytics.py --flask

# Start both services
python start_analytics.py --both

# Run tests
python start_analytics.py --test
python start_analytics.py --company-test
```

## 📊 Available Services

### Analytics Dashboard (Dash) - Port 5007
- **Purpose**: Real-time waste collection analytics and visualization
- **Features**: 
  - Secure login system
  - Interactive charts and filters
  - Vehicle performance tracking
  - Location-based insights
  - Fee calculation and reporting
- **Access**: http://localhost:5007

### Data Management App (Flask) - Port 5002
- **Purpose**: File upload, data cleaning, and database management
- **Features**:
  - File upload and processing
  - **Company unification tool** (NEW!)
  - License plate cleaning
  - Database import/export
  - Data validation utilities
- **Access**: http://localhost:5002

## 🏢 Company Unification Tool

The new company unification feature helps solve duplicate registration issues:

1. **Access**: http://localhost:5002/companies/unify
2. **Function**: Identifies similar company names (e.g., "LISWMC MATERO" vs "LISWMC MATERO LIMITED")
3. **Process**: 
   - Analyzes all companies in database
   - Groups similar entries with similarity scores
   - Allows you to review and merge duplicates
   - Improves billing accuracy

## 🛠️ Troubleshooting

### Common Issues

**Import Errors**: 
```bash
# Make sure you're in the analytics directory
cd packages/analytics
python start_analytics.py --flask
```

**Port Already in Use**:
```bash
# Kill existing processes
pkill -f "python.*flask"
pkill -f "python.*dash"
```

**Database Connection Issues**:
- Check your `.env` file has correct database credentials
- Test connection: `python start_analytics.py --test`

### Alternative Startup Methods

If the unified script doesn't work, you can still use:

```bash
# Direct Flask app startup
cd flask_app
python run.py

# Direct Dash dashboard startup
python db_dashboard.py

# Using existing shell scripts
./start_both.sh
./run_db_dashboard.sh
```

## 📝 Development Workflow

1. **Start Flask app** for data management tasks
2. **Upload and clean data** using the web interface
3. **Use company unification** to merge duplicates
4. **Switch to analytics dashboard** for reporting
5. **Export results** as needed

This unified approach makes it easier to manage the complete analytics workflow!
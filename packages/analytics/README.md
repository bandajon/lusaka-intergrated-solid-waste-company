# Analytics Dashboard

A comprehensive web-based analytics dashboard for waste management data visualization and reporting.

## Features

### 📊 Real-time Analytics
- **Overview Dashboard**: Key metrics and KPIs
- **Data Analysis**: Advanced charts and trends
- **Location Insights**: Geographic waste collection data
- **Vehicle Performance**: Fleet analytics and optimization

### 💰 Financial Management
- **Tiered Pricing System**: Automated fee calculation
- **Billing Reports**: Company-wise billing analytics
- **Fee Management**: Configurable pricing tiers

### 🔧 Data Management
- **Auto-correction**: Misclassified recycling event detection
- **Data Quality**: Automated data cleaning and validation
- **Export Functionality**: CSV/Excel export with role-based access
- **Real-time Updates**: Live data polling and refresh

## Technology Stack

- **Backend**: Python, Dash, Flask
- **Database**: PostgreSQL with SQLAlchemy
- **Frontend**: Dash/Plotly, TailwindCSS
- **Authentication**: Custom role-based auth system
- **Deployment**: Docker, Render.com

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Required environment variables (see Configuration)

### Installation

1. **Navigate to analytics package**
```bash
cd packages/analytics
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your database and configuration details
```

4. **Run database migrations**
```bash
python ../../scripts/run_migrations.py
```

5. **Start the dashboard**
```bash
python db_dashboard.py
```

The dashboard will be available at `http://localhost:5007`

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DB_HOST=localhost
DB_PORT=5432
DB_NAME=liswmc_db
DB_USER=your_username
DB_PASSWORD=your_password

# Dashboard Configuration
DASH_HOST=0.0.0.0
DASH_PORT=5007
DEBUG=True

# Authentication
SECRET_KEY=your-secret-key-here
```

## Project Structure

```
packages/analytics/
├── db_dashboard.py           # Main dashboard application
├── database_connection.py   # Database utilities
├── auth.py                  # Authentication system
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── wsgi.py                 # WSGI entry point
├── static/                 # Static assets
├── templates/              # HTML templates
├── flask_app/              # Flask components
│   └── dashboards/         # Individual dashboard modules
├── tests/                  # Test files
└── deployments/           # Deployment configurations
```

## Key Components

### Main Dashboard (`db_dashboard.py`)
- Multi-tab interface with Overview, Analysis, Locations, and Data Table views
- Real-time data polling and filtering
- Role-based access control

### Database Management (`database_connection.py`)
- PostgreSQL connection handling
- Query utilities and data loading
- Connection pooling and error handling

### Authentication (`auth.py`) 
- User management and role-based permissions
- Session handling
- Admin/Operator access levels

### Data Processing
- **Auto-correction System**: Detects and corrects misclassified recycling events
- **Location Name Cleaning**: Extracts clean location names from correction messages
- **Net Weight Calculation**: Processes entry/exit weights for accurate reporting

## Features in Detail

### Analytics Tabs

1. **Overview Tab**
   - Total waste collected (metric tons)
   - Number of collection sessions
   - Vehicle utilization metrics
   - Company performance tables

2. **Data Analysis Tab**
   - Day-of-week collection patterns
   - Top 10 vehicles by waste volume
   - Duration vs weight correlation analysis
   - Monthly collection trends

3. **Location Insights Tab**
   - Waste collection by geographical area
   - Location-based trends over time
   - Average load analysis per area

4. **Data Table Tab**
   - Detailed session-by-session data
   - Filtering and search capabilities
   - CSV export functionality (admin only)

### Data Quality Features

- **Recycling Misclassification Detection**: Automatically identifies and corrects recycling events misclassified as normal disposal
- **Progress Tracking**: Real-time progress bars for data correction operations
- **Location Name Extraction**: Clean location names from correction audit messages

## API Endpoints

The analytics package exposes several internal endpoints:

- `/` - Main dashboard interface
- `/health` - Health check endpoint
- `/export` - Data export functionality

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Test files:
- `test_filter_persistence.py` - Filter state management
- `test_deployment.py` - Deployment readiness
- `test_auto_close.py` - Session auto-closure
- `test_db_polling.py` - Database polling

## Deployment

### Docker Deployment

```bash
# Build the image
docker build -t liswmc-analytics .

# Run the container
docker run -p 5007:5007 --env-file .env liswmc-analytics
```

### Render.com Deployment

The package includes `render.yaml` for automatic deployment to Render.com.

## Development

### Adding New Features

1. Create feature branches for new dashboard tabs or analytics
2. Add corresponding tests in the `tests/` directory
3. Update this README with new functionality

### Database Schema

The analytics package works with the following main tables:
- `weigh_events` - Core weighing data
- `vehicles` - Vehicle information
- `companies` - Company details and billing tiers

### Contributing

1. Follow the existing code structure and naming conventions
2. Add tests for new functionality
3. Update documentation for new features
4. Ensure all imports use relative paths within the package

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   pkill -f "python.*db_dashboard.py"
   ```

2. **Database Connection Issues**
   - Verify DATABASE_URL in .env
   - Check PostgreSQL service status
   - Ensure database exists and user has permissions

3. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all dependencies are installed

### Logs

Dashboard logs are written to `dashboard.log` for debugging.

## License

[License information] 
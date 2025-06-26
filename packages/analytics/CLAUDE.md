# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- Install dependencies: `pip install -r requirements.txt`
- Run main analytics dashboard: `python db_dashboard.py` (available at http://localhost:5007)
- Run Flask data management app: `python flask_app/run.py` (available at http://localhost:5001)
- Start both services: `./start_both.sh`
- Run specific dashboards: `./run_db_dashboard.sh`, `./run_weigh_dashboard.sh`

### Testing
- Run all tests: `python -m pytest test_*.py -v`
- Test database connection: `python test_deployment.py`
- Test license plate cleaning: `python test_plate_cleaner.py`
- Test filter persistence: `python test_filter_persistence.py`

### Deployment
- Docker build: `docker build -t liswmc-analytics .`
- Docker run: `docker run -p 5007:5007 --env-file .env liswmc-analytics`
- WSGI server: `gunicorn wsgi:app`

## Architecture

### Multi-Application Structure
This package contains three main applications that work together:

1. **Dash Analytics Dashboard** (`db_dashboard.py`)
   - Real-time waste collection analytics and visualization
   - Multi-tab interface: Overview, Analysis, Locations, Data Table
   - Direct PostgreSQL connectivity with CSV fallback

2. **Flask Data Management App** (`flask_app/`)
   - File upload, CSV processing, data import/export
   - License plate cleaning and standardization
   - Database management utilities

3. **Jupyter Interface** (`database_manager.py`)
   - Interactive database operations and exploration
   - Batch data processing with progress tracking

### Database Architecture
- **Primary Database**: AWS RDS PostgreSQL (`users` database)
- **Connection Management**: Shared components in `/packages/shared/database/`
- **Dual Strategy**: Raw psycopg2 for transactions, SQLAlchemy for DataFrame operations
- **Core Tables**: companies, vehicles, weigh_events, liswmc_users
- **UUID-Based IDs**: New UUIDs generated on import to prevent conflicts

### Authentication System
- bcrypt password hashing with account lockout (5 attempts = 30min lockout)
- Role-based access control with 8-hour session timeout
- User activity logging and security monitoring

## Key Components

### License Plate Processing (`vehicle_plate_cleaner.py`)
- Zambian plate format standardization (GRZ formats, AAA#### patterns)
- Advanced duplicate detection across database and input files
- Rejects invalid plates (numbers-only, special characters)

### Data Import Pipeline
- **Upload → Preview → Clean → Import → Analyze** workflow
- Batch processing with progress tracking and error recovery
- Transaction rollback and retry logic for database failures

### Analytics Features
- Real-time dashboard with interactive filtering
- Location name standardization and correction handling
- CSV and Excel export with browser download (admin only)
- Custom filename support for exports
- Day-of-week patterns, vehicle performance, geographic insights

## Style Guidelines
- Use pandas for data processing and SQLAlchemy for database interactions
- Import order: standard libraries → third-party packages → local modules
- Use snake_case for variables and functions
- Document functions with docstrings describing purpose, parameters, and return values
- Handle database connections with try/except blocks and proper connection closing
- Use consistent 4-space indentation
- Wrap SQLAlchemy transactions in context managers
- For data manipulation, prefer pandas methods over Python loops
- When using regex patterns, document the pattern's purpose

## Environment Variables
Required for database connectivity:
```
DATABASE_URL=postgresql://username:password@host:port/database
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
DASH_HOST=0.0.0.0, DASH_PORT=5007
SECRET_KEY=your-secret-key
```
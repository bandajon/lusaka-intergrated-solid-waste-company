# Shared Components

Common utilities, database connections, and authentication components used across all packages in the LISWMC monorepo.

## Overview

The shared package contains reusable components that multiple packages depend on, ensuring consistency and reducing code duplication across the monorepo.

## Components

### 🗄️ Database (`database/`)
Shared database connection utilities and migrations.

**Contents:**
- `database_connection.py` - PostgreSQL connection utilities
- `migrations/` - Database schema migrations
- `models/` - Shared data models (planned)

### 🔐 Authentication (`auth/`)
Shared authentication and authorization system.

**Contents:**
- `auth.py` - User authentication and role management
- `middleware/` - Auth middleware (planned)
- `decorators/` - Auth decorators (planned)

### 🛠️ Utils (`utils/`)
Common utility functions and helpers.

**Contents:**
- Data validation utilities
- Date/time helpers
- Configuration management
- Logging utilities

## Database Components

### Connection Management

```python
from packages.shared.database.database_connection import get_db_connection

# Get database connection
conn = get_db_connection()
```

### Migration System

Located in `database/migrations/`, these SQL files define the database schema:

```
migrations/
├── 001_create_users_table.sql
├── 002_create_companies_table.sql
├── 003_create_vehicles_table.sql
└── 004_create_weigh_events_table.sql
```

Run migrations:
```bash
python scripts/run_migrations.py
```

## Authentication Components

### User Management

```python
from packages.shared.auth.auth import authenticate_user, get_user_role

# Authenticate user
user = authenticate_user(username, password)

# Check user role
role = get_user_role(user_id)
```

### Role-Based Access Control

Supported roles:
- `admin` - Full system access
- `operator` - Limited operational access
- `viewer` - Read-only access

## Usage in Packages

### Analytics Package

```python
# In packages/analytics/db_dashboard.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database.database_connection import get_db_connection
from auth.auth import require_auth
```

### Zoning Package

```python
# In packages/zoning/src/main.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database.database_connection import get_db_connection
from auth.auth import authenticate_user
```

## Configuration

### Environment Variables

Shared components use these environment variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DB_HOST=localhost
DB_PORT=5432
DB_NAME=liswmc_db
DB_USER=your_username
DB_PASSWORD=your_password

# Authentication
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret
AUTH_TOKEN_EXPIRY=3600
```

## Database Schema

### Core Tables

1. **users** - System users and authentication
2. **companies** - Waste collection companies
3. **vehicles** - Vehicle fleet information
4. **weigh_events** - Core weighing data

### Relationships

```
companies (1) ---> (*) vehicles
vehicles (1) ---> (*) weigh_events
users (1) ---> (*) audit_logs
```

## Development Guidelines

### Adding New Shared Components

1. **Database Models**: Add to `database/models/`
2. **Utilities**: Add to `utils/`
3. **Auth Functions**: Add to `auth/`

### Versioning

Shared components follow semantic versioning:
- Major: Breaking changes requiring package updates
- Minor: New features, backward compatible
- Patch: Bug fixes

### Testing

```bash
# Test shared components
cd packages/shared
python -m pytest tests/ -v
```

## Migration Management

### Creating New Migrations

1. Create SQL file in `database/migrations/`
2. Use sequential numbering: `005_description.sql`
3. Include rollback in `005_rollback_description.sql`

### Migration File Format

```sql
-- 005_add_zones_table.sql
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    boundary GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_zones_name ON zones(name);
```

## Contributing

### Guidelines

1. **Backward Compatibility**: Maintain compatibility across packages
2. **Documentation**: Update README for new components
3. **Testing**: Add tests for new shared functionality
4. **Versioning**: Follow semantic versioning

### Code Standards

```python
# Use consistent imports
from .database_connection import get_db_connection

# Type hints for public functions
def authenticate_user(username: str, password: str) -> Optional[User]:
    pass

# Docstrings for public functions
def get_db_connection():
    """
    Get PostgreSQL database connection.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        DatabaseError: If connection cannot be established
    """
    pass
```

## Dependencies

### Core Dependencies

```
psycopg2-binary>=2.9.0    # PostgreSQL adapter
sqlalchemy>=1.4.0         # ORM
bcrypt>=3.2.0            # Password hashing
pyjwt>=2.0.0             # JWT tokens
```

### Development Dependencies

```
pytest>=6.0.0            # Testing framework
pytest-cov>=2.0.0        # Coverage reporting
black>=21.0.0            # Code formatting
mypy>=0.800              # Type checking
```

## License

[License information] 
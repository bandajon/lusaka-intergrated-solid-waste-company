"""Database compatibility layer for PostgreSQL/SQLite support"""
import os
from sqlalchemy import JSON, String

# Force SQLite mode for development
IS_SQLITE = 'sqlite' in os.environ.get('DATABASE_URL', '').lower()

if IS_SQLITE:
    # SQLite mode - use JSON instead of JSONB
    HAS_POSTGIS = False
    JSONB = JSON
    ARRAY = lambda x: JSON
    Geometry = None
else:
    # PostgreSQL mode
    try:
        from geoalchemy2 import Geometry
        from sqlalchemy.dialects.postgresql import JSONB, ARRAY
        HAS_POSTGIS = True
    except ImportError:
        HAS_POSTGIS = False
        # Fallback if PostGIS not installed
        JSONB = JSON
        ARRAY = lambda x: JSON
        Geometry = None
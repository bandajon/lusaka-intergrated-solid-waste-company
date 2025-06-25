import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables at import time
load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - Fix the instance path doubling issue
    database_url = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/lusaka_zoning'
    
    # Fix SQLite instance path doubling issue
    if database_url.startswith('sqlite:///instance/'):
        # Remove the 'instance/' prefix since Flask adds it automatically
        database_url = database_url.replace('sqlite:///instance/', 'sqlite:///')
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    
    # Authentication
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Google Earth Engine
    GEE_SERVICE_ACCOUNT = os.environ.get('GEE_SERVICE_ACCOUNT', 'agripredict-earth-engine@agripredict-82e4a.iam.gserviceaccount.com')
    GEE_KEY_FILE = os.environ.get('GEE_KEY_FILE', os.path.join(os.path.dirname(__file__), 'earth-engine-service-account.json'))
    
    # External APIs
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
    
    # Map Configuration
    DEFAULT_MAP_CENTER = {
        'lat': float(os.environ.get('DEFAULT_MAP_CENTER_LAT', -15.4166)),
        'lng': float(os.environ.get('DEFAULT_MAP_CENTER_LNG', 28.2833))
    }
    
    # Pagination
    ZONES_PER_PAGE = 20
    
    # Map defaults (Lusaka coordinates)
    DEFAULT_MAP_ZOOM = int(os.environ.get('DEFAULT_MAP_ZOOM', 11))
    
    # CSV Processing
    CSV_TEMP_FOLDER = os.path.join(UPLOAD_FOLDER, 'temp')
    CSV_PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
    
    # Analysis settings
    WASTE_GENERATION_RATE = 0.5  # kg per person per day
    COLLECTION_FREQUENCY_DEFAULT = 2  # times per week


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # Development uses separate database from production
    # Fix SQLite path handling for development
    dev_database_url = os.environ.get('DATABASE_URL') or 'sqlite:///lusaka_zoning_dev.db'
    if dev_database_url.startswith('sqlite:///instance/'):
        # Remove the 'instance/' prefix since Flask adds it automatically
        dev_database_url = dev_database_url.replace('sqlite:///instance/', 'sqlite:///')
    SQLALCHEMY_DATABASE_URI = dev_database_url


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # Production uses PostgreSQL or dedicated production SQLite database
    prod_database_url = os.environ.get('PRODUCTION_DATABASE_URL') or os.environ.get('DATABASE_URL') or 'sqlite:///lusaka_zoning.db'
    if prod_database_url.startswith('sqlite:///instance/'):
        # Remove the 'instance/' prefix since Flask adds it automatically
        prod_database_url = prod_database_url.replace('sqlite:///instance/', 'sqlite:///')
    SQLALCHEMY_DATABASE_URI = prod_database_url


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
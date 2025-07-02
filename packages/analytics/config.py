#!/usr/bin/env python3
"""
Analytics Configuration
-----------------------
Central configuration for analytics services.
"""

import os
from pathlib import Path

class AnalyticsConfig:
    """Configuration for analytics services"""
    
    # Port Configuration
    PORTAL_PORT = int(os.environ.get('PORTAL_PORT', 5003))
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5002))
    DASH_PORT = int(os.environ.get('DASH_PORT', 5007))
    
    # Host Configuration
    PORTAL_HOST = os.environ.get('PORTAL_HOST', '0.0.0.0')
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    DASH_HOST = os.environ.get('DASH_HOST', '0.0.0.0')
    
    # Directory Paths
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = BASE_DIR / 'uploads'
    
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_portal_url(cls):
        """Get the Portal URL"""
        return f"http://localhost:{cls.PORTAL_PORT}"
    
    @classmethod
    def get_flask_url(cls):
        """Get the Flask app URL"""
        return f"http://localhost:{cls.FLASK_PORT}"
    
    @classmethod
    def get_dash_url(cls):
        """Get the Dash dashboard URL"""
        return f"http://localhost:{cls.DASH_PORT}"
    
    @classmethod
    def print_urls(cls):
        """Print service URLs"""
        print("🌐 LISWMC Analytics Services:")
        print(f"   🏠 Portal (Main Entry):  {cls.get_portal_url()}")
        print(f"   📊 Analytics Dashboard: {cls.get_dash_url()}")
        print(f"   🔧 Data Management:     {cls.get_flask_url()}")
        print(f"   🏢 Company Unification: {cls.get_flask_url()}/companies/unify")

# Environment-specific configurations
class DevelopmentConfig(AnalyticsConfig):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(AnalyticsConfig):
    """Production configuration"""
    DEBUG = False
    FLASK_HOST = '127.0.0.1'  # More secure for production
    DASH_HOST = '127.0.0.1'

# Default configuration
Config = DevelopmentConfig
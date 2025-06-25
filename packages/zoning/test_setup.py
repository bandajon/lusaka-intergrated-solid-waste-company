#!/usr/bin/env python
"""Test script to verify the application setup"""

import sys
from app import create_app, db

def test_setup():
    """Test basic application setup"""
    print("Testing Flask application setup...")
    
    try:
        # Create app
        app = create_app('development')
        print("✓ Application created successfully")
        
        # Test database connection
        with app.app_context():
            # Check if we can import models
            from app.models import User, Zone, CSVImport
            print("✓ Models imported successfully")
            
            # Check configuration
            print(f"✓ Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            print(f"✓ Upload folder: {app.config['UPLOAD_FOLDER']}")
            
        print("\nApplication setup is correct!")
        print("\nTo initialize the database, run:")
        print("  flask init-db")
        print("\nTo run the application:")
        print("  python run.py")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_setup()
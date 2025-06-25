#!/usr/bin/env python
"""Development server with SQLite database"""
import os
import sys
from app import create_app, db
from app.models import User, RoleEnum

# Set SQLite for development
os.environ['DATABASE_URL'] = 'sqlite:///lusaka_zoning_dev.db'

app = create_app('development')

def initialize_database():
    """Create tables and default user"""
    with app.app_context():
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create default admin
            admin = User(
                username='admin',
                email='admin@lusakawaste.zm',
                full_name='System Administrator',
                role=RoleEnum.ADMIN
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user: admin/admin123")

if __name__ == '__main__':
    # Check for port argument
    port = 5001
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                print("Invalid port number")
                sys.exit(1)
    
    print("Starting development server with SQLite database...")
    print(f"Access the application at: http://localhost:{port}")
    print("Default login: admin/admin123")
    
    # Initialize database before starting
    initialize_database()
    
    app.run(debug=True, host='0.0.0.0', port=port)
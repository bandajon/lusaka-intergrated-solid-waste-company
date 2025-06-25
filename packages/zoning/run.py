#!/usr/bin/env python
"""
Entry point for the Lusaka Zoning Platform
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app, db, socketio
from app.models import User, Role, RoleEnum, Zone, CSVImport

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Add models to flask shell context"""
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Zone': Zone,
        'CSVImport': CSVImport
    }


@app.cli.command()
def init_db():
    """Initialize the database with tables and default data"""
    db.create_all()
    print("Database tables created.")
    
    # Create default admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@lusakawaste.zm',
            full_name='System Administrator',
            role=RoleEnum.ADMIN
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        
        # Create demo users
        planner = User(
            username='planner',
            email='planner@lusakawaste.zm',
            full_name='Zone Planner',
            role=RoleEnum.PLANNER
        )
        planner.set_password('planner123')
        
        viewer = User(
            username='viewer',
            email='viewer@lusakawaste.zm',
            full_name='View Only User',
            role=RoleEnum.VIEW_ONLY
        )
        viewer.set_password('viewer123')
        
        db.session.add(planner)
        db.session.add(viewer)
        db.session.commit()
        
        print("Default users created:")
        print("  Admin: admin/admin123")
        print("  Planner: planner/planner123")
        print("  Viewer: viewer/viewer123")
    else:
        print("Admin user already exists.")


@app.cli.command()
def seed_demo_data():
    """Seed database with demo zones"""
    from app.models import Zone, ZoneTypeEnum, ZoneStatusEnum
    from shapely.geometry import Polygon
    from geoalchemy2.shape import from_shape
    
    # Demo zone coordinates (simplified polygons around Lusaka)
    demo_zones = [
        {
            'name': 'Lusaka Central Business District',
            'code': 'CBD_001',
            'zone_type': ZoneTypeEnum.COMMERCIAL,
            'coordinates': [
                (28.2833, -15.4167),
                (28.2900, -15.4167),
                (28.2900, -15.4100),
                (28.2833, -15.4100),
                (28.2833, -15.4167)
            ],
            'population': 50000,
            'businesses': 500
        },
        {
            'name': 'Kabulonga Residential',
            'code': 'RES_KAB_001',
            'zone_type': ZoneTypeEnum.RESIDENTIAL,
            'coordinates': [
                (28.3200, -15.4000),
                (28.3300, -15.4000),
                (28.3300, -15.3900),
                (28.3200, -15.3900),
                (28.3200, -15.4000)
            ],
            'population': 15000,
            'households': 3000
        }
    ]
    
    admin = User.query.filter_by(username='admin').first()
    
    for zone_data in demo_zones:
        # Check if zone exists
        if Zone.query.filter_by(code=zone_data['code']).first():
            continue
        
        # Create polygon
        polygon = Polygon(zone_data['coordinates'])
        
        zone = Zone(
            name=zone_data['name'],
            code=zone_data['code'],
            zone_type=zone_data['zone_type'],
            status=ZoneStatusEnum.ACTIVE,
            geometry=from_shape(polygon, srid=4326),
            area_sqm=polygon.area * 111000 * 111000,  # Rough conversion
            perimeter_m=polygon.length * 111000,
            centroid=from_shape(polygon.centroid, srid=4326),
            estimated_population=zone_data.get('population'),
            household_count=zone_data.get('households'),
            business_count=zone_data.get('businesses'),
            created_by=admin.id,
            import_source='seed'
        )
        
        db.session.add(zone)
    
    db.session.commit()
    print(f"Created {len(demo_zones)} demo zones.")


if __name__ == '__main__':
    # Run with SocketIO for WebSocket support
    if socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    else:
        # Fallback to regular Flask server
        app.run(debug=True, host='0.0.0.0', port=5001)
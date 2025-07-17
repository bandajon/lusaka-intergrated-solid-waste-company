from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Zone, User, CSVImport, ZoneAnalysis
from app.utils.population_service import get_population_service

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main dashboard"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get statistics
    total_zones = Zone.query.count()
    active_zones = Zone.query.filter_by(status='active').count()
    total_area = db.session.query(func.sum(Zone.area_sqm)).scalar() or 0
    
    # Prioritize Earth Engine data over database sum
    saved_population = db.session.query(func.sum(Zone.estimated_population)).scalar() or 0
    
    # Use Earth Engine service for consistent population data
    population_service = get_population_service()
    
    if saved_population == 0 and total_area > 0:
        if population_service.available:
            # For dashboard display, we could aggregate Earth Engine calls for all zones
            # For now, show that Earth Engine is preferred
            total_population = saved_population  # Will be 0, indicating need for Earth Engine data
            print("Dashboard: Earth Engine available but no zones have population data yet")
        else:
            # Only use minimal fallback when Earth Engine completely unavailable
            fallback = population_service.get_minimal_fallback_estimate(total_area)
            total_population = fallback['estimated_population'] 
            print(f"Dashboard using minimal fallback: {total_population} (Earth Engine unavailable)")
    else:
        total_population = saved_population
    
    # Recent zones
    recent_zones = Zone.query.order_by(Zone.created_at.desc()).limit(5).all()
    
    # Recent imports
    recent_imports = CSVImport.query.order_by(CSVImport.uploaded_at.desc()).limit(5).all()
    
    # Get all zones for map display and serialize them
    zones = Zone.query.all()
    zones_data = []
    for zone in zones:
        zones_data.append({
            'id': zone.id,
            'name': zone.name,
            'zone_type': zone.zone_type.value if zone.zone_type else None,
            'status': zone.status.value if zone.status else None,
            'area_sqm': zone.area_sqm,
            'estimated_population': zone.estimated_population,
            'geometry': zone.geometry
        })
    
    return render_template('main/dashboard.html',
                         total_zones=total_zones,
                         active_zones=active_zones,
                         total_area=total_area,
                         total_population=total_population,
                         recent_zones=recent_zones,
                         recent_imports=recent_imports,
                         zones=zones_data,
                         config=current_app.config)


@main_bp.route('/analysis')
@login_required
def analysis():
    """Analysis dashboard"""
    # Get aggregated analysis data
    zones = Zone.query.filter_by(status='active').all()
    
    # Waste generation by zone type
    waste_by_type = db.session.query(
        Zone.zone_type,
        func.sum(Zone.waste_generation_kg_day)
    ).group_by(Zone.zone_type).all()
    
    # Population density map data
    zone_data = []
    for zone in zones:
        if zone.geometry and zone.estimated_population and zone.area_sqm:
            zone_data.append({
                'id': zone.id,
                'name': zone.name,
                'population_density': zone.estimated_population / (zone.area_sqm / 1000000),
                'waste_generation': zone.waste_generation_kg_day,
                'geojson': zone.geojson
            })
    
    return render_template('main/analysis.html',
                         zones=zones,
                         waste_by_type=waste_by_type,
                         zone_data=zone_data)


@main_bp.route('/users')
@login_required
def users():
    """User management (admin only)"""
    if not current_user.has_role('ADMIN'):
        return redirect(url_for('main.index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('main/users.html', users=users)


@main_bp.route('/imports')
@login_required
def imports():
    """CSV import history"""
    if not current_user.has_role('ADMIN'):
        # Non-admins can only see their own imports
        imports = CSVImport.query.filter_by(uploaded_by=current_user.id)\
                                .order_by(CSVImport.uploaded_at.desc()).all()
    else:
        imports = CSVImport.query.order_by(CSVImport.uploaded_at.desc()).all()
    
    return render_template('main/imports.html', imports=imports)


@main_bp.route('/settings')
@login_required
def settings():
    """System settings (admin only)"""
    if not current_user.has_role('ADMIN'):
        return redirect(url_for('main.index'))
    
    return render_template('main/settings.html')


@main_bp.route('/health')
def health():
    """Health check endpoint for Docker containers"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check basic application status
        status = {
            'status': 'healthy',
            'service': 'zoning-service',
            'version': '1.0.0',
            'timestamp': current_app.config.get('CURRENT_TIME', 'unknown')
        }
        
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'zoning-service',
            'error': str(e)
        }), 503
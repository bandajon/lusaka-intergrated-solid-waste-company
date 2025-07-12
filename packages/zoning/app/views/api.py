from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import func
import json
from app import db
from app.models import Zone, ZoneAnalysis, CSVImport, User
from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType

api_bp = Blueprint('api', __name__)


# Schemas for API responses
class ZoneSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    code = fields.Str()
    zone_type = fields.Str()
    status = fields.Str()
    area_sqm = fields.Float()
    estimated_population = fields.Int()
    waste_generation_kg_day = fields.Float()
    created_at = fields.DateTime()
    geojson = fields.Method('get_geojson')
    
    def get_geojson(self, obj):
        return obj.geojson


class ImportSchema(Schema):
    id = fields.Int()
    filename = fields.Str()
    uploaded_at = fields.DateTime()
    status = fields.Str()
    rows_total = fields.Int()
    zones_created = fields.Int()
    success_rate = fields.Float()


# API Routes
@api_bp.route('/zones', methods=['GET'])
@login_required
def get_zones():
    """Get all zones with optional filtering"""
    # Query parameters
    zone_type = request.args.get('type')
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Build query
    query = Zone.query
    
    if zone_type:
        query = query.filter_by(zone_type=zone_type)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            db.or_(
                Zone.name.ilike(f'%{search}%'),
                Zone.code.ilike(f'%{search}%')
            )
        )
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    zones = pagination.items
    
    # Serialize
    zone_schema = ZoneSchema(many=True)
    
    return jsonify({
        'zones': zone_schema.dump(zones),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/zones/<int:zone_id>', methods=['GET'])
@login_required
def get_zone(zone_id):
    """Get single zone details"""
    zone = Zone.query.get_or_404(zone_id)
    zone_schema = ZoneSchema()
    
    return jsonify(zone_schema.dump(zone))


@api_bp.route('/zones', methods=['POST'])
@login_required
def create_zone():
    """Create new zone from GeoJSON"""
    if not current_user.can_edit_zones():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'code', 'zone_type', 'geometry']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    
    try:
        from shapely.geometry import shape, mapping
        
        # Create geometry
        geom = shape(data['geometry'])
        if not geom.is_valid:
            return jsonify({'error': 'Invalid geometry'}), 400
        
        # Create zone
        zone = Zone(
            name=data['name'],
            code=data['code'],
            zone_type=data['zone_type'],
            status=data.get('status', 'draft'),
            geometry=mapping(geom),
            area_sqm=geom.area,
            perimeter_m=geom.length,
            centroid=mapping(geom.centroid),
            created_by=current_user.id,
            import_source='api',
            estimated_population=data.get('estimated_population'),
            household_count=data.get('household_count'),
            business_count=data.get('business_count')
        )
        
        db.session.add(zone)
        db.session.commit()
        
        zone_schema = ZoneSchema()
        return jsonify(zone_schema.dump(zone)), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/zones/<int:zone_id>', methods=['PUT'])
@login_required
def update_zone(zone_id):
    """Update zone"""
    if not current_user.can_edit_zones():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    zone = Zone.query.get_or_404(zone_id)
    data = request.get_json()
    
    # Update fields
    for field in ['name', 'description', 'zone_type', 'status',
                  'estimated_population', 'household_count', 'business_count']:
        if field in data:
            setattr(zone, field, data[field])
    
    zone.modified_by = current_user.id
    db.session.commit()
    
    zone_schema = ZoneSchema()
    return jsonify(zone_schema.dump(zone))


@api_bp.route('/zones/<int:zone_id>', methods=['DELETE'])
@login_required
def delete_zone(zone_id):
    """Delete zone"""
    if not current_user.can_delete_zones():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    zone = Zone.query.get_or_404(zone_id)
    db.session.delete(zone)
    db.session.commit()
    
    return jsonify({'message': 'Zone deleted successfully'})


@api_bp.route('/zones/<int:zone_id>/analyze', methods=['POST'])
@login_required
def analyze_zone(zone_id):
    """Run analysis on zone"""
    zone = Zone.query.get_or_404(zone_id)
    
    # Run analysis using unified analyzer
    analyzer = UnifiedAnalyzer()
    
    # Create analysis request
    analysis_request = AnalysisRequest(
        analysis_type=AnalysisType.COMPREHENSIVE,
        geometry=zone.geometry,
        zone_id=str(zone.id),
        zone_name=zone.name,
        zone_type=zone.zone_type.value if zone.zone_type else None,
        options={
            'include_population': True,
            'include_buildings': True,
            'include_waste': True,
            'include_validation': True
        }
    )
    
    # Run analysis
    results = analyzer.analyze(analysis_request)
    
    # Update zone with analysis results
    zone.estimated_population = results.population_estimate or 0
    zone.household_count = results.household_estimate or 0
    zone.waste_generation_kg_day = results.waste_generation_kg_per_day or 0
    
    # Store analysis results
    analysis = ZoneAnalysis(
        zone_id=zone.id,
        total_waste_generation_kg_day=results.waste_generation_kg_per_day or 0,
        residential_waste_kg_day=(results.waste_generation_kg_per_day or 0) * 0.7,  # Estimate 70% residential
        commercial_waste_kg_day=(results.waste_generation_kg_per_day or 0) * 0.3,  # Estimate 30% commercial
        collection_points_required=results.collection_requirements.get('collection_points', 1) if results.collection_requirements else 1,
        collection_vehicles_required=results.collection_requirements.get('vehicles_required', 1) if results.collection_requirements else 1,
        projected_monthly_revenue=results.collection_requirements.get('monthly_revenue', 0) if results.collection_requirements else 0,
        created_by=current_user.id
    )
    
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify({
        'analysis_id': analysis.id,
        'results': results.to_dict()
    })


@api_bp.route('/imports', methods=['GET'])
@login_required
def get_imports():
    """Get import history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = CSVImport.query
    
    # Non-admins see only their imports
    if not current_user.has_role('ADMIN'):
        query = query.filter_by(uploaded_by=current_user.id)
    
    pagination = query.order_by(CSVImport.uploaded_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    import_schema = ImportSchema(many=True)
    
    return jsonify({
        'imports': import_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/imports/<int:import_id>', methods=['GET'])
@login_required
def get_import(import_id):
    """Get import details"""
    csv_import = CSVImport.query.get_or_404(import_id)
    
    # Check permissions
    if not current_user.has_role('ADMIN') and csv_import.uploaded_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(csv_import.to_dict())


@api_bp.route('/stats/dashboard', methods=['GET'])
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_zones': Zone.query.count(),
        'active_zones': Zone.query.filter_by(status='active').count(),
        'total_area_km2': db.session.query(func.sum(Zone.area_sqm)).scalar() or 0 / 1000000,
        'total_population': db.session.query(func.sum(Zone.estimated_population)).scalar() or 0,
        'total_waste_kg_day': db.session.query(func.sum(Zone.waste_generation_kg_day)).scalar() or 0,
        'zones_by_type': {}
    }
    
    # Zones by type
    type_counts = db.session.query(
        Zone.zone_type, func.count(Zone.id)
    ).group_by(Zone.zone_type).all()
    
    for zone_type, count in type_counts:
        if zone_type:
            stats['zones_by_type'][zone_type.value] = count
    
    return jsonify(stats)


@api_bp.route('/geojson/zones', methods=['GET'])
@login_required
def zones_geojson():
    """Get all zones as GeoJSON FeatureCollection"""
    zones = Zone.query.filter_by(status='active').all()
    
    features = []
    for zone in zones:
        if zone.geometry:
            features.append(zone.geojson)
    
    return jsonify({
        'type': 'FeatureCollection',
        'features': features
    })
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import Zone, ZoneTypeEnum, ZoneStatusEnum, ZoneAnalysis
from app.forms.zone import ZoneForm, CSVUploadForm
from app.utils.csv_processor import CSVProcessor
from app.utils.real_time_zone_analyzer import RealTimeZoneAnalyzer
import json

zones_bp = Blueprint('zones', __name__)


@zones_bp.route('/')
@login_required
def list():
    """List all zones"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    zone_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Zone.query
    
    if search:
        query = query.filter(
            db.or_(
                Zone.name.ilike(f'%{search}%'),
                Zone.code.ilike(f'%{search}%')
            )
        )
    
    if zone_type:
        query = query.filter_by(zone_type=zone_type)
    
    if status:
        query = query.filter_by(status=status)
    
    zones = query.order_by(Zone.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('zones/list.html', zones=zones)


@zones_bp.route('/map')
@login_required
def map_view():
    """Interactive map view of all zones"""
    zones = Zone.query.all()  # Show all zones regardless of status
    zone_geojson = {
        'type': 'FeatureCollection',
        'features': [zone.geojson for zone in zones if zone.geometry]
    }
    
    return render_template('zones/map.html', 
                         zone_geojson=zone_geojson,
                         center=current_app.config['DEFAULT_MAP_CENTER'],
                         zoom=current_app.config['DEFAULT_MAP_ZOOM'])


@zones_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new zone by drawing on map"""
    if not current_user.can_edit_zones():
        flash('You do not have permission to create zones.', 'danger')
        return redirect(url_for('zones.list'))
    
    form = ZoneForm()
    
    if form.validate_on_submit():
        # Process the drawn geometry from hidden field
        geometry_data = request.form.get('geometry')
        
        if not geometry_data:
            flash('No zone geometry provided. Please draw a zone on the map.', 'warning')
            # Get existing zones for display
            existing_zones = Zone.query.all()
            existing_zones_data = []
            for zone in existing_zones:
                if zone.geometry:
                    existing_zones_data.append({
                        'id': zone.id,
                        'name': zone.name,
                        'zone_type': zone.zone_type.value if zone.zone_type else None,
                        'status': zone.status.value if zone.status else None,
                        'geometry': zone.geometry
                    })
            return render_template('zones/create.html', 
                                 form=form,
                                 center=current_app.config['DEFAULT_MAP_CENTER'],
                                 zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                                 existing_zones=existing_zones_data)
        
        # Create zone from form data
        zone = Zone(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            zone_type=ZoneTypeEnum(form.zone_type.data),
            status=ZoneStatusEnum(form.status.data),
            estimated_population=form.estimated_population.data,
            household_count=form.household_count.data,
            business_count=form.business_count.data,
            collection_frequency_week=form.collection_frequency_week.data,
            created_by=current_user.id,
            import_source='manual'
        )
        
        # Process geometry
        try:
            import json
            from shapely.geometry import shape, mapping
            from shapely.ops import transform
            import pyproj
            
            geom_json = json.loads(geometry_data)
            
            # Validate geometry structure
            if not geom_json or 'type' not in geom_json or 'coordinates' not in geom_json:
                raise ValueError("Invalid geometry structure: missing type or coordinates")
            
            if geom_json['type'] != 'Polygon':
                raise ValueError(f"Expected Polygon geometry, got {geom_json['type']}")
            
            if not geom_json['coordinates'] or not geom_json['coordinates'][0] or len(geom_json['coordinates'][0]) < 4:
                raise ValueError("Polygon must have at least 4 coordinate points")
            
            # Create shapely polygon
            polygon = shape(geom_json)
            
            if not polygon.is_valid:
                # Try to fix invalid geometry
                polygon = polygon.buffer(0)
                if not polygon.is_valid:
                    raise ValueError("Cannot create valid polygon from provided coordinates")
            
            # For SQLite, store geometry as GeoJSON
            zone.geometry = mapping(polygon)
            
            # Convert to UTM for accurate area/perimeter calculation
            # Lusaka is in UTM Zone 35S
            wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (lat/lng)
            utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S
            
            # Transform to UTM for area calculation
            transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
            utm_polygon = transform(transformer.transform, polygon)
            
            print(f"Original polygon bounds: {polygon.bounds}")
            print(f"UTM polygon bounds: {utm_polygon.bounds}")
            print(f"UTM polygon area: {utm_polygon.area}")
            print(f"UTM polygon length: {utm_polygon.length}")
            
            # Calculate area and perimeter in meters
            zone.area_sqm = utm_polygon.area
            zone.perimeter_m = utm_polygon.length
            
            print(f"Final zone area_sqm: {zone.area_sqm}")
            print(f"Final zone perimeter_m: {zone.perimeter_m}")
            
            # Store centroid as GeoJSON point
            centroid = polygon.centroid
            zone.centroid = mapping(centroid)
            
            # Estimate population if not provided
            if not zone.estimated_population and zone.area_sqm > 0:
                pop_result = _estimate_population_for_zone(zone)
                if isinstance(pop_result, dict):
                    zone.estimated_population = pop_result.get('estimated_population', 0)
                    # Store additional population estimation data in metadata
                    if not zone.zone_metadata:
                        zone.zone_metadata = {}
                    zone.zone_metadata['population_estimation'] = {
                        'methods_used': pop_result.get('methods_used', []),
                        'confidence': pop_result.get('confidence', 'low'),
                        'earth_engine_population': pop_result.get('earth_engine_population', 0),
                        'building_based_population': pop_result.get('building_based_population', 0),
                        'comparison': pop_result.get('comparison', {}),
                        'primary_method': pop_result.get('primary_method', 'unknown')
                    }
                else:
                    zone.estimated_population = pop_result
            
        except Exception as e:
            flash(f'Error processing zone geometry: {str(e)}', 'danger')
            # Get existing zones for display
            existing_zones = Zone.query.all()
            existing_zones_data = []
            for zone in existing_zones:
                if zone.geometry:
                    existing_zones_data.append({
                        'id': zone.id,
                        'name': zone.name,
                        'zone_type': zone.zone_type.value if zone.zone_type else None,
                        'status': zone.status.value if zone.status else None,
                        'geometry': zone.geometry
                    })
            return render_template('zones/create.html', 
                                 form=form,
                                 center=current_app.config['DEFAULT_MAP_CENTER'],
                                 zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                                 existing_zones=existing_zones_data)
        
        db.session.add(zone)
        db.session.flush()  # Get the zone ID
        
        # Try to retrieve and save any temporary analysis data
        _save_temporary_analysis_to_zone(zone, geometry_data)
        
        db.session.commit()
        
        # Return JSON response for AJAX request
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({
                'success': True,
                'zone_id': zone.id,
                'message': f'Zone "{zone.name}" created successfully!',
                'redirect_url': url_for('zones.view', id=zone.id)
            })
        
        flash(f'Zone "{zone.name}" created successfully!', 'success')
        return redirect(url_for('zones.view', id=zone.id))
    
    # Get existing zones to show on map for reference
    existing_zones = Zone.query.all()
    existing_zones_data = []
    for zone in existing_zones:
        if zone.geometry:
            existing_zones_data.append({
                'id': zone.id,
                'name': zone.name,
                'zone_type': zone.zone_type.value if zone.zone_type else None,
                'status': zone.status.value if zone.status else None,
                'geometry': zone.geometry
            })
    
    return render_template('zones/create.html', 
                         form=form,
                         center=current_app.config['DEFAULT_MAP_CENTER'],
                         zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                         existing_zones=existing_zones_data)


@zones_bp.route('/<int:id>')
@login_required
def view(id):
    """View zone details"""
    zone = Zone.query.get_or_404(id)
    analyses = zone.analyses.order_by(ZoneAnalysis.analysis_date.desc()).limit(5).all()
    
    return render_template('zones/view.html', 
                         zone=zone, 
                         analyses=analyses,
                         center=current_app.config['DEFAULT_MAP_CENTER'],
                         zoom=current_app.config['DEFAULT_MAP_ZOOM'])


@zones_bp.route('/<int:id>/debug')
@login_required
def debug(id):
    """Debug zone map display"""
    zone = Zone.query.get_or_404(id)
    
    # Create debug information
    zone_debug = {
        'id': zone.id,
        'name': zone.name,
        'code': zone.code,
        'has_geometry': bool(zone.geometry),
        'has_centroid': bool(zone.centroid),
        'geometry_type': type(zone.geometry).__name__ if zone.geometry else None,
        'centroid_type': type(zone.centroid).__name__ if zone.centroid else None,
        'area_sqm': zone.area_sqm,
        'geometry': zone.geometry,
        'centroid': zone.centroid
    }
    
    return render_template('zones/debug.html', 
                         zone=zone,
                         zone_debug=zone_debug)


@zones_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit zone - basic metadata only"""
    zone = Zone.query.get_or_404(id)
    
    if not current_user.can_edit_zones():
        flash('You do not have permission to edit zones.', 'danger')
        return redirect(url_for('zones.view', id=id))
    
    form = ZoneForm(obj=zone)
    # Store reference to the zone being edited for validation
    form._obj = zone
    
    if form.validate_on_submit():
        try:
            # Manually handle enum fields since populate_obj doesn't handle them correctly
            zone.name = form.name.data
            zone.code = form.code.data
            zone.description = form.description.data
            
            # Convert string values back to enums
            zone.zone_type = ZoneTypeEnum(form.zone_type.data)
            zone.status = ZoneStatusEnum(form.status.data)
            
            # Handle numeric fields
            zone.estimated_population = form.estimated_population.data
            zone.household_count = form.household_count.data
            zone.business_count = form.business_count.data
            zone.collection_frequency_week = form.collection_frequency_week.data
            
            zone.modified_by = current_user.id
            db.session.commit()
            
            flash(f'Zone "{zone.name}" updated successfully!', 'success')
            return redirect(url_for('zones.view', id=zone.id))
        except Exception as e:
            db.session.rollback()
            print(f"Error updating zone: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error updating zone: {str(e)}', 'danger')
    else:
        # Print validation errors if form doesn't validate
        if request.method == 'POST':
            print(f"Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field.title()}: {error}', 'danger')
    
    return render_template('zones/edit.html', form=form, zone=zone)


@zones_bp.route('/<int:id>/edit-boundaries', methods=['GET', 'POST'])
@login_required
def edit_boundaries(id):
    """Edit zone boundaries on interactive map"""
    zone = Zone.query.get_or_404(id)
    
    if not current_user.can_edit_zones():
        flash('You do not have permission to edit zones.', 'danger')
        return redirect(url_for('zones.view', id=id))
    
    form = ZoneForm(obj=zone)
    
    if form.validate_on_submit():
        # Process the geometry data from the hidden field
        geometry_data = request.form.get('geometry')
        
        if not geometry_data:
            flash('No zone geometry provided. Please draw a zone on the map.', 'warning')
            # Get existing zones for display
            existing_zones = Zone.query.filter(Zone.id != zone.id).all()
            existing_zones_data = []
            for existing_zone in existing_zones:
                if existing_zone.geometry:
                    existing_zones_data.append({
                        'id': existing_zone.id,
                        'name': existing_zone.name,
                        'zone_type': existing_zone.zone_type.value if existing_zone.zone_type else None,
                        'status': existing_zone.status.value if existing_zone.status else None,
                        'geometry': existing_zone.geometry
                    })
            return render_template('zones/edit_boundaries.html', 
                                 form=form,
                                 zone=zone,
                                 center=current_app.config['DEFAULT_MAP_CENTER'],
                                 zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                                 existing_zones=existing_zones_data)
        
        # Update zone form data first
        zone.name = form.name.data
        zone.code = form.code.data
        zone.description = form.description.data
        zone.zone_type = ZoneTypeEnum(form.zone_type.data)
        zone.status = ZoneStatusEnum(form.status.data)
        zone.estimated_population = form.estimated_population.data
        zone.household_count = form.household_count.data
        zone.business_count = form.business_count.data
        zone.collection_frequency_week = form.collection_frequency_week.data
        zone.modified_by = current_user.id
        
        # Process geometry
        try:
            import json
            from shapely.geometry import shape, mapping
            from shapely.ops import transform
            import pyproj
            
            geom_json = json.loads(geometry_data)
            
            # Validate geometry structure
            if not geom_json or 'type' not in geom_json or 'coordinates' not in geom_json:
                raise ValueError("Invalid geometry structure: missing type or coordinates")
            
            if geom_json['type'] != 'Polygon':
                raise ValueError(f"Expected Polygon geometry, got {geom_json['type']}")
            
            if not geom_json['coordinates'] or not geom_json['coordinates'][0] or len(geom_json['coordinates'][0]) < 4:
                raise ValueError("Polygon must have at least 4 coordinate points")
            
            # Create shapely polygon
            polygon = shape(geom_json)
            
            if not polygon.is_valid:
                # Try to fix invalid geometry
                polygon = polygon.buffer(0)
                if not polygon.is_valid:
                    raise ValueError("Cannot create valid polygon from provided coordinates")
            
            # Store geometry as GeoJSON
            zone.geometry = mapping(polygon)
            
            # Convert to UTM for accurate area/perimeter calculation
            wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (lat/lng)
            utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S
            
            # Transform to UTM for area calculation
            transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
            utm_polygon = transform(transformer.transform, polygon)
            
            # Calculate area and perimeter in meters
            zone.area_sqm = utm_polygon.area
            zone.perimeter_m = utm_polygon.length
            
            # Store centroid as GeoJSON point
            centroid = polygon.centroid
            zone.centroid = mapping(centroid)
            
            # Estimate population if not provided
            if not zone.estimated_population and zone.area_sqm > 0:
                pop_result = _estimate_population_for_zone(zone)
                if isinstance(pop_result, dict):
                    zone.estimated_population = pop_result.get('estimated_population', 0)
                    # Store additional population estimation data in metadata
                    if not zone.zone_metadata:
                        zone.zone_metadata = {}
                    zone.zone_metadata['population_estimation'] = {
                        'methods_used': pop_result.get('methods_used', []),
                        'confidence': pop_result.get('confidence', 'low'),
                        'earth_engine_population': pop_result.get('earth_engine_population', 0),
                        'building_based_population': pop_result.get('building_based_population', 0),
                        'comparison': pop_result.get('comparison', {}),
                        'primary_method': pop_result.get('primary_method', 'unknown')
                    }
                else:
                    zone.estimated_population = pop_result
            
            db.session.commit()
            flash(f'Zone "{zone.name}" boundaries updated successfully!', 'success')
            return redirect(url_for('zones.view', id=zone.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing zone geometry: {str(e)}', 'danger')
            # Get existing zones for display
            existing_zones = Zone.query.filter(Zone.id != zone.id).all()
            existing_zones_data = []
            for existing_zone in existing_zones:
                if existing_zone.geometry:
                    existing_zones_data.append({
                        'id': existing_zone.id,
                        'name': existing_zone.name,
                        'zone_type': existing_zone.zone_type.value if existing_zone.zone_type else None,
                        'status': existing_zone.status.value if existing_zone.status else None,
                        'geometry': existing_zone.geometry
                    })
            return render_template('zones/edit_boundaries.html', 
                                 form=form,
                                 zone=zone,
                                 center=current_app.config['DEFAULT_MAP_CENTER'],
                                 zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                                 existing_zones=existing_zones_data)
    
    # GET request - show the edit form
    existing_zones = Zone.query.filter(Zone.id != zone.id).all()
    existing_zones_data = []
    for existing_zone in existing_zones:
        if existing_zone.geometry:
            existing_zones_data.append({
                'id': existing_zone.id,
                'name': existing_zone.name,
                'zone_type': existing_zone.zone_type.value if existing_zone.zone_type else None,
                'status': existing_zone.status.value if existing_zone.status else None,
                'geometry': existing_zone.geometry
            })
    
    return render_template('zones/edit_boundaries.html', 
                         form=form,
                         zone=zone,
                         center=current_app.config['DEFAULT_MAP_CENTER'],
                         zoom=current_app.config['DEFAULT_MAP_ZOOM'],
                         existing_zones=existing_zones_data)


@zones_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete zone"""
    zone = Zone.query.get_or_404(id)
    
    if not current_user.can_delete_zones():
        flash('You do not have permission to delete zones.', 'danger')
        return redirect(url_for('zones.view', id=id))
    
    db.session.delete(zone)
    db.session.commit()
    
    flash(f'Zone "{zone.name}" deleted successfully.', 'success')
    return redirect(url_for('zones.list'))


@zones_bp.route('/upload-csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """Upload CSV to create zones"""
    if not current_user.can_edit_zones():
        flash('You do not have permission to upload CSV files.', 'danger')
        return redirect(url_for('zones.list'))
    
    form = CSVUploadForm()
    
    if form.validate_on_submit():
        file = form.csv_file.data
        filename = secure_filename(file.filename)
        
        # Save file
        upload_path = os.path.join(current_app.config['CSV_TEMP_FOLDER'], filename)
        file.save(upload_path)
        
        # Process CSV
        processor = CSVProcessor()
        result = processor.process_file(
            upload_path,
            user_id=current_user.id,
            csv_format=form.csv_format.data,
            name_prefix=form.name_prefix.data,
            default_zone_type=form.default_zone_type.data
        )
        
        if result['success']:
            flash(f'CSV processed successfully! Created {result["zones_created"]} zones.', 'success')
            return redirect(url_for('zones.list'))
        else:
            flash(f'Error processing CSV: {result["error"]}', 'danger')
            
    return render_template('zones/upload_csv.html', form=form)


@zones_bp.route('/<int:id>/run-analysis')
@login_required
def run_analysis(id):
    """Run analysis for a zone"""
    zone = Zone.query.get_or_404(id)
    
    try:
        from app.utils.analysis import WasteAnalyzer
        
        # Run analysis
        analyzer = WasteAnalyzer()
        results = analyzer.analyze_zone(zone)
        
        # Save analysis results
        zone_analysis = ZoneAnalysis(
            zone_id=zone.id,
            population_density_per_sqkm=results['population_density'],
            total_waste_generation_kg_day=results['total_waste_generation'],
            residential_waste_kg_day=results['residential_waste'],
            commercial_waste_kg_day=results['commercial_waste'],
            collection_points_required=results['collection_points'],
            collection_vehicles_required=results['vehicles_required'],
            projected_monthly_revenue=results['total_revenue'],
            residential_revenue=results['residential_revenue'],
            commercial_revenue=results['commercial_revenue'],
            created_by=current_user.id
        )
        
        db.session.add(zone_analysis)
        db.session.commit()
        
        flash('Analysis completed successfully!', 'success')
    except Exception as e:
        flash(f'Error running analysis: {str(e)}', 'danger')
    
    return redirect(url_for('zones.view', id=zone.id))


@zones_bp.route('/<int:id>/delete-ajax', methods=['POST'])
@login_required
def delete_ajax(id):
    """Delete a zone via AJAX with enhanced error handling"""
    if not current_user.can_delete_zones():
        return jsonify({'error': 'You do not have permission to delete zones'}), 403
    
    zone = Zone.query.get_or_404(id)
    zone_name = zone.name  # Store name before deletion for logging
    zone_code = zone.code
    
    try:
        # Check for any dependencies that might prevent deletion
        from app.models import ZoneAnalysis
        
        # Check if zone has analysis data
        analysis_count = ZoneAnalysis.query.filter_by(zone_id=zone.id).count()
        
        # Log the deletion attempt
        current_app.logger.info(f"User {current_user.username} is deleting zone {zone_name} ({zone_code}) with {analysis_count} analysis records")
        
        # Delete related analysis records first (if any)
        if analysis_count > 0:
            ZoneAnalysis.query.filter_by(zone_id=zone.id).delete()
            current_app.logger.info(f"Deleted {analysis_count} analysis records for zone {zone_name}")
        
        # Delete the zone
        db.session.delete(zone)
        db.session.commit()
        
        current_app.logger.info(f"Successfully deleted zone {zone_name} ({zone_code})")
        return jsonify({
            'success': True, 
            'message': f'Zone "{zone_name}" has been successfully deleted'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_message = f"Failed to delete zone '{zone_name}': {str(e)}"
        current_app.logger.error(error_message)
        return jsonify({'error': error_message}), 500


@zones_bp.route('/api/analyze-zone', methods=['POST'])
def analyze_zone():
    """Real-time analysis of drawn zone using enhanced analyzer"""
    try:
        data = request.get_json()
        if not data or 'geometry' not in data:
            return jsonify({'error': 'Invalid zone data'}), 400
        
        # Initialize the enhanced real-time analyzer
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Get zone metadata if provided
        zone_metadata = data.get('metadata', {})
        
        # Perform comprehensive enhanced analysis
        analysis_results = analyzer.analyze_drawn_zone(data['geometry'], zone_metadata)
        
        # Persist analysis results for session
        _persist_temporary_analysis(data['geometry'], analysis_results, data.get('session_id'))
        
        return jsonify({
            'success': True,
            'analysis': analysis_results,
            'recommendations': analysis_results.get('optimization_recommendations', []),
            'viability_score': analysis_results.get('zone_viability_score', 0),
            'critical_issues': analysis_results.get('critical_issues', []),
            'confidence_assessment': analysis_results.get('confidence_assessment', {}),
            'performance_metrics': analysis_results.get('performance_metrics', {}),
            'cross_validation': analysis_results.get('cross_validation', {}),
            'uncertainty_analysis': analysis_results.get('uncertainty_analysis', {}),
            'enhanced_estimates_mode': analysis_results.get('enhanced_estimates_mode', False),
            'enhanced_components': analysis_results.get('enhanced_components', []),
            'analysis_persisted': True  # Indicate that analysis was saved
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@zones_bp.route('/api/validate-zone-boundary', methods=['POST'])
def validate_zone_boundary():
    """Quick validation of zone boundary without full analysis"""
    try:
        data = request.get_json()
        if not data or 'geometry' not in data:
            return jsonify({'error': 'Invalid zone data'}), 400
        
        # Use enhanced analyzer for better validation
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Quick geometric validation
        geometry_analysis = analyzer._analyze_geometry(data['geometry'])
        
        validation_result = {
            'is_valid': not geometry_analysis.get('error'),
            'area_sqkm': geometry_analysis.get('area_sqkm', 0),
            'compactness_score': geometry_analysis.get('shape_quality', {}).get('compactness_score', 0),
            'size_assessment': geometry_analysis.get('shape_quality', {}).get('size_appropriateness', ''),
            'quick_recommendations': []
        }
        
        # Enhanced recommendations based on geometry
        area = geometry_analysis.get('area_sqkm', 0)
        compactness = geometry_analysis.get('compactness_index', 0)
        aspect_ratio = geometry_analysis.get('aspect_ratio', 1)
        
        if area > 5:
            validation_result['quick_recommendations'].append('Zone is large - consider splitting for better management')
        elif area < 0.1:
            validation_result['quick_recommendations'].append('Zone is small - consider merging with adjacent areas')
        
        if compactness < 0.3:
            validation_result['quick_recommendations'].append('Zone shape is not compact - make it more circular for efficient collection')
        
        if aspect_ratio > 3:
            validation_result['quick_recommendations'].append('Zone is too elongated - consider making it more square-shaped')
        
        # Add enhanced geometry insights
        shape_quality = geometry_analysis.get('shape_quality', {})
        validation_result['shape_insights'] = {
            'compactness_level': shape_quality.get('compactness_level', 'Unknown'),
            'size_category': shape_quality.get('size_category', 'Unknown'),
            'collection_complexity': 'High' if compactness < 0.3 or aspect_ratio > 3 else 'Low'
        }
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@zones_bp.route('/api/dashboard-data', methods=['POST'])
def get_dashboard_data():
    """Get enhanced dashboard data for zone analysis visualization"""
    try:
        data = request.get_json()
        if not data or 'analysis' not in data:
            return jsonify({'error': 'Invalid analysis data'}), 400
        
        # Initialize DashboardCore
        from app.utils.dashboard_core import DashboardCore
        dashboard = DashboardCore()
        
        # Generate dashboard data from analysis results
        analysis_data = data['analysis']
        analysis_modules = analysis_data.get('analysis_modules', {})
        
        # Extract data from analysis modules
        population_module = analysis_modules.get('population_estimation', {})
        waste_module = analysis_modules.get('waste_analysis', {})
        earth_engine_module = analysis_modules.get('earth_engine', {})
        geometry_module = analysis_modules.get('geometry', {})
        
        # Format data for DashboardCore with proper structure
        formatted_data = {
            'zone_id': 'temp_zone',
            'zone_name': 'Drawing Zone',
            'analysis_modules': analysis_modules,
            'geometry_analysis': geometry_module,
            'population_analysis': population_module,
            'waste_analysis': waste_module,
            'earth_engine_analysis': earth_engine_module,
            'collection_feasibility': analysis_modules.get('collection_feasibility', {}),
            'zone_viability_score': analysis_data.get('zone_viability_score', 0),
            'optimization_recommendations': analysis_data.get('optimization_recommendations', []),
            'critical_issues': analysis_data.get('critical_issues', []),
            
            # Add flattened data that DashboardCore expects with best available population source
            'enhanced_population_estimate': _get_best_population_estimate(
                population_module, earth_engine_module, waste_module
            ),
            'buildings_analysis': {
                'building_count': earth_engine_module.get('buildings_data', {}).get('building_count', 0),
                'features': {
                    'building_density': earth_engine_module.get('buildings_data', {}).get('building_density', 0)
                },
                'error': earth_engine_module.get('buildings_data', {}).get('error')
            },
            'total_waste_kg_day': waste_module.get('total_waste_kg_day', 0),
            'population_density_per_km2': population_module.get('density_per_sqkm', 0),
            'collection_points': waste_module.get('optimal_collection_points', 0),
            'vehicles_required': waste_module.get('trucks_required', 0),
            'monthly_revenue': waste_module.get('monthly_revenue_kwacha', 0) * 0.045,  # Convert to USD
            'annual_revenue': waste_module.get('monthly_revenue_kwacha', 0) * 0.045 * 12,
            
            # Add the actual values for real-time display
            'daily_waste': waste_module.get('total_waste_kg_day', 0),
            'trucks_needed': waste_module.get('trucks_required', 0)
        }
        
        # Generate comprehensive dashboard data
        dashboard_data = dashboard.generate_zone_overview_dashboard(formatted_data)
        
        # Add interactive map data
        map_data = dashboard.generate_interactive_map_data(formatted_data)
        
        # Prepare visualization data
        visualizations = {
            'population_heatmap': dashboard.generate_population_heatmap(formatted_data),
            'waste_charts': dashboard.generate_waste_prediction_charts(formatted_data),
            'building_visualization': dashboard.generate_building_detection_visualization(formatted_data)
        }
        
        return jsonify({
            'success': True,
            'dashboard_data': dashboard_data,
            'map_data': map_data,
            'visualizations': visualizations,
            'offline_mode': analysis_data.get('offline_mode', False),
            'enhanced_estimates_mode': analysis_data.get('enhanced_estimates_mode', False)
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard data generation failed: {str(e)}'}), 500


def _get_best_population_estimate(population_module, earth_engine_module, waste_module):
    """Get the best available population estimate from multiple sources"""
    # Try GHSL population first (most reliable for urban areas)
    ghsl_data = earth_engine_module.get('ghsl_population', {})
    if not ghsl_data.get('error') and ghsl_data.get('total_population', 0) > 0:
        return {
            'estimated_population': ghsl_data.get('total_population', 0),
            'confidence': ghsl_data.get('confidence_assessment', {}).get('data_quality', 'medium').title(),
            'error': None,
            'source': 'GHSL'
        }
    
    # Try WorldPop population estimate
    worldpop_data = waste_module.get('population_estimate', {})
    if not worldpop_data.get('error') and worldpop_data.get('estimated_population', 0) > 0:
        return {
            'estimated_population': worldpop_data.get('estimated_population', 0),
            'confidence': worldpop_data.get('confidence', 'Unknown').title(),
            'error': None,
            'source': 'WorldPop'
        }
    
    # Fall back to consensus estimate
    if isinstance(population_module, dict) and population_module.get('consensus_estimate', 0) > 0:
        return {
            'estimated_population': population_module.get('consensus_estimate', 0),
            'confidence': population_module.get('confidence_level', 'Medium').title(),
            'error': population_module.get('error'),
            'source': 'Consensus'
        }
    
    # No population data available
    return {
        'estimated_population': 0,
        'confidence': 'Unknown',
        'error': 'No population data available',
        'source': 'None'
    }


def _estimate_population_for_zone(zone):
    """
    Estimate population for a zone using multiple methods and Earth Engine data
    """
    if not zone.area_sqm or zone.area_sqm <= 0:
        return {
            'estimated_population': 0,
            'methods_used': [],
            'error': 'Invalid zone area'
        }
    
    try:
        from app.utils.population_estimation import PopulationEstimator
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        from app.utils.analysis import WasteAnalyzer
        import pandas as pd
        
        results = {
            'estimated_population': 0,
            'methods_used': [],
            'earth_engine_population': 0,
            'building_based_population': 0,
            'ensemble_population': 0,
            'comparison': {},
            'confidence': 'low'
        }
        
        # Method 1: Earth Engine WorldPop Population Estimate
        try:
            earth_engine = EarthEngineAnalyzer()
            if earth_engine.initialize():
                worldpop_data = earth_engine.get_population_estimate(zone)
                if not worldpop_data.get('error'):
                    results['earth_engine_population'] = worldpop_data.get('estimated_population', 0)
                    results['methods_used'].append('WorldPop_EarthEngine')
                    results['worldpop_data'] = worldpop_data
        except Exception as e:
            print(f"Earth Engine population estimation failed: {e}")
        
        # Method 2: Building-based Population Estimation (if building data exists)
        try:
            analyzer = WasteAnalyzer()
            # Try to get building data for the zone
            buildings_data = analyzer.earth_engine.get_building_footprints(zone) if hasattr(analyzer, 'earth_engine') and analyzer.earth_engine.initialized else None
            
            if buildings_data and not buildings_data.get('error'):
                # Create mock building DataFrame for PopulationEstimator
                building_count = buildings_data.get('building_count', 0)
                if building_count > 0:
                    # Create simplified building data
                    building_df = pd.DataFrame({
                        'id': range(building_count),
                        'area': [100] * building_count,  # Default 100 sqm per building
                        'building_type': ['residential'] * building_count,
                        'settlement_type': [_infer_settlement_type_from_zone_type(zone.zone_type)] * building_count,
                        'height': [4.0] * building_count  # Default single story
                    })
                    
                    # Use sophisticated population estimator
                    pop_estimator = PopulationEstimator(region="lusaka")
                    
                    # Get ensemble estimate
                    ensemble_result = pop_estimator.estimate_population_ensemble(
                        building_df, zone_area_sqm=zone.area_sqm
                    )
                    
                    if ensemble_result:
                        results['building_based_population'] = ensemble_result.get('total_population', 0)
                        results['ensemble_population'] = ensemble_result.get('total_population', 0)
                        results['methods_used'].append('Building_Based_Ensemble')
                        results['ensemble_details'] = ensemble_result
                        
                        # Calculate confidence based on ensemble agreement
                        ensemble_cv = ensemble_result.get('ensemble_cv', 1.0)
                        if ensemble_cv < 0.15:
                            results['confidence'] = 'high'
                        elif ensemble_cv < 0.25:
                            results['confidence'] = 'medium'
                        else:
                            results['confidence'] = 'low'
        
        except Exception as e:
            print(f"Building-based population estimation failed: {e}")
        
        # Method 3: Simple Area-based Fallback
        if not results['methods_used']:
            # Population density estimates per zone type (people per sq km)
            density_estimates = {
                'RESIDENTIAL': 15000,    # High density for informal settlements
                'COMMERCIAL': 2000,      # Lower density - mostly workers
                'INDUSTRIAL': 500,       # Very low density - workers only
                'INSTITUTIONAL': 1000,   # Schools, hospitals etc.
                'MIXED_USE': 8000,      # Medium density
                'GREEN_SPACE': 50,      # Very low - park users only
                'TRANSPORT': 100        # Minimal permanent population
            }
            
            # Convert area to square kilometers
            area_sqkm = zone.area_sqm / 1000000
            
            # Get density for zone type
            zone_type = zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type)
            density_per_sqkm = density_estimates.get(zone_type, 8000)
            
            # Calculate population
            simple_estimate = area_sqkm * density_per_sqkm
            results['simple_area_estimate'] = round(simple_estimate)
            results['methods_used'].append('Simple_Area_Based')
        
        # Choose best estimate and create comparison
        estimates = []
        if results['earth_engine_population'] > 0:
            estimates.append(('WorldPop', results['earth_engine_population']))
        if results['building_based_population'] > 0:
            estimates.append(('Building_Based', results['building_based_population']))
        if results.get('simple_area_estimate', 0) > 0:
            estimates.append(('Area_Based', results['simple_area_estimate']))
        
        if estimates:
            # Use WorldPop if available, otherwise use building-based, fallback to area-based
            if results['earth_engine_population'] > 0:
                results['estimated_population'] = results['earth_engine_population']
                results['primary_method'] = 'WorldPop_EarthEngine'
            elif results['building_based_population'] > 0:
                results['estimated_population'] = results['building_based_population']
                results['primary_method'] = 'Building_Based_Ensemble'
            else:
                results['estimated_population'] = results.get('simple_area_estimate', 0)
                results['primary_method'] = 'Simple_Area_Based'
            
            # Create comparison if multiple estimates exist
            if len(estimates) > 1:
                results['comparison'] = {
                    'estimates': dict(estimates),
                    'max_difference_pct': _calculate_max_difference_percentage(estimates),
                    'agreement_level': _assess_agreement_level(estimates)
                }
        
        return results
        
    except Exception as e:
        # Fallback to simple calculation
        area_sqkm = zone.area_sqm / 1000000
        zone_type = zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type)
        density_per_sqkm = 8000  # Default density
        simple_estimate = area_sqkm * density_per_sqkm
        
        return {
            'estimated_population': round(simple_estimate),
            'methods_used': ['Simple_Fallback'],
            'error': f'Advanced estimation failed: {str(e)}',
            'confidence': 'low'
        }


def _infer_settlement_type_from_zone_type(zone_type):
    """Infer settlement type from zone type"""
    zone_type_str = zone_type.value if hasattr(zone_type, 'value') else str(zone_type)
    
    if zone_type_str in ['RESIDENTIAL', 'MIXED_USE']:
        return 'mixed'
    elif zone_type_str in ['COMMERCIAL', 'INDUSTRIAL']:
        return 'formal'
    else:
        return 'mixed'


def _calculate_max_difference_percentage(estimates):
    """Calculate maximum percentage difference between estimates"""
    if len(estimates) < 2:
        return 0
    
    values = [est[1] for est in estimates]
    max_val = max(values)
    min_val = min(values)
    
    if min_val == 0:
        return 100
    
    return ((max_val - min_val) / min_val) * 100


def _assess_agreement_level(estimates):
    """Assess agreement level between different estimation methods"""
    max_diff_pct = _calculate_max_difference_percentage(estimates)
    
    if max_diff_pct < 15:
        return 'excellent'
    elif max_diff_pct < 30:
        return 'good'
    elif max_diff_pct < 50:
        return 'fair'
    else:
        return 'poor'


def _persist_temporary_analysis(geometry, analysis_results, session_id=None):
    """Persist analysis results for temporary zones during drawing"""
    try:
        import hashlib
        import json
        from datetime import datetime, timedelta
        from flask import session
        from flask_login import current_user
        from app.models.zone import TemporaryZoneAnalysis
        from app import db
        
        # Generate session ID if not provided
        if not session_id:
            session_id = session.get('session_id', session.sid if hasattr(session, 'sid') else str(hash(str(datetime.utcnow()))))
        
        # Generate geometry hash for deduplication
        geometry_str = json.dumps(geometry, sort_keys=True)
        geometry_hash = hashlib.md5(geometry_str.encode()).hexdigest()
        
        # Check if we already have this analysis
        existing = TemporaryZoneAnalysis.query.filter_by(
            session_id=session_id,
            geometry_hash=geometry_hash
        ).first()
        
        if existing:
            # Update existing analysis
            existing.analysis_data = analysis_results
            existing.created_at = datetime.utcnow()
            existing.expires_at = datetime.utcnow() + timedelta(hours=24)
        else:
            # Create new temporary analysis
            temp_analysis = TemporaryZoneAnalysis(
                session_id=session_id,
                geometry_hash=geometry_hash,
                analysis_data=analysis_results,
                estimated_population=analysis_results.get('population_analysis', {}).get('total_population', 0),
                total_waste_kg_day=analysis_results.get('waste_analysis', {}).get('total_waste_generation_kg_day', 0),
                area_sqkm=analysis_results.get('geometry_analysis', {}).get('area_sqkm', 0),
                viability_score=analysis_results.get('zone_viability_score', 0),
                created_by=current_user.id if current_user.is_authenticated else None,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(temp_analysis)
        
        db.session.commit()
        return True
        
    except Exception as e:
        # Log error but don't fail the analysis
        print(f"Warning: Could not persist temporary analysis: {str(e)}")
        return False


def _get_temporary_analysis(session_id, geometry_hash):
    """Retrieve temporary analysis if it exists"""
    try:
        from app.models.zone import TemporaryZoneAnalysis
        
        analysis = TemporaryZoneAnalysis.query.filter_by(
            session_id=session_id,
            geometry_hash=geometry_hash
        ).first()
        
        if analysis and analysis.expires_at > datetime.utcnow():
            return analysis.analysis_data
        return None
        
    except Exception as e:
        print(f"Warning: Could not retrieve temporary analysis: {str(e)}")
        return None


def _save_temporary_analysis_to_zone(zone, geometry_data):
    """Save temporary analysis data to permanent zone analysis"""
    try:
        import hashlib
        import json
        from datetime import datetime
        from flask import session
        from app.models.zone import TemporaryZoneAnalysis, ZoneAnalysis
        from app import db
        
        # Generate geometry hash to find matching temporary analysis
        geometry_str = json.dumps(json.loads(geometry_data), sort_keys=True)
        geometry_hash = hashlib.md5(geometry_str.encode()).hexdigest()
        
        # Try to find temporary analysis for this geometry
        session_id = session.get('session_id', session.sid if hasattr(session, 'sid') else None)
        
        temp_analysis = None
        if session_id:
            temp_analysis = TemporaryZoneAnalysis.query.filter_by(
                session_id=session_id,
                geometry_hash=geometry_hash
            ).first()
        
        if not temp_analysis:
            # Try to find any temporary analysis with this geometry hash (fallback)
            temp_analysis = TemporaryZoneAnalysis.query.filter_by(
                geometry_hash=geometry_hash
            ).order_by(TemporaryZoneAnalysis.created_at.desc()).first()
        
        if temp_analysis and temp_analysis.analysis_data:
            # Create permanent zone analysis from temporary data
            analysis_data = temp_analysis.analysis_data
            
            zone_analysis = ZoneAnalysis(
                zone_id=zone.id,
                analysis_date=datetime.utcnow(),
                # Population analysis
                population_density_per_sqkm=analysis_data.get('population_analysis', {}).get('population_density_per_sqkm', 0),
                household_density_per_sqkm=analysis_data.get('population_analysis', {}).get('household_density_per_sqkm', 0),
                # Waste generation analysis
                total_waste_generation_kg_day=analysis_data.get('waste_analysis', {}).get('total_waste_generation_kg_day', 0),
                residential_waste_kg_day=analysis_data.get('waste_analysis', {}).get('residential_waste_kg_day', 0),
                commercial_waste_kg_day=analysis_data.get('waste_analysis', {}).get('commercial_waste_kg_day', 0),
                industrial_waste_kg_day=analysis_data.get('waste_analysis', {}).get('industrial_waste_kg_day', 0),
                # Collection analysis
                collection_points_required=analysis_data.get('truck_requirements', {}).get('collection_points_required', 0),
                collection_vehicles_required=analysis_data.get('truck_requirements', {}).get('total_trucks_required', 0),
                collection_staff_required=analysis_data.get('truck_requirements', {}).get('total_staff_required', 0),
                optimal_route_distance_km=analysis_data.get('truck_requirements', {}).get('optimal_route_distance_km', 0),
                # Revenue projection
                projected_monthly_revenue=analysis_data.get('financial_analysis', {}).get('projected_monthly_revenue', 0),
                residential_revenue=analysis_data.get('financial_analysis', {}).get('residential_revenue', 0),
                commercial_revenue=analysis_data.get('financial_analysis', {}).get('commercial_revenue', 0),
                industrial_revenue=analysis_data.get('financial_analysis', {}).get('industrial_revenue', 0),
                # Earth Engine analysis results
                building_count=analysis_data.get('earth_engine_analysis', {}).get('building_count', 0),
                vegetation_coverage_percent=analysis_data.get('earth_engine_analysis', {}).get('vegetation_coverage_percent', 0),
                impervious_surface_percent=analysis_data.get('earth_engine_analysis', {}).get('impervious_surface_percent', 0),
                land_use_classification=analysis_data.get('earth_engine_analysis', {}).get('land_use_classification', {}),
                # Analysis metadata
                analysis_parameters=analysis_data.get('analysis_parameters', {}),
                earth_engine_task_id=analysis_data.get('earth_engine_task_id'),
                processing_time_seconds=analysis_data.get('performance_metrics', {}).get('total_processing_time_seconds', 0),
                created_by=zone.created_by
            )
            
            db.session.add(zone_analysis)
            
            # Clean up the temporary analysis
            db.session.delete(temp_analysis)
            
            return True
            
    except Exception as e:
        print(f"Warning: Could not save temporary analysis to zone: {str(e)}")
        return False
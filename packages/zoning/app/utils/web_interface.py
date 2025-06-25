"""
Phase 7: Web Interface Module
Flask-based web interface for interactive waste management analytics dashboard
"""
from flask import Flask, render_template, request, jsonify, send_file
import json
import io
import base64
from datetime import datetime
import logging

from .dashboard_core import DashboardCore
from .visualization_engine import VisualizationEngine
from .map_interface import MapInterface
from ..models.zone import Zone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebInterface:
    """
    Web interface controller for Phase 7 dashboard system
    """
    
    def __init__(self, app=None):
        """Initialize web interface"""
        self.dashboard_core = DashboardCore()
        self.visualization_engine = VisualizationEngine()
        self.map_interface = MapInterface()
        
        if app:
            self.init_app(app)
        
        logger.info("Web interface initialized")
    
    def init_app(self, app):
        """Initialize Flask app with dashboard routes"""
        
        @app.route('/dashboard')
        def dashboard_home():
            """Main dashboard page"""
            return render_template('dashboard/index.html',
                                 title="Lusaka Waste Management Analytics",
                                 page_title="Analytics Dashboard")
        
        @app.route('/dashboard/zone/<int:zone_id>')
        def zone_dashboard(zone_id):
            """Individual zone dashboard"""
            try:
                # Get zone analysis data (this would come from your existing analysis)
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return render_template('dashboard/error.html', 
                                         error=zone_analysis['error'])
                
                # Generate dashboard data
                dashboard_data = self.dashboard_core.generate_zone_overview_dashboard(zone_analysis)
                
                return render_template('dashboard/zone_overview.html',
                                     zone_data=dashboard_data,
                                     zone_id=zone_id,
                                     title=f"Zone {zone_id} Dashboard")
                
            except Exception as e:
                logger.error(f"Zone dashboard error: {str(e)}")
                return render_template('dashboard/error.html', 
                                     error=f"Dashboard error: {str(e)}")
        
        @app.route('/api/dashboard/zone/<int:zone_id>')
        def api_zone_dashboard(zone_id):
            """API endpoint for zone dashboard data"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                dashboard_data = self.dashboard_core.generate_zone_overview_dashboard(zone_analysis)
                return jsonify(dashboard_data)
                
            except Exception as e:
                logger.error(f"API zone dashboard error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/building-detection/<int:zone_id>')
        def api_building_detection(zone_id):
            """API endpoint for building detection visualization"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                building_viz = self.dashboard_core.generate_building_detection_visualization(zone_analysis)
                return jsonify(building_viz)
                
            except Exception as e:
                logger.error(f"Building detection API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/population-heatmap/<int:zone_id>')
        def api_population_heatmap(zone_id):
            """API endpoint for population heatmap data"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                heatmap_data = self.dashboard_core.generate_population_heatmap(zone_analysis)
                return jsonify(heatmap_data)
                
            except Exception as e:
                logger.error(f"Population heatmap API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/waste-predictions/<int:zone_id>')
        def api_waste_predictions(zone_id):
            """API endpoint for waste prediction charts"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                charts_data = self.dashboard_core.generate_waste_prediction_charts(zone_analysis)
                return jsonify(charts_data)
                
            except Exception as e:
                logger.error(f"Waste predictions API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/map-data/<int:zone_id>')
        def api_map_data(zone_id):
            """API endpoint for interactive map data"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                map_data = self.dashboard_core.generate_interactive_map_data(zone_analysis)
                return jsonify(map_data)
                
            except Exception as e:
                logger.error(f"Map data API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/export/<int:zone_id>')
        def api_export_data(zone_id):
            """API endpoint for data export"""
            try:
                export_format = request.args.get('format', 'json').lower()
                
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                dashboard_data = self.dashboard_core.generate_zone_overview_dashboard(zone_analysis)
                export_result = self.dashboard_core.export_dashboard_data(dashboard_data, export_format)
                
                if export_result.get('error'):
                    return jsonify({'error': export_result['error']}), 400
                
                # Create file response
                file_data = io.BytesIO(export_result['data'].encode('utf-8'))
                
                return send_file(
                    file_data,
                    as_attachment=True,
                    download_name=export_result['filename'],
                    mimetype=export_result['content_type']
                )
                
            except Exception as e:
                logger.error(f"Export API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/dashboard/comparison/<int:zone_id>')
        def comparison_dashboard(zone_id):
            """Census comparison dashboard"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                census_data = self._get_census_data(zone_id)  # Optional
                
                if zone_analysis.get('error'):
                    return render_template('dashboard/error.html', 
                                         error=zone_analysis['error'])
                
                comparison_data = self.dashboard_core.generate_census_comparison_dashboard(
                    zone_analysis, census_data
                )
                
                return render_template('dashboard/comparison.html',
                                     comparison_data=comparison_data,
                                     zone_id=zone_id,
                                     title=f"Zone {zone_id} Comparison")
                
            except Exception as e:
                logger.error(f"Comparison dashboard error: {str(e)}")
                return render_template('dashboard/error.html', 
                                     error=f"Comparison dashboard error: {str(e)}")
        
        @app.route('/dashboard/interactive-map/<int:zone_id>')
        def interactive_map(zone_id):
            """Interactive map page"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return render_template('dashboard/error.html', 
                                         error=zone_analysis['error'])
                
                map_data = self.dashboard_core.generate_interactive_map_data(zone_analysis)
                
                return render_template('dashboard/interactive_map.html',
                                     map_data=map_data,
                                     zone_id=zone_id,
                                     title=f"Zone {zone_id} Interactive Map")
                
            except Exception as e:
                logger.error(f"Interactive map error: {str(e)}")
                return render_template('dashboard/error.html', 
                                     error=f"Interactive map error: {str(e)}")
        
        @app.route('/api/chart-image/<chart_type>/<int:zone_id>')
        def api_chart_image(chart_type, zone_id):
            """Generate chart images dynamically"""
            try:
                zone_analysis = self._get_zone_analysis(zone_id)
                
                if zone_analysis.get('error'):
                    return jsonify({'error': zone_analysis['error']}), 400
                
                # Generate chart based on type
                chart_image = self.visualization_engine.generate_chart_image(
                    chart_type, zone_analysis, zone_id
                )
                
                if chart_image.get('error'):
                    return jsonify({'error': chart_image['error']}), 400
                
                # Return base64 encoded image
                return jsonify({
                    'image': chart_image['base64_image'],
                    'format': chart_image['format'],
                    'title': chart_image['title']
                })
                
            except Exception as e:
                logger.error(f"Chart image API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/live-updates/<int:zone_id>')
        def api_live_updates(zone_id):
            """API endpoint for live dashboard updates"""
            try:
                # This would implement real-time updates
                # For now, return current status
                return jsonify({
                    'last_updated': datetime.now().isoformat(),
                    'status': 'active',
                    'zone_id': zone_id,
                    'updates_available': False
                })
                
            except Exception as e:
                logger.error(f"Live updates API error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Add error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('dashboard/404.html'), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return render_template('dashboard/500.html'), 500
    
    def _get_zone_analysis(self, zone_id):
        """Get zone analysis data (placeholder - integrate with existing system)"""
        try:
            # This is a placeholder - in real implementation, this would:
            # 1. Fetch zone from database
            # 2. Run comprehensive analysis using all Phase 1-6 components
            # 3. Return analysis results
            
            # For demonstration, return mock data structure
            mock_analysis = {
                'zone_id': zone_id,
                'zone_name': f'Zone {zone_id}',
                'zone_type': 'residential',
                'area_km2': 2.5,
                'total_waste_kg_day': 1250,
                'residential_waste': 1000,
                'commercial_waste': 200,
                'industrial_waste': 50,
                'monthly_revenue': 3750,
                'annual_revenue': 45000,
                'collection_points': 8,
                'vehicles_required': 2,
                'population_density_per_km2': 4800,
                'enhanced_population_estimate': {
                    'estimated_population': 12000,
                    'confidence': 'High',
                    'settlement_type': 'formal'
                },
                'buildings_analysis': {
                    'building_count': 2400,
                    'features': {
                        'building_density': 960,  # buildings per km2
                        'area_statistics': {
                            'mean': 85  # average building size
                        }
                    }
                },
                'population_estimate': {
                    'total_population': 11800,
                    'population_density_per_sqkm': 4720
                },
                'settlement_classification': {
                    'settlement_type': 'formal',
                    'confidence': 0.85
                },
                'waste_predictions': {
                    'predictions': {
                        'monthly_estimates': [1250, 1275, 1300, 1325, 1350, 1375]
                    }
                },
                'ai_insights': {
                    'priority_actions': [
                        'Optimize collection routes for 15% efficiency gain',
                        'Implement waste separation program',
                        'Increase collection frequency during wet season',
                        'Consider additional collection point in northern area'
                    ]
                }
            }
            
            logger.info(f"Retrieved analysis for zone {zone_id}")
            return mock_analysis
            
        except Exception as e:
            logger.error(f"Error getting zone analysis for zone {zone_id}: {str(e)}")
            return {'error': f'Failed to retrieve zone analysis: {str(e)}'}
    
    def _get_census_data(self, zone_id):
        """Get census data for comparison (optional)"""
        try:
            # Placeholder for census data retrieval
            # In real implementation, this would fetch from census database
            return {
                'population': 11500,
                'households': 2300,
                'data_year': 2022,
                'source': 'Zambia Census Bureau'
            }
        except Exception as e:
            logger.warning(f"Could not retrieve census data for zone {zone_id}: {str(e)}")
            return None
    
    def register_custom_filters(self, app):
        """Register custom Jinja2 filters for templates"""
        
        @app.template_filter('format_number')
        def format_number(value):
            """Format numbers with commas"""
            try:
                return f"{value:,.0f}"
            except (ValueError, TypeError):
                return value
        
        @app.template_filter('format_percentage')
        def format_percentage(value):
            """Format as percentage"""
            try:
                return f"{value:.1f}%"
            except (ValueError, TypeError):
                return value
        
        @app.template_filter('format_currency')
        def format_currency(value):
            """Format as currency"""
            try:
                return f"${value:,.2f}"
            except (ValueError, TypeError):
                return value
        
        @app.template_filter('format_date')
        def format_date(value):
            """Format ISO date string"""
            try:
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M')
                return value
            except (ValueError, TypeError):
                return value


# Convenience function for Flask app integration
def create_web_interface(app):
    """Create and configure web interface for Flask app"""
    web_interface = WebInterface(app)
    web_interface.register_custom_filters(app)
    return web_interface 
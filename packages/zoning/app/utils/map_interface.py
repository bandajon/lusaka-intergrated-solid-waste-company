"""
Phase 7: Map Interface Module
Interactive mapping functionality for waste management analytics dashboard
"""
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapInterface:
    """
    Interactive map interface for visualizing waste management analytics
    """
    
    def __init__(self):
        """Initialize map interface"""
        self.map_config = {
            'default_center': [-15.4166, 28.2833],  # Lusaka, Zambia
            'default_zoom': 12,
            'tile_layers': {
                'OpenStreetMap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'Satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'Terrain': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
            }
        }
        
        logger.info("Map interface initialized")
    
    def generate_zone_map_data(self, zone_analysis_data):
        """Generate comprehensive map data for a zone"""
        try:
            zone_id = zone_analysis_data.get('zone_id', 'Unknown')
            
            map_data = {
                'center': self.map_config['default_center'],
                'zoom': self.map_config['default_zoom'],
                'layers': {
                    'base_layers': self._generate_base_layers(),
                    'data_layers': self._generate_data_layers(zone_analysis_data)
                },
                'controls': {'zoom_control': True, 'layer_control': True},
                'popups': self._generate_popup_templates()
            }
            
            logger.info(f"Generated map data for zone {zone_id}")
            return map_data
            
        except Exception as e:
            logger.error(f"Map data generation failed: {str(e)}")
            return {"error": f"Map data generation failed: {str(e)}"}
    
    def _generate_base_layers(self):
        """Generate base map layer configurations"""
        return {
            'OpenStreetMap': {
                'type': 'tile',
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': '© OpenStreetMap contributors',
                'default': True
            },
            'Satellite': {
                'type': 'tile',
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attribution': '© Esri, DigitalGlobe, GeoEye, Earthstar Geographics',
                'default': False
            }
        }
    
    def _generate_data_layers(self, zone_analysis_data):
        """Generate data layers from analysis results"""
        data_layers = {}
        
        # Zone boundary layer
        data_layers['zone_boundary'] = {
            'type': 'vector',
            'data': {
                'type': 'FeatureCollection',
                'features': [{
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [28.27, -15.41],
                            [28.29, -15.41],
                            [28.29, -15.42],
                            [28.27, -15.42],
                            [28.27, -15.41]
                        ]]
                    },
                    'properties': {
                        'zone_id': zone_analysis_data.get('zone_id', ''),
                        'area_km2': zone_analysis_data.get('area_km2', 0),
                        'population': zone_analysis_data.get('enhanced_population_estimate', {}).get('estimated_population', 0),
                        'daily_waste_kg': zone_analysis_data.get('total_waste_kg_day', 0)
                    }
                }]
            },
            'style': {
                'fillColor': '#2E8B57',
                'fillOpacity': 0.3,
                'color': '#2E8B57',
                'weight': 2
            },
            'visible': True,
            'interactive': True
        }
        
        # Building layer (simplified)
        buildings_analysis = zone_analysis_data.get('buildings_analysis', {})
        if not buildings_analysis.get('error'):
            building_count = buildings_analysis.get('building_count', 0)
            data_layers['buildings'] = {
                'type': 'vector',
                'data': {
                    'type': 'FeatureCollection',
                    'features': self._generate_mock_building_features(building_count)
                },
                'style': {
                    'fillColor': '#4169E1',
                    'fillOpacity': 0.6,
                    'color': '#000000',
                    'weight': 1
                },
                'visible': True,
                'interactive': True
            }
        
        # Collection points layer
        collection_points_count = zone_analysis_data.get('collection_points', 0)
        if collection_points_count > 0:
            data_layers['collection_points'] = {
                'type': 'vector',
                'data': {
                    'type': 'FeatureCollection',
                    'features': self._generate_mock_collection_points(collection_points_count)
                },
                'style': {
                    'fillColor': '#FF6347',
                    'fillOpacity': 0.8,
                    'color': '#000000',
                    'weight': 2,
                    'radius': 8
                },
                'visible': True,
                'interactive': True
            }
        
        return data_layers
    
    def _generate_popup_templates(self):
        """Generate popup templates for different features"""
        return {
            'building_popup': {
                'template': """
                <div class="building-popup">
                    <h4>Building Information</h4>
                    <p><strong>Area:</strong> {{area_sqm}} m²</p>
                    <p><strong>Type:</strong> {{building_type}}</p>
                    <p><strong>Estimated Population:</strong> {{estimated_population}}</p>
                </div>
                """
            },
            'collection_point_popup': {
                'template': """
                <div class="collection-popup">
                    <h4>Collection Point</h4>
                    <p><strong>ID:</strong> CP-{{id}}</p>
                    <p><strong>Capacity:</strong> {{capacity_kg}} kg</p>
                    <p><strong>Service Frequency:</strong> {{frequency}}</p>
                </div>
                """
            },
            'zone_popup': {
                'template': """
                <div class="zone-popup">
                    <h4>Zone {{zone_id}}</h4>
                    <p><strong>Area:</strong> {{area_km2}} km²</p>
                    <p><strong>Population:</strong> {{population:,}}</p>
                    <p><strong>Daily Waste:</strong> {{daily_waste_kg:,}} kg/day</p>
                </div>
                """
            }
        }
    
    def _generate_mock_building_features(self, building_count):
        """Generate mock building features for demonstration"""
        features = []
        
        # Generate a sample of building features (limit to 50 for performance)
        sample_count = min(building_count, 50)
        
        for i in range(sample_count):
            # Random location within zone bounds
            lat = -15.41 - (i % 10) * 0.001
            lng = 28.27 + (i % 10) * 0.001
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [lng, lat],
                        [lng + 0.0001, lat],
                        [lng + 0.0001, lat + 0.0001],
                        [lng, lat + 0.0001],
                        [lng, lat]
                    ]]
                },
                'properties': {
                    'building_id': f'B-{i+1}',
                    'area_sqm': 50 + (i % 150),  # 50-200 sqm
                    'building_type': 'residential' if i % 4 < 3 else 'commercial',
                    'estimated_population': 4 + (i % 4)
                }
            })
        
        return features
    
    def _generate_mock_collection_points(self, collection_points_count):
        """Generate mock collection point features"""
        features = []
        
        for i in range(collection_points_count):
            # Distributed collection points
            lat = -15.41 - (i % 3) * 0.003
            lng = 28.27 + (i % 3) * 0.003
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lng, lat]
                },
                'properties': {
                    'id': i + 1,
                    'capacity_kg': 1000,
                    'frequency': 'Every 2 days'
                }
            })
        
        return features
    
    def export_map_data(self, map_data, export_format='geojson'):
        """Export map data in various formats"""
        try:
            if export_format.lower() == 'geojson':
                # Combine all vector layers into a single GeoJSON
                combined_features = []
                
                data_layers = map_data.get('layers', {}).get('data_layers', {})
                for layer_name, layer_data in data_layers.items():
                    if layer_data.get('type') == 'vector':
                        features = layer_data.get('data', {}).get('features', [])
                        for feature in features:
                            feature['properties']['layer'] = layer_name
                            combined_features.append(feature)
                
                geojson_data = {
                    'type': 'FeatureCollection',
                    'features': combined_features
                }
                
                return {
                    'data': json.dumps(geojson_data, indent=2),
                    'filename': f"map_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                    'content_type': 'application/geo+json'
                }
            
            else:
                return {"error": f"Unsupported export format: {export_format}"}
                
        except Exception as e:
            logger.error(f"Map data export failed: {str(e)}")
            return {"error": f"Map export failed: {str(e)}"} 
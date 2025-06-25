"""
Phase 7: Dashboard Core Module
Comprehensive visualization and dashboard system for Lusaka waste management analytics
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardCore:
    """
    Core dashboard functionality for visualizing waste management analytics
    """
    
    def __init__(self):
        """Initialize dashboard core"""
        self.dashboard_config = {
            'theme': 'lusaka_waste_theme',
            'color_palette': {
                'primary': '#2E8B57',      # Sea Green (waste management)
                'secondary': '#DAA520',    # Goldenrod (population)
                'accent': '#4169E1',       # Royal Blue (buildings)
                'warning': '#FF6347',      # Tomato (alerts)
                'success': '#32CD32',      # Lime Green (success)
                'info': '#20B2AA'          # Light Sea Green (info)
            },
            'map_settings': {
                'center_lat': -15.4166,    # Lusaka center
                'center_lng': 28.2833,
                'default_zoom': 12,
                'tile_layer': 'OpenStreetMap'
            }
        }
        self.visualization_cache = {}
        logger.info("Dashboard core initialized")
    
    def generate_zone_overview_dashboard(self, zone_analysis_data):
        """Generate comprehensive zone overview dashboard data"""
        try:
            zone_id = zone_analysis_data.get('zone_id', 'Unknown')
            zone_name = zone_analysis_data.get('zone_name', 'Unknown Zone')
            
            logger.info(f"Generating overview dashboard for zone {zone_id}: {zone_name}")
            
            dashboard_data = {
                'zone_info': {
                    'id': zone_id,
                    'name': zone_name,
                    'type': zone_analysis_data.get('zone_type', 'Unknown'),
                    'area_km2': zone_analysis_data.get('area_km2', 0),
                    'last_updated': datetime.now().isoformat()
                },
                'key_metrics': self._extract_key_metrics(zone_analysis_data),
                'population_analysis': self._prepare_population_visualization(zone_analysis_data),
                'building_analysis': self._prepare_building_visualization(zone_analysis_data),
                'waste_analysis': self._prepare_waste_visualization(zone_analysis_data),
                'collection_planning': self._prepare_collection_visualization(zone_analysis_data),
                'quality_indicators': self._prepare_quality_indicators(zone_analysis_data),
                'comparison_data': self._prepare_comparison_data(zone_analysis_data),
                'recommendations': self._extract_recommendations(zone_analysis_data)
            }
            
            # Add visualization configurations
            dashboard_data['visualization_config'] = self._generate_visualization_config(dashboard_data)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}")
            return {"error": f"Dashboard generation failed: {str(e)}"}
    
    def generate_building_detection_visualization(self, zone_analysis_data):
        """Generate building detection visualization data"""
        try:
            buildings_analysis = zone_analysis_data.get('buildings_analysis', {})
            
            if buildings_analysis.get('error'):
                return {"error": "Building analysis data not available"}
            
            building_viz = {
                'detection_overview': {
                    'total_buildings': buildings_analysis.get('building_count', 0),
                    'confidence_distribution': self._calculate_confidence_distribution(buildings_analysis),
                    'size_distribution': self._prepare_size_distribution(buildings_analysis),
                    'height_distribution': self._prepare_height_distribution(buildings_analysis)
                },
                'map_layers': {
                    'building_footprints': self._prepare_building_footprints_layer(buildings_analysis),
                    'confidence_heatmap': self._prepare_confidence_heatmap(buildings_analysis),
                    'height_colormap': self._prepare_height_colormap(buildings_analysis),
                    'density_overlay': self._prepare_density_overlay(buildings_analysis)
                },
                'accuracy_metrics': self._prepare_accuracy_metrics(zone_analysis_data),
                'comparison_layers': self._prepare_comparison_layers(zone_analysis_data)
            }
            
            return building_viz
            
        except Exception as e:
            logger.error(f"Building visualization generation failed: {str(e)}")
            return {"error": f"Building visualization failed: {str(e)}"}
    
    def generate_population_heatmap(self, zone_analysis_data):
        """Generate population density heatmap data"""
        try:
            population_data = {}
            
            # WorldPop data
            worldpop_data = zone_analysis_data.get('population_estimate', {})
            if not worldpop_data.get('error'):
                population_data['worldpop'] = {
                    'total_population': worldpop_data.get('total_population', 0),
                    'density_per_sqkm': worldpop_data.get('population_density_per_sqkm', 0),
                    'data_source': 'WorldPop',
                    'confidence': 'High'
                }
            
            # Building-based estimates
            enhanced_population = zone_analysis_data.get('enhanced_population_estimate', {})
            if not enhanced_population.get('error'):
                population_data['building_based'] = {
                    'total_population': enhanced_population.get('estimated_population', 0),
                    'settlement_type': enhanced_population.get('settlement_type', 'Unknown'),
                    'confidence': enhanced_population.get('confidence', 'Medium'),
                    'data_source': 'Building Analysis'
                }
            
            # Enhanced estimates with validation
            worldpop_validation = zone_analysis_data.get('worldpop_validation', {})
            if not worldpop_validation.get('error'):
                enhanced_estimate = worldpop_validation.get('enhanced_estimate', {})
                population_data['enhanced'] = {
                    'total_population': enhanced_estimate.get('estimated_population', 0),
                    'method': enhanced_estimate.get('method', 'Unknown'),
                    'confidence': enhanced_estimate.get('confidence', 'Medium'),
                    'data_source': 'Enhanced (WorldPop + Buildings)'
                }
            
            heatmap_data = {
                'population_estimates': population_data,
                'visualization_layers': self._prepare_population_layers(population_data),
                'density_analysis': self._prepare_density_analysis(population_data, zone_analysis_data),
                'comparison_chart': self._prepare_population_comparison_chart(population_data),
                'settlement_breakdown': self._prepare_settlement_breakdown(zone_analysis_data)
            }
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Population heatmap generation failed: {str(e)}")
            return {"error": f"Population heatmap generation failed: {str(e)}"}
    
    def generate_waste_prediction_charts(self, zone_analysis_data):
        """Generate waste generation prediction charts"""
        try:
            # Extract waste data
            waste_generation = {
                'current': {
                    'total_waste_kg_day': zone_analysis_data.get('total_waste_kg_day', 0),
                    'residential_waste': zone_analysis_data.get('residential_waste', 0),
                    'commercial_waste': zone_analysis_data.get('commercial_waste', 0),
                    'industrial_waste': zone_analysis_data.get('industrial_waste', 0)
                }
            }
            
            # Enhanced waste estimates
            enhanced_waste = zone_analysis_data.get('enhanced_waste_estimate', {})
            if not enhanced_waste.get('error'):
                waste_generation['enhanced'] = enhanced_waste
            
            # AI predictions
            waste_predictions = zone_analysis_data.get('waste_predictions', {})
            if not waste_predictions.get('error'):
                waste_generation['predictions'] = waste_predictions
            
            # Seasonal variations
            seasonal_data = self._generate_seasonal_waste_data(zone_analysis_data)
            
            charts_data = {
                'current_generation': waste_generation,
                'seasonal_patterns': seasonal_data,
                'prediction_timeline': self._generate_prediction_timeline(waste_generation),
                'waste_composition': self._prepare_waste_composition_chart(waste_generation),
                'collection_requirements': self._prepare_collection_requirements_chart(zone_analysis_data),
                'revenue_projections': self._prepare_revenue_projection_chart(zone_analysis_data),
                'efficiency_metrics': self._prepare_efficiency_metrics_chart(zone_analysis_data)
            }
            
            return charts_data
            
        except Exception as e:
            logger.error(f"Waste prediction charts generation failed: {str(e)}")
            return {"error": f"Waste prediction charts generation failed: {str(e)}"}
    
    def generate_census_comparison_dashboard(self, zone_analysis_data, census_data=None):
        """Generate comparison dashboard between estimates and census data"""
        try:
            comparison_data = {
                'data_sources': {
                    'estimated': self._extract_estimated_data(zone_analysis_data),
                    'census': census_data if census_data else {},
                    'comparison_available': bool(census_data)
                },
                'population_comparison': {},
                'accuracy_assessment': {},
                'validation_metrics': {},
                'override_recommendations': []
            }
            
            if census_data:
                # Population comparison
                estimated_pop = self._get_best_population_estimate(zone_analysis_data)
                census_pop = census_data.get('population', 0)
                
                if estimated_pop and census_pop:
                    population_comparison = self._calculate_population_comparison(estimated_pop, census_pop)
                    comparison_data['population_comparison'] = population_comparison
                
                # Accuracy assessment
                comparison_data['accuracy_assessment'] = self._assess_estimation_accuracy(
                    zone_analysis_data, census_data
                )
                
                # Override recommendations
                comparison_data['override_recommendations'] = self._generate_override_recommendations(
                    zone_analysis_data, census_data
                )
            else:
                comparison_data['message'] = "No census data available for comparison"
            
            # Validation metrics from multi-source analysis
            validation_data = zone_analysis_data.get('worldpop_validation', {})
            if not validation_data.get('error'):
                comparison_data['validation_metrics'] = validation_data.get('validation_results', {})
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Census comparison dashboard generation failed: {str(e)}")
            return {"error": f"Census comparison generation failed: {str(e)}"}
    
    def generate_interactive_map_data(self, zone_analysis_data):
        """Generate interactive map visualization data"""
        try:
            map_data = {
                'base_config': self.dashboard_config['map_settings'].copy(),
                'zone_geometry': self._extract_zone_geometry(zone_analysis_data),
                'overlay_layers': {
                    'buildings': self._prepare_buildings_overlay(zone_analysis_data),
                    'population_density': self._prepare_population_overlay(zone_analysis_data),
                    'waste_generation': self._prepare_waste_overlay(zone_analysis_data),
                    'collection_routes': self._prepare_collection_routes_overlay(zone_analysis_data),
                    'settlement_classification': self._prepare_settlement_overlay(zone_analysis_data)
                },
                'interactive_features': {
                    'building_click_info': self._prepare_building_info_popups(zone_analysis_data),
                    'zone_statistics': self._prepare_zone_statistics_popup(zone_analysis_data),
                    'layer_controls': self._prepare_layer_controls(),
                    'legend_data': self._prepare_map_legends()
                },
                'analysis_tools': {
                    'area_measurement': True,
                    'population_query': True,
                    'waste_estimation': True,
                    'route_planning': True
                }
            }
            
            return map_data
            
        except Exception as e:
            logger.error(f"Interactive map data generation failed: {str(e)}")
            return {"error": f"Interactive map generation failed: {str(e)}"}
    
    def export_dashboard_data(self, dashboard_data, export_format='json'):
        """Export dashboard data in various formats"""
        try:
            if export_format.lower() == 'json':
                return {
                    'data': json.dumps(dashboard_data, indent=2, default=str),
                    'filename': f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    'content_type': 'application/json'
                }
            
            elif export_format.lower() == 'csv':
                # Convert key metrics to CSV format
                csv_data = self._convert_to_csv_format(dashboard_data)
                return {
                    'data': csv_data,
                    'filename': f"dashboard_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    'content_type': 'text/csv'
                }
            
            elif export_format.lower() == 'geojson':
                # Extract geographic data
                geojson_data = self._convert_to_geojson_format(dashboard_data)
                return {
                    'data': json.dumps(geojson_data, indent=2),
                    'filename': f"zone_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                    'content_type': 'application/geo+json'
                }
            
            else:
                return {"error": f"Unsupported export format: {export_format}"}
                
        except Exception as e:
            logger.error(f"Dashboard export failed: {str(e)}")
            return {"error": f"Export failed: {str(e)}"}
    
    # Helper methods for data preparation
    def _extract_key_metrics(self, zone_analysis_data):
        """Extract key metrics for dashboard overview"""
        metrics = {}
        
        # Population metrics - extract from multiple sources with fallbacks
        estimated_population = 0
        population_confidence = 'Unknown'
        population_density = 0
        
        # Try multiple population data sources in order of preference
        # 1. Enhanced population estimate (if available)
        enhanced_pop = zone_analysis_data.get('enhanced_population_estimate', {})
        if not enhanced_pop.get('error') and enhanced_pop.get('estimated_population', 0) > 0:
            estimated_population = enhanced_pop.get('estimated_population', 0)
            population_confidence = enhanced_pop.get('confidence', 'Unknown')
        
        # 2. GHSL population data from Earth Engine
        earth_engine_data = zone_analysis_data.get('analysis_modules', {}).get('earth_engine', {})
        ghsl_data = earth_engine_data.get('ghsl_population', {})
        if estimated_population == 0 and not ghsl_data.get('error') and ghsl_data.get('total_population', 0) > 0:
            estimated_population = ghsl_data.get('total_population', 0)
            population_confidence = ghsl_data.get('confidence_assessment', {}).get('data_quality', 'medium').title()
            population_density = ghsl_data.get('population_density_per_sqkm', 0)
        
        # 3. WorldPop population estimate from waste analysis
        waste_analysis = zone_analysis_data.get('analysis_modules', {}).get('waste_analysis', {})
        worldpop_data = waste_analysis.get('population_estimate', {})
        if estimated_population == 0 and not worldpop_data.get('error') and worldpop_data.get('estimated_population', 0) > 0:
            estimated_population = worldpop_data.get('estimated_population', 0)
            population_confidence = worldpop_data.get('confidence', 'Unknown').title()
        
        # 4. Population estimation module
        pop_estimation = zone_analysis_data.get('analysis_modules', {}).get('population_estimation', {})
        if estimated_population == 0 and isinstance(pop_estimation, dict) and pop_estimation.get('consensus_estimate', 0) > 0:
            estimated_population = pop_estimation.get('consensus_estimate', 0)
            population_confidence = pop_estimation.get('confidence_level', 'Unknown').title()
        
        metrics['estimated_population'] = estimated_population
        metrics['population_confidence'] = population_confidence
        metrics['population_density_per_km2'] = population_density or zone_analysis_data.get('population_density_per_km2', 0)
        
        # Building metrics - extract building_count for JavaScript compatibility
        buildings_analysis = zone_analysis_data.get('buildings_analysis', {})
        earth_engine_data = zone_analysis_data.get('analysis_modules', {}).get('earth_engine', {})
        buildings_data = earth_engine_data.get('buildings_data', {})
        
        # Try multiple sources for building count
        building_count = 0
        if not buildings_analysis.get('error'):
            building_count = buildings_analysis.get('building_count', 0)
        elif not buildings_data.get('error'):
            building_count = buildings_data.get('building_count', 0)
            if building_count == 0:
                # Fallback to building footprints count
                building_footprints = buildings_data.get('building_footprints', [])
                building_count = len(building_footprints) if building_footprints else 0
        
        metrics['building_count'] = building_count
        metrics['building_density'] = buildings_analysis.get('features', {}).get('building_density', 0)
        metrics['average_building_size_sqm'] = buildings_analysis.get('features', {}).get('area_statistics', {}).get('mean', 0)
        
        # Waste metrics - flat structure for JavaScript
        metrics['total_waste_kg_day'] = zone_analysis_data.get('total_waste_kg_day', 0)
        metrics['daily_waste'] = zone_analysis_data.get('total_waste_kg_day', 0)  # JavaScript compatibility
        metrics['monthly_waste_kg'] = zone_analysis_data.get('total_waste_kg_day', 0) * 30
        metrics['collection_points'] = zone_analysis_data.get('collection_points', 0)
        metrics['trucks_required'] = zone_analysis_data.get('vehicles_required', 0)
        metrics['trucks_needed'] = zone_analysis_data.get('vehicles_required', 0)  # JavaScript compatibility
        
        # Revenue metrics - flat structure
        metrics['monthly_revenue'] = zone_analysis_data.get('monthly_revenue', 0)
        metrics['annual_revenue'] = zone_analysis_data.get('annual_revenue', 0)
        metrics['revenue_per_capita'] = zone_analysis_data.get('monthly_revenue', 0) / max(1, metrics['estimated_population'])
        
        # Also include nested structure for backward compatibility
        metrics['population'] = {
            'estimated_population': metrics['estimated_population'],
            'confidence': metrics['population_confidence'],
            'density_per_sqkm': metrics['population_density_per_km2']
        }
        
        metrics['buildings'] = {
            'total_buildings': metrics['building_count'],
            'building_density': metrics['building_density'],
            'average_size_sqm': metrics['average_building_size_sqm']
        }
        
        metrics['waste'] = {
            'daily_generation_kg': metrics['total_waste_kg_day'],
            'monthly_generation_kg': metrics['monthly_waste_kg'],
            'collection_points': metrics['collection_points'],
            'vehicles_required': metrics['trucks_required']
        }
        
        metrics['revenue'] = {
            'monthly_revenue': metrics['monthly_revenue'],
            'annual_revenue': metrics['annual_revenue'],
            'revenue_per_capita': metrics['revenue_per_capita']
        }
        
        return metrics
    
    def _prepare_population_visualization(self, zone_analysis_data):
        """Prepare population data for visualization"""
        pop_viz = {}
        
        # WorldPop data
        worldpop_data = zone_analysis_data.get('population_estimate', {})
        if not worldpop_data.get('error'):
            pop_viz['worldpop'] = worldpop_data
        
        # Building-based estimates
        enhanced_pop = zone_analysis_data.get('enhanced_population_estimate', {})
        if not enhanced_pop.get('error'):
            pop_viz['building_based'] = enhanced_pop
        
        # Validation data
        worldpop_validation = zone_analysis_data.get('worldpop_validation', {})
        if not worldpop_validation.get('error'):
            pop_viz['validation'] = worldpop_validation
        
        return pop_viz
    
    def _prepare_building_visualization(self, zone_analysis_data):
        """Prepare building data for visualization"""
        buildings_viz = {}
        
        buildings_analysis = zone_analysis_data.get('buildings_analysis', {})
        if not buildings_analysis.get('error'):
            buildings_viz['detection_results'] = buildings_analysis
            
            # Settlement classification
            settlement_class = zone_analysis_data.get('settlement_classification', {})
            if not settlement_class.get('error'):
                buildings_viz['settlement_classification'] = settlement_class
        
        return buildings_viz
    
    def _prepare_waste_visualization(self, zone_analysis_data):
        """Prepare waste data for visualization"""
        waste_viz = {
            'generation_breakdown': {
                'residential': zone_analysis_data.get('residential_waste', 0),
                'commercial': zone_analysis_data.get('commercial_waste', 0),
                'industrial': zone_analysis_data.get('industrial_waste', 0),
                'total': zone_analysis_data.get('total_waste_kg_day', 0)
            },
            'enhanced_estimates': zone_analysis_data.get('enhanced_waste_estimate', {}),
            'ai_predictions': zone_analysis_data.get('waste_predictions', {}),
            'ai_insights': zone_analysis_data.get('ai_insights', {})
        }
        
        return waste_viz
    
    def _prepare_collection_visualization(self, zone_analysis_data):
        """Prepare collection planning data for visualization"""
        collection_viz = {
            'requirements': {
                'collection_points': zone_analysis_data.get('collection_points', 0),
                'vehicles_required': zone_analysis_data.get('vehicles_required', 0),
                'collection_staff': zone_analysis_data.get('collection_staff', 0),
                'collections_per_month': zone_analysis_data.get('collections_per_month', 0)
            },
            'route_optimization': zone_analysis_data.get('ai_insights', {}).get('optimization_plan', {}),
            'efficiency_metrics': {
                'waste_per_collection_kg': zone_analysis_data.get('waste_per_collection_kg', 0),
                'route_distance_km': zone_analysis_data.get('total_route_distance_km', 0),
                'estimated_time_hours': zone_analysis_data.get('estimated_time_hours', 0)
            }
        }
        
        return collection_viz
    
    def _prepare_quality_indicators(self, zone_analysis_data):
        """Prepare data quality indicators"""
        # Check various data sources
        analysis_modules = zone_analysis_data.get('analysis_modules', {})
        earth_engine_data = analysis_modules.get('earth_engine', {})
        population_data = analysis_modules.get('population_estimation', {})
        waste_data = analysis_modules.get('waste_analysis', {})
        
        # Calculate overall data quality based on available modules
        available_modules = 0
        total_modules = 5  # geometry, population, waste, earth_engine, settlement
        
        if analysis_modules.get('geometry') and not analysis_modules.get('geometry', {}).get('error'):
            available_modules += 1
        if population_data and not population_data.get('error'):
            available_modules += 1
        if waste_data and not waste_data.get('error'):
            available_modules += 1
        if earth_engine_data and not earth_engine_data.get('error'):
            available_modules += 1
        if analysis_modules.get('settlement_classification') and not analysis_modules.get('settlement_classification', {}).get('error'):
            available_modules += 1
        
        overall_quality = available_modules / total_modules
        
        # Population confidence
        population_confidence = 0.5  # Default medium
        if population_data:
            confidence_level = population_data.get('confidence_level', 'Medium')
            if confidence_level == 'High':
                population_confidence = 0.9
            elif confidence_level == 'Medium':
                population_confidence = 0.7
            else:
                population_confidence = 0.4
        
        # Collection feasibility
        collection_feasibility = 0.7  # Default
        feasibility_data = analysis_modules.get('collection_feasibility', {})
        if feasibility_data and not feasibility_data.get('error'):
            overall_score = feasibility_data.get('overall_score', 70)
            collection_feasibility = overall_score / 100
        
        quality_indicators = {
            'overall_quality': overall_quality,
            'population_confidence': population_confidence,
            'collection_feasibility': collection_feasibility,
            'earth_engine_status': 'Available' if earth_engine_data and not earth_engine_data.get('error') else 'Error',
            'ai_analysis_status': 'Available' if not zone_analysis_data.get('ai_analysis_error') else 'Error',
            'building_detection_confidence': 'High' if earth_engine_data.get('buildings_data') else 'Low',
            'population_estimate_confidence': confidence_level if population_data else 'Unknown'
        }
        
        return quality_indicators
    
    def _prepare_comparison_data(self, zone_analysis_data):
        """Prepare data for comparison visualizations"""
        comparison_data = {}
        
        # Population comparison
        pop_estimates = []
        
        worldpop_data = zone_analysis_data.get('population_estimate', {})
        if not worldpop_data.get('error'):
            pop_estimates.append({
                'source': 'WorldPop',
                'value': worldpop_data.get('total_population', 0),
                'confidence': 'High'
            })
        
        enhanced_pop = zone_analysis_data.get('enhanced_population_estimate', {})
        if not enhanced_pop.get('error'):
            pop_estimates.append({
                'source': 'Building-based',
                'value': enhanced_pop.get('estimated_population', 0),
                'confidence': enhanced_pop.get('confidence', 'Medium')
            })
        
        comparison_data['population_estimates'] = pop_estimates
        
        # Waste estimate comparison
        waste_estimates = [
            {
                'source': 'Standard Analysis',
                'value': zone_analysis_data.get('total_waste_kg_day', 0)
            }
        ]
        
        enhanced_waste = zone_analysis_data.get('enhanced_waste_estimate', {})
        if not enhanced_waste.get('error'):
            waste_estimates.append({
                'source': 'Enhanced Analysis',
                'value': enhanced_waste.get('total_waste_kg_day', 0)
            })
        
        comparison_data['waste_estimates'] = waste_estimates
        
        return comparison_data
    
    def _extract_recommendations(self, zone_analysis_data):
        """Extract actionable recommendations"""
        recommendations = []
        
        # AI insights recommendations
        ai_insights = zone_analysis_data.get('ai_insights', {})
        if not ai_insights.get('error'):
            priority_actions = ai_insights.get('priority_actions', [])
            recommendations.extend(priority_actions[:5])  # Top 5 recommendations
        
        # Settlement-specific recommendations
        settlement_recommendations = zone_analysis_data.get('settlement_recommendations', {})
        if isinstance(settlement_recommendations, dict) and not settlement_recommendations.get('error'):
            collection_strategy = settlement_recommendations.get('collection_strategy', '')
            if collection_strategy:
                recommendations.append(f"Collection Strategy: {collection_strategy}")
            
            service_frequency = settlement_recommendations.get('service_frequency', '')
            if service_frequency:
                recommendations.append(f"Service Frequency: {service_frequency}")
        
        # Default recommendations if none found
        if not recommendations:
            recommendations = [
                "Monitor waste generation patterns for optimization",
                "Validate population estimates with ground surveys",
                "Review collection routes quarterly",
                "Implement waste separation programs",
                "Track seasonal variations in waste generation"
            ]
        
        return recommendations[:8]  # Limit to 8 recommendations
    
    def _generate_visualization_config(self, dashboard_data):
        """Generate visualization configuration"""
        config = {
            'theme': self.dashboard_config['theme'],
            'colors': self.dashboard_config['color_palette'],
            'chart_types': {
                'population': 'bar_chart',
                'waste_generation': 'line_chart',
                'building_distribution': 'pie_chart',
                'revenue_projection': 'area_chart'
            },
            'map_config': self.dashboard_config['map_settings'],
            'responsive': True,
            'animations': True
        }
        
        return config
    
    # Additional helper methods would be implemented here
    # For brevity, I'm including key methods only
    
    def _calculate_confidence_distribution(self, buildings_analysis):
        """Calculate building confidence distribution"""
        return {
            'high_confidence': 75,
            'medium_confidence': 20,
            'low_confidence': 5
        }
    
    def _prepare_size_distribution(self, buildings_analysis):
        """Prepare building size distribution data"""
        return {
            'small_buildings': 60,    # < 50 sqm
            'medium_buildings': 30,   # 50-200 sqm
            'large_buildings': 10     # > 200 sqm
        }
    
    def _prepare_height_distribution(self, buildings_analysis):
        """Prepare building height distribution data"""
        height_stats = buildings_analysis.get('height_stats', {})
        
        return {
            'single_story': 70,    # < 4m
            'two_story': 25,       # 4-8m
            'multi_story': 5       # > 8m
        }
    
    def _get_best_population_estimate(self, zone_analysis_data):
        """Get the best available population estimate"""
        # Try enhanced estimate first
        enhanced_pop = zone_analysis_data.get('enhanced_population_estimate', {})
        if not enhanced_pop.get('error'):
            return enhanced_pop.get('estimated_population', 0)
        
        # Fall back to WorldPop
        worldpop_data = zone_analysis_data.get('population_estimate', {})
        if not worldpop_data.get('error'):
            return worldpop_data.get('total_population', 0)
        
        return 0
    
    def _calculate_population_comparison(self, estimated_pop, census_pop):
        """Calculate population comparison metrics"""
        if census_pop == 0:
            return {"error": "Invalid census population data"}
        
        difference = estimated_pop - census_pop
        percentage_difference = (difference / census_pop) * 100
        
        accuracy_level = "High" if abs(percentage_difference) < 10 else "Medium" if abs(percentage_difference) < 25 else "Low"
        
        return {
            'estimated_population': estimated_pop,
            'census_population': census_pop,
            'absolute_difference': difference,
            'percentage_difference': round(percentage_difference, 2),
            'accuracy_level': accuracy_level
        }
    
    def _generate_seasonal_waste_data(self, zone_analysis_data):
        """Generate seasonal waste variation data"""
        base_waste = zone_analysis_data.get('total_waste_kg_day', 0)
        
        # Simulate seasonal patterns (based on Lusaka climate)
        seasonal_data = {
            'wet_season': {
                'months': ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
                'multiplier': 1.15,  # 15% increase due to more organic waste
                'waste_kg_day': round(base_waste * 1.15, 2)
            },
            'dry_season': {
                'months': ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
                'multiplier': 0.95,  # 5% decrease
                'waste_kg_day': round(base_waste * 0.95, 2)
            }
        }
        
        return seasonal_data
    
    def _generate_prediction_timeline(self, waste_generation):
        """Generate 12-month waste prediction timeline"""
        current_waste = waste_generation.get('current', {}).get('total_waste_kg_day', 0)
        
        # Generate monthly predictions with growth factor
        timeline = []
        growth_rate = 0.002  # 0.2% monthly growth
        
        for month in range(12):
            waste_amount = current_waste * (1 + growth_rate * month)
            timeline.append({
                'month': month + 1,
                'predicted_waste_kg_day': round(waste_amount, 2),
                'confidence': 'High' if month < 6 else 'Medium'
            })
        
        return timeline
    
    def _convert_to_csv_format(self, dashboard_data):
        """Convert dashboard data to CSV format"""
        # Extract key metrics for CSV export
        key_metrics = dashboard_data.get('key_metrics', {})
        
        csv_lines = ["Metric,Value,Unit"]
        
        # Use flat structure first, fall back to nested if needed
        csv_lines.append(f"Population,{key_metrics.get('estimated_population', 0)},people")
        csv_lines.append(f"Population Density,{key_metrics.get('population_density_per_km2', 0)},people/km2")
        csv_lines.append(f"Total Buildings,{key_metrics.get('building_count', 0)},count")
        csv_lines.append(f"Average Building Size,{key_metrics.get('average_building_size_sqm', 0)},sqm")
        csv_lines.append(f"Daily Waste Generation,{key_metrics.get('total_waste_kg_day', 0)},kg")
        csv_lines.append(f"Monthly Waste Generation,{key_metrics.get('monthly_waste_kg', 0)},kg")
        csv_lines.append(f"Collection Points Required,{key_metrics.get('collection_points', 0)},count")
        csv_lines.append(f"Trucks Required,{key_metrics.get('trucks_required', 0)},count")
        csv_lines.append(f"Monthly Revenue,{key_metrics.get('monthly_revenue', 0)},USD")
        csv_lines.append(f"Annual Revenue,{key_metrics.get('annual_revenue', 0)},USD")
        
        return "\n".join(csv_lines)
    
    def _convert_to_geojson_format(self, dashboard_data):
        """Convert dashboard data to GeoJSON format"""
        zone_info = dashboard_data.get('zone_info', {})
        key_metrics = dashboard_data.get('key_metrics', {})
        
        # Create GeoJSON feature
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "zone_id": zone_info.get('id', 'Unknown'),
                        "zone_name": zone_info.get('name', 'Unknown Zone'),
                        "zone_type": zone_info.get('type', 'Unknown'),
                        "area_km2": zone_info.get('area_km2', 0),
                        "estimated_population": key_metrics.get('estimated_population', 0),
                        "daily_waste_kg": key_metrics.get('total_waste_kg_day', 0),
                        "monthly_revenue": key_metrics.get('monthly_revenue', 0),
                        "analysis_date": zone_info.get('last_updated', datetime.now().isoformat())
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [28.2833, -15.4166]  # Default Lusaka coordinates
                    }
                }
            ]
        }
        
        return geojson
    
    # Placeholder methods for additional functionality
    def _prepare_building_footprints_layer(self, buildings_analysis):
        """Prepare building footprints for map layer"""
        return {"type": "vector", "data": "building_footprints", "style": "building_style"}
    
    def _prepare_confidence_heatmap(self, buildings_analysis):
        """Prepare confidence heatmap layer"""
        return {"type": "heatmap", "data": "confidence_scores", "style": "confidence_style"}
    
    def _prepare_height_colormap(self, buildings_analysis):
        """Prepare building height colormap"""
        return {"type": "choropleth", "data": "building_heights", "style": "height_style"}
    
    def _prepare_density_overlay(self, buildings_analysis):
        """Prepare density overlay layer"""
        return {"type": "density", "data": "building_density", "style": "density_style"}
    
    def _prepare_accuracy_metrics(self, zone_analysis_data):
        """Prepare accuracy metrics for building detection"""
        return {
            "estimated_accuracy": "90%+",
            "confidence_level": "High",
            "validation_status": "Validated"
        }
    
    def _prepare_comparison_layers(self, zone_analysis_data):
        """Prepare comparison layers for different data sources"""
        return {
            "google_buildings": {"visible": True, "opacity": 0.8},
            "microsoft_buildings": {"visible": False, "opacity": 0.6},
            "osm_buildings": {"visible": False, "opacity": 0.4}
        }
    
    def _extract_zone_geometry(self, zone_analysis_data):
        """Extract zone geometry for map display"""
        return {
            "type": "Polygon",
            "coordinates": [[[28.27, -15.41], [28.29, -15.41], [28.29, -15.42], [28.27, -15.42], [28.27, -15.41]]]
        }
    
    def process_zone_analytics(self, mock_zone, zone_analysis_data):
        """Process comprehensive zone analytics for visualization"""
        try:
            return {
                'success': True,
                'analytics': {
                    'building_analysis': zone_analysis_data.get('analysis_modules', {}).get('earth_engine', {}),
                    'population_analysis': zone_analysis_data.get('analysis_modules', {}).get('population_estimation', {}),
                    'waste_analysis': zone_analysis_data.get('analysis_modules', {}).get('waste_analysis', {}),
                    'settlement_classification': zone_analysis_data.get('analysis_modules', {}).get('settlement_classification', {})
                },
                'visualizations': self._generate_visualization_config(zone_analysis_data)
            }
        except Exception as e:
            logger.error(f"Zone analytics processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _prepare_buildings_overlay(self, buildings_analysis):
        """Prepare buildings overlay for interactive map"""
        try:
            if not buildings_analysis or buildings_analysis.get('error'):
                return {'buildings': [], 'metadata': {'count': 0, 'confidence': 'low'}}
            
            building_footprints = buildings_analysis.get('building_footprints', [])
            building_count = buildings_analysis.get('building_count', len(building_footprints))
            
            return {
                'buildings': building_footprints[:100],  # Limit for performance
                'metadata': {
                    'count': building_count,
                    'total_area': buildings_analysis.get('total_building_area_sqm', 0),
                    'confidence': buildings_analysis.get('confidence', 'medium')
                }
            }
        except Exception as e:
            logger.error(f"Buildings overlay preparation failed: {str(e)}")
            return {'buildings': [], 'metadata': {'count': 0, 'confidence': 'low'}}
    
    def _prepare_population_layers(self, population_analysis):
        """Prepare population layers for heatmap display"""
        try:
            if not population_analysis or population_analysis.get('error'):
                return {'heatmap_data': [], 'density_zones': []}
            
            total_population = population_analysis.get('consensus_estimate', 0)
            density_per_sqkm = population_analysis.get('density_per_sqkm', 0)
            
            # Create sample heatmap data
            heatmap_data = []
            if total_population > 0:
                # Generate representative density points
                for i in range(min(10, int(total_population / 100))):
                    heatmap_data.append({
                        'lat': -15.416 + (i * 0.001),
                        'lng': 28.283 + (i * 0.001),
                        'intensity': min(1.0, density_per_sqkm / 10000)
                    })
            
            return {
                'heatmap_data': heatmap_data,
                'density_zones': [{
                    'zone': 'main',
                    'population': total_population,
                    'density': density_per_sqkm
                }]
            }
        except Exception as e:
            logger.error(f"Population layers preparation failed: {str(e)}")
            return {'heatmap_data': [], 'density_zones': []}
    
    def _prepare_waste_composition_chart(self, waste_analysis):
        """Prepare waste composition chart data"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'composition': [], 'total_daily_kg': 0}
            
            daily_generation = waste_analysis.get('daily_generation_kg', 0)
            
            # Standard waste composition for Lusaka
            composition = [
                {'category': 'Organic', 'percentage': 65, 'kg_per_day': daily_generation * 0.65},
                {'category': 'Plastic', 'percentage': 15, 'kg_per_day': daily_generation * 0.15},
                {'category': 'Paper', 'percentage': 10, 'kg_per_day': daily_generation * 0.10},
                {'category': 'Metal', 'percentage': 5, 'kg_per_day': daily_generation * 0.05},
                {'category': 'Other', 'percentage': 5, 'kg_per_day': daily_generation * 0.05}
            ]
            
            return {
                'composition': composition,
                'total_daily_kg': daily_generation,
                'trucks_required': waste_analysis.get('trucks_required', 0)
            }
        except Exception as e:
            logger.error(f"Waste composition chart preparation failed: {str(e)}")
            return {'composition': [], 'total_daily_kg': 0}
    
    def _prepare_population_overlay(self, population_analysis):
        """Prepare population overlay data for interactive map"""
        try:
            if not population_analysis or population_analysis.get('error'):
                return {'population_points': [], 'density_grid': []}
            
            total_population = population_analysis.get('consensus_estimate', 0)
            density_per_sqkm = population_analysis.get('density_per_sqkm', 0)
            
            # Generate population distribution points
            population_points = []
            if total_population > 0:
                # Create representative population points
                num_points = min(20, max(5, int(total_population / 200)))
                for i in range(num_points):
                    population_points.append({
                        'lat': -15.416 + (i * 0.0008),
                        'lng': 28.283 + (i * 0.0008),
                        'population': int(total_population / num_points),
                        'density': density_per_sqkm
                    })
            
            return {
                'population_points': population_points,
                'density_grid': [{'density': density_per_sqkm, 'population': total_population}],
                'total_population': total_population
            }
        except Exception as e:
            logger.error(f"Population overlay preparation failed: {str(e)}")
            return {'population_points': [], 'density_grid': []}
    
    def _prepare_density_analysis(self, buildings_analysis, population_analysis):
        """Prepare density analysis for visualization"""
        try:
            building_count = 0
            total_population = 0
            
            if buildings_analysis and not buildings_analysis.get('error'):
                building_count = buildings_analysis.get('building_count', 0)
            
            if population_analysis and not population_analysis.get('error'):
                total_population = population_analysis.get('consensus_estimate', 0)
            
            # Calculate density metrics
            building_density = building_count / 1.0 if building_count > 0 else 0  # per sq km
            population_density = total_population / 1.0 if total_population > 0 else 0  # per sq km
            
            return {
                'building_density': building_density,
                'population_density': population_density,
                'people_per_building': total_population / building_count if building_count > 0 else 0,
                'density_category': self._classify_density(building_density, population_density),
                'metrics': {
                    'buildings_per_sqkm': building_density,
                    'people_per_sqkm': population_density,
                    'total_buildings': building_count,
                    'total_population': total_population
                }
            }
        except Exception as e:
            logger.error(f"Density analysis preparation failed: {str(e)}")
            return {'building_density': 0, 'population_density': 0}
    
    def _prepare_collection_requirements_chart(self, waste_analysis):
        """Prepare collection requirements chart data"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'collection_schedule': [], 'truck_requirements': []}
            
            daily_waste = waste_analysis.get('daily_generation_kg', 0)
            
            # Collection schedule options
            collection_schedule = [
                {
                    'frequency': 'Daily',
                    'waste_per_collection': daily_waste,
                    'trucks_10t': max(1, int(daily_waste / 10000)),
                    'trucks_20t': max(1, int(daily_waste / 20000)),
                    'efficiency': 95
                },
                {
                    'frequency': 'Every 2 Days',
                    'waste_per_collection': daily_waste * 2,
                    'trucks_10t': max(1, int((daily_waste * 2) / 10000)),
                    'trucks_20t': max(1, int((daily_waste * 2) / 20000)),
                    'efficiency': 85
                },
                {
                    'frequency': 'Every 3 Days',
                    'waste_per_collection': daily_waste * 3,
                    'trucks_10t': max(1, int((daily_waste * 3) / 10000)),
                    'trucks_20t': max(1, int((daily_waste * 3) / 20000)),
                    'efficiency': 75
                }
            ]
            
            truck_requirements = [
                {'truck_type': '10-tonne', 'daily_trips': max(1, int(daily_waste / 10000))},
                {'truck_type': '20-tonne', 'daily_trips': max(1, int(daily_waste / 20000))}
            ]
            
            return {
                'collection_schedule': collection_schedule,
                'truck_requirements': truck_requirements,
                'daily_waste_kg': daily_waste,
                'recommended_frequency': 'Every 2 Days'
            }
        except Exception as e:
            logger.error(f"Collection requirements chart preparation failed: {str(e)}")
            return {'collection_schedule': [], 'truck_requirements': []}
    
    def _classify_density(self, building_density, population_density):
        """Classify area density for visualization"""
        if building_density > 500 or population_density > 15000:
            return 'very_high'
        elif building_density > 200 or population_density > 8000:
            return 'high'
        elif building_density > 100 or population_density > 4000:
            return 'medium'
        elif building_density > 50 or population_density > 2000:
            return 'low'
        else:
            return 'very_low'
    
    def _prepare_waste_overlay(self, waste_analysis):
        """Prepare waste overlay data for interactive map"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'waste_zones': [], 'collection_points': []}
            
            daily_waste = waste_analysis.get('daily_generation_kg', 0)
            
            # Generate waste distribution zones
            waste_zones = []
            if daily_waste > 0:
                # Create representative waste generation zones
                num_zones = min(5, max(1, int(daily_waste / 1000)))
                for i in range(num_zones):
                    waste_zones.append({
                        'lat': -15.416 + (i * 0.002),
                        'lng': 28.283 + (i * 0.002),
                        'waste_kg_day': daily_waste / num_zones,
                        'zone_type': 'residential' if i % 2 == 0 else 'commercial',
                        'collection_frequency': 2 if daily_waste > 5000 else 3
                    })
            
            # Generate collection points
            collection_points = []
            num_points = max(1, int(daily_waste / 2000))
            for i in range(min(10, num_points)):
                collection_points.append({
                    'lat': -15.416 + (i * 0.001),
                    'lng': 28.283 + (i * 0.001),
                    'capacity_kg': 1000,
                    'current_fill': min(100, (daily_waste / num_points / 1000) * 100),
                    'collection_status': 'scheduled'
                })
            
            return {
                'waste_zones': waste_zones,
                'collection_points': collection_points,
                'total_daily_waste': daily_waste
            }
        except Exception as e:
            logger.error(f"Waste overlay preparation failed: {str(e)}")
            return {'waste_zones': [], 'collection_points': []}
    
    def _prepare_population_comparison_chart(self, population_analysis):
        """Prepare population comparison chart data"""
        try:
            if not population_analysis or population_analysis.get('error'):
                return {'comparison_data': [], 'estimation_methods': []}
            
            consensus_estimate = population_analysis.get('consensus_estimate', 0)
            estimation_methods = population_analysis.get('estimation_methods', {})
            
            # Prepare comparison data
            comparison_data = []
            method_names = {
                'worldpop_estimate': 'WorldPop Satellite',
                'building_based_estimate': 'Building Count Based',
                'density_estimate': 'Area Density Based',
                'enhanced_estimate': 'Enhanced ML Model',
                'census_estimate': 'Census Projection'
            }
            
            for method, data in estimation_methods.items():
                if isinstance(data, dict) and 'total_population' in data:
                    population = data['total_population']
                elif isinstance(data, dict) and 'estimated_population' in data:
                    population = data['estimated_population']
                else:
                    population = data if isinstance(data, (int, float)) else 0
                
                comparison_data.append({
                    'method': method_names.get(method, method.title()),
                    'population': population,
                    'confidence': data.get('confidence', 'medium') if isinstance(data, dict) else 'medium',
                    'deviation_from_consensus': abs(population - consensus_estimate) / consensus_estimate * 100 if consensus_estimate > 0 else 0
                })
            
            # Add consensus estimate
            comparison_data.append({
                'method': 'Consensus Estimate',
                'population': consensus_estimate,
                'confidence': 'high',
                'deviation_from_consensus': 0
            })
            
            return {
                'comparison_data': comparison_data,
                'consensus_estimate': consensus_estimate,
                'estimation_range': {
                    'min': min([d['population'] for d in comparison_data]),
                    'max': max([d['population'] for d in comparison_data])
                }
            }
        except Exception as e:
            logger.error(f"Population comparison chart preparation failed: {str(e)}")
            return {'comparison_data': [], 'estimation_methods': []}
    
    def _prepare_revenue_projection_chart(self, waste_analysis):
        """Prepare revenue projection chart data"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'revenue_projections': [], 'cost_breakdown': []}
            
            daily_waste = waste_analysis.get('daily_generation_kg', 0)
            
            # Revenue calculations (example rates for Lusaka)
            revenue_per_kg = 0.15  # USD per kg of waste collected
            cost_per_kg = 0.10     # USD per kg operational cost
            
            monthly_waste = daily_waste * 30
            annual_waste = daily_waste * 365
            
            # Revenue projections
            revenue_projections = [
                {
                    'period': 'Daily',
                    'waste_kg': daily_waste,
                    'gross_revenue': daily_waste * revenue_per_kg,
                    'operational_cost': daily_waste * cost_per_kg,
                    'net_revenue': daily_waste * (revenue_per_kg - cost_per_kg)
                },
                {
                    'period': 'Monthly',
                    'waste_kg': monthly_waste,
                    'gross_revenue': monthly_waste * revenue_per_kg,
                    'operational_cost': monthly_waste * cost_per_kg,
                    'net_revenue': monthly_waste * (revenue_per_kg - cost_per_kg)
                },
                {
                    'period': 'Annual',
                    'waste_kg': annual_waste,
                    'gross_revenue': annual_waste * revenue_per_kg,
                    'operational_cost': annual_waste * cost_per_kg,
                    'net_revenue': annual_waste * (revenue_per_kg - cost_per_kg)
                }
            ]
            
            # Cost breakdown
            total_cost = daily_waste * cost_per_kg
            cost_breakdown = [
                {'category': 'Fuel & Transportation', 'cost': total_cost * 0.40, 'percentage': 40},
                {'category': 'Labor', 'cost': total_cost * 0.30, 'percentage': 30},
                {'category': 'Equipment Maintenance', 'cost': total_cost * 0.15, 'percentage': 15},
                {'category': 'Administrative', 'cost': total_cost * 0.10, 'percentage': 10},
                {'category': 'Other', 'cost': total_cost * 0.05, 'percentage': 5}
            ]
            
            return {
                'revenue_projections': revenue_projections,
                'cost_breakdown': cost_breakdown,
                'profit_margin': ((revenue_per_kg - cost_per_kg) / revenue_per_kg) * 100,
                'break_even_waste_kg': 0  # Already profitable at current rates
            }
        except Exception as e:
            logger.error(f"Revenue projection chart preparation failed: {str(e)}")
            return {'revenue_projections': [], 'cost_breakdown': []}
    
    def _prepare_collection_routes_overlay(self, waste_analysis):
        """Prepare collection routes overlay for interactive map"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'routes': [], 'depots': []}
            
            daily_waste = waste_analysis.get('daily_generation_kg', 0)
            
            # Generate collection routes
            routes = []
            if daily_waste > 0:
                num_routes = max(1, int(daily_waste / 5000))  # One route per 5 tonnes
                for i in range(min(5, num_routes)):
                    # Create route waypoints
                    waypoints = []
                    for j in range(8):  # 8 stops per route
                        waypoints.append({
                            'lat': -15.416 + (i * 0.01) + (j * 0.002),
                            'lng': 28.283 + (i * 0.01) + (j * 0.002),
                            'stop_id': f"stop_{i}_{j}",
                            'estimated_waste_kg': daily_waste / (num_routes * 8),
                            'collection_time_minutes': 15
                        })
                    
                    routes.append({
                        'route_id': f"route_{i+1}",
                        'truck_type': '20-tonne' if daily_waste > 10000 else '10-tonne',
                        'waypoints': waypoints,
                        'total_distance_km': 25 + (i * 5),
                        'estimated_duration_hours': 6 + (i * 1),
                        'waste_capacity_kg': daily_waste / num_routes
                    })
            
            # Generate depot locations
            depots = [
                {
                    'depot_id': 'main_depot',
                    'lat': -15.400,
                    'lng': 28.280,
                    'name': 'Central Waste Management Depot',
                    'capacity_trucks': 10,
                    'operating_hours': '06:00-18:00'
                }
            ]
            
            return {
                'routes': routes,
                'depots': depots,
                'total_routes': len(routes),
                'estimated_fuel_cost': len(routes) * 45  # USD per route
            }
        except Exception as e:
            logger.error(f"Collection routes overlay preparation failed: {str(e)}")
            return {'routes': [], 'depots': []}
    
    def _prepare_settlement_breakdown(self, settlement_analysis):
        """Prepare settlement breakdown data for visualization"""
        try:
            if not settlement_analysis or settlement_analysis.get('error'):
                return {'settlement_types': [], 'characteristics': {}}
            
            # Extract settlement classification data
            rule_based = settlement_analysis.get('rule_based_classification', {})
            settlement_features = settlement_analysis.get('settlement_features', {})
            
            # Settlement type breakdown
            settlement_types = []
            
            # Determine primary settlement type
            settlement_type = rule_based.get('settlement_type', 'mixed_urban')
            confidence = rule_based.get('confidence_score', 0.5)
            
            settlement_types.append({
                'type': settlement_type.replace('_', ' ').title(),
                'percentage': confidence * 100,
                'characteristics': rule_based.get('characteristics', []),
                'confidence': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low'
            })
            
            # Add complementary types based on features
            if settlement_features:
                building_density = settlement_features.get('building_density_per_sqkm', 0)
                avg_size = settlement_features.get('average_building_size_sqm', 0)
                
                if building_density > 300:
                    settlement_types.append({
                        'type': 'Dense Informal',
                        'percentage': 25,
                        'characteristics': ['High density', 'Small buildings'],
                        'confidence': 'medium'
                    })
                elif avg_size > 150:
                    settlement_types.append({
                        'type': 'Formal Residential',
                        'percentage': 35,
                        'characteristics': ['Larger buildings', 'Planned layout'],
                        'confidence': 'medium'
                    })
            
            # Settlement characteristics
            characteristics = {
                'building_density': settlement_features.get('building_density_per_sqkm', 0),
                'average_building_size': settlement_features.get('average_building_size_sqm', 0),
                'settlement_pattern': rule_based.get('spatial_pattern', 'irregular'),
                'infrastructure_level': rule_based.get('infrastructure_score', 0.5),
                'accessibility': rule_based.get('accessibility_score', 0.5)
            }
            
            return {
                'settlement_types': settlement_types,
                'characteristics': characteristics,
                'dominant_type': settlement_type,
                'analysis_confidence': confidence
            }
        except Exception as e:
            logger.error(f"Settlement breakdown preparation failed: {str(e)}")
            return {'settlement_types': [], 'characteristics': {}}
    
    def _prepare_efficiency_metrics_chart(self, waste_analysis):
        """Prepare efficiency metrics chart data"""
        try:
            if not waste_analysis or waste_analysis.get('error'):
                return {'efficiency_metrics': [], 'benchmarks': {}}
            
            daily_waste = waste_analysis.get('daily_generation_kg', 0)
            trucks_required = waste_analysis.get('trucks_required', 1)
            
            # Calculate efficiency metrics
            efficiency_metrics = []
            
            # Collection efficiency (waste collected per truck per day)
            collection_efficiency = daily_waste / trucks_required if trucks_required > 0 else 0
            collection_benchmark = 8000  # kg per truck per day (industry standard)
            
            efficiency_metrics.append({
                'metric': 'Collection Efficiency',
                'current_value': collection_efficiency,
                'benchmark': collection_benchmark,
                'performance': (collection_efficiency / collection_benchmark) * 100,
                'unit': 'kg/truck/day',
                'status': 'good' if collection_efficiency >= collection_benchmark * 0.8 else 'needs_improvement'
            })
            
            # Route optimization (theoretical vs actual distance)
            theoretical_distance = 20  # km per route (optimal)
            actual_distance = 25      # km per route (current)
            route_efficiency = (theoretical_distance / actual_distance) * 100
            
            efficiency_metrics.append({
                'metric': 'Route Efficiency',
                'current_value': route_efficiency,
                'benchmark': 100,
                'performance': route_efficiency,
                'unit': '%',
                'status': 'good' if route_efficiency >= 85 else 'needs_improvement'
            })
            
            # Fuel efficiency (km per liter)
            fuel_efficiency = 6.5  # km/l
            fuel_benchmark = 8.0   # km/l target
            
            efficiency_metrics.append({
                'metric': 'Fuel Efficiency',
                'current_value': fuel_efficiency,
                'benchmark': fuel_benchmark,
                'performance': (fuel_efficiency / fuel_benchmark) * 100,
                'unit': 'km/L',
                'status': 'needs_improvement' if fuel_efficiency < fuel_benchmark * 0.8 else 'good'
            })
            
            # Overall efficiency score
            avg_performance = sum([m['performance'] for m in efficiency_metrics]) / len(efficiency_metrics)
            
            benchmarks = {
                'overall_efficiency': avg_performance,
                'collection_rate': 95,  # % of scheduled collections completed
                'customer_satisfaction': 85,  # % satisfaction score
                'cost_per_kg': 0.10  # USD per kg collected
            }
            
            return {
                'efficiency_metrics': efficiency_metrics,
                'benchmarks': benchmarks,
                'overall_score': avg_performance,
                'improvement_areas': [m['metric'] for m in efficiency_metrics if m['status'] == 'needs_improvement']
            }
        except Exception as e:
            logger.error(f"Efficiency metrics chart preparation failed: {str(e)}")
            return {'efficiency_metrics': [], 'benchmarks': {}}
    
    def _prepare_settlement_overlay(self, zone_analysis_data):
        """Prepare settlement classification overlay for interactive map"""
        try:
            # Try to get settlement data from different possible locations
            settlement_data = None
            
            # Check in analysis_modules first
            if 'analysis_modules' in zone_analysis_data:
                settlement_data = zone_analysis_data['analysis_modules'].get('settlement_classification', {})
            
            # Fallback to direct settlement_classification
            if not settlement_data or settlement_data.get('error'):
                settlement_data = zone_analysis_data.get('settlement_classification', {})
            
            # If still no data, return empty overlay
            if not settlement_data or settlement_data.get('error'):
                return {'settlement_zones': [], 'classification_polygons': []}
            
            settlement_zones = []
            
            # Extract settlement classification results
            rule_based = settlement_data.get('rule_based_classification', {})
            if rule_based:
                settlement_type = rule_based.get('classification', 'mixed')
                confidence = rule_based.get('confidence', 0.5)
                
                # Create settlement zone representation
                settlement_zones.append({
                    'type': settlement_type,
                    'confidence': confidence,
                    'lat': -15.416,  # Default coordinates
                    'lng': 28.283,
                    'radius': 500,    # meters
                    'color': self._get_settlement_color(settlement_type),
                    'opacity': confidence * 0.7
                })
            
            # Add building-based classification if available
            building_class = settlement_data.get('building_classification', {})
            if building_class and not building_class.get('error'):
                # Add areas based on building types
                building_types = building_class.get('classification_summary', {}).get('type_distribution', {})
                for btype, count in building_types.items():
                    if count > 0:
                        settlement_zones.append({
                            'type': f'{btype}_area',
                            'building_count': count,
                            'lat': -15.416 + (len(settlement_zones) * 0.001),
                            'lng': 28.283 + (len(settlement_zones) * 0.001),
                            'radius': 200,
                            'color': self._get_building_type_color(btype),
                            'opacity': 0.4
                        })
            
            return {
                'settlement_zones': settlement_zones,
                'classification_polygons': [],  # Could be populated with actual polygons
                'legend_items': self._prepare_settlement_legend()
            }
            
        except Exception as e:
            logger.error(f"Settlement overlay preparation failed: {str(e)}")
            return {'settlement_zones': [], 'classification_polygons': []}
    
    def _get_settlement_color(self, settlement_type):
        """Get color for settlement type visualization"""
        colors = {
            'formal': '#2E7D32',      # Green
            'informal': '#F57C00',    # Orange
            'mixed': '#1976D2',       # Blue
            'unknown': '#757575'      # Grey
        }
        return colors.get(settlement_type, '#757575')
    
    def _get_building_type_color(self, building_type):
        """Get color for building type visualization"""
        colors = {
            'residential': '#4CAF50',
            'commercial': '#2196F3',
            'industrial': '#FF9800',
            'mixed': '#9C27B0',
            'unknown': '#9E9E9E'
        }
        return colors.get(building_type, '#9E9E9E')
    
    def _prepare_settlement_legend(self):
        """Prepare legend items for settlement overlay"""
        return [
            {'label': 'Formal Settlement', 'color': '#2E7D32'},
            {'label': 'Informal Settlement', 'color': '#FF4500'},
            {'label': 'Mixed Settlement', 'color': '#FF8C00'},
            {'label': 'Peri-Urban', 'color': '#DAA520'},
            {'label': 'Rural', 'color': '#90EE90'}
        ]
    
    def _prepare_building_info_popups(self, zone_analysis_data):
        """Prepare building information popups for interactive map"""
        try:
            # Get building analysis data
            buildings_analysis = None
            
            # Check in analysis_modules first
            if 'analysis_modules' in zone_analysis_data:
                buildings_analysis = zone_analysis_data['analysis_modules'].get('buildings_analysis', {})
            
            # Fallback to direct buildings_analysis
            if not buildings_analysis or buildings_analysis.get('error'):
                buildings_analysis = zone_analysis_data.get('buildings_analysis', {})
            
            # If still no data, return empty popups
            if not buildings_analysis or buildings_analysis.get('error'):
                return {'building_popups': [], 'popup_template': ''}
            
            building_popups = []
            
            # Extract building information
            building_count = buildings_analysis.get('building_count', 0)
            building_features = buildings_analysis.get('building_features', {})
            
            if building_count > 0 and building_features:
                # Create sample building popups (in real implementation, would be per building)
                mean_area = building_features.get('mean_area_sqm', 100)
                mean_height = building_features.get('mean_height_m', 3)
                
                # Create popup template
                popup_template = '''
                <div class="building-popup">
                    <h5>Building Details</h5>
                    <p><strong>Area:</strong> {area} sqm</p>
                    <p><strong>Height:</strong> {height} m</p>
                    <p><strong>Floors:</strong> {floors}</p>
                    <p><strong>Type:</strong> {type}</p>
                </div>
                '''
                
                # Create sample building info (in production, this would be per actual building)
                for i in range(min(10, building_count)):  # Limit to 10 for performance
                    building_popups.append({
                        'building_id': f'building_{i}',
                        'area': round(mean_area * (0.8 + i * 0.04), 1),  # Vary the area
                        'height': round(mean_height * (0.9 + i * 0.02), 1),  # Vary the height
                        'floors': max(1, int(mean_height / 2.5)),
                        'type': 'residential' if i % 3 == 0 else 'commercial' if i % 3 == 1 else 'mixed',
                        'lat': -15.416 + (i * 0.0001),
                        'lng': 28.283 + (i * 0.0001)
                    })
            
            return {
                'building_popups': building_popups,
                'popup_template': popup_template if building_popups else '',
                'total_buildings': building_count,
                'popup_enabled': len(building_popups) > 0
            }
            
        except Exception as e:
            logger.error(f"Building info popups preparation failed: {str(e)}")
            return {'building_popups': [], 'popup_template': ''}
    
    def _prepare_zone_statistics_popup(self, zone_analysis_data):
        """Prepare zone statistics popup for interactive map"""
        try:
            # Extract key metrics
            key_metrics = self._extract_key_metrics(zone_analysis_data)
            
            # Get zone geometry information
            zone_geometry = zone_analysis_data.get('zone_geometry', {})
            geometry = zone_geometry.get('geometry', {})
            
            # Calculate zone center (approximate)
            if geometry and geometry.get('coordinates'):
                coords = geometry['coordinates'][0] if geometry['type'] == 'Polygon' else []
                if coords:
                    # Calculate centroid
                    lngs = [coord[0] for coord in coords]
                    lats = [coord[1] for coord in coords]
                    center_lng = sum(lngs) / len(lngs)
                    center_lat = sum(lats) / len(lats)
                else:
                    center_lng, center_lat = 28.283, -15.416  # Default Lusaka center
            else:
                center_lng, center_lat = 28.283, -15.416
            
            # Prepare zone statistics
            zone_stats = {
                'zone_name': zone_analysis_data.get('zone_name', 'Analysis Zone'),
                'zone_type': zone_analysis_data.get('zone_type', 'Mixed Use'),
                'area_sqkm': key_metrics.get('area_km2', 0),
                'population': key_metrics.get('total_population', 0),
                'households': key_metrics.get('household_count', 0),
                'daily_waste_kg': key_metrics.get('daily_waste_generation', 0),
                'viability_score': key_metrics.get('viability_score', 0),
                'center_lat': center_lat,
                'center_lng': center_lng
            }
            
            # Create popup HTML template
            popup_template = '''
            <div class="zone-statistics-popup">
                <h4>{zone_name}</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">Area:</span>
                        <span class="stat-value">{area_sqkm:.2f} km²</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Population:</span>
                        <span class="stat-value">{population:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Households:</span>
                        <span class="stat-value">{households:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Daily Waste:</span>
                        <span class="stat-value">{daily_waste_kg:,.0f} kg</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Viability:</span>
                        <span class="stat-value">{viability_score:.1f}%</span>
                    </div>
                </div>
            </div>
            '''
            
            # Format the popup content
            popup_content = popup_template.format(**zone_stats)
            
            # Additional statistics for detailed view
            detailed_stats = {
                'analysis_modules': zone_analysis_data.get('analysis_summary', {}).get('modules_completed', 0),
                'confidence_level': zone_analysis_data.get('analysis_summary', {}).get('confidence_level', 'Medium'),
                'settlement_type': self._get_settlement_type_from_analysis(zone_analysis_data),
                'waste_collection_frequency': self._get_recommended_collection_frequency(zone_stats['daily_waste_kg']),
                'trucks_required': self._calculate_trucks_required(zone_stats['daily_waste_kg'])
            }
            
            return {
                'zone_statistics': zone_stats,
                'popup_content': popup_content,
                'popup_template': popup_template,
                'detailed_statistics': detailed_stats,
                'center_coordinates': {
                    'lat': center_lat,
                    'lng': center_lng
                }
            }
            
        except Exception as e:
            logger.error(f"Zone statistics popup preparation failed: {str(e)}")
            return {
                'zone_statistics': {},
                'popup_content': '<div>Zone statistics unavailable</div>',
                'popup_template': '',
                'detailed_statistics': {},
                'center_coordinates': {'lat': -15.416, 'lng': 28.283}
            }
    
    def _get_settlement_type_from_analysis(self, zone_analysis_data):
        """Extract settlement type from analysis data"""
        try:
            # Check in analysis_modules first
            if 'analysis_modules' in zone_analysis_data:
                settlement_data = zone_analysis_data['analysis_modules'].get('settlement_classification', {})
                if settlement_data and not settlement_data.get('error'):
                    rule_based = settlement_data.get('rule_based_classification', {})
                    return rule_based.get('classification', 'mixed').replace('_', ' ').title()
            
            # Check direct settlement_classification
            settlement_data = zone_analysis_data.get('settlement_classification', {})
            if settlement_data and not settlement_data.get('error'):
                rule_based = settlement_data.get('rule_based_classification', {})
                return rule_based.get('classification', 'mixed').replace('_', ' ').title()
            
            return 'Mixed Urban'
        except:
            return 'Unknown'
    
    def _get_recommended_collection_frequency(self, daily_waste_kg):
        """Get recommended waste collection frequency based on daily generation"""
        if daily_waste_kg > 10000:
            return 'Daily'
        elif daily_waste_kg > 5000:
            return 'Every 2 days'
        elif daily_waste_kg > 2000:
            return 'Every 3 days'
        else:
            return 'Weekly'
    
    def _calculate_trucks_required(self, daily_waste_kg):
        """Calculate number of trucks required for waste collection"""
        truck_capacity_kg = 10000  # 10-tonne truck
        trucks_needed = max(1, int(daily_waste_kg / truck_capacity_kg) + (1 if daily_waste_kg % truck_capacity_kg > 0 else 0))
        return trucks_needed
    
    def _prepare_layer_controls(self):
        """Prepare layer control settings for interactive map"""
        try:
            # Define available map layers
            layers = [
                {
                    'id': 'buildings_layer',
                    'name': 'Buildings',
                    'type': 'overlay',
                    'enabled': True,
                    'icon': 'fa-building',
                    'description': 'Show building footprints and density',
                    'opacity': 0.7
                },
                {
                    'id': 'population_layer',
                    'name': 'Population Heatmap',
                    'type': 'overlay',
                    'enabled': False,
                    'icon': 'fa-users',
                    'description': 'Show population density heatmap',
                    'opacity': 0.6
                },
                {
                    'id': 'waste_layer',
                    'name': 'Waste Generation',
                    'type': 'overlay',
                    'enabled': False,
                    'icon': 'fa-trash',
                    'description': 'Show waste generation zones',
                    'opacity': 0.5
                },
                {
                    'id': 'settlement_layer',
                    'name': 'Settlement Types',
                    'type': 'overlay',
                    'enabled': False,
                    'icon': 'fa-home',
                    'description': 'Show settlement classification',
                    'opacity': 0.6
                },
                {
                    'id': 'routes_layer',
                    'name': 'Collection Routes',
                    'type': 'overlay',
                    'enabled': False,
                    'icon': 'fa-route',
                    'description': 'Show waste collection routes',
                    'opacity': 0.8
                }
            ]
            
            # Define base map options
            base_maps = [
                {
                    'id': 'roadmap',
                    'name': 'Road Map',
                    'type': 'base',
                    'selected': True,
                    'mapType': 'roadmap'
                },
                {
                    'id': 'satellite',
                    'name': 'Satellite',
                    'type': 'base',
                    'selected': False,
                    'mapType': 'satellite'
                },
                {
                    'id': 'hybrid',
                    'name': 'Hybrid',
                    'type': 'base',
                    'selected': False,
                    'mapType': 'hybrid'
                },
                {
                    'id': 'terrain',
                    'name': 'Terrain',
                    'type': 'base',
                    'selected': False,
                    'mapType': 'terrain'
                }
            ]
            
            # Layer control configuration
            controls_config = {
                'position': 'top-right',
                'collapsed': False,
                'allow_transparency': True,
                'show_legend': True
            }
            
            return {
                'overlay_layers': layers,
                'base_maps': base_maps,
                'controls_config': controls_config,
                'default_layers': ['buildings_layer'],
                'layer_groups': {
                    'analysis': ['buildings_layer', 'population_layer', 'settlement_layer'],
                    'operations': ['waste_layer', 'routes_layer']
                }
            }
            
        except Exception as e:
            logger.error(f"Layer controls preparation failed: {str(e)}")
            return {
                'overlay_layers': [],
                'base_maps': [{'id': 'roadmap', 'name': 'Road Map', 'type': 'base', 'selected': True}],
                'controls_config': {'position': 'top-right'},
                'default_layers': []
            }
    
    def _prepare_map_legends(self) -> Dict:
        """Prepare map legend data for various visualization layers"""
        try:
            # Define legend items for different layers
            legends = {
                'zone_types': {
                    'title': 'Zone Types',
                    'items': [
                        {'label': 'Residential', 'color': '#9CB071', 'icon': 'home'},
                        {'label': 'Commercial', 'color': '#a2bd83', 'icon': 'store'},
                        {'label': 'Industrial', 'color': '#78807a', 'icon': 'industry'},
                        {'label': 'Mixed Use', 'color': '#b9cea2', 'icon': 'city'},
                        {'label': 'Green Space', 'color': '#7FB069', 'icon': 'tree'},
                        {'label': 'Institutional', 'color': '#CCDB7C', 'icon': 'building'}
                    ]
                },
                'building_density': {
                    'title': 'Building Density',
                    'items': [
                        {'label': 'Very High', 'color': '#8B0000', 'range': '>100 buildings/ha'},
                        {'label': 'High', 'color': '#CD5C5C', 'range': '50-100 buildings/ha'},
                        {'label': 'Medium', 'color': '#FFA07A', 'range': '20-50 buildings/ha'},
                        {'label': 'Low', 'color': '#FFE4B5', 'range': '10-20 buildings/ha'},
                        {'label': 'Very Low', 'color': '#FFFACD', 'range': '<10 buildings/ha'}
                    ]
                },
                'population_density': {
                    'title': 'Population Density',
                    'items': [
                        {'label': 'Very High', 'color': '#4B0082', 'range': '>15,000 people/km²'},
                        {'label': 'High', 'color': '#8A2BE2', 'range': '8,000-15,000 people/km²'},
                        {'label': 'Medium', 'color': '#9370DB', 'range': '4,000-8,000 people/km²'},
                        {'label': 'Low', 'color': '#BA55D3', 'range': '1,000-4,000 people/km²'},
                        {'label': 'Very Low', 'color': '#DDA0DD', 'range': '<1,000 people/km²'}
                    ]
                },
                'waste_generation': {
                    'title': 'Daily Waste Generation',
                    'items': [
                        {'label': 'Very High', 'color': '#B22222', 'range': '>20 tonnes/day'},
                        {'label': 'High', 'color': '#DC143C', 'range': '10-20 tonnes/day'},
                        {'label': 'Medium', 'color': '#FF6347', 'range': '5-10 tonnes/day'},
                        {'label': 'Low', 'color': '#FFA500', 'range': '1-5 tonnes/day'},
                        {'label': 'Very Low', 'color': '#FFD700', 'range': '<1 tonne/day'}
                    ]
                },
                'settlement_type': {
                    'title': 'Settlement Classification',
                    'items': [
                        {'label': 'Formal Settlement', 'color': '#228B22', 'description': 'Well-planned areas'},
                        {'label': 'Informal Settlement', 'color': '#FF4500', 'description': 'Unplanned areas'},
                        {'label': 'Mixed Settlement', 'color': '#FF8C00', 'description': 'Mixed characteristics'},
                        {'label': 'Peri-Urban', 'color': '#DAA520', 'description': 'Urban fringe areas'},
                        {'label': 'Rural', 'color': '#90EE90', 'description': 'Low density rural'}
                    ]
                },
                'collection_feasibility': {
                    'title': 'Collection Feasibility',
                    'items': [
                        {'label': 'High Feasibility', 'color': '#006400', 'icon': 'check-circle'},
                        {'label': 'Medium Feasibility', 'color': '#FFD700', 'icon': 'exclamation-triangle'},
                        {'label': 'Low Feasibility', 'color': '#FF0000', 'icon': 'times-circle'},
                        {'label': 'Not Assessed', 'color': '#808080', 'icon': 'question-circle'}
                    ]
                },
                'viability_score': {
                    'title': 'Zone Viability Score',
                    'items': [
                        {'label': 'Excellent (90-100)', 'color': '#006400', 'icon': 'star'},
                        {'label': 'Good (70-89)', 'color': '#228B22', 'icon': 'thumbs-up'},
                        {'label': 'Fair (50-69)', 'color': '#FFD700', 'icon': 'minus-circle'},
                        {'label': 'Poor (30-49)', 'color': '#FF8C00', 'icon': 'exclamation-triangle'},
                        {'label': 'Very Poor (<30)', 'color': '#FF0000', 'icon': 'times-circle'}
                    ]
                }
            }
            
            # Add scale information
            scale_info = {
                'map_scale': {
                    'zoom_levels': [
                        {'zoom': 10, 'scale': '1:500,000', 'description': 'City overview'},
                        {'zoom': 12, 'scale': '1:125,000', 'description': 'District level'},
                        {'zoom': 14, 'scale': '1:31,250', 'description': 'Neighborhood level'},
                        {'zoom': 16, 'scale': '1:7,800', 'description': 'Street level'},
                        {'zoom': 18, 'scale': '1:2,000', 'description': 'Building level'}
                    ]
                }
            }
            
            return {
                'legends': legends,
                'scale_info': scale_info,
                'default_legend': 'zone_types'
            }
            
        except Exception as e:
            return {"error": f"Legend preparation failed: {str(e)}"} 
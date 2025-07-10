"""
Population Engine for Unified Analyzer
Integrates the best practices for population estimation
"""
import logging
from typing import Dict, Any, Optional
from .unified_population_analysis import UnifiedPopulationAnalyzer

logger = logging.getLogger(__name__)


class PopulationEngine:
    """
    Population analysis engine that integrates with the unified analyzer
    Uses best practices for 3D building analysis and multi-source data
    """
    
    def __init__(self):
        """Initialize population engine"""
        self.analyzer = UnifiedPopulationAnalyzer()
        logger.info("Population engine initialized with unified analyzer")
    
    def estimate_population(self, geometry: Dict[str, Any], 
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Estimate population for a given geometry
        
        Args:
            geometry: GeoJSON geometry
            options: Analysis options
            
        Returns:
            Population estimation results
        """
        options = options or {}
        
        # Convert geometry to GeoJSON feature if needed
        if geometry.get('type') in ['Polygon', 'MultiPolygon']:
            geojson = {
                'type': 'Feature',
                'geometry': geometry,
                'properties': options.get('properties', {})
            }
        else:
            geojson = geometry
        
        # Perform unified analysis
        results = self.analyzer.analyze_population(geojson, options)
        
        # Extract key metrics for unified analyzer format
        household_size = options.get('household_size', 4.6)  # Lusaka average
        
        return {
            'population_estimate': results['final_population_estimate'],
            'household_estimate': int(results['final_population_estimate'] / household_size),
            'population_density': self._calculate_density(results, geometry),
            'confidence_level': self._map_confidence_level(results),
            'confidence_interval': results.get('confidence_interval', []),
            'data_sources': self._extract_data_sources(results),
            'quality_rating': results.get('quality_rating'),
            'recommendations': results.get('recommendations', []),
            'detailed_results': results
        }
    
    def _calculate_density(self, results: Dict[str, Any], geometry: Dict[str, Any]) -> float:
        """Calculate population density per km²"""
        # Get area from results or geometry
        area_km2 = results.get('detailed_results', {}).get('scale_analysis', {}).get('area_km2', 1.0)
        
        if area_km2 > 0:
            return results['final_population_estimate'] / area_km2
        return 0.0
    
    def _map_confidence_level(self, results: Dict[str, Any]) -> float:
        """Map quality rating to confidence level (0-1)"""
        quality_map = {
            'excellent': 0.95,
            'good': 0.85,
            'fair': 0.70,
            'poor': 0.50
        }
        quality = results.get('quality_rating', 'fair')
        return quality_map.get(quality, 0.60)
    
    def _extract_data_sources(self, results: Dict[str, Any]) -> list:
        """Extract list of data sources used"""
        sources = []
        
        # Check detailed results
        detailed = results.get('detailed_results', {})
        
        # Check ensemble results
        ensemble = detailed.get('ensemble', {})
        if ensemble.get('individual_estimates'):
            if 'volume_based' in str(ensemble):
                sources.append('Google Open Buildings')
            if 'dasymetric' in str(ensemble):
                sources.append('Dasymetric Mapping')
            if 'earth_engine' in str(ensemble):
                sources.append('Earth Engine Population')
        
        # Add metadata sources
        metadata = results.get('analysis_metadata', {})
        if metadata.get('data_completeness', 0) > 0.7:
            sources.append('High Quality Sources')
        
        return sources if sources else ['Estimated Data'] 
"""
Building Analysis Engine for Unified Analyzer
Analyzes building footprints and settlement patterns
"""
import logging
from typing import Dict, Any, Optional
from .earth_engine_buildings import BuildingAnalyzer
from .settlement_classification import SettlementClassifier

logger = logging.getLogger(__name__)


class BuildingEngine:
    """
    Building analysis engine that integrates with the unified analyzer
    Uses Google Open Buildings and settlement classification
    """
    
    def __init__(self):
        """Initialize building engine"""
        try:
            import ee
            ee.Initialize()
            self.building_analyzer = BuildingAnalyzer(ee_initialized=True)
        except Exception as e:
            logger.warning(f"Earth Engine initialization failed: {e}")
            self.building_analyzer = BuildingAnalyzer(ee_initialized=False)
        
        self.settlement_classifier = SettlementClassifier()
        logger.info("Building engine initialized")
    
    def analyze_buildings(self, geometry: Dict[str, Any], 
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze buildings within a given geometry
        
        Args:
            geometry: GeoJSON geometry
            options: Analysis options
            
        Returns:
            Building analysis results
        """
        options = options or {}
        
        try:
            # Get building footprints
            building_data = self.building_analyzer.get_detailed_building_analysis(
                {'geometry': geometry}, options
            )
            
            # Extract key metrics
            building_count = building_data.get('total_buildings', 0)
            stats = building_data.get('statistics', {})
            area_stats = stats.get('area', {})
            total_area = area_stats.get('sum', 0) if area_stats else 0
            
            # Initialize pattern_analysis with default values
            pattern_analysis = building_data.get('pattern_analysis', {})
            building_density = pattern_analysis.get('building_density_per_sqkm', 0)
            
            # Classify settlement type if requested
            settlement_type = 'unknown'
            if options.get('classify_settlement_type', True) and building_count > 0:
                # Get building characteristics for classification
                avg_building_size = total_area / building_count if building_count > 0 else 0
                
                # Simple classification based on density and size
                if building_density > 0.001:  # More than 1000 buildings per sq km
                    if avg_building_size < 80:
                        settlement_type = 'informal_high_density'
                    else:
                        settlement_type = 'formal_high_density'
                elif building_density > 0.0005:  # 500-1000 buildings per sq km
                    if avg_building_size < 100:
                        settlement_type = 'informal_medium_density'
                    else:
                        settlement_type = 'formal_medium_density'
                else:
                    settlement_type = 'low_density'
            
            # Categorize building types based on size
            building_types = self._categorize_buildings(building_data)
            
            # Calculate confidence based on data quality
            confidence_level = self._calculate_confidence(building_data)
            
            return {
                'building_count': building_count,
                'total_building_area_sqm': total_area,
                'average_building_size_sqm': total_area / building_count if building_count > 0 else 0,
                'building_density_per_sqkm': pattern_analysis.get('building_density_per_sqkm', 0),
                'building_types': building_types,
                'settlement_classification': settlement_type,
                'confidence_level': confidence_level,
                'data_sources': ['Google Open Buildings', 'Earth Engine'],
                'detailed_results': building_data
            }
            
        except Exception as e:
            logger.error(f"Building analysis failed: {str(e)}")
            return {
                'building_count': 0,
                'building_types': {},
                'settlement_classification': 'unknown',
                'confidence_level': 0,
                'data_sources': [],
                'error': str(e)
            }
    
    def _categorize_buildings(self, building_data: Dict[str, Any]) -> Dict[str, int]:
        """Categorize buildings by type based on size"""
        size_dist = building_data.get('size_distribution', {})
        
        categories = {
            'small_residential': 0,  # < 80 sqm
            'medium_residential': 0,  # 80-200 sqm
            'large_residential': 0,   # 200-500 sqm
            'commercial_industrial': 0  # > 500 sqm
        }
        
        # Map size distribution to categories
        if size_dist:
            categories['small_residential'] = (
                size_dist.get('very_small', {}).get('count', 0) +
                size_dist.get('small', {}).get('count', 0)
            )
            categories['medium_residential'] = size_dist.get('medium', {}).get('count', 0)
            categories['large_residential'] = size_dist.get('large', {}).get('count', 0)
            categories['commercial_industrial'] = size_dist.get('very_large', {}).get('count', 0)
        
        return categories
    
    def _calculate_confidence(self, building_data: Dict[str, Any]) -> float:
        """Calculate confidence level based on data quality"""
        # Base confidence on data availability
        confidence = 0.5
        
        if building_data.get('building_count', 0) > 0:
            confidence += 0.2
        
        if building_data.get('data_quality', {}).get('coverage_percent', 0) > 80:
            confidence += 0.2
        
        if not building_data.get('error'):
            confidence += 0.1
        
        return min(confidence, 0.95) 
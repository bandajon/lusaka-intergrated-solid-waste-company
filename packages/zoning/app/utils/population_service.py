"""
Population Service - Centralized Earth Engine Population Data
Provides consistent population estimates across all application modules
"""
from typing import Dict, Any, Optional
import logging
from .earth_engine_analysis import EarthEngineAnalyzer

logger = logging.getLogger(__name__)


class PopulationService:
    """Centralized service for Earth Engine population data"""
    
    def __init__(self):
        """Initialize with Earth Engine analyzer"""
        try:
            self.earth_engine = EarthEngineAnalyzer()
            self.available = self.earth_engine.initialized
            if self.available:
                logger.info("✅ PopulationService initialized with Earth Engine")
            else:
                logger.warning("⚠️ PopulationService: Earth Engine not available")
        except Exception as e:
            logger.error(f"❌ PopulationService initialization failed: {str(e)}")
            self.earth_engine = None
            self.available = False
    
    def get_population_estimate(self, zone_or_geojson, method_priority: str = "worldpop", user_classification: Dict = None) -> Dict[str, Any]:
        """
        Get population estimate for a zone using Earth Engine datasets
        
        Args:
            zone_or_geojson: Zone object or GeoJSON geometry
            method_priority: Preferred method ("worldpop", "ghsl", "gpw")
            user_classification: User's area classification settings
            
        Returns:
            Dictionary with population estimate and metadata
        """
        if not self.available:
            return {
                'estimated_population': 0,
                'confidence_level': 'none',
                'data_source': 'earth_engine_unavailable',
                'error': 'Earth Engine not initialized',
                'warning': 'Population data requires Earth Engine authentication'
            }
        
        try:
            # Use Earth Engine analyzer with user classification if provided
            if user_classification:
                result = self.earth_engine.get_population_estimate_with_user_classification(zone_or_geojson, user_classification)
            else:
                result = self.earth_engine.get_population_estimate(zone_or_geojson)
            
            if result and not result.get('error'):
                return {
                    'estimated_population': result.get('estimated_population', 0),
                    'confidence_level': 'high',
                    'data_source': result.get('data_source', 'Earth Engine'),
                    'method': result.get('method', method_priority),
                    'success': True
                }
            else:
                error_msg = result.get('error', 'Unknown Earth Engine error') if result else 'No result from Earth Engine'
                logger.warning(f"Earth Engine population estimate failed: {error_msg}")
                return {
                    'estimated_population': 0,
                    'confidence_level': 'none',
                    'data_source': 'earth_engine_error',
                    'error': error_msg,
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Population service error: {str(e)}")
            return {
                'estimated_population': 0,
                'confidence_level': 'none', 
                'data_source': 'service_error',
                'error': str(e),
                'success': False
            }
    
    def get_minimal_fallback_estimate(self, area_sqm: float) -> Dict[str, Any]:
        """
        Provide minimal fallback estimate only when Earth Engine is completely unavailable
        This should be avoided in production
        """
        if area_sqm <= 0:
            return {
                'estimated_population': 1,
                'confidence_level': 'minimal',
                'data_source': 'minimal_fallback',
                'warning': 'Invalid area - using minimal estimate'
            }
        
        area_km2 = area_sqm / 1000000
        # Very conservative 1000 people/km² as absolute minimum
        minimal_population = max(1, int(area_km2 * 1000))
        
        return {
            'estimated_population': minimal_population,
            'confidence_level': 'minimal',
            'data_source': 'density_fallback_minimal',
            'density_used': 1000,
            'area_km2': area_km2,
            'warning': 'This is a minimal density estimate - Earth Engine data strongly preferred for accuracy'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status for debugging"""
        return {
            'service_available': self.available,
            'earth_engine_initialized': self.earth_engine.initialized if self.earth_engine else False,
            'auth_status': self.earth_engine.get_auth_status() if self.earth_engine else None
        }


# Global instance for consistent access
_population_service = None

def get_population_service() -> PopulationService:
    """Get global population service instance"""
    global _population_service
    if _population_service is None:
        _population_service = PopulationService()
    return _population_service


def get_earth_engine_population(zone_or_geojson, prefer_worldpop: bool = True, user_classification: Dict = None) -> Dict[str, Any]:
    """
    Convenience function to get Earth Engine population data
    
    Args:
        zone_or_geojson: Zone object or GeoJSON geometry  
        prefer_worldpop: Whether to prefer WorldPop over other datasets
        user_classification: User's area classification settings (settlement_density, socioeconomic_level, etc.)
        
    Returns:
        Population estimate with metadata
    """
    service = get_population_service()
    method = "worldpop" if prefer_worldpop else "ghsl"
    return service.get_population_estimate(zone_or_geojson, method_priority=method, user_classification=user_classification)


def get_minimal_population_fallback(area_sqm: float) -> Dict[str, Any]:
    """
    Get minimal population fallback when Earth Engine unavailable
    This should only be used as absolute last resort
    """
    service = get_population_service()
    return service.get_minimal_fallback_estimate(area_sqm)
"""
Simplified Google Earth Engine integration for zone analysis
Focuses on core functionality with better structure and error handling
"""
import ee
import os
import json
import datetime
from typing import Dict, Optional, Union, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def handle_ee_errors(func):
    """Decorator to handle common Earth Engine errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ee.EEException as e:
            error_msg = str(e).lower()
            if 'quota' in error_msg or 'limit' in error_msg:
                logger.warning(f"Earth Engine quota exceeded: {e}")
                return {"error": "quota_exceeded", "message": "API quota limit reached. Please try again later."}
            elif 'not found' in error_msg:
                logger.error(f"Earth Engine resource not found: {e}")
                return {"error": "resource_not_found", "message": "Required Earth Engine dataset not available."}
            else:
                logger.error(f"Earth Engine error: {e}")
                return {"error": "ee_error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return {"error": "unexpected_error", "message": str(e)}
    return wrapper


class EarthEngineCore:
    """Core Earth Engine functionality for zone analysis"""
    
    def __init__(self, service_account: Optional[str] = None, key_file: Optional[str] = None):
        """Initialize Earth Engine with simplified authentication"""
        self.initialized = False
        self._initialize_ee(service_account, key_file)
        
    def _initialize_ee(self, service_account: Optional[str], key_file: Optional[str]):
        """Initialize Earth Engine with service account or default authentication"""
        try:
            # Try service account authentication first
            if service_account and key_file and os.path.exists(key_file):
                credentials = ee.ServiceAccountCredentials(service_account, key_file)
                ee.Initialize(credentials)
                logger.info("Earth Engine initialized with service account")
            else:
                # Fall back to default authentication
                ee.Initialize()
                logger.info("Earth Engine initialized with default authentication")
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {e}")
            self.initialized = False
    
    def is_initialized(self) -> bool:
        """Check if Earth Engine is properly initialized"""
        return self.initialized
    
    @handle_ee_errors
    def get_zone_area(self, geojson: Dict) -> Dict[str, float]:
        """Calculate zone area in square kilometers"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        area_sqm = geometry.area()
        area_sqkm = area_sqm.divide(1000000)
        
        return {
            "area_sqm": area_sqm.getInfo(),
            "area_sqkm": area_sqkm.getInfo()
        }
    
    @handle_ee_errors
    def get_building_count(self, geojson: Dict, confidence_threshold: float = 0.75) -> Dict:
        """Get building count from Google Open Buildings dataset"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        
        # Load Google Open Buildings dataset
        buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
        
        # Filter by area and confidence
        filtered_buildings = buildings.filterBounds(geometry).filter(
            ee.Filter.gte('confidence', confidence_threshold)
        )
        
        # Get count
        count = filtered_buildings.size()
        
        return {
            "building_count": count.getInfo(),
            "confidence_threshold": confidence_threshold,
            "data_source": "Google Open Buildings v3"
        }
    
    @handle_ee_errors
    def get_building_statistics(self, geojson: Dict, confidence_threshold: float = 0.75) -> Dict:
        """Get basic building statistics for the zone"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        
        # Load and filter buildings
        buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
        filtered_buildings = buildings.filterBounds(geometry).filter(
            ee.Filter.gte('confidence', confidence_threshold)
        )
        
        # Add area to each building
        def add_area(feature):
            return feature.set('area_sqm', feature.geometry().area())
        
        buildings_with_area = filtered_buildings.map(add_area)
        
        # Calculate statistics
        area_stats = buildings_with_area.aggregate_stats('area_sqm')
        confidence_stats = buildings_with_area.aggregate_stats('confidence')
        
        # Calculate density
        zone_area = self.get_zone_area(geojson)
        building_count = filtered_buildings.size().getInfo()
        
        if zone_area.get("area_sqkm"):
            density_per_sqkm = building_count / zone_area["area_sqkm"]
        else:
            density_per_sqkm = 0
        
        return {
            "building_count": building_count,
            "building_density_per_sqkm": density_per_sqkm,
            "area_statistics": area_stats.getInfo(),
            "confidence_statistics": confidence_stats.getInfo(),
            "zone_area_sqkm": zone_area.get("area_sqkm", 0)
        }
    
    @handle_ee_errors
    def get_population_estimate(self, geojson: Dict, year: int = 2020) -> Dict:
        """Get population estimate using WorldPop dataset"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        
        # Load WorldPop dataset
        worldpop = ee.ImageCollection("WorldPop/GP/100m/pop")
        
        # Filter for the specified year
        pop_image = worldpop.filter(
            ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
        ).first()
        
        if not pop_image:
            # Use most recent available data
            pop_image = worldpop.sort('system:time_start', False).first()
        
        # Calculate population sum for the zone
        population_sum = pop_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=100,  # 100m resolution
            maxPixels=1e9
        )
        
        # Get the actual year of data
        data_year = ee.Date(pop_image.get('system:time_start')).format('YYYY')
        
        return {
            "population": population_sum.get('population').getInfo(),
            "data_year": data_year.getInfo(),
            "data_source": "WorldPop",
            "resolution_m": 100
        }
    
    @handle_ee_errors
    def get_basic_land_cover(self, geojson: Dict, year: int = 2023) -> Dict:
        """Get basic land cover statistics using Sentinel-2"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        
        # Load Sentinel-2 data
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        
        # Filter for the year and cloud coverage
        filtered = sentinel2.filterBounds(geometry).filter(
            ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
        ).filter(
            ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)
        )
        
        # Create median composite
        composite = filtered.median()
        
        # Calculate NDVI for vegetation detection
        ndvi = composite.normalizedDifference(['B8', 'B4']).rename('ndvi')
        
        # Calculate basic statistics
        ndvi_stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.stdDev(), '', True
            ).combine(
                ee.Reducer.percentile([10, 50, 90]), '', True
            ),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        
        # Classify into basic categories based on NDVI
        vegetation_threshold = 0.3
        vegetation_mask = ndvi.gt(vegetation_threshold)
        
        # Calculate areas
        pixel_area = ee.Image.pixelArea()
        vegetation_area = vegetation_mask.multiply(pixel_area).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        
        total_area = pixel_area.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        
        veg_area_sqm = vegetation_area.get('ndvi').getInfo()
        total_area_sqm = total_area.get('area').getInfo()
        
        vegetation_percentage = (veg_area_sqm / total_area_sqm * 100) if total_area_sqm > 0 else 0
        
        return {
            "ndvi_statistics": ndvi_stats.getInfo(),
            "vegetation_area_sqm": veg_area_sqm,
            "vegetation_percentage": vegetation_percentage,
            "total_area_sqm": total_area_sqm,
            "data_year": year,
            "data_source": "Sentinel-2"
        }
    
    def analyze_zone(self, geojson: Dict, options: Optional[Dict] = None) -> Dict:
        """Perform comprehensive zone analysis with all available data"""
        if not self.initialized:
            return {"error": "not_initialized", "message": "Earth Engine not initialized"}
        
        options = options or {}
        results = {
            "analysis_timestamp": datetime.datetime.utcnow().isoformat(),
            "zone_geometry": geojson
        }
        
        # Get zone area
        area_data = self.get_zone_area(geojson)
        if not area_data.get("error"):
            results["area"] = area_data
        
        # Get building statistics
        if options.get("include_buildings", True):
            building_data = self.get_building_statistics(
                geojson, 
                options.get("building_confidence", 0.75)
            )
            if not building_data.get("error"):
                results["buildings"] = building_data
        
        # Get population estimate
        if options.get("include_population", True):
            population_data = self.get_population_estimate(
                geojson,
                options.get("population_year", 2020)
            )
            if not population_data.get("error"):
                results["population"] = population_data
        
        # Get land cover data
        if options.get("include_land_cover", True):
            land_cover_data = self.get_basic_land_cover(
                geojson,
                options.get("land_cover_year", 2023)
            )
            if not land_cover_data.get("error"):
                results["land_cover"] = land_cover_data
        
        # Calculate waste generation estimate
        if "population" in results and results["population"].get("population"):
            population = results["population"]["population"]
            # Simple waste generation calculation
            # Average waste generation per capita in Lusaka: 0.5 kg/person/day
            daily_waste_kg = population * 0.5
            monthly_waste_tons = (daily_waste_kg * 30) / 1000
            
            results["waste_estimate"] = {
                "daily_waste_kg": daily_waste_kg,
                "monthly_waste_tons": monthly_waste_tons,
                "per_capita_kg_day": 0.5,
                "calculation_method": "simple_per_capita"
            }
        
        return results


# Convenience function for backward compatibility
def create_analyzer(config=None):
    """Create an Earth Engine analyzer instance"""
    if config and hasattr(config, 'GEE_SERVICE_ACCOUNT') and hasattr(config, 'GEE_KEY_FILE'):
        return EarthEngineCore(
            service_account=config.GEE_SERVICE_ACCOUNT,
            key_file=config.GEE_KEY_FILE
        )
    else:
        return EarthEngineCore()
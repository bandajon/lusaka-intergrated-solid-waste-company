"""
Population analysis module for Earth Engine
Handles multiple population datasets and provides unified interface
"""
import ee
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from .earth_engine_simplified import handle_ee_errors, logger


class PopulationAnalyzer:
    """Population analysis using multiple Earth Engine datasets"""
    
    def __init__(self, ee_initialized: bool = True):
        """Initialize population analyzer"""
        self.initialized = ee_initialized
        self.datasets = {
            'worldpop': {
                'collection': 'WorldPop/GP/100m/pop',
                'band': 'population',
                'scale': 100,
                'description': 'WorldPop Global Population'
            },
            'ghsl': {
                'collection': 'JRC/GHSL/P2023A/GHS_POP',
                'band': 'b1',
                'scale': 100,
                'description': 'Global Human Settlement Layer'
            }
        }
    
    @handle_ee_errors
    def get_population_estimate(self, geojson: Dict, year: int = 2020, 
                              dataset: str = 'worldpop') -> Dict:
        """Get population estimate from specified dataset"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        if dataset not in self.datasets:
            return {"error": "invalid_dataset", "available": list(self.datasets.keys())}
        
        geometry = ee.Geometry(geojson['geometry'])
        dataset_info = self.datasets[dataset]
        
        # Get population data based on dataset type
        if dataset == 'worldpop':
            result = self._get_worldpop_population(geometry, year, dataset_info)
        elif dataset == 'ghsl':
            result = self._get_ghsl_population(geometry, year, dataset_info)
        else:
            result = {"error": "dataset_not_implemented"}
        
        return result
    
    @handle_ee_errors
    def _get_worldpop_population(self, geometry: ee.Geometry, year: int, 
                                dataset_info: Dict) -> Dict:
        """Get population from WorldPop dataset"""
        collection = ee.ImageCollection(dataset_info['collection'])
        
        # Filter for the specified year
        yearly_image = collection.filter(
            ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
        ).first()
        
        if not yearly_image:
            # Get the most recent available year
            yearly_image = collection.sort('system:time_start', False).first()
            actual_year = ee.Date(yearly_image.get('system:time_start')).format('YYYY')
        else:
            actual_year = str(year)
        
        # Calculate population sum
        population_sum = yearly_image.select(dataset_info['band']).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=dataset_info['scale'],
            maxPixels=1e9
        )
        
        # Calculate additional statistics
        population_stats = yearly_image.select(dataset_info['band']).reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.stdDev(), '', True
            ).combine(
                ee.Reducer.max(), '', True
            ),
            geometry=geometry,
            scale=dataset_info['scale'],
            maxPixels=1e9
        )
        
        return {
            "population": population_sum.get(dataset_info['band']).getInfo(),
            "statistics": population_stats.getInfo(),
            "data_year": actual_year.getInfo(),
            "requested_year": year,
            "dataset": dataset_info['description'],
            "resolution_m": dataset_info['scale']
        }
    
    @handle_ee_errors
    def _get_ghsl_population(self, geometry: ee.Geometry, year: int, 
                           dataset_info: Dict) -> Dict:
        """Get population from GHSL dataset"""
        # GHSL has specific epoch years
        available_years = [1975, 1990, 2000, 2015, 2020, 2025, 2030]
        
        # Find closest available year
        closest_year = min(available_years, key=lambda x: abs(x - year))
        
        # Construct image ID for the specific year
        image_id = f"{dataset_info['collection']}/GHS_POP_E{closest_year}_GLOBE_R2023A_54009_100_V1_0"
        
        try:
            ghsl_image = ee.Image(image_id)
            
            # Calculate population sum
            population_sum = ghsl_image.select(dataset_info['band']).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=dataset_info['scale'],
                maxPixels=1e9
            )
            
            # Calculate density (people per hectare)
            area_hectares = geometry.area().divide(10000)
            population_value = ee.Number(population_sum.get(dataset_info['band']))
            density = population_value.divide(area_hectares)
            
            return {
                "population": population_value.getInfo(),
                "population_density_per_hectare": density.getInfo(),
                "data_year": closest_year,
                "requested_year": year,
                "dataset": dataset_info['description'],
                "resolution_m": dataset_info['scale'],
                "epoch_note": f"Using epoch year {closest_year} (closest to {year})"
            }
            
        except Exception as e:
            logger.error(f"GHSL data error for year {closest_year}: {e}")
            return {"error": "ghsl_data_unavailable", "year": closest_year}
    
    @handle_ee_errors
    def get_multi_dataset_estimate(self, geojson: Dict, year: int = 2020) -> Dict:
        """Get population estimates from multiple datasets for comparison"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        results = {}
        
        # Get estimates from each available dataset
        for dataset_name in self.datasets:
            result = self.get_population_estimate(geojson, year, dataset_name)
            results[dataset_name] = result
        
        # Calculate consensus estimate
        valid_estimates = [
            r['population'] for r in results.values() 
            if 'population' in r and r['population'] is not None
        ]
        
        if valid_estimates:
            avg_population = sum(valid_estimates) / len(valid_estimates)
            min_population = min(valid_estimates)
            max_population = max(valid_estimates)
            
            consensus = {
                "average_population": round(avg_population),
                "min_population": round(min_population),
                "max_population": round(max_population),
                "variance": round(max_population - min_population),
                "confidence": "high" if (max_population - min_population) / avg_population < 0.2 else "medium"
            }
        else:
            consensus = {"error": "no_valid_estimates"}
        
        return {
            "individual_estimates": results,
            "consensus": consensus,
            "analysis_year": year,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @handle_ee_errors
    def get_population_density_map(self, geojson: Dict, year: int = 2020,
                                 dataset: str = 'worldpop') -> Dict:
        """Get population density statistics for visualization"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        if dataset not in self.datasets:
            return {"error": "invalid_dataset"}
        
        geometry = ee.Geometry(geojson['geometry'])
        dataset_info = self.datasets[dataset]
        
        # Get the appropriate population image
        if dataset == 'worldpop':
            collection = ee.ImageCollection(dataset_info['collection'])
            pop_image = collection.filter(
                ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
            ).first()
            
            if not pop_image:
                pop_image = collection.sort('system:time_start', False).first()
        else:
            # GHSL - use closest epoch
            available_years = [1975, 1990, 2000, 2015, 2020, 2025, 2030]
            closest_year = min(available_years, key=lambda x: abs(x - year))
            image_id = f"{dataset_info['collection']}/GHS_POP_E{closest_year}_GLOBE_R2023A_54009_100_V1_0"
            pop_image = ee.Image(image_id)
        
        # Calculate density classes
        pop_band = pop_image.select(dataset_info['band'])
        
        # Define density thresholds (people per pixel)
        # Adjust based on pixel size (100m x 100m = 1 hectare)
        density_thresholds = [0, 10, 50, 100, 200, 500]  # people per hectare
        
        # Calculate area for each density class
        density_areas = {}
        
        for i in range(len(density_thresholds) - 1):
            min_threshold = density_thresholds[i]
            max_threshold = density_thresholds[i + 1]
            
            mask = pop_band.gte(min_threshold).And(pop_band.lt(max_threshold))
            area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=dataset_info['scale'],
                maxPixels=1e8
            )
            
            density_areas[f"{min_threshold}-{max_threshold}"] = {
                "area_sqm": area.getInfo(),
                "threshold_range": f"{min_threshold}-{max_threshold} people/hectare"
            }
        
        # Very high density
        very_high_mask = pop_band.gte(density_thresholds[-1])
        very_high_area = very_high_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=dataset_info['scale'],
            maxPixels=1e8
        )
        
        density_areas[f"{density_thresholds[-1]}+"] = {
            "area_sqm": very_high_area.getInfo(),
            "threshold_range": f"{density_thresholds[-1]}+ people/hectare"
        }
        
        return {
            "density_distribution": density_areas,
            "dataset": dataset_info['description'],
            "year": year,
            "scale_m": dataset_info['scale'],
            "density_classes": [
                {"range": "0-10", "description": "Very Low"},
                {"range": "10-50", "description": "Low"},
                {"range": "50-100", "description": "Medium"},
                {"range": "100-200", "description": "High"},
                {"range": "200-500", "description": "Very High"},
                {"range": "500+", "description": "Extremely High"}
            ]
        }
    
    @handle_ee_errors
    def calculate_population_growth(self, geojson: Dict, start_year: int = 2015,
                                  end_year: int = 2020, dataset: str = 'worldpop') -> Dict:
        """Calculate population growth between two years"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        # Get population for both years
        start_pop = self.get_population_estimate(geojson, start_year, dataset)
        end_pop = self.get_population_estimate(geojson, end_year, dataset)
        
        if start_pop.get("error") or end_pop.get("error"):
            return {"error": "failed_to_get_population_data"}
        
        start_value = start_pop.get("population", 0)
        end_value = end_pop.get("population", 0)
        
        if start_value > 0:
            absolute_growth = end_value - start_value
            growth_rate = ((end_value - start_value) / start_value) * 100
            annual_growth_rate = growth_rate / (end_year - start_year)
        else:
            absolute_growth = end_value
            growth_rate = 100 if end_value > 0 else 0
            annual_growth_rate = growth_rate / (end_year - start_year)
        
        return {
            "start_year": start_year,
            "end_year": end_year,
            "start_population": round(start_value),
            "end_population": round(end_value),
            "absolute_growth": round(absolute_growth),
            "growth_rate_percent": round(growth_rate, 2),
            "annual_growth_rate_percent": round(annual_growth_rate, 2),
            "dataset": dataset,
            "projection_2030": round(end_value * (1 + annual_growth_rate/100) ** (2030 - end_year))
        }
"""
Specialized building analysis module for Earth Engine
Handles advanced building detection and classification
"""
import ee
from typing import Dict, Optional, List, Tuple
from .earth_engine_simplified import handle_ee_errors, logger


class BuildingAnalyzer:
    """Advanced building analysis using Google Open Buildings and Earth Engine"""
    
    def __init__(self, ee_initialized: bool = True):
        """Initialize building analyzer"""
        self.initialized = ee_initialized
        self._building_dataset = 'GOOGLE/Research/open-buildings/v3/polygons'
        self._temporal_dataset = 'GOOGLE/Research/open-buildings-temporal/v1'
    
    @handle_ee_errors
    def get_detailed_building_analysis(self, geojson: Dict, options: Optional[Dict] = None) -> Dict:
        """Get detailed building analysis including size distribution and patterns"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        options = options or {}
        confidence_threshold = options.get('confidence_threshold', 0.75)
        
        geometry = ee.Geometry(geojson['geometry'])
        buildings = ee.FeatureCollection(self._building_dataset)
        
        # Filter buildings
        filtered = buildings.filterBounds(geometry).filter(
            ee.Filter.gte('confidence', confidence_threshold)
        )
        
        # Add area calculation
        def calculate_building_metrics(feature):
            area = feature.geometry().area()
            perimeter = feature.geometry().perimeter()
            # Simple compactness measure
            compactness = ee.Number(4).multiply(3.14159).multiply(area).divide(
                perimeter.pow(2)
            )
            return feature.set({
                'area_sqm': area,
                'perimeter_m': perimeter,
                'compactness': compactness
            })
        
        buildings_with_metrics = filtered.map(calculate_building_metrics)
        
        # Get size distribution
        size_distribution = self._calculate_size_distribution(buildings_with_metrics)
        
        # Get pattern analysis
        pattern_analysis = self._analyze_building_patterns(buildings_with_metrics, geometry)
        
        # Aggregate statistics
        stats = self._aggregate_building_statistics(buildings_with_metrics)
        
        return {
            "total_buildings": filtered.size().getInfo(),
            "confidence_threshold": confidence_threshold,
            "statistics": stats,
            "size_distribution": size_distribution,
            "pattern_analysis": pattern_analysis,
            "data_source": "Google Open Buildings v3"
        }
    
    @handle_ee_errors
    def _calculate_size_distribution(self, buildings: ee.FeatureCollection) -> Dict:
        """Calculate building size distribution"""
        # Define size categories (in square meters)
        size_categories = [
            (0, 50, 'very_small'),
            (50, 100, 'small'),
            (100, 200, 'medium'),
            (200, 500, 'large'),
            (500, float('inf'), 'very_large')
        ]
        
        distribution = {}
        
        for min_size, max_size, category in size_categories:
            if max_size == float('inf'):
                filter_condition = ee.Filter.gte('area_sqm', min_size)
            else:
                filter_condition = ee.Filter.And(
                    ee.Filter.gte('area_sqm', min_size),
                    ee.Filter.lt('area_sqm', max_size)
                )
            
            count = buildings.filter(filter_condition).size()
            distribution[category] = {
                'count': count.getInfo(),
                'range_sqm': f"{min_size}-{max_size if max_size != float('inf') else '+'}"
            }
        
        return distribution
    
    @handle_ee_errors
    def _analyze_building_patterns(self, buildings: ee.FeatureCollection, zone_geometry: ee.Geometry) -> Dict:
        """Analyze spatial patterns of buildings"""
        # Calculate building density and clustering metrics
        building_count = buildings.size()
        zone_area = zone_geometry.area()
        
        # Density calculation
        density = building_count.divide(zone_area.divide(1000000))  # buildings per sq km
        
        # Average nearest neighbor distance (simplified)
        # This is a proxy for clustering - closer buildings indicate higher density areas
        
        # Get average building size and compactness
        avg_metrics = buildings.reduceColumns(
            reducer=ee.Reducer.mean().repeat(3),
            selectors=['area_sqm', 'perimeter_m', 'compactness']
        )
        
        return {
            "building_density_per_sqkm": density.getInfo(),
            "average_metrics": avg_metrics.getInfo(),
            "pattern_classification": self._classify_settlement_pattern(
                density.getInfo(),
                avg_metrics.getInfo()
            )
        }
    
    def _classify_settlement_pattern(self, density: float, avg_metrics: Dict) -> Dict:
        """Classify settlement pattern based on density and building characteristics"""
        # Simple classification based on Lusaka patterns
        pattern_type = "unknown"
        confidence = 0.5
        
        avg_area = avg_metrics.get('mean', [0])[0] if avg_metrics.get('mean') else 0
        
        if density > 150 and avg_area < 80:
            pattern_type = "high_density_informal"
            confidence = 0.8
        elif density > 100 and avg_area < 120:
            pattern_type = "medium_density_mixed"
            confidence = 0.7
        elif density < 50 and avg_area > 150:
            pattern_type = "low_density_formal"
            confidence = 0.8
        elif density < 100 and avg_area > 100:
            pattern_type = "medium_density_formal"
            confidence = 0.7
        
        return {
            "pattern_type": pattern_type,
            "confidence": confidence,
            "characteristics": {
                "density_class": "high" if density > 100 else "medium" if density > 50 else "low",
                "building_size_class": "small" if avg_area < 100 else "medium" if avg_area < 200 else "large"
            }
        }
    
    @handle_ee_errors
    def _aggregate_building_statistics(self, buildings: ee.FeatureCollection) -> Dict:
        """Aggregate comprehensive building statistics"""
        # Calculate various statistics
        area_stats = buildings.aggregate_stats('area_sqm')
        confidence_stats = buildings.aggregate_stats('confidence')
        compactness_stats = buildings.aggregate_stats('compactness')
        
        return {
            "area": area_stats.getInfo(),
            "confidence": confidence_stats.getInfo(),
            "compactness": compactness_stats.getInfo()
        }
    
    @handle_ee_errors
    def estimate_building_heights(self, geojson: Dict, year: int = 2023) -> Dict:
        """Estimate building heights using temporal data if available"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        geometry = ee.Geometry(geojson['geometry'])
        
        try:
            # Try to load temporal building data
            temporal_data = ee.ImageCollection(self._temporal_dataset)
            
            # Filter by year and geometry
            filtered = temporal_data.filter(
                ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
            ).filterBounds(geometry)
            
            if filtered.size().getInfo() > 0:
                # Use actual height data
                height_image = filtered.first().select('building_height')
                
                height_stats = height_image.reduceRegion(
                    reducer=ee.Reducer.percentile([10, 25, 50, 75, 90]).combine(
                        ee.Reducer.mean(), '', True
                    ).combine(
                        ee.Reducer.stdDev(), '', True
                    ),
                    geometry=geometry,
                    scale=10,
                    maxPixels=1e9
                )
                
                return {
                    "height_statistics": height_stats.getInfo(),
                    "data_source": "temporal_data",
                    "year": year
                }
            else:
                # Fall back to estimates based on building size
                return self._estimate_heights_from_size(geojson)
                
        except Exception as e:
            logger.warning(f"Could not load temporal data: {e}")
            return self._estimate_heights_from_size(geojson)
    
    def _estimate_heights_from_size(self, geojson: Dict) -> Dict:
        """Estimate building heights based on building footprint size"""
        # Enhanced heuristic based on research showing 3D improves accuracy
        # Based on typical Lusaka building patterns
        
        building_analysis = self.get_detailed_building_analysis(geojson)
        if building_analysis.get("error"):
            return building_analysis
        
        size_dist = building_analysis.get("size_distribution", {})
        pattern_type = building_analysis.get("pattern_analysis", {}).get("pattern_classification", {}).get("pattern_type", "unknown")
        
        # Enhanced height estimates by category and pattern type
        height_estimates = {
            "very_small": {
                "formal": {"avg_height_m": 3.5, "floors": 1, "volume_factor": 0.85},
                "informal": {"avg_height_m": 3.0, "floors": 1, "volume_factor": 0.75},
                "mixed": {"avg_height_m": 3.2, "floors": 1, "volume_factor": 0.80}
            },
            "small": {
                "formal": {"avg_height_m": 4.0, "floors": 1.2, "volume_factor": 0.90},
                "informal": {"avg_height_m": 3.5, "floors": 1, "volume_factor": 0.80},
                "mixed": {"avg_height_m": 3.8, "floors": 1.1, "volume_factor": 0.85}
            },
            "medium": {
                "formal": {"avg_height_m": 7.0, "floors": 2, "volume_factor": 0.95},
                "informal": {"avg_height_m": 4.5, "floors": 1.5, "volume_factor": 0.85},
                "mixed": {"avg_height_m": 6.0, "floors": 1.8, "volume_factor": 0.90}
            },
            "large": {
                "formal": {"avg_height_m": 10.5, "floors": 3, "volume_factor": 1.0},
                "informal": {"avg_height_m": 6.0, "floors": 2, "volume_factor": 0.90},
                "mixed": {"avg_height_m": 9.0, "floors": 2.5, "volume_factor": 0.95}
            },
            "very_large": {
                "formal": {"avg_height_m": 14.0, "floors": 4, "volume_factor": 1.0},
                "informal": {"avg_height_m": 7.0, "floors": 2, "volume_factor": 0.85},
                "mixed": {"avg_height_m": 12.0, "floors": 3.5, "volume_factor": 0.95}
            }
        }
        
        # Determine settlement pattern
        settlement_pattern = "mixed"  # default
        if "formal" in pattern_type.lower():
            settlement_pattern = "formal"
        elif "informal" in pattern_type.lower():
            settlement_pattern = "informal"
        
        # Calculate weighted average with volume considerations
        total_buildings = sum(cat.get("count", 0) for cat in size_dist.values())
        
        if total_buildings > 0:
            weighted_height = 0
            weighted_floors = 0
            weighted_volume_factor = 0
            
            for size_cat, count_info in size_dist.items():
                count = count_info.get("count", 0)
                if count > 0 and size_cat in height_estimates:
                    estimates = height_estimates[size_cat].get(settlement_pattern, height_estimates[size_cat]["mixed"])
                    weight = count / total_buildings
                    
                    weighted_height += estimates["avg_height_m"] * weight
                    weighted_floors += estimates["floors"] * weight
                    weighted_volume_factor += estimates["volume_factor"] * weight
        else:
            weighted_height = 3.5
            weighted_floors = 1
            weighted_volume_factor = 0.85
        
        # Calculate volume estimates
        avg_area = building_analysis.get("statistics", {}).get("area", {}).get("mean", 100)
        estimated_avg_volume = avg_area * weighted_height * weighted_volume_factor
        
        return {
            "estimated_avg_height_m": round(weighted_height, 1),
            "estimated_avg_floors": round(weighted_floors, 1),
            "estimated_avg_volume_m3": round(estimated_avg_volume, 0),
            "volume_factor": round(weighted_volume_factor, 2),
            "estimation_method": "enhanced_size_based_heuristic",
            "settlement_pattern": settlement_pattern,
            "size_distribution": size_dist,
            "confidence_level": "medium" if total_buildings > 10 else "low"
        }
    
    @handle_ee_errors
    def detect_building_changes(self, geojson: Dict, start_year: int, end_year: int) -> Dict:
        """Detect building changes between two time periods"""
        if not self.initialized:
            return {"error": "not_initialized"}
        
        # This is a simplified version - full implementation would compare
        # actual building footprints between periods
        
        geometry = ee.Geometry(geojson['geometry'])
        buildings = ee.FeatureCollection(self._building_dataset)
        
        # For now, return a structure showing what this analysis would provide
        return {
            "analysis_period": f"{start_year}-{end_year}",
            "status": "simplified_analysis",
            "message": "Full temporal analysis requires additional data processing",
            "available_metrics": [
                "new_buildings_count",
                "demolished_buildings_count", 
                "total_area_change_sqm",
                "growth_rate_percent"
            ]
        }
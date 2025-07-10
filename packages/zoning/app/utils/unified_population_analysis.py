"""
Unified Population Analysis Service
Integrates best practices for population estimation using 3D building data,
settlement classification, and multiple data sources
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

# Import existing modules
from .earth_engine_buildings import BuildingAnalyzer
from .population_estimation import PopulationEstimator
from .dasymetric_mapping import DasymetricMapper
from .settlement_classification import SettlementClassifier
from .population_service import get_earth_engine_population

logger = logging.getLogger(__name__)


class UnifiedPopulationAnalyzer:
    """
    Unified service for population analysis incorporating:
    - 3D building analysis (volume-based estimation)
    - Building use classification
    - Multi-source data integration
    - Scale-aware estimation
    - Uncertainty quantification
    """
    
    def __init__(self):
        """Initialize unified analyzer with all components"""
        self.building_analyzer = BuildingAnalyzer()
        self.population_estimator = PopulationEstimator()
        self.dasymetric_mapper = DasymetricMapper()
        self.settlement_classifier = SettlementClassifier()
        
        # Scale-based accuracy thresholds (based on research)
        self.scale_thresholds = {
            'block': {'min_area_km2': 0.01, 'expected_error': 0.3},      # 30% error
            'neighborhood': {'min_area_km2': 0.1, 'expected_error': 0.15}, # 15% error
            'district': {'min_area_km2': 1.0, 'expected_error': 0.08},     # 8% error
            'city': {'min_area_km2': 10.0, 'expected_error': 0.03}        # 3% error
        }
        
        # Building use classification rules
        self.building_use_rules = {
            'residential_indicators': ['small_footprint', 'regular_shape', 'clustered'],
            'commercial_indicators': ['large_footprint', 'irregular_shape', 'isolated'],
            'mixed_indicators': ['medium_footprint', 'variable_shape', 'mixed_clustering']
        }
    
    def analyze_population(self, geojson: Dict, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive population analysis
        
        Args:
            geojson: Zone geometry in GeoJSON format
            options: Analysis options (methods, data_sources, etc.)
            
        Returns:
            Comprehensive population analysis results
        """
        logger.info("Starting unified population analysis...")
        start_time = datetime.now()
        
        options = options or {}
        
        # Step 1: Analyze zone scale
        scale_analysis = self._analyze_zone_scale(geojson)
        
        # Step 2: Get building data with 3D analysis
        building_analysis = self._analyze_buildings_3d(geojson, options)
        
        # Step 3: Classify buildings by use
        building_classification = self._classify_building_use(building_analysis)
        
        # Step 4: Get population from multiple sources
        multi_source_population = self._get_multi_source_population(geojson)
        
        # Step 5: Perform volume-based estimation
        volume_estimation = self._estimate_population_volume_based(
            building_analysis, 
            building_classification
        )
        
        # Step 6: Apply dasymetric refinement
        dasymetric_result = self._apply_dasymetric_refinement(
            multi_source_population,
            building_analysis,
            building_classification
        )
        
        # Step 7: Calculate ensemble estimate with uncertainty
        ensemble_result = self._calculate_ensemble_estimate(
            volume_estimation,
            dasymetric_result,
            multi_source_population,
            scale_analysis
        )
        
        # Step 8: Apply scale-based adjustments
        final_result = self._apply_scale_adjustments(ensemble_result, scale_analysis)
        
        # Add metadata
        final_result['analysis_metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
            'scale_category': scale_analysis['category'],
            'confidence_level': self._calculate_confidence_level(final_result),
            'data_completeness': self._assess_data_completeness(building_analysis, multi_source_population)
        }
        
        logger.info(f"Unified population analysis completed in {final_result['analysis_metadata']['processing_time_seconds']:.2f} seconds")
        return final_result
    
    def _analyze_zone_scale(self, geojson: Dict) -> Dict[str, Any]:
        """Analyze the scale of the zone for accuracy expectations"""
        # Calculate area
        # Note: In production, use proper geometric calculations
        area_km2 = geojson.get('properties', {}).get('area_km2', 0.5)
        
        # Determine scale category
        category = 'block'
        for scale_name, thresholds in sorted(self.scale_thresholds.items(), 
                                           key=lambda x: x[1]['min_area_km2']):
            if area_km2 >= thresholds['min_area_km2']:
                category = scale_name
        
        return {
            'area_km2': area_km2,
            'category': category,
            'expected_error': self.scale_thresholds[category]['expected_error'],
            'recommendation': self._get_scale_recommendation(category)
        }
    
    def _get_scale_recommendation(self, category: str) -> str:
        """Get recommendation based on scale"""
        recommendations = {
            'block': "Consider aggregating with neighboring blocks for better accuracy",
            'neighborhood': "Good scale for population estimation",
            'district': "Excellent scale for accurate population estimation",
            'city': "Ideal scale for population analysis with minimal error"
        }
        return recommendations.get(category, "Analyze at appropriate scale")
    
    def _analyze_buildings_3d(self, geojson: Dict, options: Dict) -> Dict[str, Any]:
        """Analyze buildings with 3D data"""
        # Get detailed building analysis
        building_data = self.building_analyzer.get_detailed_building_analysis(geojson, options)
        
        # Get height/volume estimates
        height_data = self.building_analyzer.estimate_building_heights(geojson)
        
        # Combine results
        return {
            'building_analysis': building_data,
            'height_estimates': height_data,
            'total_buildings': building_data.get('total_buildings', 0),
            'has_3d_data': height_data.get('data_source') == 'temporal_data'
        }
    
    def _classify_building_use(self, building_analysis: Dict) -> Dict[str, Any]:
        """Classify buildings by use (residential vs non-residential)"""
        # Get settlement classification
        settlement_result = self.settlement_classifier.classify_settlement(
            building_analysis.get('building_analysis', {})
        )
        
        # Analyze building patterns for use classification
        size_distribution = building_analysis.get('building_analysis', {}).get('size_distribution', {})
        
        # Simple classification based on size and pattern
        residential_ratio = 0.7  # Default
        
        if settlement_result.get('classification') == 'formal':
            # Formal areas: larger buildings might be commercial
            large_building_ratio = (
                size_distribution.get('large', {}).get('count', 0) +
                size_distribution.get('very_large', {}).get('count', 0)
            ) / max(1, building_analysis.get('total_buildings', 1))
            
            residential_ratio = max(0.5, 0.8 - large_building_ratio)
            
        elif settlement_result.get('classification') == 'informal':
            # Informal areas: mostly residential
            residential_ratio = 0.9
        
        return {
            'settlement_classification': settlement_result,
            'residential_ratio': residential_ratio,
            'commercial_ratio': 1 - residential_ratio,
            'classification_confidence': settlement_result.get('confidence', 0.5)
        }
    
    def _get_multi_source_population(self, geojson: Dict) -> Dict[str, Any]:
        """Get population estimates from multiple sources"""
        sources = {}
        
        # Earth Engine population
        ee_pop = get_earth_engine_population(geojson)
        if ee_pop.get('success'):
            sources['earth_engine'] = {
                'population': ee_pop.get('estimated_population', 0),
                'source': ee_pop.get('data_source', 'unknown'),
                'confidence': 0.8 if ee_pop.get('confidence_level') == 'high' else 0.5
            }
        
        # Add other sources as available
        # sources['census'] = {...}
        # sources['mobile_data'] = {...}
        
        return {
            'sources': sources,
            'source_count': len(sources),
            'has_high_quality_source': any(s.get('confidence', 0) > 0.7 for s in sources.values())
        }
    
    def _estimate_population_volume_based(self, building_analysis: Dict, 
                                        building_classification: Dict) -> Dict[str, Any]:
        """Estimate population using 3D volume data"""
        height_data = building_analysis.get('height_estimates', {})
        building_stats = building_analysis.get('building_analysis', {})
        
        # Get volume estimates
        avg_height = height_data.get('estimated_avg_height_m', 3.5)
        avg_volume = height_data.get('estimated_avg_volume_m3', 350)
        total_buildings = building_analysis.get('total_buildings', 0)
        
        # Apply residential ratio
        residential_ratio = building_classification.get('residential_ratio', 0.7)
        residential_buildings = total_buildings * residential_ratio
        
        # Volume-based estimation (people per cubic meter)
        # Based on research: 1 person per 35-50 m³ in residential buildings
        if building_classification.get('settlement_classification', {}).get('classification') == 'informal':
            people_per_m3 = 1 / 35  # Higher density
        else:
            people_per_m3 = 1 / 50  # Lower density
        
        # Calculate population
        total_residential_volume = residential_buildings * avg_volume
        volume_based_population = total_residential_volume * people_per_m3
        
        # Add commercial/mixed use population
        commercial_population = (total_buildings - residential_buildings) * 2  # 2 workers per commercial building average
        
        return {
            'method': 'volume_based',
            'residential_population': int(volume_based_population),
            'commercial_population': int(commercial_population),
            'total_population': int(volume_based_population + commercial_population),
            'avg_building_volume_m3': avg_volume,
            'people_per_m3': people_per_m3,
            'confidence': 0.7 if height_data.get('has_3d_data') else 0.5
        }
    
    def _apply_dasymetric_refinement(self, multi_source_pop: Dict,
                                    building_analysis: Dict,
                                    building_classification: Dict) -> Dict[str, Any]:
        """Apply dasymetric mapping for refined distribution"""
        # Get base population from best available source
        base_population = 0
        best_source = None
        
        for source_name, source_data in multi_source_pop.get('sources', {}).items():
            if source_data.get('confidence', 0) > 0.5:
                base_population = source_data.get('population', 0)
                best_source = source_name
                break
        
        if base_population == 0:
            return {'method': 'dasymetric', 'total_population': 0, 'refined': False}
        
        # Apply building-based redistribution
        building_factor = min(2.0, max(0.5, building_analysis.get('total_buildings', 0) / 50))
        settlement_factor = 1.3 if building_classification.get('settlement_classification', {}).get('classification') == 'informal' else 1.0
        
        refined_population = base_population * building_factor * settlement_factor
        
        return {
            'method': 'dasymetric',
            'base_population': base_population,
            'base_source': best_source,
            'refined_population': int(refined_population),
            'building_factor': building_factor,
            'settlement_factor': settlement_factor,
            'refined': True
        }
    
    def _calculate_ensemble_estimate(self, volume_est: Dict, dasymetric_est: Dict,
                                   multi_source: Dict, scale_analysis: Dict) -> Dict[str, Any]:
        """Calculate ensemble estimate with uncertainty"""
        estimates = []
        weights = []
        
        # Add volume-based estimate
        if volume_est.get('total_population', 0) > 0:
            estimates.append(volume_est['total_population'])
            weights.append(volume_est.get('confidence', 0.5))
        
        # Add dasymetric estimate
        if dasymetric_est.get('refined'):
            estimates.append(dasymetric_est['refined_population'])
            weights.append(0.7)  # Good confidence for dasymetric
        
        # Add source estimates
        for source_data in multi_source.get('sources', {}).values():
            if source_data.get('population', 0) > 0:
                estimates.append(source_data['population'])
                weights.append(source_data.get('confidence', 0.5))
        
        if not estimates:
            return {'ensemble_population': 0, 'confidence_interval': [0, 0], 'uncertainty': 1.0}
        
        # Calculate weighted average
        weights = np.array(weights)
        estimates = np.array(estimates)
        weights = weights / weights.sum()
        
        ensemble_population = int(np.sum(estimates * weights))
        
        # Calculate uncertainty
        std_dev = np.std(estimates)
        cv = std_dev / ensemble_population if ensemble_population > 0 else 1.0
        
        # Confidence interval (95%)
        margin = 1.96 * std_dev
        confidence_interval = [
            max(0, int(ensemble_population - margin)),
            int(ensemble_population + margin)
        ]
        
        return {
            'ensemble_population': ensemble_population,
            'individual_estimates': list(estimates),
            'weights': list(weights),
            'standard_deviation': std_dev,
            'coefficient_of_variation': cv,
            'confidence_interval': confidence_interval,
            'uncertainty': cv
        }
    
    def _apply_scale_adjustments(self, ensemble_result: Dict, scale_analysis: Dict) -> Dict[str, Any]:
        """Apply scale-based adjustments to final estimate"""
        population = ensemble_result['ensemble_population']
        expected_error = scale_analysis['expected_error']
        
        # Adjust confidence interval based on scale
        scale_factor = 1 + expected_error
        adjusted_interval = [
            max(0, int(population / scale_factor)),
            int(population * scale_factor)
        ]
        
        # Determine quality rating
        cv = ensemble_result.get('coefficient_of_variation', 1.0)
        if cv < 0.1 and scale_analysis['category'] in ['district', 'city']:
            quality = 'excellent'
        elif cv < 0.2 and scale_analysis['category'] in ['neighborhood', 'district']:
            quality = 'good'
        elif cv < 0.3:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'final_population_estimate': population,
            'confidence_interval': adjusted_interval,
            'scale_adjusted_interval': adjusted_interval,
            'quality_rating': quality,
            'scale_category': scale_analysis['category'],
            'expected_error_rate': expected_error,
            'recommendations': self._generate_recommendations(quality, scale_analysis),
            'detailed_results': {
                'ensemble': ensemble_result,
                'scale_analysis': scale_analysis
            }
        }
    
    def _calculate_confidence_level(self, result: Dict) -> str:
        """Calculate overall confidence level"""
        quality = result.get('quality_rating', 'poor')
        confidence_map = {
            'excellent': 'very_high',
            'good': 'high',
            'fair': 'medium',
            'poor': 'low'
        }
        return confidence_map.get(quality, 'low')
    
    def _assess_data_completeness(self, building_analysis: Dict, multi_source: Dict) -> float:
        """Assess completeness of input data"""
        scores = []
        
        # Building data completeness
        building_count = building_analysis.get('total_buildings', 0)
        building_score = min(1.0, building_count / 50)  # 50+ buildings = complete
        scores.append(building_score)
        
        # 3D data availability
        has_3d = building_analysis.get('has_3d_data', False)
        scores.append(1.0 if has_3d else 0.5)
        
        # Multi-source data
        source_count = multi_source.get('source_count', 0)
        source_score = min(1.0, source_count / 3)  # 3+ sources = complete
        scores.append(source_score)
        
        return np.mean(scores)
    
    def _generate_recommendations(self, quality: str, scale_analysis: Dict) -> List[str]:
        """Generate recommendations for improving estimates"""
        recommendations = []
        
        if quality in ['poor', 'fair']:
            recommendations.append("Consider analyzing a larger area for better accuracy")
            
        if scale_analysis['category'] == 'block':
            recommendations.append("Aggregate multiple blocks for more reliable estimates")
            
        if quality == 'poor':
            recommendations.append("Collect additional building data or use higher resolution imagery")
            recommendations.append("Verify building use classification through field surveys")
            
        if not recommendations:
            recommendations.append("Current analysis provides reliable population estimates")
            
        return recommendations


# Example usage
def demonstrate_unified_analysis():
    """Demonstrate the unified population analysis"""
    
    # Example zone geometry
    test_zone = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.2, -15.4],
                [28.21, -15.4],
                [28.21, -15.41],
                [28.2, -15.41],
                [28.2, -15.4]
            ]]
        },
        "properties": {
            "area_km2": 1.21,
            "name": "Test Zone"
        }
    }
    
    # Initialize analyzer
    analyzer = UnifiedPopulationAnalyzer()
    
    # Perform analysis
    results = analyzer.analyze_population(test_zone, {
        'confidence_threshold': 0.7,
        'include_commercial': True
    })
    
    # Display results
    print("Unified Population Analysis Results")
    print("=" * 50)
    print(f"Final Population Estimate: {results['final_population_estimate']:,}")
    print(f"Confidence Interval: {results['confidence_interval'][0]:,} - {results['confidence_interval'][1]:,}")
    print(f"Quality Rating: {results['quality_rating']}")
    print(f"Scale Category: {results['scale_category']}")
    print(f"Expected Error Rate: {results['expected_error_rate']:.1%}")
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"  - {rec}")


if __name__ == "__main__":
    demonstrate_unified_analysis() 
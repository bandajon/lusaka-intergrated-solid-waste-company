"""
Building-based Population Estimation System
Estimates population using building characteristics and settlement-specific factors
Based on Task 13 requirements for enhanced population modeling
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from scipy.stats import gamma, lognorm, norm
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PopulationEstimator:
    """
    Building-based population estimation system
    Uses building characteristics, settlement types, and demographic factors
    """
    
    def __init__(self, region: str = "lusaka"):
        """
        Initialize the population estimator
        
        Args:
            region: Geographic region for calibration parameters
        """
        self.region = region.lower()
        
        # Population estimation parameters for Lusaka
        self.lusaka_parameters = {
            # People per unit area (sqm) by settlement type
            'people_per_sqm': {
                'formal': {
                    'residential': 0.08,    # 8 people per 100 sqm
                    'commercial': 0.02,     # 2 people per 100 sqm
                    'mixed': 0.06,          # 6 people per 100 sqm
                    'industrial': 0.01,     # 1 person per 100 sqm
                    'unknown': 0.05         # 5 people per 100 sqm
                },
                'informal': {
                    'residential': 0.15,    # 15 people per 100 sqm (higher density)
                    'commercial': 0.05,     # 5 people per 100 sqm
                    'mixed': 0.12,          # 12 people per 100 sqm
                    'industrial': 0.02,     # 2 people per 100 sqm
                    'unknown': 0.10         # 10 people per 100 sqm
                },
                'mixed': {
                    'residential': 0.11,    # 11 people per 100 sqm
                    'commercial': 0.03,     # 3 people per 100 sqm
                    'mixed': 0.09,          # 9 people per 100 sqm
                    'industrial': 0.015,    # 1.5 people per 100 sqm
                    'unknown': 0.07         # 7 people per 100 sqm
                }
            },
            
            # Floor-based estimation (people per floor)
            'people_per_floor': {
                'formal': {
                    'residential': 3.5,     # Average household size in formal areas
                    'commercial': 1.0,      # Worker density
                    'mixed': 2.5,
                    'industrial': 0.5,
                    'unknown': 2.0
                },
                'informal': {
                    'residential': 4.5,     # Larger household size in informal areas
                    'commercial': 2.0,
                    'mixed': 3.5,
                    'industrial': 1.0,
                    'unknown': 3.0
                },
                'mixed': {
                    'residential': 4.0,
                    'commercial': 1.5,
                    'mixed': 3.0,
                    'industrial': 0.7,
                    'unknown': 2.5
                }
            },
            
            # Building height to floor conversion
            'floor_height': 3.5,  # Average 3.5m per floor
            
            # Settlement density multipliers
            'settlement_density_multipliers': {
                'formal': 1.0,
                'informal': 1.3,    # 30% higher density
                'mixed': 1.15       # 15% higher density
            },
            
            # Building age factors (newer buildings = different occupancy)
            'age_factors': {
                'new': 1.1,         # 10% higher occupancy
                'medium': 1.0,      # Baseline
                'old': 0.9          # 10% lower occupancy
            },
            
            # Seasonal variations
            'seasonal_factors': {
                'dry_season': 0.95,  # 5% lower during dry season (migration)
                'wet_season': 1.05   # 5% higher during wet season
            },
            
            # Uncertainty ranges (coefficient of variation)
            'uncertainty': {
                'area_based': 0.20,    # 20% CV
                'floor_based': 0.25,   # 25% CV
                'settlement_based': 0.15,  # 15% CV
                'combined': 0.18       # 18% CV
            }
        }
        
        # Default to Lusaka parameters
        self.parameters = self.lusaka_parameters
        
        # Estimation results
        self.estimation_results = {}
        self.uncertainty_analysis = {}
        
        # Validation data
        self.validation_data = {}
    
    def estimate_population_area_based(self, building_data: pd.DataFrame, 
                                     settlement_classifications: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Estimate population based on building area and settlement types
        
        Args:
            building_data: DataFrame with building features
            settlement_classifications: Optional settlement type classifications
            
        Returns:
            Dictionary with area-based population estimates
        """
        logger.info("Performing area-based population estimation...")
        
        total_population = 0
        settlement_populations = {}
        building_type_populations = {}
        detailed_estimates = []
        
        # Initialize settlement and building type counters
        for settlement_type in ['formal', 'informal', 'mixed', 'unknown']:
            settlement_populations[settlement_type] = 0
            
        for building_type in ['residential', 'commercial', 'mixed', 'industrial', 'unknown']:
            building_type_populations[building_type] = 0
        
        for idx, building in building_data.iterrows():
            # Get building characteristics
            area = building.get('area', 100)  # Default 100 sqm
            building_type = building.get('building_type', 'unknown')
            
            # Get settlement type
            settlement_type = building.get('settlement_type', 'unknown')
            if settlement_classifications and idx in settlement_classifications:
                settlement_result = settlement_classifications[idx]
                if isinstance(settlement_result, dict):
                    settlement_type = settlement_result.get('classification', 'unknown')
                else:
                    settlement_type = str(settlement_result)
            
            # Ensure settlement type is valid
            if settlement_type not in self.parameters['people_per_sqm']:
                settlement_type = 'mixed'  # Default fallback
            
            # Get population density
            if building_type in self.parameters['people_per_sqm'][settlement_type]:
                people_per_sqm = self.parameters['people_per_sqm'][settlement_type][building_type]
            else:
                people_per_sqm = self.parameters['people_per_sqm'][settlement_type]['unknown']
            
            # Calculate base population
            building_population = area * people_per_sqm
            
            # Apply settlement density multiplier
            settlement_multiplier = self.parameters['settlement_density_multipliers'].get(settlement_type, 1.0)
            building_population *= settlement_multiplier
            
            # Apply building age factor if available
            building_age = building.get('age_category', 'medium')
            age_factor = self.parameters['age_factors'].get(building_age, 1.0)
            building_population *= age_factor
            
            # Update totals
            total_population += building_population
            settlement_populations[settlement_type] += building_population
            building_type_populations[building_type] += building_population
            
            # Store detailed estimate
            detailed_estimates.append({
                'building_id': building.get('id', idx),
                'area': area,
                'building_type': building_type,
                'settlement_type': settlement_type,
                'people_per_sqm': people_per_sqm,
                'settlement_multiplier': settlement_multiplier,
                'age_factor': age_factor,
                'estimated_population': building_population
            })
        
        result = {
            'method': 'area_based',
            'total_population': total_population,
            'settlement_populations': settlement_populations,
            'building_type_populations': building_type_populations,
            'detailed_estimates': detailed_estimates,
            'buildings_processed': len(building_data),
            'average_people_per_building': total_population / len(building_data) if len(building_data) > 0 else 0
        }
        
        logger.info(f"Area-based estimation completed: {total_population:.0f} people from {len(building_data)} buildings")
        return result
    
    def estimate_population_floor_based(self, building_data: pd.DataFrame,
                                      settlement_classifications: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Estimate population based on building floors and settlement types
        
        Args:
            building_data: DataFrame with building features
            settlement_classifications: Optional settlement type classifications
            
        Returns:
            Dictionary with floor-based population estimates
        """
        logger.info("Performing floor-based population estimation...")
        
        total_population = 0
        settlement_populations = {}
        building_type_populations = {}
        detailed_estimates = []
        
        # Initialize counters
        for settlement_type in ['formal', 'informal', 'mixed', 'unknown']:
            settlement_populations[settlement_type] = 0
            
        for building_type in ['residential', 'commercial', 'mixed', 'industrial', 'unknown']:
            building_type_populations[building_type] = 0
        
        for idx, building in building_data.iterrows():
            # Get building characteristics
            height = building.get('height', 4.0)  # Default single story
            building_type = building.get('building_type', 'unknown')
            
            # Calculate number of floors
            floors = max(1, int(height / self.parameters['floor_height']))
            
            # Get settlement type
            settlement_type = building.get('settlement_type', 'unknown')
            if settlement_classifications and idx in settlement_classifications:
                settlement_result = settlement_classifications[idx]
                if isinstance(settlement_result, dict):
                    settlement_type = settlement_result.get('classification', 'unknown')
                else:
                    settlement_type = str(settlement_result)
            
            # Ensure settlement type is valid
            if settlement_type not in self.parameters['people_per_floor']:
                settlement_type = 'mixed'
            
            # Get people per floor
            if building_type in self.parameters['people_per_floor'][settlement_type]:
                people_per_floor = self.parameters['people_per_floor'][settlement_type][building_type]
            else:
                people_per_floor = self.parameters['people_per_floor'][settlement_type]['unknown']
            
            # Calculate building population
            building_population = floors * people_per_floor
            
            # Apply settlement density multiplier
            settlement_multiplier = self.parameters['settlement_density_multipliers'].get(settlement_type, 1.0)
            building_population *= settlement_multiplier
            
            # Update totals
            total_population += building_population
            settlement_populations[settlement_type] += building_population
            building_type_populations[building_type] += building_population
            
            # Store detailed estimate
            detailed_estimates.append({
                'building_id': building.get('id', idx),
                'height': height,
                'floors': floors,
                'building_type': building_type,
                'settlement_type': settlement_type,
                'people_per_floor': people_per_floor,
                'settlement_multiplier': settlement_multiplier,
                'estimated_population': building_population
            })
        
        result = {
            'method': 'floor_based',
            'total_population': total_population,
            'settlement_populations': settlement_populations,
            'building_type_populations': building_type_populations,
            'detailed_estimates': detailed_estimates,
            'buildings_processed': len(building_data),
            'average_floors_per_building': np.mean([est['floors'] for est in detailed_estimates]) if detailed_estimates else 0
        }
        
        logger.info(f"Floor-based estimation completed: {total_population:.0f} people from {len(building_data)} buildings")
        return result
    
    def estimate_population_settlement_based(self, building_data: pd.DataFrame,
                                           settlement_classifications: Optional[Dict] = None,
                                           zone_area_sqm: Optional[float] = None) -> Dict[str, Any]:
        """
        Estimate population based on settlement-specific density patterns
        
        Args:
            building_data: DataFrame with building features
            settlement_classifications: Optional settlement type classifications
            zone_area_sqm: Optional zone area for density calculations
            
        Returns:
            Dictionary with settlement-based population estimates
        """
        logger.info("Performing settlement-based population estimation...")
        
        # Analyze settlement composition
        settlement_composition = {'formal': 0, 'informal': 0, 'mixed': 0, 'unknown': 0}
        total_building_area = 0
        
        for idx, building in building_data.iterrows():
            area = building.get('area', 100)
            total_building_area += area
            
            # Get settlement type
            settlement_type = building.get('settlement_type', 'unknown')
            if settlement_classifications and idx in settlement_classifications:
                settlement_result = settlement_classifications[idx]
                if isinstance(settlement_result, dict):
                    settlement_type = settlement_result.get('classification', 'unknown')
                else:
                    settlement_type = str(settlement_result)
            
            if settlement_type in settlement_composition:
                settlement_composition[settlement_type] += area
            else:
                settlement_composition['unknown'] += area
        
        # Calculate settlement-based estimates
        settlement_populations = {}
        total_population = 0
        
        for settlement_type, total_area in settlement_composition.items():
            if total_area > 0:
                # Use weighted average of settlement-specific densities
                if settlement_type in self.parameters['people_per_sqm']:
                    type_densities = self.parameters['people_per_sqm'][settlement_type]
                    avg_density = np.mean(list(type_densities.values()))
                else:
                    avg_density = 0.07  # Default density
                
                # Apply settlement multiplier
                settlement_multiplier = self.parameters['settlement_density_multipliers'].get(settlement_type, 1.0)
                adjusted_density = avg_density * settlement_multiplier
                
                # Calculate population for this settlement type
                settlement_pop = total_area * adjusted_density
                settlement_populations[settlement_type] = settlement_pop
                total_population += settlement_pop
        
        # Calculate area efficiency metrics
        if zone_area_sqm:
            building_coverage_ratio = total_building_area / zone_area_sqm
            population_density_per_sqkm = (total_population / zone_area_sqm) * 1000000
        else:
            building_coverage_ratio = 0.3  # Assumed 30% coverage
            population_density_per_sqkm = 0
        
        result = {
            'method': 'settlement_based',
            'total_population': total_population,
            'settlement_populations': settlement_populations,
            'settlement_composition_sqm': settlement_composition,
            'total_building_area': total_building_area,
            'building_coverage_ratio': building_coverage_ratio,
            'population_density_per_sqkm': population_density_per_sqkm,
            'buildings_processed': len(building_data)
        }
        
        logger.info(f"Settlement-based estimation completed: {total_population:.0f} people")
        return result
    
    def estimate_population_ensemble(self, building_data: pd.DataFrame,
                                   settlement_classifications: Optional[Dict] = None,
                                   zone_area_sqm: Optional[float] = None,
                                   weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Estimate population using ensemble of multiple methods
        
        Args:
            building_data: DataFrame with building features
            settlement_classifications: Optional settlement type classifications
            zone_area_sqm: Optional zone area
            weights: Optional custom weights for ensemble methods
            
        Returns:
            Dictionary with ensemble population estimates
        """
        logger.info("Performing ensemble population estimation...")
        
        # Default ensemble weights
        if weights is None:
            weights = {
                'area_based': 0.4,
                'floor_based': 0.3,
                'settlement_based': 0.3
            }
        
        # Perform individual estimates
        area_result = self.estimate_population_area_based(building_data, settlement_classifications)
        floor_result = self.estimate_population_floor_based(building_data, settlement_classifications)
        settlement_result = self.estimate_population_settlement_based(
            building_data, settlement_classifications, zone_area_sqm
        )
        
        # Calculate weighted ensemble
        ensemble_population = (
            area_result['total_population'] * weights['area_based'] +
            floor_result['total_population'] * weights['floor_based'] +
            settlement_result['total_population'] * weights['settlement_based']
        )
        
        # Combine settlement populations
        ensemble_settlement_pops = {}
        for settlement_type in ['formal', 'informal', 'mixed', 'unknown']:
            ensemble_settlement_pops[settlement_type] = (
                area_result['settlement_populations'][settlement_type] * weights['area_based'] +
                floor_result['settlement_populations'][settlement_type] * weights['floor_based'] +
                settlement_result['settlement_populations'].get(settlement_type, 0) * weights['settlement_based']
            )
        
        # Calculate ensemble metrics
        method_estimates = {
            'area_based': area_result['total_population'],
            'floor_based': floor_result['total_population'],
            'settlement_based': settlement_result['total_population']
        }
        
        # Calculate uncertainty
        estimate_values = list(method_estimates.values())
        ensemble_std = np.std(estimate_values)
        ensemble_cv = ensemble_std / ensemble_population if ensemble_population > 0 else 0
        
        result = {
            'method': 'ensemble',
            'total_population': ensemble_population,
            'settlement_populations': ensemble_settlement_pops,
            'method_estimates': method_estimates,
            'ensemble_weights': weights,
            'ensemble_std': ensemble_std,
            'ensemble_cv': ensemble_cv,
            'confidence_interval_95': [
                ensemble_population - 1.96 * ensemble_std,
                ensemble_population + 1.96 * ensemble_std
            ],
            'individual_results': {
                'area_based': area_result,
                'floor_based': floor_result,
                'settlement_based': settlement_result
            },
            'buildings_processed': len(building_data)
        }
        
        logger.info(f"Ensemble estimation completed: {ensemble_population:.0f} people (±{ensemble_std:.0f})")
        return result
    
    def apply_seasonal_adjustments(self, population_estimate: Dict[str, Any], 
                                 season: str = "average") -> Dict[str, Any]:
        """
        Apply seasonal population adjustments
        
        Args:
            population_estimate: Population estimate dictionary
            season: Season ("dry_season", "wet_season", or "average")
            
        Returns:
            Seasonally adjusted population estimate
        """
        if season == "average":
            return population_estimate
        
        seasonal_factor = self.parameters['seasonal_factors'].get(season, 1.0)
        
        adjusted_estimate = population_estimate.copy()
        adjusted_estimate['total_population'] *= seasonal_factor
        
        if 'settlement_populations' in adjusted_estimate:
            for settlement_type in adjusted_estimate['settlement_populations']:
                adjusted_estimate['settlement_populations'][settlement_type] *= seasonal_factor
        
        adjusted_estimate['seasonal_adjustment'] = {
            'season': season,
            'factor': seasonal_factor,
            'original_population': population_estimate['total_population']
        }
        
        return adjusted_estimate
    
    def calculate_uncertainty_bounds(self, population_estimate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate uncertainty bounds for population estimates
        
        Args:
            population_estimate: Population estimate dictionary
            
        Returns:
            Dictionary with uncertainty analysis
        """
        method = population_estimate.get('method', 'unknown')
        total_pop = population_estimate.get('total_population', 0)
        
        # Get uncertainty coefficient for method
        uncertainty_cv = self.parameters['uncertainty'].get(method, 0.20)
        
        # Calculate standard deviation
        pop_std = total_pop * uncertainty_cv
        
        # Calculate confidence intervals
        confidence_intervals = {
            '68%': [total_pop - pop_std, total_pop + pop_std],
            '95%': [total_pop - 1.96 * pop_std, total_pop + 1.96 * pop_std],
            '99%': [total_pop - 2.58 * pop_std, total_pop + 2.58 * pop_std]
        }
        
        # Ensure non-negative bounds
        for interval in confidence_intervals.values():
            interval[0] = max(0, interval[0])
        
        uncertainty_analysis = {
            'method': method,
            'point_estimate': total_pop,
            'standard_deviation': pop_std,
            'coefficient_of_variation': uncertainty_cv,
            'confidence_intervals': confidence_intervals,
            'relative_uncertainty': uncertainty_cv * 100  # Percentage
        }
        
        return uncertainty_analysis
    
    def validate_estimates(self, estimated_population: float, 
                         validation_population: float,
                         validation_source: str = "census") -> Dict[str, Any]:
        """
        Validate population estimates against reference data
        
        Args:
            estimated_population: Estimated population
            validation_population: Reference population
            validation_source: Source of validation data
            
        Returns:
            Dictionary with validation metrics
        """
        if validation_population <= 0:
            return {"error": "Invalid validation population"}
        
        # Calculate validation metrics
        absolute_error = abs(estimated_population - validation_population)
        relative_error = absolute_error / validation_population
        bias = (estimated_population - validation_population) / validation_population
        
        # Classification of accuracy
        if relative_error < 0.10:
            accuracy_class = "Excellent"
        elif relative_error < 0.20:
            accuracy_class = "Good"
        elif relative_error < 0.30:
            accuracy_class = "Fair"
        else:
            accuracy_class = "Poor"
        
        validation_result = {
            'estimated_population': estimated_population,
            'validation_population': validation_population,
            'validation_source': validation_source,
            'absolute_error': absolute_error,
            'relative_error': relative_error,
            'bias': bias,
            'accuracy_class': accuracy_class,
            'within_20_percent': relative_error < 0.20,
            'within_30_percent': relative_error < 0.30
        }
        
        return validation_result
    
    def get_estimation_summary(self, estimation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of population estimation results
        
        Args:
            estimation_result: Population estimation result
            
        Returns:
            Summary dictionary
        """
        method = estimation_result.get('method', 'unknown')
        total_pop = estimation_result.get('total_population', 0)
        buildings_processed = estimation_result.get('buildings_processed', 0)
        
        # Basic metrics
        avg_people_per_building = total_pop / buildings_processed if buildings_processed > 0 else 0
        
        # Settlement analysis
        settlement_pops = estimation_result.get('settlement_populations', {})
        dominant_settlement = max(settlement_pops.items(), key=lambda x: x[1])[0] if settlement_pops else 'unknown'
        
        # Method-specific metrics
        method_specific = {}
        if method == 'area_based':
            method_specific['total_building_area'] = sum([est['area'] for est in estimation_result.get('detailed_estimates', [])])
        elif method == 'floor_based':
            method_specific['average_floors'] = estimation_result.get('average_floors_per_building', 0)
        elif method == 'settlement_based':
            method_specific['population_density_per_sqkm'] = estimation_result.get('population_density_per_sqkm', 0)
        elif method == 'ensemble':
            method_specific['ensemble_cv'] = estimation_result.get('ensemble_cv', 0)
            method_specific['method_agreement'] = "High" if estimation_result.get('ensemble_cv', 1) < 0.15 else "Medium" if estimation_result.get('ensemble_cv', 1) < 0.25 else "Low"
        
        summary = {
            'estimation_method': method,
            'total_estimated_population': total_pop,
            'buildings_analyzed': buildings_processed,
            'average_people_per_building': avg_people_per_building,
            'dominant_settlement_type': dominant_settlement,
            'settlement_distribution': settlement_pops,
            'method_specific_metrics': method_specific,
            'estimation_quality': self._assess_estimation_quality(estimation_result)
        }
        
        return summary
    
    def _assess_estimation_quality(self, estimation_result: Dict[str, Any]) -> str:
        """Assess the quality of population estimation"""
        
        method = estimation_result.get('method', 'unknown')
        buildings_count = estimation_result.get('buildings_processed', 0)
        
        # Basic quality assessment
        if buildings_count < 5:
            return "Low - Insufficient building data"
        elif buildings_count < 20:
            base_quality = "Medium"
        else:
            base_quality = "High"
        
        # Method-specific adjustments
        if method == 'ensemble':
            cv = estimation_result.get('ensemble_cv', 0)
            if cv < 0.15:
                return f"{base_quality} - Excellent method agreement"
            elif cv < 0.25:
                return f"{base_quality} - Good method agreement"
            else:
                return f"{base_quality} - Poor method agreement"
        
        return f"{base_quality} - {method.replace('_', ' ').title()} estimation"


def create_test_population_data() -> Tuple[pd.DataFrame, Dict]:
    """Create test data for population estimation demonstration"""
    
    np.random.seed(42)
    building_data = []
    
    # Create diverse building dataset
    for i in range(100):
        # Settlement type distribution
        settlement_type = np.random.choice(['formal', 'informal', 'mixed'], p=[0.4, 0.4, 0.2])
        
        # Building type based on settlement
        if settlement_type == 'informal':
            building_type = np.random.choice(['residential', 'mixed', 'commercial'], p=[0.8, 0.15, 0.05])
            area = np.random.normal(65, 25)  # Smaller buildings
            height = np.random.normal(3.2, 0.8)  # Single story mostly
        elif settlement_type == 'formal':
            building_type = np.random.choice(['residential', 'commercial', 'mixed'], p=[0.6, 0.25, 0.15])
            area = np.random.normal(180, 60)  # Larger buildings
            height = np.random.normal(5.5, 2.0)  # Multi-story potential
        else:  # mixed
            building_type = np.random.choice(['residential', 'mixed', 'commercial'], p=[0.7, 0.2, 0.1])
            area = np.random.normal(120, 40)  # Medium buildings
            height = np.random.normal(4.2, 1.5)  # Mixed heights
        
        # Ensure realistic ranges
        area = max(25, area)
        height = max(2.5, height)
        
        # Building age
        age_category = np.random.choice(['new', 'medium', 'old'], p=[0.2, 0.5, 0.3])
        
        building_data.append({
            'id': i,
            'area': area,
            'height': height,
            'building_type': building_type,
            'settlement_type': settlement_type,
            'age_category': age_category
        })
    
    building_df = pd.DataFrame(building_data)
    
    # Settlement classifications (for testing)
    settlement_classifications = {}
    for i in range(len(building_data)):
        settlement_classifications[i] = {
            'classification': building_data[i]['settlement_type'],
            'confidence': np.random.uniform(0.7, 0.95)
        }
    
    return building_df, settlement_classifications


if __name__ == "__main__":
    print("Building-based Population Estimation Demo")
    print("=" * 50)
    
    # Create test data
    print("Creating test building dataset...")
    building_data, settlement_classifications = create_test_population_data()
    
    print(f"Dataset created with {len(building_data)} buildings")
    print(f"Settlement distribution: {building_data['settlement_type'].value_counts().to_dict()}")
    print(f"Building type distribution: {building_data['building_type'].value_counts().to_dict()}")
    
    # Initialize population estimator
    print("\nInitializing population estimator for Lusaka...")
    estimator = PopulationEstimator(region="lusaka")
    
    # Test different estimation methods
    print("\n1. Area-based Population Estimation:")
    area_result = estimator.estimate_population_area_based(building_data, settlement_classifications)
    print(f"   Total population: {area_result['total_population']:.0f}")
    print(f"   Average people per building: {area_result['average_people_per_building']:.1f}")
    
    print("\n2. Floor-based Population Estimation:")
    floor_result = estimator.estimate_population_floor_based(building_data, settlement_classifications)
    print(f"   Total population: {floor_result['total_population']:.0f}")
    print(f"   Average floors per building: {floor_result['average_floors_per_building']:.1f}")
    
    print("\n3. Settlement-based Population Estimation:")
    settlement_result = estimator.estimate_population_settlement_based(
        building_data, settlement_classifications, zone_area_sqm=2000000
    )
    print(f"   Total population: {settlement_result['total_population']:.0f}")
    print(f"   Population density: {settlement_result['population_density_per_sqkm']:.0f} people/km²")
    
    print("\n4. Ensemble Population Estimation:")
    ensemble_result = estimator.estimate_population_ensemble(
        building_data, settlement_classifications, zone_area_sqm=2000000
    )
    print(f"   Total population: {ensemble_result['total_population']:.0f}")
    print(f"   Uncertainty (CV): {ensemble_result['ensemble_cv']:.2f}")
    print(f"   95% CI: [{ensemble_result['confidence_interval_95'][0]:.0f}, {ensemble_result['confidence_interval_95'][1]:.0f}]")
    
    # Show method comparison
    print("\nMethod Comparison:")
    for method, estimate in ensemble_result['method_estimates'].items():
        print(f"   {method.replace('_', ' ').title()}: {estimate:.0f}")
    
    # Settlement distribution
    print("\nSettlement Population Distribution (Ensemble):")
    for settlement_type, population in ensemble_result['settlement_populations'].items():
        if population > 0:
            print(f"   {settlement_type.title()}: {population:.0f} ({population/ensemble_result['total_population']*100:.1f}%)")
    
    # Get estimation summary
    summary = estimator.get_estimation_summary(ensemble_result)
    print(f"\nEstimation Quality: {summary['estimation_quality']}")
    
    # Simulate validation
    print("\nValidation Example:")
    simulated_census = ensemble_result['total_population'] * np.random.uniform(0.85, 1.15)  # ±15% variation
    validation = estimator.validate_estimates(
        ensemble_result['total_population'],
        simulated_census,
        "simulated_census"
    )
    print(f"   Estimated: {validation['estimated_population']:.0f}")
    print(f"   Reference: {validation['validation_population']:.0f}")
    print(f"   Relative error: {validation['relative_error']*100:.1f}%")
    print(f"   Accuracy: {validation['accuracy_class']}")
    
    print("\nDemo completed successfully!") 
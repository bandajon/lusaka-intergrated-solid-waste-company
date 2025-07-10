"""
Validation Engine for Unified Analyzer
Validates analysis results for quality and consistency
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Validation engine that checks analysis results for quality and consistency
    """
    
    # Validation thresholds for Lusaka
    THRESHOLDS = {
        'min_population_density': 100,      # min people per sq km
        'max_population_density': 50000,    # max people per sq km
        'min_waste_per_person': 0.1,        # min kg per person per day
        'max_waste_per_person': 2.0,        # max kg per person per day
        'min_building_size': 20,            # min building size sq m
        'max_building_size': 10000,         # max building size sq m
    }
    
    def __init__(self):
        """Initialize validation engine"""
        logger.info("Validation engine initialized")
    
    def validate_results(self, result: Any) -> Dict[str, Any]:
        """
        Validate analysis results
        
        Args:
            result: AnalysisResult object or dict
            
        Returns:
            Validation results with metrics and warnings
        """
        # Convert to dict if needed
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = result
        
        validation_results = {
            'is_valid': True,
            'metrics': {},
            'warnings': [],
            'errors': []
        }
        
        # Validate population estimates
        if result_dict.get('population_estimate') is not None:
            pop_validation = self._validate_population(result_dict)
            validation_results['metrics']['population_validity'] = pop_validation['score']
            validation_results['warnings'].extend(pop_validation['warnings'])
            if pop_validation['errors']:
                validation_results['errors'].extend(pop_validation['errors'])
                validation_results['is_valid'] = False
        
        # Validate building data
        if result_dict.get('building_count') is not None:
            building_validation = self._validate_buildings(result_dict)
            validation_results['metrics']['building_validity'] = building_validation['score']
            validation_results['warnings'].extend(building_validation['warnings'])
        
        # Validate waste calculations
        if result_dict.get('waste_generation_kg_per_day') is not None:
            waste_validation = self._validate_waste(result_dict)
            validation_results['metrics']['waste_validity'] = waste_validation['score']
            validation_results['warnings'].extend(waste_validation['warnings'])
        
        # Cross-validate different metrics
        if all(key in result_dict for key in ['population_estimate', 'building_count']):
            cross_validation = self._cross_validate_metrics(result_dict)
            validation_results['metrics']['cross_validation_score'] = cross_validation['score']
            validation_results['warnings'].extend(cross_validation['warnings'])
        
        # Calculate overall validity score
        if validation_results['metrics']:
            validation_results['overall_score'] = sum(
                validation_results['metrics'].values()
            ) / len(validation_results['metrics'])
        else:
            validation_results['overall_score'] = 0.5
        
        # Add quality assessment
        validation_results['quality_assessment'] = self._assess_quality(
            validation_results['overall_score']
        )
        
        return validation_results
    
    def _validate_population(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate population estimates"""
        population = result.get('population_estimate', 0)
        density = result.get('population_density', 0)
        
        warnings = []
        errors = []
        score = 1.0
        
        # Check if population is positive
        if population <= 0:
            errors.append("Population estimate is zero or negative")
            score = 0.0
            return {'score': score, 'warnings': warnings, 'errors': errors}
        
        # Check density bounds
        if density > 0:
            if density < self.THRESHOLDS['min_population_density']:
                warnings.append(f"Population density ({density:.0f}/km²) is unusually low for urban area")
                score *= 0.8
            elif density > self.THRESHOLDS['max_population_density']:
                warnings.append(f"Population density ({density:.0f}/km²) is extremely high")
                score *= 0.9
        
        # Check confidence level
        confidence = result.get('confidence_level', 0)
        if confidence < 0.5:
            warnings.append("Low confidence in population estimate")
            score *= 0.8
        
        # Check data sources
        sources = result.get('data_sources', [])
        if not sources:
            warnings.append("No data sources specified for population estimate")
            score *= 0.7
        
        return {'score': score, 'warnings': warnings, 'errors': errors}
    
    def _validate_buildings(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate building data"""
        building_count = result.get('building_count', 0)
        building_types = result.get('building_types', {})
        
        warnings = []
        score = 1.0
        
        # Check if buildings exist
        if building_count == 0:
            warnings.append("No buildings detected in zone")
            score *= 0.5
        
        # Check building type distribution
        if building_types:
            total_typed = sum(building_types.values())
            if total_typed != building_count:
                warnings.append(f"Building type counts ({total_typed}) don't match total ({building_count})")
                score *= 0.9
        
        # Check settlement classification
        settlement = result.get('settlement_classification')
        if settlement == 'unknown':
            warnings.append("Unable to classify settlement type")
            score *= 0.9
        
        return {'score': score, 'warnings': warnings, 'errors': []}
    
    def _validate_waste(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate waste calculations"""
        daily_waste = result.get('waste_generation_kg_per_day', 0)
        population = result.get('population_estimate', 0)
        
        warnings = []
        score = 1.0
        
        # Check if waste is positive
        if daily_waste <= 0:
            warnings.append("Waste generation is zero or negative")
            score = 0.0
            return {'score': score, 'warnings': warnings, 'errors': []}
        
        # Check waste per capita if population available
        if population > 0:
            waste_per_capita = daily_waste / population
            
            if waste_per_capita < self.THRESHOLDS['min_waste_per_person']:
                warnings.append(f"Waste per capita ({waste_per_capita:.2f} kg/day) is unusually low")
                score *= 0.8
            elif waste_per_capita > self.THRESHOLDS['max_waste_per_person']:
                warnings.append(f"Waste per capita ({waste_per_capita:.2f} kg/day) is unusually high")
                score *= 0.8
        
        # Check collection requirements
        collection_req = result.get('collection_requirements', {})
        if not collection_req.get('vehicle_requirements'):
            warnings.append("No vehicle requirements calculated")
            score *= 0.9
        
        return {'score': score, 'warnings': warnings, 'errors': []}
    
    def _cross_validate_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-validate different metrics for consistency"""
        population = result.get('population_estimate', 0)
        buildings = result.get('building_count', 0)
        households = result.get('household_estimate', 0)
        
        warnings = []
        score = 1.0
        
        # Check people per building ratio
        if buildings > 0 and population > 0:
            people_per_building = population / buildings
            
            # Typical range for Lusaka: 4-20 people per building
            if people_per_building < 2:
                warnings.append(f"People per building ({people_per_building:.1f}) seems too low")
                score *= 0.8
            elif people_per_building > 50:
                warnings.append(f"People per building ({people_per_building:.1f}) seems too high")
                score *= 0.8
        
        # Check household consistency
        if households > 0 and population > 0:
            people_per_household = population / households
            
            # Typical household size in Lusaka: 4-6 people
            if people_per_household < 3:
                warnings.append(f"People per household ({people_per_household:.1f}) is below typical range")
                score *= 0.9
            elif people_per_household > 8:
                warnings.append(f"People per household ({people_per_household:.1f}) is above typical range")
                score *= 0.9
        
        # Check if households exceed buildings (shouldn't happen)
        if households > buildings * 10:  # Max 10 households per building
            warnings.append("Household count seems too high relative to buildings")
            score *= 0.7
        
        return {'score': score, 'warnings': warnings}
    
    def _assess_quality(self, score: float) -> str:
        """Assess overall quality based on score"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        elif score >= 0.4:
            return "Poor"
        else:
            return "Very Poor" 
"""
WorldPop-based Dasymetric Mapping Integration
Implements dasymetric mapping using WorldPop data for improved population distribution
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DasymetricMapper:
    """
    Dasymetric mapping system using WorldPop data and building footprints
    Redistributes population data based on building characteristics and settlement types
    """
    
    def __init__(self, resolution: float = 100.0):
        """Initialize the dasymetric mapper"""
        self.resolution = resolution
        
        # Population grids and ancillary data
        self.worldpop_data = None
        self.building_density_data = None
        self.settlement_classifications = None
        self.refined_population_data = None
        
        # Dasymetric weights and parameters
        self.settlement_weights = {
            'formal': 1.0,
            'informal': 1.5,  # Higher density factor for informal settlements
            'mixed': 1.2,
            'unknown': 1.0
        }
        
        self.building_type_weights = {
            'residential': 1.0,
            'commercial': 0.3,  # Lower residential population
            'industrial': 0.1,  # Very low residential population
            'mixed': 0.8,
            'unknown': 0.7
        }
        
        # Processing state
        self.is_initialized = False
        self.processing_stats = {}
    
    def initialize_with_data(self, worldpop_data: Dict, building_data: pd.DataFrame, 
                           settlement_classifications: Optional[Dict] = None) -> None:
        """
        Initialize the mapper with WorldPop and building data
        
        Args:
            worldpop_data: Dictionary with WorldPop population data
            building_data: DataFrame with building features
            settlement_classifications: Optional settlement classifications
        """
        logger.info("Initializing dasymetric mapper with data...")
        
        self.worldpop_data = worldpop_data
        self.settlement_classifications = settlement_classifications or {}
        self.building_density_data = self._process_building_data(building_data)
        
        self.is_initialized = True
        logger.info("Dasymetric mapper initialized successfully")
    
    def _process_building_data(self, building_data: pd.DataFrame) -> Dict:
        """Process building data to create density metrics"""
        
        processed_data = {
            'total_buildings': len(building_data),
            'total_area': 0,
            'weighted_area': 0,
            'settlement_distribution': {'formal': 0, 'informal': 0, 'mixed': 0, 'unknown': 0},
            'building_type_distribution': {'residential': 0, 'commercial': 0, 'industrial': 0, 'mixed': 0, 'unknown': 0}
        }
        
        if building_data.empty:
            return processed_data
        
        # Calculate total area
        if 'area' in building_data.columns:
            processed_data['total_area'] = building_data['area'].sum()
        
        # Process each building
        weighted_area = 0
        for idx, building in building_data.iterrows():
            # Get building area
            area = building.get('area', 100)  # Default 100 sqm
            
            # Get building type
            building_type = building.get('building_type', 'unknown')
            building_type_weight = self.building_type_weights.get(building_type, 0.7)
            
            # Get settlement type
            settlement_type = building.get('settlement_type', 'unknown')
            if idx in self.settlement_classifications:
                settlement_type = self.settlement_classifications[idx].get('classification', 'unknown')
            
            settlement_weight = self.settlement_weights.get(settlement_type, 1.0)
            
            # Calculate weighted area
            building_weighted_area = area * building_type_weight * settlement_weight
            weighted_area += building_weighted_area
            
            # Update distributions
            if settlement_type in processed_data['settlement_distribution']:
                processed_data['settlement_distribution'][settlement_type] += area
            else:
                processed_data['settlement_distribution']['unknown'] += area
            
            if building_type in processed_data['building_type_distribution']:
                processed_data['building_type_distribution'][building_type] += area
            else:
                processed_data['building_type_distribution']['unknown'] += area
        
        processed_data['weighted_area'] = weighted_area
        
        return processed_data
    
    def perform_dasymetric_mapping(self, zone_geometry: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform dasymetric mapping to redistribute population
        
        Args:
            zone_geometry: Optional zone geometry for spatial constraints
            
        Returns:
            Dictionary with refined population estimates
        """
        if not self.is_initialized:
            raise ValueError("Mapper must be initialized before performing dasymetric mapping")
        
        logger.info("Performing dasymetric mapping...")
        
        # Get original WorldPop population
        original_population = self.worldpop_data.get('total_population', 0)
        
        if original_population == 0:
            logger.warning("No population data available for redistribution")
            return self._create_empty_result()
        
        # Calculate redistribution weights
        redistribution_weights = self._calculate_redistribution_weights()
        
        # Redistribute population based on building characteristics
        refined_population = self._redistribute_population(original_population, redistribution_weights)
        
        # Apply spatial constraints if zone geometry provided
        if zone_geometry:
            refined_population = self._apply_spatial_constraints(refined_population, zone_geometry)
        
        # Calculate processing statistics
        self._calculate_processing_stats(original_population, refined_population)
        
        logger.info("Dasymetric mapping completed")
        return refined_population
    
    def _calculate_redistribution_weights(self) -> Dict[str, float]:
        """Calculate weights for population redistribution"""
        
        weights = {
            'building_density_weight': 0.0,
            'settlement_weight': 0.0,
            'building_type_weight': 0.0,
            'combined_weight': 0.0
        }
        
        building_data = self.building_density_data
        
        if building_data['total_buildings'] == 0:
            return weights
        
        # Building density weight (normalized)
        total_area = building_data['total_area']
        if total_area > 0:
            weights['building_density_weight'] = min(1.0, total_area / 10000)  # Normalize to 1 hectare
        
        # Settlement type weight (based on distribution)
        settlement_dist = building_data['settlement_distribution']
        total_settlement_area = sum(settlement_dist.values())
        
        if total_settlement_area > 0:
            # Calculate weighted average of settlement factors
            settlement_weight = 0
            for settlement_type, area in settlement_dist.items():
                if area > 0:
                    settlement_weight += (area / total_settlement_area) * self.settlement_weights.get(settlement_type, 1.0)
            weights['settlement_weight'] = settlement_weight
        else:
            weights['settlement_weight'] = 1.0
        
        # Building type weight (based on distribution)
        building_type_dist = building_data['building_type_distribution']
        total_building_type_area = sum(building_type_dist.values())
        
        if total_building_type_area > 0:
            # Calculate weighted average of building type factors
            building_type_weight = 0
            for building_type, area in building_type_dist.items():
                if area > 0:
                    building_type_weight += (area / total_building_type_area) * self.building_type_weights.get(building_type, 0.7)
            weights['building_type_weight'] = building_type_weight
        else:
            weights['building_type_weight'] = 0.7
        
        # Combined weight
        weights['combined_weight'] = (
            weights['building_density_weight'] * 
            weights['settlement_weight'] * 
            weights['building_type_weight']
        )
        
        return weights
    
    def _redistribute_population(self, original_population: float, weights: Dict[str, float]) -> Dict[str, Any]:
        """Redistribute population using calculated weights"""
        
        combined_weight = weights['combined_weight']
        
        # Base redistribution factor
        if combined_weight > 0:
            redistribution_factor = min(2.0, max(0.5, combined_weight))
        else:
            redistribution_factor = 1.0
        
        # Calculate refined population
        refined_total_population = original_population * redistribution_factor
        
        # Distribute by settlement type
        settlement_dist = self.building_density_data['settlement_distribution']
        total_settlement_area = sum(settlement_dist.values())
        
        settlement_populations = {}
        if total_settlement_area > 0:
            for settlement_type, area in settlement_dist.items():
                if area > 0:
                    settlement_weight = self.settlement_weights.get(settlement_type, 1.0)
                    settlement_proportion = (area / total_settlement_area) * settlement_weight
                    settlement_populations[settlement_type] = refined_total_population * settlement_proportion
                else:
                    settlement_populations[settlement_type] = 0
        else:
            settlement_populations = {settlement_type: 0 for settlement_type in self.settlement_weights.keys()}
        
        # Distribute by building type
        building_type_dist = self.building_density_data['building_type_distribution']
        total_building_type_area = sum(building_type_dist.values())
        
        building_type_populations = {}
        if total_building_type_area > 0:
            for building_type, area in building_type_dist.items():
                if area > 0:
                    building_type_weight = self.building_type_weights.get(building_type, 0.7)
                    building_type_proportion = (area / total_building_type_area) * building_type_weight
                    building_type_populations[building_type] = refined_total_population * building_type_proportion
                else:
                    building_type_populations[building_type] = 0
        else:
            building_type_populations = {building_type: 0 for building_type in self.building_type_weights.keys()}
        
        return {
            'total_population': refined_total_population,
            'redistribution_factor': redistribution_factor,
            'settlement_populations': settlement_populations,
            'building_type_populations': building_type_populations,
            'redistribution_weights': weights,
            'method': 'dasymetric_mapping'
        }
    
    def _apply_spatial_constraints(self, refined_population: Dict, zone_geometry: Dict) -> Dict[str, Any]:
        """Apply spatial constraints based on zone geometry"""
        
        # For now, this is a simplified spatial constraint
        # In a full implementation, this would use actual geometric operations
        
        zone_area = zone_geometry.get('area_sqm', 1000000)  # Default 1 km²
        
        # Density constraint (people per km²)
        max_density_per_km2 = 50000  # Maximum 50,000 people per km²
        max_population_for_zone = (zone_area / 1000000) * max_density_per_km2
        
        # Apply constraint
        if refined_population['total_population'] > max_population_for_zone:
            constraint_factor = max_population_for_zone / refined_population['total_population']
            
            # Scale down all populations
            refined_population['total_population'] = max_population_for_zone
            
            for settlement_type in refined_population['settlement_populations']:
                refined_population['settlement_populations'][settlement_type] *= constraint_factor
            
            for building_type in refined_population['building_type_populations']:
                refined_population['building_type_populations'][building_type] *= constraint_factor
            
            refined_population['spatial_constraint_applied'] = True
            refined_population['constraint_factor'] = constraint_factor
        else:
            refined_population['spatial_constraint_applied'] = False
            refined_population['constraint_factor'] = 1.0
        
        return refined_population
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create an empty result when no data is available"""
        return {
            'total_population': 0,
            'redistribution_factor': 1.0,
            'settlement_populations': {settlement_type: 0 for settlement_type in self.settlement_weights.keys()},
            'building_type_populations': {building_type: 0 for building_type in self.building_type_weights.keys()},
            'redistribution_weights': {},
            'method': 'no_data_available',
            'error': 'No population data available for redistribution'
        }
    
    def _calculate_processing_stats(self, original_population: float, refined_population: Dict) -> None:
        """Calculate statistics about the dasymetric mapping process"""
        
        refined_total = refined_population['total_population']
        
        # Population conservation
        conservation_ratio = refined_total / original_population if original_population > 0 else 0
        
        # Building integration metrics
        building_data = self.building_density_data
        building_coverage = building_data['total_buildings'] / max(1, building_data['total_buildings'])
        
        self.processing_stats = {
            'original_population': original_population,
            'refined_population': refined_total,
            'population_change': refined_total - original_population,
            'conservation_ratio': conservation_ratio,
            'redistribution_factor': refined_population.get('redistribution_factor', 1.0),
            'building_count': building_data['total_buildings'],
            'total_building_area': building_data['total_area'],
            'weighted_building_area': building_data['weighted_area'],
            'spatial_constraint_applied': refined_population.get('spatial_constraint_applied', False)
        }
    
    def extract_population_for_zones(self, zones: List[Dict]) -> List[Dict]:
        """
        Extract population estimates for specific zones using dasymetric mapping
        
        Args:
            zones: List of zone dictionaries with geometry information
            
        Returns:
            List of dictionaries with population estimates for each zone
        """
        logger.info(f"Extracting dasymetric population estimates for {len(zones)} zones...")
        
        results = []
        
        for i, zone in enumerate(zones):
            try:
                # Get zone geometry
                zone_geometry = {
                    'area_sqm': zone.get('area_sqm', 1000000),  # Default 1 km²
                    'perimeter_m': zone.get('perimeter_m', 4000)  # Default 4 km perimeter
                }
                
                # Perform dasymetric mapping for this zone
                zone_population_result = self.perform_dasymetric_mapping(zone_geometry)
                
                result = {
                    'zone_id': zone.get('id', i),
                    'zone_name': zone.get('name', f'Zone_{i}'),
                    'dasymetric_result': zone_population_result,
                    'original_worldpop_population': self.worldpop_data.get('total_population', 0),
                    'improvement_summary': self._generate_improvement_summary(zone_population_result)
                }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'zone_id': zone.get('id', i),
                    'error': f'Dasymetric mapping failed: {str(e)}'
                })
        
        logger.info("Zone dasymetric population extraction completed")
        return results
    
    def _generate_improvement_summary(self, zone_result: Dict) -> Dict[str, Any]:
        """Generate a summary of improvements from dasymetric mapping"""
        
        original_pop = self.worldpop_data.get('total_population', 0)
        refined_pop = zone_result.get('total_population', 0)
        
        return {
            'population_change': refined_pop - original_pop,
            'improvement_ratio': refined_pop / original_pop if original_pop > 0 else 0,
            'redistribution_applied': zone_result.get('redistribution_factor', 1.0) != 1.0,
            'building_integration': self.building_density_data['total_buildings'] > 0,
            'settlement_diversity': len([v for v in zone_result.get('settlement_populations', {}).values() if v > 0]),
            'spatial_refinement_quality': 'High' if zone_result.get('spatial_constraint_applied', False) else 'Standard'
        }
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of the dasymetric mapping process"""
        
        if not self.processing_stats:
            return {"error": "No processing statistics available"}
        
        summary = self.processing_stats.copy()
        
        # Add quality assessments
        conservation_quality = "Excellent" if abs(summary['conservation_ratio'] - 1.0) < 0.05 else \
                             "Good" if abs(summary['conservation_ratio'] - 1.0) < 0.1 else \
                             "Fair" if abs(summary['conservation_ratio'] - 1.0) < 0.2 else "Poor"
        
        summary['conservation_quality'] = conservation_quality
        
        # Building integration effectiveness
        building_integration = "High" if summary['building_count'] > 20 else \
                             "Medium" if summary['building_count'] > 5 else "Low"
        
        summary['building_integration_effectiveness'] = building_integration
        
        return summary


def create_test_data() -> Tuple[Dict, pd.DataFrame, List[Dict]]:
    """Create test data for dasymetric mapping demonstration"""
    
    # WorldPop data
    worldpop_data = {
        'total_population': 5000,
        'population_density_per_sqkm': 2500,
        'data_source': 'WorldPop_test',
        'year': 2023
    }
    
    # Building data
    np.random.seed(42)
    building_data = []
    
    for i in range(50):
        settlement_type = np.random.choice(['formal', 'informal', 'mixed'], p=[0.5, 0.3, 0.2])
        building_type = np.random.choice(['residential', 'commercial', 'mixed'], p=[0.7, 0.2, 0.1])
        
        if settlement_type == 'informal':
            area = np.random.normal(60, 20)  # Smaller buildings
        elif settlement_type == 'formal':
            area = np.random.normal(150, 40)  # Larger buildings
        else:
            area = np.random.normal(100, 30)  # Mixed
        
        area = max(30, area)  # Minimum 30 sqm
        
        building_data.append({
            'id': i,
            'area': area,
            'building_type': building_type,
            'settlement_type': settlement_type
        })
    
    building_df = pd.DataFrame(building_data)
    
    # Test zones
    zones = [
        {
            'id': 1,
            'name': 'Test_Zone_1',
            'area_sqm': 2000000,  # 2 km²
            'perimeter_m': 6000
        },
        {
            'id': 2,
            'name': 'Test_Zone_2',
            'area_sqm': 1500000,  # 1.5 km²
            'perimeter_m': 5000
        }
    ]
    
    return worldpop_data, building_df, zones


if __name__ == "__main__":
    print("WorldPop-based Dasymetric Mapping Demo")
    print("=" * 50)
    
    # Create test data
    print("Creating test data...")
    worldpop_data, building_data, test_zones = create_test_data()
    
    # Initialize dasymetric mapper
    print("Initializing dasymetric mapper...")
    mapper = DasymetricMapper(resolution=100.0)
    
    # Initialize with data
    mapper.initialize_with_data(worldpop_data, building_data)
    
    # Extract population for zones
    print("Performing dasymetric mapping for test zones...")
    zone_results = mapper.extract_population_for_zones(test_zones)
    
    # Display results
    print("\nDasymetric Mapping Results:")
    print(f"Original WorldPop population: {worldpop_data['total_population']:,}")
    
    print("\nZone Population Estimates:")
    for result in zone_results:
        if 'error' not in result:
            dasymetric_pop = result['dasymetric_result']['total_population']
            original_pop = result['original_worldpop_population']
            improvement = result['improvement_summary']
            
            print(f"  {result['zone_name']}:")
            print(f"    Dasymetric population: {dasymetric_pop:.0f}")
            print(f"    Original WorldPop: {original_pop:,}")
            print(f"    Improvement ratio: {improvement['improvement_ratio']:.2f}")
            print(f"    Settlement diversity: {improvement['settlement_diversity']} types")
    
    # Get processing summary
    summary = mapper.get_processing_summary()
    print(f"\nProcessing Summary:")
    print(f"  Building integration: {summary['building_integration_effectiveness']}")
    print(f"  Total buildings processed: {summary['building_count']}")
    print(f"  Total building area: {summary['total_building_area']:.0f} sqm")
    
    print("Demo completed successfully!") 
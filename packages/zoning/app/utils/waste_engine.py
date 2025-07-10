"""
Waste Generation Engine for Unified Analyzer
Calculates waste generation and collection requirements
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WasteEngine:
    """
    Waste analysis engine that integrates with the unified analyzer
    Calculates waste generation based on Lusaka-specific rates
    """
    
    # Waste generation rates for Lusaka (kg per person per day)
    WASTE_RATES = {
        'RESIDENTIAL': 0.5,      # Standard residential rate
        'COMMERCIAL': 0.8,       # Higher for commercial areas
        'INDUSTRIAL': 0.6,       # Industrial waste (non-hazardous)
        'INSTITUTIONAL': 0.4,    # Schools, hospitals
        'MIXED_USE': 0.6,       # Mixed residential/commercial
        'GREEN_SPACE': 0.1,     # Minimal waste from parks
        'TRANSPORT': 0.2        # Transport hubs
    }
    
    # Collection vehicle capacity (tons)
    VEHICLE_CAPACITY = {
        'small_truck': 3,       # 3-ton truck
        'medium_truck': 7,      # 7-ton truck
        'large_truck': 12,      # 12-ton compactor
        'skip_loader': 8        # Skip loader
    }
    
    def __init__(self):
        """Initialize waste engine"""
        logger.info("Waste engine initialized")
    
    def calculate_waste_generation(self, population: int, 
                                 zone_type: Optional[str] = None,
                                 options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate waste generation and collection requirements
        
        Args:
            population: Estimated population
            zone_type: Type of zone (residential, commercial, etc.)
            options: Additional options
            
        Returns:
            Waste generation analysis results
        """
        options = options or {}
        
        # Get waste generation rate
        if zone_type:
            zone_type_upper = zone_type.upper() if isinstance(zone_type, str) else str(zone_type).upper()
            waste_rate = self.WASTE_RATES.get(zone_type_upper, 0.5)
        else:
            waste_rate = options.get('waste_rate_kg_per_person', 0.5)
        
        # Calculate daily waste generation
        daily_waste_kg = population * waste_rate
        
        # Calculate collection requirements
        collection_frequency = options.get('collection_frequency', 2)  # times per week
        
        # Calculate waste per collection
        days_between_collection = 7 / collection_frequency if collection_frequency > 0 else 7
        waste_per_collection_kg = daily_waste_kg * days_between_collection
        waste_per_collection_tons = waste_per_collection_kg / 1000
        
        # Determine vehicle requirements
        vehicle_requirements = self._calculate_vehicle_requirements(waste_per_collection_tons)
        
        # Calculate monthly and annual projections
        monthly_waste_kg = daily_waste_kg * 30
        annual_waste_kg = daily_waste_kg * 365
        
        # Collection points estimation
        collection_points = self._estimate_collection_points(population, zone_type)
        
        return {
            'waste_generation_kg_per_day': round(daily_waste_kg, 2),
            'waste_generation_tons_per_day': round(daily_waste_kg / 1000, 2),
            'waste_per_collection_kg': round(waste_per_collection_kg, 2),
            'waste_per_collection_tons': round(waste_per_collection_tons, 2),
            'monthly_waste_tons': round(monthly_waste_kg / 1000, 2),
            'annual_waste_tons': round(annual_waste_kg / 1000, 2),
            'collection_requirements': {
                'frequency_per_week': collection_frequency,
                'vehicle_requirements': vehicle_requirements,
                'estimated_collection_points': collection_points,
                'recommended_bins': self._calculate_bin_requirements(daily_waste_kg, collection_frequency)
            },
            'waste_composition': self._get_waste_composition(zone_type),
            'recycling_potential': self._calculate_recycling_potential(daily_waste_kg, zone_type),
            'operational_recommendations': self._get_operational_recommendations(
                population, daily_waste_kg, zone_type
            )
        }
    
    def _calculate_vehicle_requirements(self, waste_tons: float) -> Dict[str, Any]:
        """Calculate required vehicles for collection"""
        requirements = {}
        
        # Optimal vehicle selection based on waste amount
        if waste_tons <= 3:
            requirements['primary_vehicle'] = 'small_truck'
            requirements['vehicles_needed'] = 1
        elif waste_tons <= 7:
            requirements['primary_vehicle'] = 'medium_truck'
            requirements['vehicles_needed'] = 1
        elif waste_tons <= 12:
            requirements['primary_vehicle'] = 'large_truck'
            requirements['vehicles_needed'] = 1
        else:
            # Multiple vehicles needed
            large_trucks = int(waste_tons / 12)
            remaining = waste_tons % 12
            
            requirements['primary_vehicle'] = 'large_truck'
            requirements['vehicles_needed'] = large_trucks
            
            if remaining > 7:
                requirements['secondary_vehicle'] = 'large_truck'
                requirements['vehicles_needed'] += 1
            elif remaining > 3:
                requirements['secondary_vehicle'] = 'medium_truck'
            elif remaining > 0:
                requirements['secondary_vehicle'] = 'small_truck'
        
        requirements['total_capacity_tons'] = sum(
            self.VEHICLE_CAPACITY[v] for v in 
            [requirements.get('primary_vehicle')] + 
            ([requirements.get('secondary_vehicle')] if requirements.get('secondary_vehicle') else [])
            if v
        ) * requirements.get('vehicles_needed', 1)
        
        return requirements
    
    def _estimate_collection_points(self, population: int, zone_type: Optional[str] = None) -> int:
        """Estimate number of collection points needed"""
        # Base calculation: 1 collection point per 200 people
        base_points = max(1, population // 200)
        
        # Adjust based on zone type
        if zone_type and zone_type.upper() in ['COMMERCIAL', 'INDUSTRIAL']:
            # Commercial/industrial areas need more frequent collection points
            return int(base_points * 1.5)
        elif zone_type and zone_type.upper() == 'RESIDENTIAL':
            # High-density residential might need more points
            if population > 5000:
                return int(base_points * 1.2)
        
        return base_points
    
    def _calculate_bin_requirements(self, daily_waste_kg: float, frequency: int) -> Dict[str, int]:
        """Calculate bin requirements"""
        # Waste between collections
        days_between = 7 / frequency if frequency > 0 else 7
        waste_between_collections = daily_waste_kg * days_between
        
        # Add 20% buffer for peak periods
        waste_with_buffer = waste_between_collections * 1.2
        
        # Standard bin sizes (liters) and their capacity (kg)
        bin_sizes = {
            'small_bin_240L': 50,      # 50 kg capacity
            'medium_bin_660L': 140,    # 140 kg capacity
            'large_bin_1100L': 230,    # 230 kg capacity
            'skip_bin_7m3': 1400       # 1400 kg capacity
        }
        
        recommendations = {}
        
        # Calculate optimal bin combination
        if waste_with_buffer <= 500:
            # Small area - use 240L bins
            recommendations['small_bin_240L'] = max(1, int(waste_with_buffer / 50))
        elif waste_with_buffer <= 2000:
            # Medium area - mix of 660L and 1100L bins
            recommendations['large_bin_1100L'] = int(waste_with_buffer / 230)
            remaining = waste_with_buffer % 230
            if remaining > 140:
                recommendations['large_bin_1100L'] += 1
            elif remaining > 0:
                recommendations['medium_bin_660L'] = 1
        else:
            # Large area - use skip bins
            recommendations['skip_bin_7m3'] = int(waste_with_buffer / 1400)
            remaining = waste_with_buffer % 1400
            if remaining > 230:
                recommendations['large_bin_1100L'] = int(remaining / 230)
        
        return recommendations
    
    def _get_waste_composition(self, zone_type: Optional[str] = None) -> Dict[str, float]:
        """Get typical waste composition by zone type"""
        # Default residential composition for Lusaka
        default_composition = {
            'organic': 0.45,         # 45% organic waste
            'plastic': 0.15,         # 15% plastics
            'paper': 0.10,          # 10% paper
            'glass': 0.05,          # 5% glass
            'metal': 0.05,          # 5% metals
            'textiles': 0.05,       # 5% textiles
            'other': 0.15           # 15% other waste
        }
        
        if not zone_type:
            return default_composition
        
        zone_type_upper = zone_type.upper()
        
        if zone_type_upper == 'COMMERCIAL':
            return {
                'organic': 0.30,
                'plastic': 0.20,
                'paper': 0.25,
                'glass': 0.10,
                'metal': 0.05,
                'textiles': 0.02,
                'other': 0.08
            }
        elif zone_type_upper == 'INDUSTRIAL':
            return {
                'organic': 0.10,
                'plastic': 0.25,
                'paper': 0.20,
                'glass': 0.05,
                'metal': 0.20,
                'textiles': 0.05,
                'other': 0.15
            }
        
        return default_composition
    
    def _calculate_recycling_potential(self, daily_waste_kg: float, 
                                     zone_type: Optional[str] = None) -> Dict[str, float]:
        """Calculate recycling potential"""
        composition = self._get_waste_composition(zone_type)
        
        # Recycling recovery rates (conservative estimates for Lusaka)
        recovery_rates = {
            'plastic': 0.30,    # 30% of plastic can be recycled
            'paper': 0.40,      # 40% of paper
            'glass': 0.50,      # 50% of glass
            'metal': 0.60,      # 60% of metals
        }
        
        recycling_potential = {}
        total_recyclable = 0
        
        for material, rate in recovery_rates.items():
            if material in composition:
                recyclable_kg = daily_waste_kg * composition[material] * rate
                recycling_potential[f'{material}_kg_per_day'] = round(recyclable_kg, 2)
                total_recyclable += recyclable_kg
        
        recycling_potential['total_recyclable_kg_per_day'] = round(total_recyclable, 2)
        recycling_potential['recycling_rate_potential'] = round(
            (total_recyclable / daily_waste_kg * 100) if daily_waste_kg > 0 else 0, 1
        )
        
        return recycling_potential
    
    def _get_operational_recommendations(self, population: int, 
                                       daily_waste_kg: float,
                                       zone_type: Optional[str] = None) -> list:
        """Get operational recommendations"""
        recommendations = []
        
        # Population-based recommendations
        if population > 10000:
            recommendations.append("Consider establishing a transfer station for efficient long-haul transport")
        
        if population > 5000:
            recommendations.append("Implement source segregation program to improve recycling rates")
        
        # Waste amount recommendations
        if daily_waste_kg > 5000:
            recommendations.append("Deploy compactor trucks to reduce collection trips")
        
        # Zone-specific recommendations
        if zone_type:
            zone_type_upper = zone_type.upper()
            
            if zone_type_upper == 'COMMERCIAL':
                recommendations.append("Schedule early morning collections to avoid business hours")
                recommendations.append("Provide separate bins for recyclables at commercial premises")
            
            elif zone_type_upper == 'RESIDENTIAL':
                recommendations.append("Establish community collection points for better accessibility")
                recommendations.append("Promote home composting for organic waste reduction")
            
            elif zone_type_upper == 'INDUSTRIAL':
                recommendations.append("Ensure proper handling of potentially hazardous waste")
                recommendations.append("Coordinate with industries for waste minimization programs")
        
        # General recommendations
        if daily_waste_kg > 1000:
            recommendations.append("Consider daily collection for high-waste areas")
        
        recommendations.append("Regular monitoring of illegal dumping hotspots")
        
        return recommendations 
"""
Analytics Configuration
Manual settings for waste management analytics including fuel prices and rates
"""
import os
from typing import Dict, Any, Optional


class AnalyticsConfig:
    """Configuration class for analytics settings with manual overrides"""
    
    # Manual Fuel Price Configuration (ZMW per liter)
    FUEL_PRICE_PER_LITER = float(os.getenv('FUEL_PRICE_PER_LITER', 25.0))
    
    # Client Payment Rates (percentage likely to pay)
    CLIENT_PAYMENT_RATES = {
        'residential': 0.70,    # 70% payment rate for residential
        'commercial': 0.90,     # 90% payment rate for commercial  
        'industrial': 0.95,     # 95% payment rate for industrial
        'mixed': 0.75           # 75% payment rate for mixed zones
    }
    
    # Waste Generation Rates by Area Type and Settlement Density (kg per person per day)
    WASTE_GENERATION_RATES = {
        'residential': {
            'high_density': 0.4,       # kg/person/day - High density areas, less consumption space
            'medium_density': 0.5,      # kg/person/day - Standard Lusaka rate  
            'low_density': 0.6,        # kg/person/day - Low density, more consumption
            'informal_settlement': 0.3  # kg/person/day - Lower consumption due to income
        },
        'commercial': {
            'high_density': 2.5,       # kg/employee/day - Dense commercial areas
            'medium_density': 2.0,      # kg/employee/day - Standard commercial
            'low_density': 1.5,        # kg/employee/day - Suburban commercial
            'informal_settlement': 1.0  # kg/employee/day - Small informal businesses
        },
        'industrial': {
            'high_density': 8.0,       # kg/employee/day - Heavy industrial
            'medium_density': 6.0,      # kg/employee/day - Standard industrial
            'low_density': 4.0,        # kg/employee/day - Light industrial
            'informal_settlement': 2.0  # kg/employee/day - Informal manufacturing
        },
        'mixed_use': {
            'high_density': 0.7,       # kg/person/day - Mix of residential/commercial
            'medium_density': 0.6,      # kg/person/day - Balanced mixed use
            'low_density': 0.5,        # kg/person/day - Suburban mixed use
            'informal_settlement': 0.4  # kg/person/day - Informal mixed areas
        },
        'institutional': {
            'high_density': 1.5,       # kg/person/day - Schools, hospitals
            'medium_density': 1.2,      # kg/person/day - Government offices
            'low_density': 1.0,        # kg/person/day - Small institutions
            'informal_settlement': 0.8  # kg/person/day - Basic services
        }
    }
    
    # Socioeconomic Level Multipliers for Waste Generation
    SOCIOECONOMIC_MULTIPLIERS = {
        'low_income': 0.7,      # 30% less waste generation
        'middle_income': 1.0,   # Base rate
        'high_income': 1.4,     # 40% more waste generation  
        'mixed_income': 1.0     # Average rate
    }
    
    # Payment Capacity by Socioeconomic Level (percentage likely to pay full amount)
    PAYMENT_CAPACITY_RATES = {
        'low_income': 0.50,     # 50% payment capacity
        'middle_income': 0.75,  # 75% payment capacity
        'high_income': 0.95,    # 95% payment capacity
        'mixed_income': 0.70    # 70% average payment capacity
    }
    
    # Collection Parameters
    COLLECTION_PARAMS = {
        'truck_capacity_10t': 10000,       # 10 ton truck capacity (kg)
        'truck_capacity_20t': 20000,       # 20 ton truck capacity (kg)
        'collection_efficiency': 0.85,     # 85% efficiency factor
        'working_days_per_month': 26,      # Working days
        'trips_per_truck_per_day': 3       # Average trips per truck
    }
    
    # Revenue Rates (ZMW per kg)
    REVENUE_RATES = {
        'residential': 2.70,    # K2.70 per kg
        'commercial': 4.05,     # K4.05 per kg  
        'industrial': 5.40,     # K5.40 per kg
        'mixed': 3.24           # K3.24 per kg
    }
    
    # Building Classification Thresholds
    BUILDING_CLASSIFICATION = {
        'residential_area_max': 300,        # sqm - max for typical residential
        'commercial_area_min': 100,         # sqm - min for commercial
        'industrial_area_min': 500,         # sqm - min for industrial
        'height_residential_max': 6.0,      # meters - max for residential
        'height_commercial_min': 4.0        # meters - min for commercial
    }
    
    # Distance and Transportation
    TRANSPORTATION = {
        'chunga_landfill_lat': -15.4500,    # Chunga landfill coordinates
        'chunga_landfill_lng': 28.2000,
        'vehicle_speed_kmh': 25,            # Average speed in Lusaka
        'fuel_consumption_per_km': 0.35     # Liters per km
    }
    
    @classmethod
    def set_fuel_price(cls, price_per_liter: float) -> None:
        """Manually set fuel price per liter"""
        if price_per_liter <= 0:
            raise ValueError("Fuel price must be positive")
        cls.FUEL_PRICE_PER_LITER = price_per_liter
        # Update environment variable for persistence
        os.environ['FUEL_PRICE_PER_LITER'] = str(price_per_liter)
    
    @classmethod 
    def get_fuel_price(cls) -> float:
        """Get current fuel price per liter"""
        return cls.FUEL_PRICE_PER_LITER
    
    @classmethod
    def set_payment_rate(cls, zone_type: str, rate: float) -> None:
        """Manually set payment rate for zone type"""
        if zone_type not in cls.CLIENT_PAYMENT_RATES:
            raise ValueError(f"Unknown zone type: {zone_type}")
        if not 0 <= rate <= 1:
            raise ValueError("Payment rate must be between 0 and 1")
        cls.CLIENT_PAYMENT_RATES[zone_type] = rate
    
    @classmethod
    def get_payment_rate(cls, zone_type: str) -> float:
        """Get payment rate for zone type"""
        return cls.CLIENT_PAYMENT_RATES.get(zone_type, cls.CLIENT_PAYMENT_RATES['mixed'])
    
    @classmethod
    def calculate_fuel_cost(cls, distance_km: float) -> float:
        """Calculate fuel cost for given distance"""
        fuel_needed = distance_km * cls.TRANSPORTATION['fuel_consumption_per_km']
        return fuel_needed * cls.FUEL_PRICE_PER_LITER
    
    @classmethod
    def get_collection_frequency_recommendation(cls, daily_waste_kg: float) -> str:
        """Get recommended collection frequency based on waste volume"""
        if daily_waste_kg > 1000:
            return "daily"
        elif daily_waste_kg > 500:
            return "3x_per_week"  
        elif daily_waste_kg > 200:
            return "2x_per_week"
        else:
            return "weekly"
    
    @classmethod
    def get_waste_generation_rate(cls, zone_type: str, settlement_density: str, 
                                 socioeconomic_level: str, custom_rate: Optional[float] = None) -> float:
        """Get area-specific waste generation rate"""
        # If custom rate is provided, use it with socioeconomic multiplier
        if custom_rate is not None:
            base_rate = custom_rate
        else:
            # Get base rate from zone type and density
            zone_rates = cls.WASTE_GENERATION_RATES.get(zone_type.lower(), cls.WASTE_GENERATION_RATES['mixed_use'])
            base_rate = zone_rates.get(settlement_density, zone_rates['medium_density'])
        
        # Apply socioeconomic multiplier
        multiplier = cls.SOCIOECONOMIC_MULTIPLIERS.get(socioeconomic_level, 1.0)
        return base_rate * multiplier
    
    @classmethod
    def get_payment_capacity_rate(cls, socioeconomic_level: str) -> float:
        """Get payment capacity rate for socioeconomic level"""
        return cls.PAYMENT_CAPACITY_RATES.get(socioeconomic_level, cls.PAYMENT_CAPACITY_RATES['mixed_income'])
    
    @classmethod
    def calculate_expected_revenue(cls, household_count: int, average_household_charge: float, 
                                 socioeconomic_level: str) -> Dict[str, float]:
        """Calculate expected revenue considering payment capacity"""
        payment_capacity = cls.get_payment_capacity_rate(socioeconomic_level)
        
        # Calculate revenue projections
        gross_monthly_revenue = household_count * average_household_charge
        expected_monthly_revenue = gross_monthly_revenue * payment_capacity
        revenue_shortfall = gross_monthly_revenue - expected_monthly_revenue
        
        return {
            'gross_monthly_revenue': gross_monthly_revenue,
            'expected_monthly_revenue': expected_monthly_revenue,
            'payment_capacity_rate': payment_capacity,
            'revenue_shortfall': revenue_shortfall,
            'collection_efficiency': payment_capacity * 100  # As percentage
        }
    
    @classmethod
    def get_truck_recommendation(cls, waste_per_collection: float) -> Dict[str, Any]:
        """Get truck type recommendation based on waste volume"""
        efficiency = cls.COLLECTION_PARAMS['collection_efficiency']
        
        # Calculate trucks needed for each type
        trucks_10t = max(1, int(waste_per_collection / (cls.COLLECTION_PARAMS['truck_capacity_10t'] * efficiency)))
        trucks_20t = max(1, int(waste_per_collection / (cls.COLLECTION_PARAMS['truck_capacity_20t'] * efficiency)))
        
        # Recommend based on efficiency
        if trucks_20t == 1 and waste_per_collection > 8000:
            recommendation = "20t_truck"
            trucks_needed = trucks_20t
        else:
            recommendation = "10t_truck"
            trucks_needed = trucks_10t
            
        return {
            'recommendation': recommendation,
            'trucks_needed': trucks_needed,
            'trucks_10t_option': trucks_10t,
            'trucks_20t_option': trucks_20t
        }
    
    @classmethod
    def export_settings(cls) -> Dict[str, Any]:
        """Export all current settings"""
        return {
            'fuel_price_per_liter': cls.FUEL_PRICE_PER_LITER,
            'client_payment_rates': cls.CLIENT_PAYMENT_RATES.copy(),
            'waste_generation_rates': cls.WASTE_GENERATION_RATES.copy(),
            'collection_params': cls.COLLECTION_PARAMS.copy(),
            'revenue_rates': cls.REVENUE_RATES.copy(),
            'building_classification': cls.BUILDING_CLASSIFICATION.copy(),
            'transportation': cls.TRANSPORTATION.copy()
        }
    
    @classmethod
    def load_settings(cls, settings: Dict[str, Any]) -> None:
        """Load settings from dictionary"""
        if 'fuel_price_per_liter' in settings:
            cls.set_fuel_price(settings['fuel_price_per_liter'])
        
        if 'client_payment_rates' in settings:
            cls.CLIENT_PAYMENT_RATES.update(settings['client_payment_rates'])
            
        # Add other setting updates as needed

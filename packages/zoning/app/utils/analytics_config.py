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
    
    # Waste Generation Rates (kg per person/unit per day) 
    WASTE_GENERATION_RATES = {
        'residential': {
            'per_person': 0.5,      # kg/person/day
            'per_household': 2.5    # kg/household/day (avg 5 people)
        },
        'commercial': {
            'small_business': 10,   # kg/day
            'medium_business': 50,  # kg/day
            'large_business': 200   # kg/day
        },
        'industrial': {
            'light_industry': 500,  # kg/day
            'heavy_industry': 2000  # kg/day
        }
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
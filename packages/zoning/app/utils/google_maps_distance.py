"""
Google Maps Distance Matrix API Integration
==========================================

This module provides real-time distance and travel time calculations
to Chunga dump site using Google Maps Distance Matrix API with traffic data.

Features:
- Real driving distances and travel times
- Traffic-aware calculations for peak hours
- Caching to minimize API calls
- Error handling and fallback calculations

Author: Claude Code
Date: 2025
"""

import logging
import time
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chunga dump site coordinates
CHUNGA_DUMP_SITE = {
    'lat': -15.349850,
    'lng': 28.268712
}

class GoogleMapsDistanceCalculator:
    """
    Google Maps Distance Matrix API integration for calculating
    real driving distances and travel times to Chunga dump site
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the distance calculator
        
        Args:
            api_key: Google Maps API key (optional, can be set via environment)
        """
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
        # Cache for distance calculations (24 hour TTL)
        self.cache = {}
        self.cache_expiry = {}
        self.cache_ttl = timedelta(hours=24)
        
        # Fallback calculations
        self.fallback_speed_kmh = 25  # Average urban speed in Lusaka
        self.fuel_efficiency_km_per_liter = 8  # Typical waste truck efficiency
        
        if not self.api_key:
            logger.warning("⚠️ Google Maps API key not found. Will use fallback calculations.")
        else:
            logger.info("✅ Google Maps Distance Calculator initialized")
    
    def calculate_distance_and_time(self, origin_lat: float, origin_lng: float, 
                                  traffic_model: str = "best_guess",
                                  departure_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate driving distance and travel time to Chunga dump site
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            traffic_model: Traffic model ("best_guess", "pessimistic", "optimistic")
            departure_time: Departure time for traffic calculation (default: now)
            
        Returns:
            Dictionary with distance, duration, and cost information
        """
        if departure_time is None:
            departure_time = datetime.now()
        
        # Generate cache key
        cache_key = self._generate_cache_key(origin_lat, origin_lng, traffic_model, departure_time)
        
        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"📦 Using cached distance calculation")
            return cached_result
        
        try:
            if self.api_key:
                result = self._calculate_with_api(origin_lat, origin_lng, traffic_model, departure_time)
            else:
                result = self._calculate_fallback(origin_lat, origin_lng)
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Distance calculation failed: {str(e)}")
            return self._calculate_fallback(origin_lat, origin_lng, error_msg=str(e))
    
    def _calculate_with_api(self, origin_lat: float, origin_lng: float,
                          traffic_model: str, departure_time: datetime) -> Dict[str, Any]:
        """Calculate using Google Maps Distance Matrix API"""
        
        # Prepare request parameters
        origin = f"{origin_lat},{origin_lng}"
        destination = f"{CHUNGA_DUMP_SITE['lat']},{CHUNGA_DUMP_SITE['lng']}"
        
        params = {
            'origins': origin,
            'destinations': destination,
            'key': self.api_key,
            'mode': 'driving',
            'language': 'en',
            'units': 'metric',
            'traffic_model': traffic_model,
            'departure_time': int(departure_time.timestamp())
        }
        
        logger.info(f"🌐 Requesting Google Maps distance from ({origin_lat:.6f}, {origin_lng:.6f}) to Chunga dump site")
        
        # Make API request
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API response status
        if data['status'] != 'OK':
            raise Exception(f"Google Maps API error: {data['status']}")
        
        # Extract results
        element = data['rows'][0]['elements'][0]
        
        if element['status'] != 'OK':
            raise Exception(f"Route calculation failed: {element['status']}")
        
        # Extract distance and duration
        distance_meters = element['distance']['value']
        distance_km = distance_meters / 1000
        
        duration_seconds = element['duration']['value']
        duration_minutes = duration_seconds / 60
        
        # Check for traffic-aware duration
        duration_in_traffic_seconds = element.get('duration_in_traffic', {}).get('value', duration_seconds)
        duration_in_traffic_minutes = duration_in_traffic_seconds / 60
        
        # Calculate costs
        fuel_cost = self._calculate_fuel_cost(distance_km)
        
        result = {
            'distance_km': round(distance_km, 2),
            'distance_meters': distance_meters,
            'duration_minutes': round(duration_minutes, 1),
            'duration_with_traffic_minutes': round(duration_in_traffic_minutes, 1),
            'duration_seconds': duration_seconds,
            'duration_with_traffic_seconds': duration_in_traffic_seconds,
            'fuel_cost_kwacha': round(fuel_cost, 2),
            'data_source': 'Google Maps Distance Matrix API',
            'traffic_model': traffic_model,
            'calculation_time': departure_time.isoformat(),
            'success': True,
            'round_trip_distance_km': round(distance_km * 2, 2),
            'round_trip_duration_minutes': round(duration_in_traffic_minutes * 2, 1),
            'round_trip_fuel_cost_kwacha': round(fuel_cost * 2, 2)
        }
        
        logger.info(f"✅ Google Maps calculation: {distance_km:.1f} km, {duration_in_traffic_minutes:.1f} min (with traffic)")
        
        return result
    
    def _calculate_fallback(self, origin_lat: float, origin_lng: float, 
                          error_msg: Optional[str] = None) -> Dict[str, Any]:
        """Fallback calculation using haversine distance"""
        
        # Calculate haversine (straight-line) distance
        distance_km = self._haversine_distance(
            origin_lat, origin_lng,
            CHUNGA_DUMP_SITE['lat'], CHUNGA_DUMP_SITE['lng']
        )
        
        # Apply urban routing factor (roads are not straight)
        routing_factor = 1.3  # 30% longer due to road network
        driving_distance_km = distance_km * routing_factor
        
        # Calculate travel time based on average urban speed
        duration_minutes = (driving_distance_km / self.fallback_speed_kmh) * 60
        
        # Add traffic factor for busy periods
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Peak hours
            traffic_factor = 1.4  # 40% longer during peak hours
        else:
            traffic_factor = 1.2  # 20% longer during normal hours
        
        duration_with_traffic_minutes = duration_minutes * traffic_factor
        
        # Calculate costs
        fuel_cost = self._calculate_fuel_cost(driving_distance_km)
        
        result = {
            'distance_km': round(driving_distance_km, 2),
            'distance_meters': int(driving_distance_km * 1000),
            'duration_minutes': round(duration_minutes, 1),
            'duration_with_traffic_minutes': round(duration_with_traffic_minutes, 1),
            'duration_seconds': int(duration_minutes * 60),
            'duration_with_traffic_seconds': int(duration_with_traffic_minutes * 60),
            'fuel_cost_kwacha': round(fuel_cost, 2),
            'data_source': 'Fallback calculation (haversine + routing factors)',
            'traffic_model': 'estimated',
            'calculation_time': datetime.now().isoformat(),
            'success': False,
            'round_trip_distance_km': round(driving_distance_km * 2, 2),
            'round_trip_duration_minutes': round(duration_with_traffic_minutes * 2, 1),
            'round_trip_fuel_cost_kwacha': round(fuel_cost * 2, 2),
            'error_message': error_msg
        }
        
        if error_msg:
            logger.warning(f"⚠️ Using fallback calculation due to error: {error_msg}")
        else:
            logger.info(f"ℹ️ Using fallback calculation: {driving_distance_km:.1f} km, {duration_with_traffic_minutes:.1f} min")
        
        return result
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance between two points"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def _calculate_fuel_cost(self, distance_km: float) -> float:
        """
        Calculate fuel cost for the journey
        
        Args:
            distance_km: Distance in kilometers
            
        Returns:
            Fuel cost in Kwacha
        """
        # Fuel consumption calculation
        liters_needed = distance_km / self.fuel_efficiency_km_per_liter
        
        # Current fuel price in Lusaka (K23 per liter as of 2025)
        fuel_price_per_liter = 23.0
        
        total_fuel_cost = liters_needed * fuel_price_per_liter
        
        return total_fuel_cost
    
    def calculate_collection_logistics(self, zone_center_lat: float, zone_center_lng: float,
                                     collection_frequency_per_week: int = 2) -> Dict[str, Any]:
        """
        Calculate comprehensive logistics for waste collection
        
        Args:
            zone_center_lat: Zone center latitude
            zone_center_lng: Zone center longitude
            collection_frequency_per_week: Number of collections per week
            
        Returns:
            Comprehensive logistics information
        """
        # Get distance and time for peak traffic (worst case scenario)
        peak_time = datetime.now().replace(hour=8, minute=0, second=0)  # Morning peak
        
        logistics = self.calculate_distance_and_time(
            zone_center_lat, zone_center_lng,
            traffic_model="pessimistic",  # Use worst-case traffic
            departure_time=peak_time
        )
        
        # Calculate weekly and monthly logistics
        weekly_trips = collection_frequency_per_week
        weekly_distance = logistics['round_trip_distance_km'] * weekly_trips
        weekly_fuel_cost = logistics['round_trip_fuel_cost_kwacha'] * weekly_trips
        weekly_travel_time = logistics['round_trip_duration_minutes'] * weekly_trips
        
        monthly_distance = weekly_distance * 4.33  # Average weeks per month
        monthly_fuel_cost = weekly_fuel_cost * 4.33
        monthly_travel_time = weekly_travel_time * 4.33
        
        # Add logistics overhead (driver wages, vehicle maintenance, etc.)
        driver_cost_per_trip = 150  # K150 per trip
        maintenance_cost_per_km = 2  # K2 per km
        
        weekly_driver_cost = driver_cost_per_trip * weekly_trips
        weekly_maintenance_cost = maintenance_cost_per_km * weekly_distance
        monthly_driver_cost = weekly_driver_cost * 4.33
        monthly_maintenance_cost = weekly_maintenance_cost * 4.33
        
        logistics.update({
            'collection_frequency_per_week': collection_frequency_per_week,
            'weekly_metrics': {
                'total_distance_km': round(weekly_distance, 1),
                'total_travel_time_hours': round(weekly_travel_time / 60, 1),
                'fuel_cost_kwacha': round(weekly_fuel_cost, 2),
                'driver_cost_kwacha': round(weekly_driver_cost, 2),
                'maintenance_cost_kwacha': round(weekly_maintenance_cost, 2),
                'total_cost_kwacha': round(weekly_fuel_cost + weekly_driver_cost + weekly_maintenance_cost, 2)
            },
            'monthly_metrics': {
                'total_distance_km': round(monthly_distance, 1),
                'total_travel_time_hours': round(monthly_travel_time / 60, 1),
                'fuel_cost_kwacha': round(monthly_fuel_cost, 2),
                'driver_cost_kwacha': round(monthly_driver_cost, 2),
                'maintenance_cost_kwacha': round(monthly_maintenance_cost, 2),
                'total_cost_kwacha': round(monthly_fuel_cost + monthly_driver_cost + monthly_maintenance_cost, 2)
            }
        })
        
        return logistics
    
    def _generate_cache_key(self, lat: float, lng: float, traffic_model: str, 
                          departure_time: datetime) -> str:
        """Generate cache key for distance calculation"""
        # Round time to nearest hour for cache efficiency
        rounded_time = departure_time.replace(minute=0, second=0, microsecond=0)
        
        content = f"{lat:.6f},{lng:.6f},{traffic_model},{rounded_time.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        if cache_key not in self.cache:
            return None
        
        # Check if cache expired
        if datetime.now() > self.cache_expiry.get(cache_key, datetime.min):
            del self.cache[cache_key]
            del self.cache_expiry[cache_key]
            return None
        
        return self.cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache distance calculation result"""
        self.cache[cache_key] = result
        self.cache_expiry[cache_key] = datetime.now() + self.cache_ttl
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("🧹 Distance calculation cache cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get calculator status information"""
        return {
            'api_key_configured': bool(self.api_key),
            'cache_enabled': True,
            'cached_calculations': len(self.cache),
            'chunga_coordinates': CHUNGA_DUMP_SITE,
            'fallback_speed_kmh': self.fallback_speed_kmh,
            'fuel_efficiency_km_per_liter': self.fuel_efficiency_km_per_liter
        }


# Global calculator instance
distance_calculator = GoogleMapsDistanceCalculator()
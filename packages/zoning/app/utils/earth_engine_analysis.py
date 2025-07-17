"""
Google Earth Engine integration for advanced zone analysis
Provides satellite imagery analysis, land use classification, and environmental monitoring
"""
import ee
import os
import json
import datetime
import time
import hashlib
import math
from typing import Dict, List, Optional, Union
from app.models import Zone
from config.config import Config


class EarthEngineAnalyzer:
    """Analyzes zones using Google Earth Engine satellite data"""
    
    def __init__(self):
        """Initialize Earth Engine with service account or default authentication"""
        self.cache = {}  # Simple in-memory cache for building data
        self.initialized = False
        self.auth_error_details = None
        
        try:
            # First try service account authentication (for production)
            if hasattr(Config, 'GEE_SERVICE_ACCOUNT') and hasattr(Config, 'GEE_KEY_FILE'):
                if Config.GEE_SERVICE_ACCOUNT and Config.GEE_KEY_FILE and os.path.exists(Config.GEE_KEY_FILE):
                    try:
                        credentials = ee.ServiceAccountCredentials(
                            Config.GEE_SERVICE_ACCOUNT, 
                            Config.GEE_KEY_FILE
                        )
                        ee.Initialize(credentials)
                        print("✅ Earth Engine initialized with service account")
                        self.initialized = True
                        return
                    except Exception as sa_error:
                        print(f"⚠️  Service account initialization failed: {str(sa_error)}")
                        print(f"📁 Key file: {Config.GEE_KEY_FILE}")
                        print(f"📧 Service account: {Config.GEE_SERVICE_ACCOUNT}")
                        self.auth_error_details = f"Service account error: {str(sa_error)}"
                else:
                    print(f"⚠️  Service account configuration incomplete:")
                    print(f"   - Service account: {Config.GEE_SERVICE_ACCOUNT}")
                    print(f"   - Key file: {Config.GEE_KEY_FILE}")
                    print(f"   - Key file exists: {os.path.exists(Config.GEE_KEY_FILE) if Config.GEE_KEY_FILE else False}")
            
            # Fall back to default authentication (for development)
            try:
                ee.Initialize()
                print("Earth Engine initialized with default authentication")
                self.initialized = True
            except Exception as default_error:
                error_msg = str(default_error)
                print(f"Default initialization also failed: {error_msg}")
                self.auth_error_details = error_msg
                
                # Provide more specific guidance based on error type
                if "OAuth2 Client configuration" in error_msg:
                    print("EARTH ENGINE SETUP ISSUE: OAuth2 configuration conflict detected.")
                    print("SOLUTION: Use a different Google Cloud Project or create a new one for Earth Engine.")
                    print("FALLBACK: System will use enhanced area-based estimates instead.")
                elif "authenticate" in error_msg.lower():
                    print("Please run 'earthengine authenticate' in your terminal")
                else:
                    print("Earth Engine authentication failed - using enhanced estimates instead")
                    
                self.initialized = False
                
        except Exception as e:
            print(f"Earth Engine initialization failed: {str(e)}")
            self.auth_error_details = str(e)
            self.initialized = False
    
    def get_auth_status(self):
        """Get detailed authentication status for debugging"""
        return {
            'initialized': self.initialized,
            'error_details': self.auth_error_details,
            'can_provide_estimates': True  # We always have fallback capability
        }

    # ==================== GOOGLE OPEN BUILDINGS INTEGRATION ====================
    
    def load_google_open_buildings(self, aoi_geometry: ee.Geometry = None, confidence_threshold: float = 0.75) -> ee.FeatureCollection:
        """
        Load Google Open Buildings dataset from Earth Engine Data Catalog
        
        Args:
            aoi_geometry: Area of interest geometry for spatial filtering
            confidence_threshold: Minimum confidence score (default 0.75 for 75%)
            
        Returns:
            ee.FeatureCollection: Filtered building polygons
        """
        if not self.initialized:
            raise Exception("Earth Engine not initialized")
        
        try:
            # Load the Google Open Buildings dataset
            open_buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
            
            # Apply spatial filtering if AOI is provided
            if aoi_geometry:
                open_buildings = open_buildings.filterBounds(aoi_geometry)
            
            # Apply confidence filtering
            if confidence_threshold:
                open_buildings = open_buildings.filter(ee.Filter.gte('confidence', confidence_threshold))
            
            return open_buildings
            
        except Exception as e:
            raise Exception(f"Failed to load Google Open Buildings: {str(e)}")
    
    def load_open_buildings_temporal(self, aoi_geometry: ee.Geometry = None, year: int = 2023) -> ee.Image:
        """
        Load Google Open Buildings temporal data for building heights
        
        Args:
            aoi_geometry: Area of interest geometry
            year: Year of data to load (default 2023)
            
        Returns:
            ee.Image: Temporal building data with height information
        """
        if not self.initialized:
            raise Exception("Earth Engine not initialized")
        
        try:
            # Load temporal data
            temporal_data = ee.ImageCollection('GOOGLE/Research/open-buildings-temporal/v1')
            
            # Filter by date and bounds
            filtered_data = temporal_data.filter(
                ee.Filter.date(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year + 1, 1, 1))
            )
            
            if aoi_geometry:
                filtered_data = filtered_data.filterBounds(aoi_geometry)
            
            # Return mosaic of the collection
            return filtered_data.mosaic()
            
        except Exception as e:
            raise Exception(f"Failed to load temporal building data: {str(e)}")
    
    def extract_buildings_for_zone(self, zone: Zone, confidence_threshold: float = 0.75, 
                                 use_cache: bool = True) -> Dict:
        """
        Extract building polygons for a specific zone with caching
        
        Args:
            zone: Zone object with geometry
            confidence_threshold: Minimum confidence score
            use_cache: Whether to use caching for performance
            
        Returns:
            Dict: Building analysis results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(zone.geojson, confidence_threshold)
            
            # Check cache first
            if use_cache and cache_key in self.cache:
                print(f"Cache hit for zone {zone.id}")
                return self.cache[cache_key]
            
            # Convert zone geometry to Earth Engine format
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Extract buildings with retry logic
            buildings_result = self._extract_buildings_with_retry(ee_geometry, confidence_threshold)
            
            # Store in cache
            if use_cache:
                self.cache[cache_key] = buildings_result
                print(f"Cached results for zone {zone.id}")
            
            return buildings_result
            
        except Exception as e:
            return {"error": f"Building extraction failed: {str(e)}"}
    
    def _extract_buildings_with_retry(self, ee_geometry: ee.Geometry, confidence_threshold: float, 
                                    max_retries: int = 3) -> Dict:
        """
        Extract buildings with exponential backoff retry logic for quota handling
        
        Args:
            ee_geometry: Earth Engine geometry
            confidence_threshold: Confidence threshold
            max_retries: Maximum number of retries
            
        Returns:
            Dict: Building extraction results
        """
        for attempt in range(max_retries + 1):
            try:
                # Load buildings
                buildings = self.load_google_open_buildings(ee_geometry, confidence_threshold)
                
                # Get building count
                building_count = buildings.size()
                
                # Extract building features
                building_features = self._extract_building_features(buildings, ee_geometry)
                
                # Get temporal data for heights
                temporal_data = self.load_open_buildings_temporal(ee_geometry)
                height_stats = self._extract_height_statistics(temporal_data, ee_geometry)
                
                return {
                    'building_count': building_count.getInfo(),
                    'features': building_features,
                    'height_stats': height_stats,
                    'confidence_threshold': confidence_threshold,
                    'extraction_date': datetime.datetime.now().isoformat(),
                    'data_source': 'Google Open Buildings v3'
                }
                
            except ee.EEException as e:
                if 'quota' in str(e).lower() or 'limit' in str(e).lower():
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + (attempt * 0.1)  # Exponential backoff
                        print(f"Quota limit hit, retrying in {wait_time:.1f} seconds (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"API quota exceeded after {max_retries} retries")
                else:
                    raise e
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 1 + (attempt * 0.5)
                    print(f"Error occurred, retrying in {wait_time:.1f} seconds: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        
        raise Exception("Max retries exceeded")
    
    def _extract_building_features(self, buildings: ee.FeatureCollection, ee_geometry: ee.Geometry) -> Dict:
        """
        Extract detailed building features from the collection
        
        Args:
            buildings: Building feature collection
            ee_geometry: Area of interest geometry
            
        Returns:
            Dict: Building feature statistics
        """
        try:
            # Calculate area statistics
            def add_area(feature):
                return feature.set('area_sqm', feature.geometry().area())
            
            buildings_with_area = buildings.map(add_area)
            
            # Get area statistics
            area_stats = buildings_with_area.aggregate_stats('area_sqm')
            
            # Calculate building density (buildings per square kilometer)
            zone_area_sqm = ee_geometry.area()
            zone_area_sqkm = zone_area_sqm.divide(1000000)
            building_density = buildings.size().divide(zone_area_sqkm)
            
            # Get confidence statistics
            confidence_stats = buildings.aggregate_stats('confidence')
            
            return {
                'area_statistics': area_stats.getInfo(),
                'building_density_per_sqkm': building_density.getInfo(),
                'confidence_statistics': confidence_stats.getInfo(),
                'zone_area_sqkm': zone_area_sqkm.getInfo()
            }
            
        except Exception as e:
            return {"error": f"Feature extraction failed: {str(e)}"}
    
    def _extract_height_statistics(self, temporal_data: ee.Image, ee_geometry: ee.Geometry) -> Dict:
        """
        Extract building height statistics from temporal data
        
        Args:
            temporal_data: Temporal building image
            ee_geometry: Area of interest geometry
            
        Returns:
            Dict: Height statistics
        """
        try:
            # Extract building height band
            height_band = temporal_data.select('building_height')
            
            # Calculate height statistics
            height_stats = height_band.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.minMax(), '', True
                ).combine(
                    ee.Reducer.percentile([25, 50, 75, 90]), '', True
                ),
                geometry=ee_geometry,
                scale=4,  # 4m resolution for building data
                maxPixels=1e9
            )
            
            return height_stats.getInfo()
            
        except Exception as e:
            return {"error": f"Height extraction failed: {str(e)}"}
    
    def _generate_cache_key(self, geojson: Dict, confidence_threshold: float) -> str:
        """
        Generate a unique cache key for the geometry and parameters
        
        Args:
            geojson: GeoJSON geometry
            confidence_threshold: Confidence threshold
            
        Returns:
            str: Unique cache key
        """
        # Create a string representation of the geometry and parameters
        key_string = f"{json.dumps(geojson, sort_keys=True)}_{confidence_threshold}"
        
        # Generate hash
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def classify_buildings_by_context(self, zone: Zone, buildings_data: Dict) -> Dict:
        """
        Classify buildings by settlement context (formal vs informal)
        based on building patterns and features
        
        Args:
            zone: Zone object
            buildings_data: Building data from extraction
            
        Returns:
            Dict: Classification results
        """
        try:
            if not buildings_data or 'features' not in buildings_data:
                return {"error": "No building features available for classification"}
            
            features = buildings_data['features']
            building_count = buildings_data.get('building_count', 0)
            zone_area_sqkm = features.get('zone_area_sqkm', 1)
            
            # Calculate classification metrics
            building_density = features.get('building_density_per_sqkm', 0)
            avg_building_size = features.get('area_statistics', {}).get('mean', 0)
            
            # Classification logic based on Lusaka settlement patterns
            # From analysis.md: informal settlements have higher density and smaller buildings
            is_informal = False
            confidence_score = 0.5
            
            if building_density > 100:  # High density threshold
                is_informal = True
                confidence_score += 0.3
            
            if avg_building_size < 80:  # Small building threshold (80 sqm)
                is_informal = True
                confidence_score += 0.2
            
            # Additional context from building variability
            area_std = features.get('area_statistics', {}).get('stddev', 0)
            area_mean = features.get('area_statistics', {}).get('mean', 1)
            
            if area_mean > 0 and (area_std / area_mean) > 1.0:  # High variability
                confidence_score += 0.2
            
            settlement_type = 'informal' if is_informal else 'formal'
            
            return {
                'settlement_type': settlement_type,
                'confidence': min(confidence_score, 1.0),
                'building_density': building_density,
                'average_building_size_sqm': avg_building_size,
                'building_size_variability': area_std / area_mean if area_mean > 0 else 0,
                'classification_factors': {
                    'density_based': building_density > 100,
                    'size_based': avg_building_size < 80,
                    'variability_based': (area_std / area_mean) > 1.0 if area_mean > 0 else False
                }
            }
            
        except Exception as e:
            return {"error": f"Building classification failed: {str(e)}"}
    
    def clear_cache(self):
        """Clear the building data cache"""
        self.cache.clear()
        print("Building data cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get information about the current cache state"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }

    # ==================== BUILDING FEATURE EXTRACTION ====================
    
    def extract_comprehensive_building_features(self, zone: Zone, year: int = 2023) -> Dict:
        """
        Extract comprehensive building features for enhanced analytics
        
        Args:
            zone: Zone object with geometry
            year: Year for temporal analysis (default: 2023)
            
        Returns:
            Dict: Comprehensive building feature analysis
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get zone geometry
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Generate comprehensive cache key that includes year and analysis type
            comprehensive_cache_key = f"comprehensive_{zone.id}_{year}_{hashlib.md5(json.dumps(zone.geojson, sort_keys=True).encode()).hexdigest()}"
            
            # Check comprehensive cache first
            if comprehensive_cache_key in self.cache:
                print(f"Comprehensive cache hit for zone {zone.id} (year {year})")
                return self.cache[comprehensive_cache_key]
            
            # Load Google Open Buildings data (bypass cache for fresh results)
            buildings_data = self.extract_buildings_for_zone(zone, use_cache=False)
            if buildings_data.get('error'):
                return buildings_data
            
            # Initialize comprehensive features
            comprehensive_features = {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'analysis_year': year,
                'feature_extraction_date': time.time(),
                'building_count': buildings_data.get('building_count', 0),
                'data_source': 'Google Open Buildings + Advanced Analytics'
            }
            
            # Extract detailed building areas
            area_features = self.calculate_detailed_building_areas(zone, buildings_data)
            comprehensive_features['area_features'] = area_features
            
            # Extract building heights and floor estimates
            height_features = self.estimate_building_heights_comprehensive(zone, year)
            comprehensive_features['height_features'] = height_features
            
            # Calculate shape complexity metrics
            shape_features = self.compute_building_shape_complexity(zone, buildings_data)
            comprehensive_features['shape_complexity'] = shape_features
            
            # Calculate building density metrics
            density_features = self.calculate_building_density_metrics(zone, buildings_data)
            comprehensive_features['density_metrics'] = density_features
            
            # Extract seasonal stability indicators
            stability_features = self.extract_seasonal_stability_indicators(zone, year)
            comprehensive_features['seasonal_stability'] = stability_features
            
            # Calculate derived analytics
            derived_analytics = self.calculate_derived_building_analytics(
                area_features, height_features, shape_features, density_features
            )
            comprehensive_features['derived_analytics'] = derived_analytics
            
            # Extract GHSL population data for robust population estimation
            ghsl_population = self.extract_ghsl_population_for_zone(zone, 2025)
            comprehensive_features['ghsl_population'] = ghsl_population
            
            # Calculate comprehensive waste generation with seasonal and density adjustments
            waste_generation = self.calculate_comprehensive_waste_generation(
                ghsl_population, density_features, area_features, zone
            )
            comprehensive_features['waste_generation'] = waste_generation
            
            # Add feature quality assessment
            quality_assessment = self.assess_feature_extraction_quality(comprehensive_features)
            comprehensive_features['quality_assessment'] = quality_assessment
            
            # Cache the comprehensive results
            self.cache[comprehensive_cache_key] = comprehensive_features
            print(f"Cached comprehensive results for zone {zone.id} (year {year})")
            
            return comprehensive_features
            
        except Exception as e:
            return {"error": f"Comprehensive building feature extraction failed: {str(e)}"}
    
    def calculate_comprehensive_waste_generation(self, ghsl_population: Dict, density_features: Dict, 
                                               area_features: Dict, zone: Zone) -> Dict:
        """
        Calculate comprehensive waste generation with seasonal adjustments and density-based modifications
        
        Args:
            ghsl_population: GHSL population data with density classifications
            density_features: Building density metrics
            area_features: Building area features
            zone: Zone object
            
        Returns:
            Dict: Comprehensive waste generation analysis
        """
        try:
            # Extract population data
            total_population = ghsl_population.get('total_population', 0)
            household_count = ghsl_population.get('household_count', 0)
            density_category = ghsl_population.get('density_category', 'Medium Density Urban')
            urban_classification = ghsl_population.get('waste_generation_inputs', {}).get('urban_classification', 'urban')
            
            # Enhanced fallback population estimation
            if total_population == 0:
                print(f"⚠️  GHSL population is 0 for zone {zone.id if hasattr(zone, 'id') else 'unknown'}")
                print(f"   Attempting fallback population estimation...")
                
                # Fallback 1: Use building-based estimation
                try:
                    building_count = density_features.get('building_count', 0) if not density_features.get('error') else 0
                    area_sqkm = area_features.get('total_area_sqkm', 1.0) if not area_features.get('error') else 1.0
                    
                    if building_count > 0:
                        # Estimate population based on building count (average 4-6 people per building in Lusaka)
                        estimated_population = building_count * 5.0
                        print(f"   Fallback 1: Building-based estimation = {estimated_population} people from {building_count} buildings")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Medium Density Urban'  # Default assumption
                        urban_classification = 'urban'
                        
                    elif area_sqkm > 0:
                        # Fallback 2: Area-based estimation using typical Lusaka densities
                        typical_density_per_sqkm = 5000  # Conservative estimate for Lusaka urban areas
                        estimated_population = area_sqkm * typical_density_per_sqkm
                        print(f"   Fallback 2: Area-based estimation = {estimated_population} people from {area_sqkm} km²")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Medium Density Urban'
                        urban_classification = 'urban'
                        
                    else:
                        # Fallback 3: Minimum viable population for any zone
                        estimated_population = 100  # Minimum assumption
                        print(f"   Fallback 3: Minimum viable population = {estimated_population} people")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Low Density Urban'
                        urban_classification = 'peri_urban'
                    
                    print(f"✅ Using fallback population: {total_population} people")
                    
                except Exception as fallback_error:
                    print(f"❌ All fallback methods failed: {str(fallback_error)}")
                    return {"error": f"No population data available and fallback estimation failed: {str(fallback_error)}"}
            
            if total_population == 0:
                return {"error": "No population data available for waste generation calculation"}
            
            # Base waste generation rates for Lusaka (kg per person per day)
            # Standard rate is 0.5 kg/person/day with variations by density
            base_rates = {
                'Very High Density Urban': 0.6,   # 20% more due to commercial activity
                'High Density Urban': 0.55,       # 10% more due to mixed use
                'Medium Density Urban': 0.5,      # Standard rate
                'Low Density Urban': 0.45,        # 10% less due to composting
                'Peri-Urban': 0.4,               # 20% less due to rural practices
                'Rural': 0.35                    # 30% less due to subsistence lifestyle
            }
            
            base_rate = base_rates.get(density_category, 0.5)
            
            # Seasonal adjustments (Lusaka has distinct wet/dry seasons)
            seasonal_multipliers = {
                'dry_season': {  # May to October - higher waste generation
                    'months': ['May', 'June', 'July', 'August', 'September', 'October'],
                    'multiplier': 1.15,  # 15% increase during dry season
                    'reasons': ['Increased consumption', 'More outdoor activities', 'Market activities']
                },
                'wet_season': {  # November to April - lower waste generation
                    'months': ['November', 'December', 'January', 'February', 'March', 'April'],
                    'multiplier': 0.92,  # 8% decrease during wet season
                    'reasons': ['Reduced outdoor activities', 'Agricultural season', 'Lower consumption']
                }
            }
            
            # Calculate daily waste generation by season
            daily_waste_dry = total_population * base_rate * seasonal_multipliers['dry_season']['multiplier']
            daily_waste_wet = total_population * base_rate * seasonal_multipliers['wet_season']['multiplier']
            daily_waste_average = (daily_waste_dry + daily_waste_wet) / 2
            
            # Density-based adjustments
            built_up_ratio = density_features.get('built_up_ratio_percent', 25) if not density_features.get('error') else 25
            buildings_per_hectare = density_features.get('buildings_per_hectare', 20) if not density_features.get('error') else 20
            
            # High density areas generate more waste per capita due to:
            # - More commercial activities
            # - Higher income levels
            # - More packaged goods consumption
            if built_up_ratio > 50 or buildings_per_hectare > 100:
                density_multiplier = 1.25  # 25% increase for very dense areas
                density_note = "High density commercial/residential mix increases waste generation"
            elif built_up_ratio > 30 or buildings_per_hectare > 50:
                density_multiplier = 1.10  # 10% increase for moderately dense areas
                density_note = "Moderate density with mixed land use"
            else:
                density_multiplier = 1.0   # Standard rate for lower density
                density_note = "Standard residential waste generation rate"
            
            # Apply density adjustments
            daily_waste_dry_adjusted = daily_waste_dry * density_multiplier
            daily_waste_wet_adjusted = daily_waste_wet * density_multiplier
            daily_waste_average_adjusted = daily_waste_average * density_multiplier
            
            # Waste composition by density and season
            waste_composition = self._calculate_waste_composition_by_density(density_category, urban_classification)
            
            # Collection requirements
            collection_requirements = self._calculate_collection_requirements(
                daily_waste_average_adjusted, daily_waste_dry_adjusted, density_category
            )
            
            # Add standardized vehicles_required field for compatibility
            if not collection_requirements.get('error'):
                avg_day_reqs = collection_requirements.get('average_day', {})
                collection_requirements['vehicles_required'] = {
                    '10_tonne_trucks': avg_day_reqs.get('trucks_10_tonne', 1),
                    '20_tonne_trucks': avg_day_reqs.get('trucks_20_tonne', 1)
                }
                collection_requirements['recommended_collection_frequency'] = collection_requirements.get('recommendations', {}).get('collection_frequency', 'Every 2 days')
            
            # Seasonal variations for planning
            monthly_variations = {}
            for season, data in seasonal_multipliers.items():
                for month in data['months']:
                    monthly_waste = total_population * base_rate * data['multiplier'] * density_multiplier
                    monthly_variations[month] = {
                        'daily_waste_kg': round(monthly_waste, 2),
                        'monthly_total_kg': round(monthly_waste * 30, 2),
                        'seasonal_factors': data['reasons']
                    }
            
            return {
                'population_inputs': {
                    'total_population': total_population,
                    'household_count': household_count,
                    'density_category': density_category,
                    'urban_classification': urban_classification
                },
                'waste_generation_rates': {
                    'base_rate_kg_person_day': base_rate,
                    'density_multiplier': density_multiplier,
                    'density_adjustment_note': density_note
                },
                'daily_waste_generation': {
                    'dry_season_kg_day': round(daily_waste_dry_adjusted, 2),
                    'wet_season_kg_day': round(daily_waste_wet_adjusted, 2),
                    'annual_average_kg_day': round(daily_waste_average_adjusted, 2),
                    'annual_total_tonnes': round(daily_waste_average_adjusted * 365 / 1000, 2)
                },
                'seasonal_analysis': {
                    'seasonal_variation_percent': round(((daily_waste_dry_adjusted - daily_waste_wet_adjusted) / daily_waste_average_adjusted) * 100, 1),
                    'peak_season': 'Dry season (May-October)',
                    'low_season': 'Wet season (November-April)',
                    'monthly_breakdown': monthly_variations
                },
                'waste_composition': waste_composition,
                'collection_requirements': collection_requirements,
                'sustainability_metrics': {
                    'recyclable_potential_kg_day': round(daily_waste_average_adjusted * 0.35, 2),  # 35% recyclable
                    'organic_waste_kg_day': round(daily_waste_average_adjusted * 0.65, 2),      # 65% organic
                    'composting_potential_tonnes_year': round(daily_waste_average_adjusted * 0.65 * 365 / 1000, 2)
                }
            }
            
        except Exception as e:
            return {"error": f"Comprehensive waste generation calculation failed: {str(e)}"}
    
    def _calculate_waste_composition_by_density(self, density_category: str, urban_classification: str) -> Dict:
        """Calculate waste composition based on density and urban classification"""
        try:
            # Base composition for Lusaka
            if density_category in ['Very High Density Urban', 'High Density Urban']:
                # Higher density areas have more packaging, less organic waste
                composition = {
                    'organic': {'percentage': 60, 'description': 'Food waste, yard trimmings'},
                    'plastic': {'percentage': 18, 'description': 'Packaging, bottles, bags'},
                    'paper': {'percentage': 12, 'description': 'Newspapers, cardboard, office waste'},
                    'metal': {'percentage': 5, 'description': 'Cans, appliances'},
                    'glass': {'percentage': 3, 'description': 'Bottles, containers'},
                    'other': {'percentage': 2, 'description': 'Textiles, electronics, hazardous'}
                }
            elif density_category in ['Medium Density Urban', 'Low Density Urban']:
                # Medium density - standard composition
                composition = {
                    'organic': {'percentage': 65, 'description': 'Food waste, yard trimmings'},
                    'plastic': {'percentage': 15, 'description': 'Packaging, bottles, bags'},
                    'paper': {'percentage': 10, 'description': 'Newspapers, cardboard'},
                    'metal': {'percentage': 5, 'description': 'Cans, small appliances'},
                    'glass': {'percentage': 3, 'description': 'Bottles, containers'},
                    'other': {'percentage': 2, 'description': 'Textiles, miscellaneous'}
                }
            else:  # Peri-Urban, Rural
                # Lower density areas have more organic waste, less packaging
                composition = {
                    'organic': {'percentage': 75, 'description': 'Food waste, agricultural residues'},
                    'plastic': {'percentage': 10, 'description': 'Basic packaging'},
                    'paper': {'percentage': 5, 'description': 'Limited paper waste'},
                    'metal': {'percentage': 4, 'description': 'Basic metal waste'},
                    'glass': {'percentage': 2, 'description': 'Limited glass waste'},
                    'other': {'percentage': 4, 'description': 'Natural materials, ash'}
                }
            
            return composition
            
        except Exception as e:
            return {"error": f"Waste composition calculation failed: {str(e)}"}
    
    def _calculate_collection_requirements(self, daily_waste_avg: float, daily_waste_peak: float, 
                                         density_category: str) -> Dict:
        """Calculate collection requirements for different truck types"""
        try:
            # Truck capacities
            truck_10_tonne = 10000  # kg
            truck_20_tonne = 20000  # kg
            
            # Calculate requirements for different scenarios
            requirements = {
                'average_day': {
                    'waste_kg': round(daily_waste_avg, 2),
                    'trucks_10_tonne': max(1, int(daily_waste_avg / truck_10_tonne) + (1 if daily_waste_avg % truck_10_tonne > 0 else 0)),
                    'trucks_20_tonne': max(1, int(daily_waste_avg / truck_20_tonne) + (1 if daily_waste_avg % truck_20_tonne > 0 else 0))
                },
                'peak_day': {
                    'waste_kg': round(daily_waste_peak, 2),
                    'trucks_10_tonne': max(1, int(daily_waste_peak / truck_10_tonne) + (1 if daily_waste_peak % truck_10_tonne > 0 else 0)),
                    'trucks_20_tonne': max(1, int(daily_waste_peak / truck_20_tonne) + (1 if daily_waste_peak % truck_20_tonne > 0 else 0))
                }
            }
            
            # Collection frequency recommendations
            if density_category in ['Very High Density Urban', 'High Density Urban']:
                recommended_frequency = 'Daily'
                frequency_note = 'High density areas require daily collection to prevent overflow'
            elif density_category in ['Medium Density Urban']:
                recommended_frequency = 'Every 2 days'
                frequency_note = 'Medium density allows for every-other-day collection'
            else:
                recommended_frequency = 'Every 3 days'
                frequency_note = 'Lower density areas can be served with 3-day intervals'
            
            requirements['recommendations'] = {
                'collection_frequency': recommended_frequency,
                'frequency_note': frequency_note,
                'optimal_truck_type': '20-tonne' if daily_waste_avg > 15000 else '10-tonne',
                'route_optimization_needed': daily_waste_avg > 10000
            }
            
            return requirements
            
        except Exception as e:
            return {"error": f"Collection requirements calculation failed: {str(e)}"}
    
    def calculate_detailed_building_areas(self, zone: Zone, buildings_data: Dict) -> Dict:
        """Calculate detailed building area statistics and metrics"""
        try:
            # Use existing building features from buildings_data
            features = buildings_data.get('features', {})
            area_stats = features.get('area_statistics', {})
            building_count = buildings_data.get('building_count', 0)
            
            # Enhanced area calculations
            total_building_area = area_stats.get('sum', 0)
            mean_building_area = area_stats.get('mean', 0)
            std_building_area = area_stats.get('stddev', 0)
            
            # Calculate area distribution metrics
            area_distribution = {}
            if mean_building_area > 0:
                # Building size categories based on Lusaka context
                area_distribution = {
                    'very_small_buildings_pct': self._estimate_area_category_percentage(mean_building_area, std_building_area, 0, 40),
                    'small_buildings_pct': self._estimate_area_category_percentage(mean_building_area, std_building_area, 40, 100),
                    'medium_buildings_pct': self._estimate_area_category_percentage(mean_building_area, std_building_area, 100, 200),
                    'large_buildings_pct': self._estimate_area_category_percentage(mean_building_area, std_building_area, 200, 500),
                    'very_large_buildings_pct': self._estimate_area_category_percentage(mean_building_area, std_building_area, 500, float('inf'))
                }
            
            # Calculate zone coverage metrics
            zone_area_sqm = features.get('zone_area_sqkm', 1) * 1000000  # Convert to sqm
            building_coverage_ratio = (total_building_area / zone_area_sqm) * 100 if zone_area_sqm > 0 else 0
            
            return {
                'total_building_area_sqm': total_building_area,
                'mean_building_area_sqm': mean_building_area,
                'std_building_area_sqm': std_building_area,
                'building_coverage_ratio_percent': round(building_coverage_ratio, 2),
                'area_distribution': area_distribution,
                'area_variability_coefficient': round(std_building_area / mean_building_area, 3) if mean_building_area > 0 else 0,
                'buildings_per_hectare': round(building_count / (zone_area_sqm / 10000), 2) if zone_area_sqm > 0 else 0,
                'average_building_spacing_m': self._estimate_building_spacing(building_count, zone_area_sqm),
                'extraction_method': 'GeoPandas with Google Open Buildings'
            }
            
        except Exception as e:
            return {"error": f"Detailed area calculation failed: {str(e)}"}
    
    def estimate_building_heights_comprehensive(self, zone: Zone, year: int = 2023) -> Dict:
        """Estimate building heights using multiple methods and temporal data"""
        try:
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Try to get height data from Google Open Buildings temporal dataset
            height_data = self.load_open_buildings_temporal(ee_geometry, year)
            
            if height_data.get('error'):
                # Fallback to estimation methods
                return self._estimate_heights_from_shadows_and_context(zone)
            
            # Extract height statistics
            height_stats = height_data.get('height_stats', {})
            building_height_mean = height_stats.get('building_height_mean', 3.0)
            building_height_std = height_stats.get('building_height_std', 1.0)
            building_height_max = height_stats.get('building_height_max', 6.0)
            
            # Estimate floor counts
            floor_estimates = self._calculate_floor_estimates(
                building_height_mean, building_height_std, building_height_max
            )
            
            # Categorize buildings by height
            height_categories = self._categorize_buildings_by_height(
                building_height_mean, building_height_std
            )
            
            return {
                'mean_height_m': round(building_height_mean, 2),
                'std_height_m': round(building_height_std, 2),
                'max_height_m': round(building_height_max, 2),
                'floor_estimates': floor_estimates,
                'height_categories': height_categories,
                'height_data_source': 'Google Open Buildings Temporal',
                'height_data_year': year,
                'height_reliability': self._assess_height_data_reliability(height_stats)
            }
            
        except Exception as e:
            return {"error": f"Height estimation failed: {str(e)}"}
    
    def compute_building_shape_complexity(self, zone: Zone, buildings_data: Dict) -> Dict:
        """Compute shape complexity metrics for buildings"""
        try:
            # Use building area statistics
            features = buildings_data.get('features', {})
            area_stats = features.get('area_statistics', {})
            building_count = buildings_data.get('building_count', 0)
            
            mean_area = area_stats.get('mean', 100)
            
            # Estimate perimeter from area (assuming complex shapes)
            # For rectangular buildings: perimeter = 2 * sqrt(area * aspect_ratio)
            # For Lusaka context, use varying complexity factors
            estimated_mean_perimeter = self._estimate_perimeter_from_area(mean_area)
            
            # Calculate shape complexity metrics
            perimeter_area_ratio = estimated_mean_perimeter / math.sqrt(mean_area) if mean_area > 0 else 4
            
            # Shape complexity categories based on ratio
            complexity_categories = {
                'simple_rectangular_pct': 30,  # Estimated for formal settlements
                'moderate_complexity_pct': 45,  # Mixed development
                'high_complexity_pct': 25   # Informal settlements with irregular shapes
            }
            
            # Adjust based on settlement indicators
            settlement_type = buildings_data.get('settlement_context', {}).get('predicted_type', 'mixed')
            if settlement_type == 'informal':
                complexity_categories = {
                    'simple_rectangular_pct': 15,
                    'moderate_complexity_pct': 35,
                    'high_complexity_pct': 50
                }
            elif settlement_type == 'formal':
                complexity_categories = {
                    'simple_rectangular_pct': 50,
                    'moderate_complexity_pct': 40,
                    'high_complexity_pct': 10
                }
            
            return {
                'mean_perimeter_area_ratio': round(perimeter_area_ratio, 3),
                'shape_complexity_index': self._calculate_shape_complexity_index(perimeter_area_ratio),
                'complexity_categories': complexity_categories,
                'estimated_mean_perimeter_m': round(estimated_mean_perimeter, 2),
                'compactness_index': round(4 * math.pi * mean_area / (estimated_mean_perimeter ** 2), 3) if estimated_mean_perimeter > 0 else 0,
                'calculation_method': 'Perimeter estimation from area statistics',
                'settlement_context': settlement_type
            }
            
        except Exception as e:
            return {"error": f"Shape complexity calculation failed: {str(e)}"}
    
    def calculate_building_density_metrics(self, zone: Zone, buildings_data: Dict) -> Dict:
        """Calculate comprehensive building density metrics"""
        try:
            building_count = buildings_data.get('building_count', 0)
            features = buildings_data.get('features', {})
            zone_area_sqkm = features.get('zone_area_sqkm', 1)
            total_building_area = features.get('area_statistics', {}).get('sum', 0)
            
            # Basic density metrics
            buildings_per_sqkm = building_count / zone_area_sqkm if zone_area_sqkm > 0 else 0
            buildings_per_hectare = buildings_per_sqkm / 100
            
            # Built-up density
            built_up_ratio = (total_building_area / (zone_area_sqkm * 1000000)) * 100 if zone_area_sqkm > 0 else 0
            
            # Calculate local density variations (estimated)
            density_variation = self._estimate_density_variation(buildings_per_hectare, built_up_ratio)
            
            # Building cluster analysis
            cluster_metrics = self._analyze_building_clusters(building_count, zone_area_sqkm)
            
            # Density category classification
            density_category = self._classify_building_density(buildings_per_hectare, built_up_ratio)
            
            return {
                'buildings_per_sqkm': round(buildings_per_sqkm, 2),
                'buildings_per_hectare': round(buildings_per_hectare, 2),
                'built_up_ratio_percent': round(built_up_ratio, 2),
                'density_category': density_category,
                'density_variation': density_variation,
                'cluster_metrics': cluster_metrics,
                'floor_area_ratio': round(built_up_ratio / 100, 3),  # Assuming single-story average
                'open_space_ratio_percent': round(100 - built_up_ratio, 2),
                'calculation_date': time.time()
            }
            
        except Exception as e:
            return {"error": f"Density metrics calculation failed: {str(e)}"}
    
    def extract_seasonal_stability_indicators(self, zone: Zone, year: int = 2023) -> Dict:
        """Extract seasonal stability indicators from temporal analysis"""
        try:
            # Use existing multi-temporal analysis if available
            multitemporal_results = self.analyze_multitemporal_building_detection(zone, [year])
            
            if multitemporal_results.get('error'):
                return {"error": f"Cannot assess seasonal stability: {multitemporal_results['error']}"}
            
            # Extract stability metrics from multi-temporal analysis
            year_data = multitemporal_results.get('multi_temporal_analysis', {}).get(str(year), {})
            temporal_stability = year_data.get('temporal_stability', {})
            seasonal_composites = year_data.get('seasonal_composites', {})
            
            stability_interpretation = temporal_stability.get('stability_interpretation', {})
            building_likelihood = stability_interpretation.get('building_likelihood', 'Medium')
            stability_level = stability_interpretation.get('stability_level', 'Moderate')
            
            # Calculate seasonal change indicators
            seasonal_indicators = {
                'wet_season_ndvi': seasonal_composites.get('wet_season', {}).get('ndvi_stats', {}).get('wet_ndvi_mean', 0.3),
                'dry_season_ndvi': seasonal_composites.get('dry_season', {}).get('ndvi_stats', {}).get('dry_ndvi_mean', 0.2),
                'seasonal_ndvi_difference': seasonal_composites.get('seasonal_difference', {}).get('ndvi_difference_mean', 0.1)
            }
            
            # Stability score calculation
            stability_score = self._calculate_stability_score(building_likelihood, stability_level, seasonal_indicators)
            
            return {
                'building_likelihood': building_likelihood,
                'stability_level': stability_level,
                'stability_score': stability_score,
                'seasonal_indicators': seasonal_indicators,
                'quarters_analyzed': temporal_stability.get('quarters_analyzed', 4),
                'temporal_consistency': self._assess_temporal_consistency(seasonal_indicators),
                'permanent_structure_confidence': self._calculate_permanent_structure_confidence(
                    building_likelihood, seasonal_indicators
                ),
                'analysis_method': 'Multi-temporal NDVI and building detection',
                'data_year': year
            }
            
        except Exception as e:
            return {"error": f"Seasonal stability extraction failed: {str(e)}"}
    
    def calculate_derived_building_analytics(self, area_features: Dict, height_features: Dict, 
                                           shape_features: Dict, density_features: Dict) -> Dict:
        """Calculate derived analytics from extracted building features"""
        try:
            analytics = {}
            
            # Volume estimates
            if not area_features.get('error') and not height_features.get('error'):
                mean_area = area_features.get('mean_building_area_sqm', 100)
                mean_height = height_features.get('mean_height_m', 3)
                analytics['estimated_building_volume_cum'] = round(mean_area * mean_height, 2)
                
                # Floor area estimates
                floor_estimates = height_features.get('floor_estimates', {})
                mean_floors = floor_estimates.get('estimated_mean_floors', 1)
                analytics['total_floor_area_sqm'] = round(area_features.get('total_building_area_sqm', 0) * mean_floors, 2)
            
            # Development intensity
            if not density_features.get('error'):
                built_up_ratio = density_features.get('built_up_ratio_percent', 0)
                buildings_per_hectare = density_features.get('buildings_per_hectare', 0)
                
                analytics['development_intensity'] = self._classify_development_intensity(
                    built_up_ratio, buildings_per_hectare
                )
            
            # Settlement characteristics
            if not shape_features.get('error'):
                complexity_index = shape_features.get('shape_complexity_index', 'Medium')
                settlement_context = shape_features.get('settlement_context', 'mixed')
                
                analytics['settlement_characteristics'] = {
                    'development_pattern': self._interpret_development_pattern(complexity_index, settlement_context),
                    'planning_level': self._assess_planning_level(complexity_index),
                    'building_regularity': complexity_index
                }
            
            # Capacity estimates
            if 'total_floor_area_sqm' in analytics:
                # Assume different occupancy rates by settlement type
                settlement_type = shape_features.get('settlement_context', 'mixed')
                occupancy_rate = 4.1 if settlement_type == 'formal' else 6.2  # From analysis.md
                
                analytics['estimated_occupancy_capacity'] = round(
                    analytics['total_floor_area_sqm'] * (occupancy_rate / 100), 0
                )
            
            return analytics
            
        except Exception as e:
            return {"error": f"Derived analytics calculation failed: {str(e)}"}
    
    def assess_feature_extraction_quality(self, comprehensive_features: Dict) -> Dict:
        """Assess the quality and completeness of extracted features"""
        try:
            quality_metrics = {
                'data_completeness_score': 0,
                'reliability_score': 0,
                'feature_coverage': {},
                'recommendations': []
            }
            
            # Check feature completeness
            required_features = ['area_features', 'height_features', 'shape_complexity', 'density_metrics']
            available_features = []
            
            for feature in required_features:
                if feature in comprehensive_features and not comprehensive_features[feature].get('error'):
                    available_features.append(feature)
                    quality_metrics['feature_coverage'][feature] = 'Available'
                else:
                    quality_metrics['feature_coverage'][feature] = 'Missing/Error'
            
            # Calculate completeness score
            quality_metrics['data_completeness_score'] = round(
                (len(available_features) / len(required_features)) * 100, 1
            )
            
            # Assess reliability based on data sources and methods
            reliability_factors = []
            
            # Building count reliability
            building_count = comprehensive_features.get('building_count', 0)
            if building_count > 10:
                reliability_factors.append(0.25)  # Good sample size
            elif building_count > 5:
                reliability_factors.append(0.15)  # Moderate sample size
            else:
                reliability_factors.append(0.05)  # Small sample size
            
            # Height data reliability
            height_features = comprehensive_features.get('height_features', {})
            if not height_features.get('error'):
                height_reliability = height_features.get('height_reliability', 'Medium')
                if height_reliability == 'High':
                    reliability_factors.append(0.25)
                elif height_reliability == 'Medium':
                    reliability_factors.append(0.15)
                else:
                    reliability_factors.append(0.10)
            
            # Area data reliability (Google Open Buildings is generally reliable)
            area_features = comprehensive_features.get('area_features', {})
            if not area_features.get('error'):
                reliability_factors.append(0.25)
            
            # Seasonal stability reliability
            stability_features = comprehensive_features.get('seasonal_stability', {})
            if not stability_features.get('error'):
                stability_score = stability_features.get('stability_score', 0.5)
                reliability_factors.append(stability_score * 0.25)
            
            quality_metrics['reliability_score'] = round(sum(reliability_factors) * 100, 1)
            
            # Generate recommendations
            if quality_metrics['data_completeness_score'] < 75:
                quality_metrics['recommendations'].append("Consider additional data sources for missing features")
            
            if quality_metrics['reliability_score'] < 60:
                quality_metrics['recommendations'].append("Validate results with ground truth data or additional sources")
            
            if building_count < 5:
                quality_metrics['recommendations'].append("Small building sample - results may not be representative")
            
            if not quality_metrics['recommendations']:
                quality_metrics['recommendations'].append("Feature extraction quality is good - results are reliable")
            
            # Overall quality assessment
            overall_score = (quality_metrics['data_completeness_score'] + quality_metrics['reliability_score']) / 2
            if overall_score >= 80:
                quality_metrics['overall_quality'] = 'High'
            elif overall_score >= 60:
                quality_metrics['overall_quality'] = 'Medium'
            else:
                quality_metrics['overall_quality'] = 'Low'
            
            quality_metrics['overall_score'] = round(overall_score, 1)
            
            return quality_metrics
            
        except Exception as e:
            return {"error": f"Quality assessment failed: {str(e)}"}
    
    # ==================== HELPER METHODS FOR BUILDING FEATURES ====================
    
    def _estimate_area_category_percentage(self, mean_area: float, std_area: float, 
                                         min_area: float, max_area: float) -> float:
        """Estimate percentage of buildings in a specific area category using normal distribution"""
        try:
            if std_area <= 0:
                return 0
            
            # Simple estimation using normal distribution approximation
            from math import erf, sqrt
            
            # Normalize to standard normal
            z_min = (min_area - mean_area) / std_area if min_area != 0 else float('-inf')
            z_max = (max_area - mean_area) / std_area if max_area != float('inf') else float('inf')
            
            # Calculate approximate percentage
            if z_min == float('-inf'):
                prob = 0.5 * (1 + erf(z_max / sqrt(2)))
            elif z_max == float('inf'):
                prob = 0.5 * (1 - erf(z_min / sqrt(2)))
            else:
                prob = 0.5 * (erf(z_max / sqrt(2)) - erf(z_min / sqrt(2)))
            
            return round(max(0, min(100, prob * 100)), 1)
            
        except:
            return 20  # Default estimate
    
    def _estimate_building_spacing(self, building_count: int, zone_area_sqm: float) -> float:
        """Estimate average building spacing"""
        if building_count <= 1 or zone_area_sqm <= 0:
            return 0
        
        # Approximate spacing assuming regular grid
        area_per_building = zone_area_sqm / building_count
        spacing = math.sqrt(area_per_building)
        return round(spacing, 1)
    
    def _estimate_heights_from_shadows_and_context(self, zone: Zone) -> Dict:
        """Fallback method to estimate heights from context"""
        # Use typical building heights for different settlement types
        # This is a simplified fallback method
        return {
            'mean_height_m': 3.5,
            'std_height_m': 1.2,
            'max_height_m': 8.0,
            'floor_estimates': {
                'estimated_mean_floors': 1.4,
                'single_story_pct': 70,
                'two_story_pct': 25,
                'multi_story_pct': 5
            },
            'height_categories': {
                'low_rise_pct': 85,
                'medium_rise_pct': 15,
                'high_rise_pct': 0
            },
            'height_data_source': 'Estimated from regional context',
            'height_reliability': 'Low'
        }
    
    def _calculate_floor_estimates(self, mean_height: float, std_height: float, max_height: float) -> Dict:
        """Calculate floor count estimates from height data"""
        # Assume 2.5m per floor average
        floor_height = 2.5
        
        estimated_mean_floors = max(1, mean_height / floor_height)
        estimated_max_floors = max(1, max_height / floor_height)
        
        # Estimate distribution
        single_story_pct = max(0, 100 - (estimated_mean_floors - 1) * 40)
        two_story_pct = min(50, max(0, (estimated_mean_floors - 1) * 30))
        multi_story_pct = max(0, 100 - single_story_pct - two_story_pct)
        
        return {
            'estimated_mean_floors': round(estimated_mean_floors, 1),
            'estimated_max_floors': round(estimated_max_floors, 1),
            'single_story_pct': round(single_story_pct, 1),
            'two_story_pct': round(two_story_pct, 1),
            'multi_story_pct': round(multi_story_pct, 1),
            'floor_height_assumption_m': floor_height
        }
    
    def _categorize_buildings_by_height(self, mean_height: float, std_height: float) -> Dict:
        """Categorize buildings by height ranges"""
        if mean_height < 4:
            return {
                'low_rise_pct': 85,
                'medium_rise_pct': 15,
                'high_rise_pct': 0,
                'dominant_category': 'low_rise'
            }
        elif mean_height < 8:
            return {
                'low_rise_pct': 60,
                'medium_rise_pct': 35,
                'high_rise_pct': 5,
                'dominant_category': 'mixed_low_medium'
            }
        else:
            return {
                'low_rise_pct': 30,
                'medium_rise_pct': 50,
                'high_rise_pct': 20,
                'dominant_category': 'medium_high_rise'
            }
    
    def _assess_height_data_reliability(self, height_stats: Dict) -> str:
        """Assess reliability of height data"""
        building_count = height_stats.get('building_count', 0)
        height_variance = height_stats.get('building_height_variance', 0)
        
        if building_count > 20 and height_variance < 5:
            return 'High'
        elif building_count > 10:
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_perimeter_from_area(self, area: float) -> float:
        """Estimate building perimeter from area using typical building shapes"""
        # For rectangular buildings with typical aspect ratios
        # Assuming aspect ratio between 1:1 and 2:1
        avg_aspect_ratio = 1.4
        perimeter = 2 * math.sqrt(area * avg_aspect_ratio) + 2 * math.sqrt(area / avg_aspect_ratio)
        return perimeter
    
    def _calculate_shape_complexity_index(self, perimeter_area_ratio: float) -> str:
        """Calculate shape complexity index from perimeter-to-area ratio"""
        # For a perfect circle, ratio = 2*sqrt(π) ≈ 3.54
        # For a square, ratio = 4
        # Higher ratios indicate more complex shapes
        
        if perimeter_area_ratio < 4.5:
            return 'Low'  # Regular shapes
        elif perimeter_area_ratio < 6.0:
            return 'Medium'  # Moderately irregular
        else:
            return 'High'  # Highly irregular (typical of informal settlements)
    
    def _estimate_density_variation(self, buildings_per_hectare: float, built_up_ratio: float) -> Dict:
        """Estimate density variation within the zone"""
        # Simple estimation based on overall density
        variation_level = 'Low'
        
        if buildings_per_hectare > 50:
            variation_level = 'High'  # Dense areas tend to have more variation
        elif buildings_per_hectare > 20:
            variation_level = 'Medium'
        
        return {
            'variation_level': variation_level,
            'estimated_coefficient_of_variation': round(built_up_ratio / 100 + 0.2, 2),
            'spatial_heterogeneity': 'High' if built_up_ratio > 40 else 'Medium' if built_up_ratio > 20 else 'Low'
        }
    
    def _analyze_building_clusters(self, building_count: int, zone_area_sqkm: float) -> Dict:
        """Analyze building clustering patterns"""
        if zone_area_sqkm <= 0:
            return {"error": "Invalid zone area"}
        
        density = building_count / zone_area_sqkm
        
        if density > 100:
            cluster_pattern = 'Highly clustered'
            cluster_size = 'Large clusters'
        elif density > 50:
            cluster_pattern = 'Moderately clustered'
            cluster_size = 'Medium clusters'
        elif density > 20:
            cluster_pattern = 'Scattered clusters'
            cluster_size = 'Small clusters'
        else:
            cluster_pattern = 'Dispersed'
            cluster_size = 'Individual buildings'
        
        return {
            'cluster_pattern': cluster_pattern,
            'estimated_cluster_size': cluster_size,
            'density_uniformity': 'Low' if density > 80 else 'Medium' if density > 40 else 'High'
        }
    
    def _classify_building_density(self, buildings_per_hectare: float, built_up_ratio: float) -> str:
        """Classify building density category"""
        if buildings_per_hectare > 80 or built_up_ratio > 60:
            return 'Very High Density'
        elif buildings_per_hectare > 50 or built_up_ratio > 40:
            return 'High Density'
        elif buildings_per_hectare > 25 or built_up_ratio > 25:
            return 'Medium Density'
        elif buildings_per_hectare > 10 or built_up_ratio > 10:
            return 'Low Density'
        else:
            return 'Very Low Density'
    
    def _calculate_stability_score(self, building_likelihood: str, stability_level: str, 
                                 seasonal_indicators: Dict) -> float:
        """Calculate numerical stability score from qualitative assessments"""
        score = 0.5  # Base score
        
        # Building likelihood contribution
        if building_likelihood == 'High':
            score += 0.3
        elif building_likelihood == 'Medium':
            score += 0.15
        
        # Stability level contribution
        if stability_level == 'High':
            score += 0.15
        elif stability_level == 'Moderate':
            score += 0.1
        
        # Seasonal NDVI difference (lower is better for buildings)
        ndvi_diff = seasonal_indicators.get('seasonal_ndvi_difference', 0.1)
        if ndvi_diff < 0.1:
            score += 0.05
        elif ndvi_diff > 0.3:
            score -= 0.1
        
        return round(max(0, min(1, score)), 3)
    
    def _assess_temporal_consistency(self, seasonal_indicators: Dict) -> str:
        """Assess temporal consistency of building detection"""
        ndvi_diff = seasonal_indicators.get('seasonal_ndvi_difference', 0.1)
        
        if ndvi_diff < 0.15:
            return 'High consistency (stable structures)'
        elif ndvi_diff < 0.25:
            return 'Moderate consistency'
        else:
            return 'Low consistency (may include vegetation)'
    
    def _calculate_permanent_structure_confidence(self, building_likelihood: str, 
                                                seasonal_indicators: Dict) -> float:
        """Calculate confidence that detected structures are permanent buildings"""
        base_confidence = 0.6
        
        if building_likelihood == 'High':
            base_confidence = 0.8
        elif building_likelihood == 'Low':
            base_confidence = 0.4
        
        # Adjust based on seasonal stability
        ndvi_diff = seasonal_indicators.get('seasonal_ndvi_difference', 0.1)
        if ndvi_diff < 0.1:
            base_confidence += 0.15
        elif ndvi_diff > 0.3:
            base_confidence -= 0.2
        
        return round(max(0, min(1, base_confidence)), 3)
    
    def _classify_development_intensity(self, built_up_ratio: float, buildings_per_hectare: float) -> str:
        """Classify development intensity based on multiple metrics"""
        intensity_score = (built_up_ratio / 10) + (buildings_per_hectare / 20)
        
        if intensity_score > 8:
            return 'Very High Intensity'
        elif intensity_score > 6:
            return 'High Intensity'
        elif intensity_score > 4:
            return 'Medium Intensity'
        elif intensity_score > 2:
            return 'Low Intensity'
        else:
            return 'Very Low Intensity'
    
    def _interpret_development_pattern(self, complexity_index: str, settlement_context: str) -> str:
        """Interpret development pattern from complexity and context"""
        if settlement_context == 'formal':
            if complexity_index == 'Low':
                return 'Planned formal development'
            else:
                return 'Mixed formal development'
        elif settlement_context == 'informal':
            if complexity_index == 'High':
                return 'Organic informal settlement'
            else:
                return 'Semi-organized informal settlement'
        else:
            return 'Mixed development pattern'
    
    def _assess_planning_level(self, complexity_index: str) -> str:
        """Assess planning level from shape complexity"""
        if complexity_index == 'Low':
            return 'Well planned'
        elif complexity_index == 'Medium':
            return 'Moderately planned'
        else:
            return 'Unplanned/organic growth'

    # ==================== EXISTING METHODS ====================

    def analyze_zone_land_use(self, zone):
        """Analyze land use patterns within a zone using satellite imagery"""
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Convert zone geometry to Earth Engine format
            zone_geojson = zone.geojson
            ee_geometry = ee.Geometry(zone_geojson['geometry'])
            
            # Get recent Sentinel-2 imagery (using harmonized collection)
            sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(ee_geometry) \
                .filterDate('2023-01-01', '2024-01-01') \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .select(['B2', 'B3', 'B4', 'B8', 'B11']) \
                .median()
            
            # Calculate NDVI (vegetation index)
            ndvi = sentinel2.normalizedDifference(['B8', 'B4']).rename('ndvi')
            
            # Calculate built-up area index
            ndbi = sentinel2.normalizedDifference(['B11', 'B8']).rename('ndbi')
            
            # Get statistics
            stats = ee.Image.cat([ndvi, ndbi]).reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.minMax(), '', True
                ),
                geometry=ee_geometry,
                scale=10,
                maxPixels=1e9
            )
            
            # Extract values
            stats_dict = stats.getInfo()
            
            # Classify land use based on indices
            vegetation_percentage = self._calculate_vegetation_coverage(stats_dict.get('ndvi_mean', 0))
            built_up_percentage = self._calculate_built_up_coverage(stats_dict.get('ndbi_mean', 0))
            
            return {
                'vegetation_index': round(stats_dict.get('ndvi_mean', 0), 3),
                'built_up_index': round(stats_dict.get('ndbi_mean', 0), 3),
                'vegetation_coverage_percent': vegetation_percentage,
                'built_up_area_percent': built_up_percentage,
                'bare_soil_percent': max(0, 100 - vegetation_percentage - built_up_percentage),
                'analysis_date': datetime.datetime.now().isoformat(),
                'imagery_source': 'Sentinel-2'
            }
            
        except Exception as e:
            return {"error": f"Land use analysis failed: {str(e)}"}
    
    def analyze_zone_changes(self, zone, start_date='2020-01-01', end_date='2024-01-01'):
        """Analyze temporal changes in the zone"""
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Get imagery for start and end periods
            def get_composite(date_start, date_end):
                return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                    .filterBounds(ee_geometry) \
                    .filterDate(date_start, date_end) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .select(['B2', 'B3', 'B4', 'B8', 'B11']) \
                    .median()
            
            start_composite = get_composite(start_date, ee.Date(start_date).advance(6, 'month'))
            end_composite = get_composite(ee.Date(end_date).advance(-6, 'month'), end_date)
            
            # Calculate NDVI for both periods
            start_ndvi = start_composite.normalizedDifference(['B8', 'B4'])
            end_ndvi = end_composite.normalizedDifference(['B8', 'B4'])
            
            # Calculate change
            ndvi_change = end_ndvi.subtract(start_ndvi)
            
            # Get statistics
            change_stats = ndvi_change.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.percentile([10, 90]), '', True
                ),
                geometry=ee_geometry,
                scale=10,
                maxPixels=1e9
            ).getInfo()
            
            return {
                'vegetation_change': round(change_stats.get('nd_mean', 0), 3),
                'significant_loss_areas': change_stats.get('nd_p10', 0) < -0.2,
                'significant_gain_areas': change_stats.get('nd_p90', 0) > 0.2,
                'analysis_period': f"{start_date} to {end_date}",
                'change_interpretation': self._interpret_change(change_stats.get('nd_mean', 0))
            }
            
        except Exception as e:
            return {"error": f"Change analysis failed: {str(e)}"}
    
    def get_population_estimate(self, zone_or_geojson):
        """Enhanced population estimation using GPWv4.11 primary with WorldPop validation and urban corrections"""
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Handle both zone objects and GeoJSON directly
            if hasattr(zone_or_geojson, 'geojson'):
                # Zone object with .geojson attribute
                geometry = zone_or_geojson.geojson['geometry']
                zone_obj = zone_or_geojson
            elif isinstance(zone_or_geojson, dict):
                # Check if it's a GeoJSON Feature
                if zone_or_geojson.get('type') == 'Feature':
                    geometry = zone_or_geojson['geometry']
                # Check if it's just a geometry
                elif zone_or_geojson.get('type') in ['Polygon', 'MultiPolygon']:
                    geometry = zone_or_geojson
                else:
                    return {"error": "Invalid GeoJSON format"}
                
                # Create a temporary zone-like object for GPWv4.11 method
                zone_obj = type('TempZone', (), {
                    'geojson': {'type': 'Feature', 'geometry': geometry, 'properties': {}}
                })()
            else:
                return {"error": "Invalid input - expected zone object or GeoJSON"}
            
            # Step 1: Get GPWv4.11 population estimate (more reliable for totals)
            try:
                gpw_result = self.extract_ghsl_population_for_zone(zone_obj)
                
                if gpw_result and not gpw_result.get('error'):
                    gpw_population = gpw_result.get('total_population', 0)
                    density_per_sqkm = gpw_result.get('population_density_per_sqkm', 0)
                    density_category = gpw_result.get('density_category', 'Unknown')
                    
                    # Step 2: Apply urban correction factors for Lusaka high-density areas
                    corrected_population = self._apply_urban_density_corrections(
                        gpw_population, density_per_sqkm, density_category
                    )
                    
                    # Step 3: Get WorldPop for spatial validation (but don't rely on its totals)
                    worldpop_validation = self._get_worldpop_validation(geometry)
                    
                    # Determine confidence based on data quality and urban context
                    confidence = self._calculate_population_confidence(
                        corrected_population, density_per_sqkm, density_category, worldpop_validation
                    )
                    
                    return {
                        'estimated_population': int(corrected_population),
                        'population_density_per_sqkm': density_per_sqkm,
                        'density_category': density_category,
                        'data_source': f'GPWv4.11 with Urban Corrections ({density_category})',
                        'confidence': confidence,
                        'raw_gpw_population': int(gpw_population),
                        'correction_factor': round(corrected_population / gpw_population, 2) if gpw_population > 0 else 1.0,
                        'validation_data': worldpop_validation
                    }
                    
            except Exception as gpw_error:
                print(f"GPWv4.11 failed: {gpw_error}, falling back to WorldPop...")
            
            # Fallback to original WorldPop method if GPWv4.11 fails
            ee_geometry = ee.Geometry(geometry)
            
            # Get WorldPop population density data for Zambia
            worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filter(ee.Filter.eq('country', 'ZMB')) \
                .filter(ee.Filter.eq('year', 2020)) \
                .first()
            
            # Calculate total population
            pop_sum = worldpop.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=ee_geometry,
                scale=100,
                maxPixels=1e9
            )
            
            results = pop_sum.getInfo()
            total_pop = results.get('population', 0)
            
            # Apply basic urban correction for WorldPop (known to underestimate)
            corrected_pop = total_pop * 1.8  # Conservative correction factor for urban areas
            
            return {
                'estimated_population': int(corrected_pop),
                'population_density_per_sqkm': 0,
                'data_source': 'WorldPop 2020 (corrected for urban underestimation)',
                'confidence': 'medium',
                'raw_worldpop_population': int(total_pop),
                'correction_factor': 1.8
            }
            
        except Exception as e:
            # Enhanced fallback using analysis.md methodology when Earth Engine fails
            try:
                # Calculate zone area in square meters
                import json
                from shapely.geometry import shape
                
                zone_shape = shape(zone.geojson['geometry'])
                # More accurate area calculation for Lusaka region (around -15.4° latitude)
                # At Lusaka's latitude, 1 degree ≈ 111 km longitude, 111 km latitude
                lat_factor = 111320  # meters per degree latitude
                lon_factor = 111320 * abs(math.cos(math.radians(-15.4)))  # Adjust for longitude at Lusaka latitude
                
                # Use zone.area_sqm if available, otherwise calculate from geometry
                if hasattr(zone, 'area_sqm') and zone.area_sqm:
                    area_sqm = zone.area_sqm
                else:
                    # Rough area calculation in square meters
                    area_degrees = zone_shape.area
                    area_sqm = area_degrees * lat_factor * lon_factor
                area_km2 = area_sqm / 1000000
                
                # Use analysis.md building-based density estimation
                # Mixed settlement assumption for fallback: 11 people per 100 sqm
                building_coverage = 0.30  # Typical 30% building coverage
                people_per_sqm = 0.11     # From analysis.md for mixed settlements
                
                building_area_sqm = area_sqm * building_coverage
                estimated_population = building_area_sqm * people_per_sqm
                
                # Alternative area-based calculation: 5000 people/km² for mixed Lusaka areas
                area_based_population = area_km2 * 5000
                
                # Use the higher estimate for safety
                final_population = max(estimated_population, area_based_population)
                
                return {
                    'estimated_population': int(final_population),
                    'population_density_per_hectare': round((final_population / (area_sqm / 10000)), 2),
                    'max_density_per_hectare': round((final_population / (area_sqm / 10000)), 2),
                    'data_source': 'Enhanced Fallback (analysis.md methodology)',
                    'confidence': 'medium',
                    'method': 'building_based_fallback',
                    'building_area_estimate': int(estimated_population),
                    'area_density_estimate': int(area_based_population),
                    'fallback_reason': str(e)
                }
            except Exception as fallback_error:
                return {"error": f"Population estimation failed: {str(e)}, Fallback also failed: {str(fallback_error)}"}
    
    def analyze_environmental_factors(self, zone):
        """Analyze environmental factors like temperature, precipitation"""
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Get climate data from ERA5
            climate = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY') \
                .filterBounds(ee_geometry) \
                .filterDate('2023-01-01', '2024-01-01') \
                .select(['temperature_2m', 'total_precipitation'])
            
            # Calculate annual statistics
            annual_temp = climate.select('temperature_2m').mean()
            annual_precip = climate.select('total_precipitation').sum()
            
            # Get statistics for the zone
            climate_stats = ee.Image.cat([annual_temp, annual_precip]).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee_geometry,
                scale=1000,
                maxPixels=1e9
            ).getInfo()
            
            # Convert temperature from Kelvin to Celsius
            temp_celsius = climate_stats.get('temperature_2m', 273.15) - 273.15
            # Convert precipitation from meters to mm
            precip_mm = climate_stats.get('total_precipitation', 0) * 1000
            
            return {
                'average_temperature_celsius': round(temp_celsius, 1),
                'annual_precipitation_mm': round(precip_mm, 1),
                'climate_zone': self._classify_climate(temp_celsius, precip_mm),
                'waste_decomposition_rate': self._estimate_decomposition_rate(temp_celsius, precip_mm),
                'recommended_collection_frequency': self._recommend_collection_frequency(temp_celsius)
            }
            
        except Exception as e:
            return {"error": f"Environmental analysis failed: {str(e)}"}
    
    def _calculate_vegetation_coverage(self, ndvi_mean):
        """Calculate vegetation coverage percentage from NDVI"""
        if ndvi_mean > 0.4:
            return round(70 + (ndvi_mean - 0.4) * 100, 1)
        elif ndvi_mean > 0.2:
            return round(30 + (ndvi_mean - 0.2) * 200, 1)
        else:
            return round(max(0, ndvi_mean * 150), 1)
    
    def _calculate_built_up_coverage(self, ndbi_mean):
        """Calculate built-up area percentage from NDBI"""
        if ndbi_mean > 0.1:
            return round(50 + (ndbi_mean - 0.1) * 200, 1)
        elif ndbi_mean > 0:
            return round(ndbi_mean * 500, 1)
        else:
            return 0
    
    def _interpret_change(self, change_value):
        """Interpret vegetation change value"""
        if change_value < -0.1:
            return "Significant vegetation loss - possible urbanization"
        elif change_value < -0.05:
            return "Moderate vegetation loss"
        elif change_value > 0.1:
            return "Significant vegetation gain - greening or recovery"
        elif change_value > 0.05:
            return "Moderate vegetation gain"
        else:
            return "Stable - minimal change"
    
    def _classify_climate(self, temp, precip):
        """Classify climate based on temperature and precipitation"""
        if temp > 25 and precip > 1000:
            return "Tropical wet"
        elif temp > 25 and precip < 1000:
            return "Tropical dry"
        elif temp > 18:
            return "Subtropical"
        else:
            return "Temperate"
    
    def _estimate_decomposition_rate(self, temp, precip):
        """Estimate waste decomposition rate based on climate"""
        if temp > 25 and precip > 1000:
            return "Very High - frequent collection needed"
        elif temp > 20:
            return "High - regular collection important"
        else:
            return "Moderate - standard collection schedule"
    
    def _recommend_collection_frequency(self, temperature):
        """Recommend collection frequency based on temperature"""
        if temperature > 30:
            return "Daily collection recommended"
        elif temperature > 25:
            return "3-4 times per week"
        elif temperature > 20:
            return "2-3 times per week"
        else:
            return "2 times per week"

    # ==================== SENTINEL-2 MULTI-TEMPORAL ANALYSIS ====================
    
    def setup_sentinel2_pipeline(self, aoi_geometry: ee.Geometry, start_date: str = '2022-01-01', 
                                end_date: str = '2024-01-01') -> Dict:
        """
        Set up Sentinel-2 multi-temporal imagery pipeline for Lusaka region
        
        Args:
            aoi_geometry: Area of interest geometry
            start_date: Start date for imagery collection (YYYY-MM-DD)
            end_date: End date for imagery collection (YYYY-MM-DD)
            
        Returns:
            Dict: Pipeline setup results with collection info
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Load Sentinel-2 Surface Reflectance collection
            sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(aoi_geometry) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
            # Get collection info
            collection_size = sentinel2.size()
            date_range = sentinel2.aggregate_array('system:time_start')
            
            return {
                'collection_size': collection_size.getInfo(),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'cloud_threshold': 20,
                'collection_id': 'COPERNICUS/S2_SR_HARMONIZED',
                'status': 'configured'
            }
            
        except Exception as e:
            return {"error": f"Sentinel-2 pipeline setup failed: {str(e)}"}
    
    def create_cloud_mask(self, image: ee.Image) -> ee.Image:
        """
        Create cloud mask using QA60 band and cloud probability
        
        Args:
            image: Sentinel-2 image
            
        Returns:
            ee.Image: Cloud-masked image
        """
        try:
            # Get QA60 band (cloud mask)
            qa = image.select('QA60')
            
            # Bits 10 and 11 are clouds and cirrus respectively
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            
            # Create mask: both flags should be set to zero (clear conditions)
            mask = qa.bitwiseAnd(cloud_bit_mask).eq(0) \
                .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
            
            # Apply mask and scale values
            return image.updateMask(mask).multiply(0.0001) \
                .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']) \
                .copyProperties(image, ['system:time_start'])
                
        except Exception as e:
            # Return original image if masking fails
            return image.multiply(0.0001).select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
    
    def generate_seasonal_composites(self, aoi_geometry: ee.Geometry, year: int = 2023) -> Dict:
        """
        Generate seasonal composites for Lusaka (wet and dry seasons)
        
        Args:
            aoi_geometry: Area of interest geometry
            year: Year for analysis
            
        Returns:
            Dict: Seasonal composite results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Define Lusaka's seasons based on analysis.md
            # Wet season: November-April (rainy season)
            # Dry season: May-October
            
            # Wet season composite (Nov previous year to April current year)
            wet_start = ee.Date.fromYMD(year - 1, 11, 1)
            wet_end = ee.Date.fromYMD(year, 4, 30)
            
            # Dry season composite (May to October current year)
            dry_start = ee.Date.fromYMD(year, 5, 1)
            dry_end = ee.Date.fromYMD(year, 10, 31)
            
            # Create wet season composite
            wet_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(aoi_geometry) \
                .filterDate(wet_start, wet_end) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .map(self.create_cloud_mask)
            
            wet_composite = wet_collection.median()
            
            # Create dry season composite
            dry_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(aoi_geometry) \
                .filterDate(dry_start, dry_end) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .map(self.create_cloud_mask)
            
            dry_composite = dry_collection.median()
            
            # Calculate NDVI for both seasons
            wet_ndvi = wet_composite.normalizedDifference(['B8', 'B4']).rename('wet_ndvi')
            dry_ndvi = dry_composite.normalizedDifference(['B8', 'B4']).rename('dry_ndvi')
            
            # Calculate NDBI (Normalized Difference Built-up Index)
            wet_ndbi = wet_composite.normalizedDifference(['B11', 'B8']).rename('wet_ndbi')
            dry_ndbi = dry_composite.normalizedDifference(['B11', 'B8']).rename('dry_ndbi')
            
            # Calculate seasonal differences
            ndvi_difference = wet_ndvi.subtract(dry_ndvi).rename('ndvi_seasonal_diff')
            ndbi_difference = wet_ndbi.subtract(dry_ndbi).rename('ndbi_seasonal_diff')
            
            # Get statistics
            wet_stats = wet_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            )
            
            dry_stats = dry_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            )
            
            diff_stats = ndvi_difference.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            )
            
            return {
                'year': year,
                'wet_season': {
                    'period': f"{year-1}-11-01 to {year}-04-30",
                    'images_used': wet_collection.size().getInfo(),
                    'ndvi_stats': wet_stats.getInfo()
                },
                'dry_season': {
                    'period': f"{year}-05-01 to {year}-10-31",
                    'images_used': dry_collection.size().getInfo(),
                    'ndvi_stats': dry_stats.getInfo()
                },
                'seasonal_difference': {
                    'ndvi_diff_stats': diff_stats.getInfo(),
                    'interpretation': self._interpret_seasonal_difference(diff_stats.getInfo())
                },
                'composites_created': True
            }
            
        except Exception as e:
            return {"error": f"Seasonal composite generation failed: {str(e)}"}
    
    def calculate_temporal_stability(self, aoi_geometry: ee.Geometry, 
                                   start_date: str = '2022-01-01', 
                                   end_date: str = '2024-01-01') -> Dict:
        """
        Calculate temporal stability indicators for building detection
        
        Args:
            aoi_geometry: Area of interest geometry
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict: Temporal stability analysis results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Create quarterly composites for stability analysis
            start = ee.Date(start_date)
            end = ee.Date(end_date)
            
            # Function to create quarterly composite
            def create_quarterly_composite(start_quarter):
                end_quarter = start_quarter.advance(3, 'month')
                return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                    .filterBounds(aoi_geometry) \
                    .filterDate(start_quarter, end_quarter) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .map(self.create_cloud_mask) \
                    .median() \
                    .set('start_date', start_quarter.format('YYYY-MM-dd'))
            
            # Generate quarterly composites
            quarters = ee.List.sequence(0, end.difference(start, 'month').divide(3).floor())
            quarterly_images = quarters.map(lambda i: create_quarterly_composite(
                start.advance(ee.Number(i).multiply(3), 'month')
            ))
            
            quarterly_collection = ee.ImageCollection.fromImages(quarterly_images)
            
            # Calculate NDVI for each quarter
            ndvi_collection = quarterly_collection.map(lambda img: 
                img.normalizedDifference(['B8', 'B4']).rename('ndvi')
                .copyProperties(img, ['start_date'])
            )
            
            # Calculate temporal statistics
            ndvi_mean = ndvi_collection.mean().rename('ndvi_temporal_mean')
            ndvi_stddev = ndvi_collection.reduce(ee.Reducer.stdDev()).rename('ndvi_temporal_stddev')
            
            # Calculate coefficient of variation (CV)
            ndvi_cv = ndvi_stddev.divide(ndvi_mean).rename('ndvi_cv')
            
            # Get stability statistics
            stability_stats = ee.Image.cat([ndvi_mean, ndvi_stddev, ndvi_cv]).reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.percentile([10, 25, 50, 75, 90]), '', True
                ),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            )
            
            stats_info = stability_stats.getInfo()
            
            return {
                'analysis_period': f"{start_date} to {end_date}",
                'quarters_analyzed': quarterly_collection.size().getInfo(),
                'stability_metrics': stats_info,
                'stability_interpretation': self._interpret_stability_metrics(stats_info),
                'temporal_composites_created': True
            }
            
        except Exception as e:
            return {"error": f"Temporal stability analysis failed: {str(e)}"}
    
    def apply_vegetation_mask_for_buildings(self, aoi_geometry: ee.Geometry, year: int = 2023) -> Dict:
        """
        Apply seasonal NDVI filtering to reduce false positives from vegetation
        Based on analysis.md recommendations for Lusaka
        
        Args:
            aoi_geometry: Area of interest geometry
            year: Year for analysis
            
        Returns:
            Dict: Vegetation masking results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Generate seasonal composites
            seasonal_data = self.generate_seasonal_composites(aoi_geometry, year)
            
            if seasonal_data.get('error'):
                return seasonal_data
            
            # Get seasonal NDVI difference threshold (from analysis.md)
            # Areas with high seasonal NDVI difference (>0.2) are vegetation, not buildings
            ndvi_threshold = 0.2
            
            # Create wet and dry season composites again for masking
            wet_start = ee.Date.fromYMD(year - 1, 11, 1)
            wet_end = ee.Date.fromYMD(year, 4, 30)
            dry_start = ee.Date.fromYMD(year, 5, 1)
            dry_end = ee.Date.fromYMD(year, 10, 31)
            
            # Wet season composite
            wet_composite = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(aoi_geometry) \
                .filterDate(wet_start, wet_end) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .map(self.create_cloud_mask) \
                .median()
            
            # Dry season composite
            dry_composite = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(aoi_geometry) \
                .filterDate(dry_start, dry_end) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .map(self.create_cloud_mask) \
                .median()
            
            # Calculate seasonal NDVI
            wet_ndvi = wet_composite.normalizedDifference(['B8', 'B4'])
            dry_ndvi = dry_composite.normalizedDifference(['B8', 'B4'])
            ndvi_diff = wet_ndvi.subtract(dry_ndvi)
            
            # Create vegetation mask (areas with high seasonal NDVI difference)
            vegetation_mask = ndvi_diff.gt(ndvi_threshold)
            building_mask = vegetation_mask.Not()  # Inverse for buildings
            
            # Calculate mask statistics
            total_area = aoi_geometry.area().divide(1000000)  # km²
            vegetation_area = vegetation_mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            ).get('nd')
            
            building_area = building_mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi_geometry,
                scale=10,
                maxPixels=1e9
            ).get('nd')
            
            # Convert to km² and calculate percentages
            total_area_val = total_area.getInfo()
            vegetation_area_val = ee.Number(vegetation_area).divide(1000000).getInfo()
            building_area_val = ee.Number(building_area).divide(1000000).getInfo()
            
            return {
                'year': year,
                'ndvi_threshold': ndvi_threshold,
                'total_area_km2': total_area_val,
                'vegetation_area_km2': vegetation_area_val,
                'potential_building_area_km2': building_area_val,
                'vegetation_percentage': round((vegetation_area_val / total_area_val) * 100, 2),
                'potential_building_percentage': round((building_area_val / total_area_val) * 100, 2),
                'mask_effectiveness': self._evaluate_mask_effectiveness(
                    vegetation_area_val, building_area_val, total_area_val
                ),
                'seasonal_difference_applied': True
            }
            
        except Exception as e:
            return {"error": f"Vegetation masking failed: {str(e)}"}
    
    def analyze_multitemporal_building_detection(self, zone: Zone, years: List[int] = [2022, 2023]) -> Dict:
        """
        Comprehensive multi-temporal building detection analysis
        Combines seasonal filtering, temporal stability, and building classification
        
        Args:
            zone: Zone object with geometry
            years: List of years to analyze
            
        Returns:
            Dict: Comprehensive building detection results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            results = {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'analysis_years': years,
                'multi_temporal_analysis': {}
            }
            
            # Analyze each year
            for year in years:
                year_results = {}
                
                # Generate seasonal composites
                seasonal_data = self.generate_seasonal_composites(ee_geometry, year)
                year_results['seasonal_analysis'] = seasonal_data
                
                # Apply vegetation masking
                vegetation_mask = self.apply_vegetation_mask_for_buildings(ee_geometry, year)
                year_results['vegetation_filtering'] = vegetation_mask
                
                # Calculate temporal stability
                stability_analysis = self.calculate_temporal_stability(
                    ee_geometry, 
                    f"{year}-01-01", 
                    f"{year+1}-01-01"
                )
                year_results['temporal_stability'] = stability_analysis
                
                results['multi_temporal_analysis'][str(year)] = year_results
            
            # Cross-year analysis
            if len(years) > 1:
                results['cross_year_analysis'] = self._analyze_cross_year_changes(
                    results['multi_temporal_analysis']
                )
            
            # Generate building detection recommendations
            results['building_detection_recommendations'] = self._generate_detection_recommendations(
                results
            )
            
            return results
            
        except Exception as e:
            return {"error": f"Multi-temporal building detection analysis failed: {str(e)}"}
    
    def _interpret_seasonal_difference(self, diff_stats: Dict) -> str:
        """Interpret seasonal NDVI difference statistics"""
        try:
            mean_diff = diff_stats.get('wet_ndvi_mean', 0) - diff_stats.get('dry_ndvi_mean', 0)
            
            if mean_diff > 0.3:
                return "High seasonal vegetation variation - excellent for building separation"
            elif mean_diff > 0.2:
                return "Moderate seasonal variation - good for building detection"
            elif mean_diff > 0.1:
                return "Low seasonal variation - some building separation possible"
            else:
                return "Minimal seasonal variation - limited vegetation masking effectiveness"
        except:
            return "Unable to interpret seasonal differences"
    
    def _interpret_stability_metrics(self, stats: Dict) -> Dict:
        """Interpret temporal stability metrics for building detection"""
        try:
            cv_mean = stats.get('ndvi_cv_mean', 0)
            stability_assessment = {}
            
            if cv_mean < 0.1:
                stability_assessment['stability_level'] = "Very Stable"
                stability_assessment['building_likelihood'] = "High"
            elif cv_mean < 0.2:
                stability_assessment['stability_level'] = "Stable"
                stability_assessment['building_likelihood'] = "Medium-High"
            elif cv_mean < 0.3:
                stability_assessment['stability_level'] = "Moderately Stable"
                stability_assessment['building_likelihood'] = "Medium"
            else:
                stability_assessment['stability_level'] = "Unstable"
                stability_assessment['building_likelihood'] = "Low"
            
            stability_assessment['coefficient_of_variation'] = cv_mean
            return stability_assessment
            
        except:
            return {"error": "Unable to interpret stability metrics"}
    
    def _evaluate_mask_effectiveness(self, veg_area: float, building_area: float, total_area: float) -> Dict:
        """Evaluate the effectiveness of vegetation masking"""
        try:
            veg_ratio = veg_area / total_area
            building_ratio = building_area / total_area
            
            effectiveness = {}
            
            if veg_ratio > 0.6:
                effectiveness['vegetation_detection'] = "Excellent"
            elif veg_ratio > 0.4:
                effectiveness['vegetation_detection'] = "Good"
            elif veg_ratio > 0.2:
                effectiveness['vegetation_detection'] = "Moderate"
            else:
                effectiveness['vegetation_detection'] = "Limited"
            
            if building_ratio > 0.3:
                effectiveness['building_area_identified'] = "High"
            elif building_ratio > 0.15:
                effectiveness['building_area_identified'] = "Medium"
            else:
                effectiveness['building_area_identified'] = "Low"
            
            effectiveness['balance_score'] = min(veg_ratio + building_ratio, 1.0)
            return effectiveness
            
        except:
            return {"error": "Unable to evaluate mask effectiveness"}
    
    def _analyze_cross_year_changes(self, multi_year_data: Dict) -> Dict:
        """Analyze changes across multiple years"""
        try:
            years = sorted(multi_year_data.keys())
            changes = {}
            
            if len(years) >= 2:
                # Compare vegetation percentages
                first_year = multi_year_data[years[0]]
                last_year = multi_year_data[years[-1]]
                
                first_veg = first_year.get('vegetation_filtering', {}).get('vegetation_percentage', 0)
                last_veg = last_year.get('vegetation_filtering', {}).get('vegetation_percentage', 0)
                
                first_building = first_year.get('vegetation_filtering', {}).get('potential_building_percentage', 0)
                last_building = last_year.get('vegetation_filtering', {}).get('potential_building_percentage', 0)
                
                changes = {
                    'vegetation_change_percent': round(last_veg - first_veg, 2),
                    'building_area_change_percent': round(last_building - first_building, 2),
                    'urbanization_trend': self._assess_urbanization_trend(
                        first_veg, last_veg, first_building, last_building
                    ),
                    'years_compared': f"{years[0]} to {years[-1]}"
                }
            
            return changes
            
        except:
            return {"error": "Unable to analyze cross-year changes"}
    
    def _assess_urbanization_trend(self, first_veg: float, last_veg: float, 
                                 first_building: float, last_building: float) -> str:
        """Assess urbanization trend based on vegetation and building changes"""
        veg_change = last_veg - first_veg
        building_change = last_building - first_building
        
        if building_change > 2 and veg_change < -1:
            return "Rapid urbanization detected"
        elif building_change > 1 and veg_change < 0:
            return "Moderate urbanization"
        elif building_change > 0:
            return "Slow urban growth"
        elif building_change < -1:
            return "Urban decline or redevelopment"
        else:
            return "Stable urban pattern"
    
    def _generate_detection_recommendations(self, analysis_results: Dict) -> List[str]:
        """Generate building detection recommendations based on multi-temporal analysis"""
        recommendations = []
        
        try:
            # Get latest year data
            years = list(analysis_results.get('multi_temporal_analysis', {}).keys())
            if not years:
                return ["No analysis data available for recommendations"]
            
            latest_year = max(years)
            latest_data = analysis_results['multi_temporal_analysis'][latest_year]
            
            # Vegetation filtering effectiveness
            veg_filter = latest_data.get('vegetation_filtering', {})
            veg_percent = veg_filter.get('vegetation_percentage', 0)
            
            if veg_percent > 50:
                recommendations.append("High vegetation area - seasonal NDVI filtering highly recommended")
            elif veg_percent > 30:
                recommendations.append("Moderate vegetation - apply seasonal filtering for better accuracy")
            
            # Temporal stability
            stability = latest_data.get('temporal_stability', {})
            stability_metrics = stability.get('stability_interpretation', {})
            
            if stability_metrics.get('building_likelihood') == 'High':
                recommendations.append("High temporal stability - excellent for building detection")
            elif stability_metrics.get('building_likelihood') == 'Medium':
                recommendations.append("Moderate stability - use ensemble methods for better classification")
            
            # Cross-year analysis
            cross_year = analysis_results.get('cross_year_analysis', {})
            urbanization = cross_year.get('urbanization_trend', '')
            
            if 'rapid' in urbanization.lower():
                recommendations.append("Rapid urbanization detected - frequent updates recommended")
            elif 'stable' in urbanization.lower():
                recommendations.append("Stable urban pattern - standard detection methods sufficient")
            
            # General recommendations
            recommendations.extend([
                "Use confidence threshold >75% for Google Open Buildings",
                "Apply multi-temporal composites for cloud-free analysis",
                "Combine with settlement classification for waste estimation"
            ])
            
            return recommendations
            
        except:
            return ["Unable to generate specific recommendations - use standard detection methods"]

    # ==================== WORLDPOP POPULATION DATA INTEGRATION ====================
    
    def connect_worldpop_datasets(self, country_code: str = 'ZMB') -> Dict:
        """
        Connect to WorldPop datasets and retrieve available data for Zambia
        
        Args:
            country_code: ISO3 country code (default: ZMB for Zambia)
            
        Returns:
            Dict: Available WorldPop datasets and metadata
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Load WorldPop population collection
            worldpop_collection = ee.ImageCollection('WorldPop/GP/100m/pop')
            
            # Filter for Zambia and limit the query for efficiency
            zmb_collection = worldpop_collection.filter(ee.Filter.eq('country', country_code))
            
            # Get collection size first
            collection_size = zmb_collection.size().getInfo()
            
            # Limit to last 10 images to avoid overwhelming queries
            recent_images = zmb_collection.limit(10)
            image_list = recent_images.getInfo()['features']
            
            available_years = []
            for img in image_list:
                props = img['properties']
                if 'year' in props:
                    year = props['year']
                    if year not in available_years:
                        available_years.append(year)
            
            available_years.sort()
            
            # If no years found in limited sample, try common years
            if not available_years:
                # Test for common years manually
                test_years = [2020, 2021, 2019, 2018]
                for year in test_years:
                    test_image = worldpop_collection.filter(ee.Filter.eq('country', country_code)).filter(ee.Filter.eq('year', year)).first()
                    if test_image:
                        test_info = test_image.getInfo()
                        if test_info:
                            available_years.append(year)
                
                available_years.sort()
            
            return {
                'dataset_id': 'WorldPop/GP/100m/pop',
                'country_code': country_code,
                'resolution_meters': 100,
                'available_years': available_years,
                'total_images': collection_size,
                'coordinate_system': 'EPSG:4326 (WGS84)',
                'data_type': 'Population count per 100m cell',
                'methodology': 'Random Forest-based dasymetric mapping',
                'connection_status': 'connected',
                'recommended_years': [2020, 2021],  # Most recent and reliable
                'query_method': 'limited_efficient'
            }
            
        except Exception as e:
            return {"error": f"WorldPop connection failed: {str(e)}"}
    
    def fetch_worldpop_for_lusaka(self, year: int = 2020, buffer_km: float = 0) -> Dict:
        """
        Fetch WorldPop population data for Lusaka region
        
        Args:
            year: Year of WorldPop data to fetch (default: 2020)
            buffer_km: Buffer around Lusaka in kilometers (default: 0)
            
        Returns:
            Dict: WorldPop data and statistics for Lusaka
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Define Lusaka boundary (approximate coordinates)
            lusaka_bounds = ee.Geometry.Rectangle([27.8, -15.8, 28.6, -15.1])
            
            # Apply buffer if specified
            if buffer_km > 0:
                lusaka_bounds = lusaka_bounds.buffer(buffer_km * 1000)  # Convert km to meters
            
            # Load WorldPop data for specified year
            worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filter(ee.Filter.eq('year', year)) \
                .first()
            
            if not worldpop:
                return {"error": f"No WorldPop data available for year {year}"}
            
            # Clip to Lusaka region
            lusaka_population = worldpop.clip(lusaka_bounds)
            
            # Calculate population statistics
            pop_stats = lusaka_population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.stdDev().combine(
                            ee.Reducer.count(), '', True
                        ), '', True
                    ), '', True
                ),
                geometry=lusaka_bounds,
                scale=100,
                maxPixels=1e9
            )
            
            stats_info = pop_stats.getInfo()
            
            # Calculate area
            area_sqkm = lusaka_bounds.area().divide(1000000).getInfo()
            total_population = stats_info.get('population_sum', 0)
            
            return {
                'year': year,
                'region': 'Lusaka',
                'buffer_km': buffer_km,
                'area_sqkm': round(area_sqkm, 2),
                'total_population': round(total_population) if total_population else 0,
                'population_density_per_sqkm': round(total_population / area_sqkm, 2) if total_population and area_sqkm > 0 else 0,
                'statistics': {
                    'mean_population_per_cell': round(stats_info.get('population_mean', 0), 2),
                    'std_population_per_cell': round(stats_info.get('population_stdDev', 0), 2),
                    'total_cells': stats_info.get('population_count', 0)
                },
                'data_source': 'WorldPop/GP/100m/pop',
                'resolution_meters': 100,
                'coordinate_system': 'EPSG:4326'
            }
            
        except Exception as e:
            return {"error": f"Lusaka population data fetch failed: {str(e)}"}
    
    def extract_ghsl_population_for_zone(self, zone: Zone, year: int = 2020) -> Dict:
        """
        Extract GPWv4.11 (Gridded Population of the World Version 4.11) population estimates for a specific zone
        Uses CIESIN/GPWv411/GPW_Population_Count - authoritative global population data at ~1km resolution
        
        Args:
            zone: Zone object with geometry
            year: Year of GPWv4.11 data (default 2020, available: 2000, 2005, 2010, 2015, 2020)
            
        Returns:
            Dict: Robust population statistics for the zone
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Convert zone geometry to Earth Engine geometry
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Map year to available GPWv4.11 years (use closest available)
            available_years = [2000, 2005, 2010, 2015, 2020]
            if year not in available_years:
                # Find closest available year
                year = min(available_years, key=lambda x: abs(x - year))
            
            # Load GPWv4.11 Population Count data - authoritative global population estimates
            gpw_collection = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Count")
            
            # Filter to the specific year
            gpw_population = gpw_collection.filter(ee.Filter.date(f'{year}-01-01', f'{year}-12-31')).first()
            
            # Select the population count band
            population_band = gpw_population.select('population_count')
            
            # Mask to only consider populated areas (population > 0)
            population_band = population_band.updateMask(population_band.gt(0))
            
            # Extract population for zone
            zone_population = population_band.clip(ee_geometry)
            
            # Calculate comprehensive statistics
            pop_stats = zone_population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.stdDev().combine(
                            ee.Reducer.min().combine(
                                ee.Reducer.max().combine(
                                    ee.Reducer.count(), '', True
                                ), '', True
                            ), '', True
                        ), '', True
                    ), '', True
                ),
                geometry=ee_geometry,
                scale=927.67,  # GPWv4.11 has ~1km (30 arc-second) resolution
                maxPixels=1e9
            )
            
            stats_info = pop_stats.getInfo()
            
            # Calculate zone area in square kilometers
            zone_area_sqm = ee_geometry.area().getInfo()
            zone_area_sqkm = zone_area_sqm / 1000000
            
            # Extract population statistics
            total_population = stats_info.get('population_count_sum', 0)
            mean_density = stats_info.get('population_count_mean', 0)
            std_density = stats_info.get('population_count_stdDev', 0)
            min_density = stats_info.get('population_count_min', 0)
            max_density = stats_info.get('population_count_max', 0)
            pixel_count = stats_info.get('population_count_count', 0)
            
            # Calculate enhanced metrics
            population_density_per_sqkm = total_population / zone_area_sqkm if zone_area_sqkm > 0 else 0
            populated_area_sqkm = (pixel_count * 927.67 * 927.67) / 1000000  # Convert pixels to sq km (GPWv4.11 resolution)
            populated_coverage_percent = (populated_area_sqkm / zone_area_sqkm * 100) if zone_area_sqkm > 0 else 0
            
            # Calculate confidence metrics
            population_uniformity = 1 - (std_density / mean_density) if mean_density > 0 else 0
            confidence_score = min(1.0, population_uniformity + (pixel_count / 100) * 0.1)
            
            # Determine settlement density category
            if population_density_per_sqkm > 15000:
                density_category = 'Very High Density Urban'
            elif population_density_per_sqkm > 8000:
                density_category = 'High Density Urban'
            elif population_density_per_sqkm > 4000:
                density_category = 'Medium Density Urban'
            elif population_density_per_sqkm > 1000:
                density_category = 'Low Density Urban'
            elif population_density_per_sqkm > 200:
                density_category = 'Peri-Urban'
            else:
                density_category = 'Rural'
            
            # Calculate household estimates (average 4.5 people per household in Lusaka)
            household_count = int(total_population / 4.5) if total_population > 0 else 0
            
            return {
                'data_source': 'CIESIN_GPWv411_Population_Count',
                'year': year,
                'total_population': int(total_population),
                'population_density_per_sqkm': round(population_density_per_sqkm, 2),
                'populated_area_sqkm': round(populated_area_sqkm, 4),
                'populated_coverage_percent': round(populated_coverage_percent, 2),
                'household_count': household_count,
                'zone_area_sqkm': round(zone_area_sqkm, 4),
                'density_category': density_category,
                'population_statistics': {
                    'mean_density_per_pixel': round(mean_density, 2),
                    'std_density': round(std_density, 2),
                    'min_density': round(min_density, 2),
                    'max_density': round(max_density, 2),
                    'populated_pixels': int(pixel_count),
                    'population_uniformity': round(population_uniformity, 3)
                },
                'confidence_assessment': {
                    'confidence_score': round(confidence_score, 3),
                    'data_quality': 'high' if confidence_score > 0.7 else 'medium' if confidence_score > 0.4 else 'low',
                    'accuracy_note': 'GHSL provides high accuracy for urban areas with 100m resolution'
                },
                'waste_generation_inputs': {
                    'households': household_count,
                    'population': int(total_population),
                    'density_category': density_category,
                    'urban_classification': 'urban' if population_density_per_sqkm > 1000 else 'peri_urban'
                }
            }
            
        except Exception as e:
            return {"error": f"GHSL population extraction failed: {str(e)}"}
    
    def extract_population_for_zone(self, zone: Zone, year: int = 2020) -> Dict:
        """
        Extract WorldPop population estimates for a specific zone
        
        Args:
            zone: Zone object with geometry
            year: Year of WorldPop data (default: 2020)
            
        Returns:
            Dict: Population statistics for the zone
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Convert zone geometry to Earth Engine geometry
            ee_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Load WorldPop data - filter for Zambia (ZMB) and specified year
            worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filter(ee.Filter.eq('year', year)) \
                .filter(ee.Filter.eq('country', 'ZMB')) \
                .first()
            
            if not worldpop:
                return {"error": f"No WorldPop data available for year {year}"}
            
            # Extract population for zone
            zone_population = worldpop.clip(ee_geometry)
            
            # Calculate statistics
            pop_stats = zone_population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean().combine(
                        ee.Reducer.stdDev().combine(
                            ee.Reducer.min().combine(
                                ee.Reducer.max(), '', True
                            ), '', True
                        ), '', True
                    ), '', True
                ),
                geometry=ee_geometry,
                scale=100,
                maxPixels=1e9
            )
            
            stats_info = pop_stats.getInfo()
            
            # Calculate zone area
            area_sqm = ee_geometry.area().getInfo()
            area_sqkm = area_sqm / 1000000
            total_population = stats_info.get('population_sum', 0)
            
            # Cache result for zone
            cache_key = f"worldpop_{zone.id}_{year}"
            self.cache[cache_key] = {
                'population': total_population,
                'area_sqkm': area_sqkm,
                'timestamp': time.time()
            }
            
            return {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'year': year,
                'area_sqkm': round(area_sqkm, 4),
                'total_population': round(total_population) if total_population is not None else 0,
                'population_density_per_sqkm': round(total_population / area_sqkm, 2) if total_population is not None and area_sqkm > 0 else 0,
                'population_density_per_hectare': round(total_population / (area_sqkm * 100), 2) if total_population is not None and area_sqkm > 0 else 0,
                'statistics': {
                    'mean_per_cell': round(stats_info.get('population_mean', 0) or 0, 2),
                    'std_per_cell': round(stats_info.get('population_stdDev', 0) or 0, 2),
                    'min_per_cell': round(stats_info.get('population_min', 0) or 0, 2),
                    'max_per_cell': round(stats_info.get('population_max', 0) or 0, 2),
                    'total_cells': stats_info.get('population_count', 0) or 0
                },
                'data_source': 'WorldPop/GP/100m/pop',
                'extraction_date': time.time(),
                'cached': True
            }
            
        except Exception as e:
            return {"error": f"Zone population extraction failed: {str(e)}"}
    
    def calculate_population_density_worldpop(self, zones: List[Zone], year: int = 2020) -> Dict:
        """
        Calculate population density for multiple zones using WorldPop data
        
        Args:
            zones: List of zone objects
            year: Year of WorldPop data (default: 2020)
            
        Returns:
            Dict: Population density analysis for all zones
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            zone_results = []
            total_population = 0
            total_area_sqkm = 0
            
            # Load WorldPop data once
            worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filter(ee.Filter.eq('year', year)) \
                .first()
            
            if not worldpop:
                return {"error": f"No WorldPop data available for year {year}"}
            
            # Process each zone
            for zone in zones:
                # Check cache first
                cache_key = f"worldpop_{zone.id}_{year}"
                if cache_key in self.cache:
                    cached_data = self.cache[cache_key]
                    zone_pop = cached_data['population']
                    zone_area = cached_data['area_sqkm']
                else:
                    # Extract fresh data
                    zone_data = self.extract_population_for_zone(zone, year)
                    if zone_data.get('error'):
                        continue
                    zone_pop = zone_data['total_population']
                    zone_area = zone_data['area_sqkm']
                
                zone_density = zone_pop / zone_area if zone_area > 0 else 0
                
                zone_results.append({
                    'zone_id': zone.id,
                    'zone_name': zone.name,
                    'population': zone_pop,
                    'area_sqkm': zone_area,
                    'density_per_sqkm': round(zone_density, 2),
                    'density_category': self._categorize_population_density(zone_density)
                })
                
                total_population += zone_pop
                total_area_sqkm += zone_area
            
            # Calculate overall statistics
            overall_density = total_population / total_area_sqkm if total_area_sqkm > 0 else 0
            densities = [z['density_per_sqkm'] for z in zone_results]
            
            return {
                'year': year,
                'zones_analyzed': len(zone_results),
                'total_population': round(total_population),
                'total_area_sqkm': round(total_area_sqkm, 2),
                'overall_density_per_sqkm': round(overall_density, 2),
                'density_statistics': {
                    'mean_density': round(sum(densities) / len(densities), 2) if densities else 0,
                    'min_density': round(min(densities), 2) if densities else 0,
                    'max_density': round(max(densities), 2) if densities else 0
                },
                'zone_results': zone_results,
                'data_source': 'WorldPop/GP/100m/pop'
            }
            
        except Exception as e:
            return {"error": f"Population density calculation failed: {str(e)}"}
    
    def validate_building_population_with_worldpop(self, zone: Zone, building_estimate: Dict, year: int = 2020) -> Dict:
        """
        Validate building-based population estimates against WorldPop data
        
        Args:
            zone: Zone object
            building_estimate: Building-based population estimate
            year: WorldPop data year for comparison
            
        Returns:
            Dict: Validation results and accuracy metrics
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get WorldPop population for zone
            worldpop_data = self.extract_population_for_zone(zone, year)
            
            if worldpop_data.get('error'):
                return worldpop_data
            
            worldpop_population = worldpop_data['total_population']
            building_population = building_estimate.get('estimated_population', 0)
            
            # Calculate validation metrics
            if worldpop_population > 0:
                absolute_error = abs(building_population - worldpop_population)
                percentage_error = (absolute_error / worldpop_population) * 100
                accuracy = max(0, 100 - percentage_error)
                
                # Determine agreement level
                if percentage_error <= 10:
                    agreement = "Excellent"
                elif percentage_error <= 20:
                    agreement = "Good"
                elif percentage_error <= 35:
                    agreement = "Moderate"
                else:
                    agreement = "Poor"
            else:
                absolute_error = building_population
                percentage_error = 100 if building_population > 0 else 0
                accuracy = 0
                agreement = "Unable to validate (WorldPop shows 0 population)"
            
            return {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'validation_year': year,
                'worldpop_population': worldpop_population,
                'building_estimate_population': building_population,
                'absolute_error': round(absolute_error),
                'percentage_error': round(percentage_error, 2),
                'accuracy_percent': round(accuracy, 2),
                'agreement_level': agreement,
                'worldpop_density_per_sqkm': worldpop_data.get('population_density_per_sqkm', 0),
                'building_method': building_estimate.get('calculation_method', 'Unknown'),
                'validation_notes': self._generate_validation_notes(
                    percentage_error, agreement, worldpop_population, building_population
                ),
                'recommended_adjustments': self._recommend_population_adjustments(
                    percentage_error, building_estimate, worldpop_data
                )
            }
            
        except Exception as e:
            return {"error": f"Population validation failed: {str(e)}"}
    
    def create_worldpop_cache_system(self, zones: List[Zone], years: List[int] = [2020, 2021]) -> Dict:
        """
        Create optimized caching system for WorldPop data queries
        
        Args:
            zones: List of zones to cache data for
            years: Years of WorldPop data to cache
            
        Returns:
            Dict: Caching operation results
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            cache_results = {
                'cached_zones': 0,
                'cached_years': years,
                'cache_size_mb': 0,
                'operation_time_seconds': 0,
                'errors': []
            }
            
            start_time = time.time()
            
            # Pre-load WorldPop images for all years
            worldpop_images = {}
            for year in years:
                worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                    .filter(ee.Filter.eq('year', year)) \
                    .first()
                if worldpop:
                    worldpop_images[year] = worldpop
            
            # Cache population data for each zone and year
            for zone in zones:
                zone_cached = True
                for year in years:
                    if year not in worldpop_images:
                        cache_results['errors'].append(f"No data for year {year}")
                        continue
                    
                    cache_key = f"worldpop_{zone.id}_{year}"
                    
                    # Skip if already cached and recent
                    if cache_key in self.cache:
                        cached_time = self.cache[cache_key].get('timestamp', 0)
                        if time.time() - cached_time < 3600:  # 1 hour cache validity
                            continue
                    
                    try:
                        # Extract and cache population data
                        zone_data = self.extract_population_for_zone(zone, year)
                        if not zone_data.get('error'):
                            self.cache[cache_key] = {
                                'population': zone_data['total_population'],
                                'area_sqkm': zone_data['area_sqkm'],
                                'density': zone_data['population_density_per_sqkm'],
                                'statistics': zone_data['statistics'],
                                'timestamp': time.time()
                            }
                        else:
                            zone_cached = False
                            cache_results['errors'].append(f"Zone {zone.id} year {year}: {zone_data['error']}")
                    
                    except Exception as e:
                        zone_cached = False
                        cache_results['errors'].append(f"Zone {zone.id} year {year}: {str(e)}")
                
                if zone_cached:
                    cache_results['cached_zones'] += 1
            
            # Calculate cache size estimate
            cache_results['cache_size_mb'] = round(len(self.cache) * 0.001, 2)  # Rough estimate
            cache_results['operation_time_seconds'] = round(time.time() - start_time, 2)
            
            return cache_results
            
        except Exception as e:
            return {"error": f"Cache system creation failed: {str(e)}"}
    
    def get_cached_worldpop_data(self, zone_id: int, year: int = 2020) -> Dict:
        """
        Retrieve cached WorldPop data for a zone
        
        Args:
            zone_id: ID of the zone
            year: Year of data (default: 2020)
            
        Returns:
            Dict: Cached population data or None if not cached
        """
        cache_key = f"worldpop_{zone_id}_{year}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_age_hours = (time.time() - cached_data.get('timestamp', 0)) / 3600
            
            return {
                'zone_id': zone_id,
                'year': year,
                'population': cached_data.get('population', 0),
                'area_sqkm': cached_data.get('area_sqkm', 0),
                'density_per_sqkm': cached_data.get('density', 0),
                'statistics': cached_data.get('statistics', {}),
                'cached': True,
                'cache_age_hours': round(cache_age_hours, 2)
            }
        else:
            return {"error": f"No cached data for zone {zone_id}, year {year}"}
    
    def _categorize_population_density(self, density_per_sqkm: float) -> str:
        """Categorize population density for Lusaka context"""
        if density_per_sqkm < 500:
            return "Very Low Density (Rural/Peri-urban)"
        elif density_per_sqkm < 2000:
            return "Low Density (Suburban)"
        elif density_per_sqkm < 5000:
            return "Medium Density (Urban)"
        elif density_per_sqkm < 10000:
            return "High Density (Dense Urban)"
        else:
            return "Very High Density (Informal Settlements)"
    
    def _generate_validation_notes(self, percentage_error: float, agreement: str, 
                                 worldpop_pop: float, building_pop: float) -> List[str]:
        """Generate validation notes based on comparison results"""
        notes = []
        
        if agreement == "Excellent":
            notes.append("Building-based estimate closely matches WorldPop data")
        elif agreement == "Good":
            notes.append("Building-based estimate shows good agreement with WorldPop")
        elif agreement == "Moderate":
            notes.append("Some discrepancy between methods - consider refinement")
        else:
            notes.append("Significant discrepancy - investigate methodological differences")
        
        if building_pop > worldpop_pop * 1.5:
            notes.append("Building method may be overestimating - check density factors")
        elif building_pop < worldpop_pop * 0.5:
            notes.append("Building method may be underestimating - check coverage")
        
        if worldpop_pop < 100:
            notes.append("Low WorldPop population may indicate rural/sparse area")
        
        return notes
    
    def _recommend_population_adjustments(self, percentage_error: float, 
                                        building_estimate: Dict, worldpop_data: Dict) -> List[str]:
        """Recommend adjustments to building-based population estimation"""
        recommendations = []
        
        if percentage_error > 50:
            recommendations.append("Consider recalibrating density factors using WorldPop as reference")
        elif percentage_error > 25:
            recommendations.append("Fine-tune settlement classification or occupancy rates")
        
        building_method = building_estimate.get('calculation_method', '')
        if 'formal' in building_method.lower() and percentage_error > 20:
            recommendations.append("Review formal settlement density assumptions")
        elif 'informal' in building_method.lower() and percentage_error > 30:
            recommendations.append("Adjust informal settlement density factors")
        
        worldpop_density = worldpop_data.get('population_density_per_sqkm', 0)
        if worldpop_density > 8000:
            recommendations.append("High density area - consider multi-story building factors")
        elif worldpop_density < 1000:
            recommendations.append("Low density area - verify building detection completeness")
        
        if not recommendations:
            recommendations.append("Current estimation method appears well-calibrated")
        
        return recommendations

    def _apply_urban_density_corrections(self, gpw_population: float, density_per_sqkm: float, density_category: str) -> float:
        """
        Apply urban density correction factors for Lusaka high-density areas
        
        Args:
            gpw_population: Raw GPWv4.11 population estimate
            density_per_sqkm: Population density per square kilometer
            density_category: Density category classification
            
        Returns:
            float: Corrected population estimate
        """
        # Lusaka-specific urban correction factors based on local research
        correction_factors = {
            'Very High Density (>15000/km²)': 1.4,  # GPWv4.11 often underestimates informal settlements
            'High Density (8000-15000/km²)': 1.3,   # Moderate underestimation correction
            'Medium-High Density (5000-8000/km²)': 1.2,  # Light correction for mixed areas
            'Medium Density (2000-5000/km²)': 1.1,   # Minimal correction
            'Low-Medium Density (1000-2000/km²)': 1.05,  # Very light correction
            'Low Density (<1000/km²)': 1.0          # No correction needed
        }
        
        correction_factor = correction_factors.get(density_category, 1.1)
        
        # Additional context-aware corrections for Lusaka
        if density_per_sqkm > 12000:
            # Very high density areas (likely informal settlements) - apply higher correction
            correction_factor = max(correction_factor, 1.5)
        elif density_per_sqkm > 8000:
            # High density mixed areas - moderate correction
            correction_factor = max(correction_factor, 1.3)
        
        corrected_population = gpw_population * correction_factor
        
        print(f"Applied urban correction: {gpw_population:.0f} -> {corrected_population:.0f} (factor: {correction_factor})")
        
        return corrected_population

    def _get_worldpop_validation(self, geometry: dict) -> dict:
        """
        Get WorldPop data for spatial validation (not for total population)
        
        Args:
            geometry: GeoJSON geometry
            
        Returns:
            dict: WorldPop validation data
        """
        try:
            ee_geometry = ee.Geometry(geometry)
            
            # Get WorldPop 2020 data for spatial distribution validation
            worldpop = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filter(ee.Filter.eq('country', 'ZMB')) \
                .filter(ee.Filter.eq('year', 2020)) \
                .first()
            
            # Calculate spatial statistics
            pop_stats = worldpop.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.max(),
                    sharedInputs=True
                ).combine(
                    reducer2=ee.Reducer.stdDev(),
                    sharedInputs=True
                ),
                geometry=ee_geometry,
                scale=100,
                maxPixels=1e9
            )
            
            results = pop_stats.getInfo()
            
            return {
                'mean_density': results.get('population_mean', 0),
                'max_density': results.get('population_max', 0),
                'std_deviation': results.get('population_stdDev', 0),
                'spatial_variability': 'high' if results.get('population_stdDev', 0) > 50 else 'low',
                'data_source': 'WorldPop 2020 (validation only)'
            }
            
        except Exception as e:
            print(f"WorldPop validation failed: {e}")
            return {
                'error': str(e),
                'data_source': 'WorldPop validation unavailable'
            }

    def _calculate_population_confidence(self, corrected_population: float, density_per_sqkm: float, 
                                       density_category: str, worldpop_validation: dict) -> float:
        """
        Calculate confidence level for population estimate
        
        Args:
            corrected_population: Corrected population estimate
            density_per_sqkm: Population density per square kilometer
            density_category: Density category classification
            worldpop_validation: WorldPop validation data
            
        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        base_confidence = 0.85  # High base confidence for GPWv4.11
        
        # Adjust confidence based on density category
        density_confidence_adjustments = {
            'Very High Density (>15000/km²)': -0.05,  # Slightly lower for complex informal areas
            'High Density (8000-15000/km²)': 0.0,     # Standard confidence
            'Medium-High Density (5000-8000/km²)': 0.02,  # Slightly higher for well-mapped areas
            'Medium Density (2000-5000/km²)': 0.03,   # Higher for suburban areas
            'Low-Medium Density (1000-2000/km²)': 0.02,  # Good for rural-urban transition
            'Low Density (<1000/km²)': -0.02          # Lower for sparse rural areas
        }
        
        confidence = base_confidence + density_confidence_adjustments.get(density_category, 0.0)
        
        # Adjust based on WorldPop validation quality
        if not worldpop_validation.get('error'):
            spatial_var = worldpop_validation.get('spatial_variability', 'unknown')
            if spatial_var == 'low':
                confidence += 0.03  # More uniform areas are easier to estimate
            elif spatial_var == 'high':
                confidence -= 0.02  # High variability adds uncertainty
        else:
            confidence -= 0.05  # Reduce confidence if validation unavailable
        
        # Ensure confidence stays within bounds
        confidence = max(0.65, min(0.95, confidence))
        
        return round(confidence, 2)

    def get_population_estimate_with_user_classification(self, zone_or_geojson, user_classification: dict):
        """
        Enhanced population estimation that prioritizes user's area classification
        
        Args:
            zone_or_geojson: Zone object or GeoJSON geometry
            user_classification: Dict containing user's area settings like settlement_density, socioeconomic_level
        
        Returns:
            Dict: Population estimate with user classification prioritized
        """
        if not self.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get basic population estimate using satellite data
            base_result = self.get_population_estimate(zone_or_geojson)
            
            if base_result.get('error'):
                return base_result
            
            # Extract user's area classification
            settlement_density = user_classification.get('settlement_density', 'medium_density')
            socioeconomic_level = user_classification.get('socioeconomic_level', 'middle_income')
            
            # Map user's settlement density to our correction categories
            user_density_mapping = {
                'very_low_density': 'Low Density (<1000/km²)',
                'low_density': 'Low-Medium Density (1000-2000/km²)', 
                'medium_density': 'Medium Density (2000-5000/km²)',
                'high_density': 'Medium-High Density (5000-8000/km²)',
                'very_high_density': 'Very High Density (>15000/km²)'
            }
            
            # Use user's classification as the primary density category
            user_density_category = user_density_mapping.get(settlement_density, 'Medium Density (2000-5000/km²)')
            
            # Get raw population from base result
            raw_population = base_result.get('raw_gpw_population', base_result.get('estimated_population', 0))
            if not raw_population:
                raw_population = base_result.get('estimated_population', 0)
            
            # Apply user-based corrections instead of satellite-derived ones
            corrected_population = self._apply_user_density_corrections(
                raw_population, user_density_category, socioeconomic_level
            )
            
            # Calculate confidence based on user input quality
            confidence = self._calculate_user_classification_confidence(
                settlement_density, socioeconomic_level
            )
            
            return {
                'estimated_population': int(corrected_population),
                'population_density_per_sqkm': base_result.get('population_density_per_sqkm', 0),
                'density_category': user_density_category,
                'data_source': f'User Classification: {settlement_density.replace("_", " ").title()} + Satellite Data',
                'confidence': confidence,
                'raw_satellite_population': raw_population,
                'user_correction_factor': round(corrected_population / raw_population, 2) if raw_population > 0 else 1.0,
                'user_classification': {
                    'settlement_density': settlement_density,
                    'socioeconomic_level': socioeconomic_level,
                    'source': 'user_input'
                },
                'validation_data': base_result.get('validation_data', {})
            }
            
        except Exception as e:
            return {"error": f"User classification population estimation failed: {str(e)}"}

    def _apply_user_density_corrections(self, raw_population: float, user_density_category: str, socioeconomic_level: str) -> float:
        """
        Apply corrections based on user's area classification
        
        Args:
            raw_population: Raw satellite population estimate
            user_density_category: User's density category
            socioeconomic_level: User's socioeconomic level
            
        Returns:
            float: Corrected population estimate
        """
        # Base correction factors based on user's density classification
        base_corrections = {
            'Very High Density (>15000/km²)': 1.6,  # Higher correction for user-identified high density
            'Medium-High Density (5000-8000/km²)': 1.4,  # User knows their area better than satellite
            'Medium Density (2000-5000/km²)': 1.2,
            'Low-Medium Density (1000-2000/km²)': 1.1,
            'Low Density (<1000/km²)': 1.0
        }
        
        base_factor = base_corrections.get(user_density_category, 1.2)
        
        # Socioeconomic adjustments - higher income areas tend to have better data quality
        socio_adjustments = {
            'low_income': 1.1,     # Higher correction for underrepresented areas
            'middle_income': 1.0,   # Standard
            'high_income': 0.95     # Slight reduction as these areas are often well-mapped
        }
        
        socio_factor = socio_adjustments.get(socioeconomic_level, 1.0)
        
        # Combined correction
        total_correction = base_factor * socio_factor
        
        corrected_population = raw_population * total_correction
        
        print(f"User-based correction: {raw_population:.0f} -> {corrected_population:.0f} (density: {base_factor}, socio: {socio_factor})")
        
        return corrected_population

    def _calculate_user_classification_confidence(self, settlement_density: str, socioeconomic_level: str) -> float:
        """
        Calculate confidence based on user classification quality
        
        Args:
            settlement_density: User's settlement density classification
            socioeconomic_level: User's socioeconomic level classification
            
        Returns:
            float: Confidence level
        """
        # High base confidence when user provides classification
        base_confidence = 0.92
        
        # User input is generally more reliable than satellite-only estimates
        # because users have local knowledge
        
        # Adjust based on density clarity
        density_confidence = {
            'very_high_density': 0.95,  # Users know when areas are very dense
            'high_density': 0.93,
            'medium_density': 0.90,     # Most common, well understood
            'low_density': 0.92,
            'very_low_density': 0.88    # Sometimes hard to distinguish from medium
        }
        
        confidence = density_confidence.get(settlement_density, base_confidence)
        
        # Slightly higher confidence when socioeconomic info is provided
        if socioeconomic_level and socioeconomic_level != 'unknown':
            confidence += 0.02
        
        return round(min(0.98, confidence), 2)  # Cap at 98% confidence
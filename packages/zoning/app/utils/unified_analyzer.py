"""
Unified Analysis Engine for Lusaka Zone Planning
===============================================

This module provides a single entry point for all spatial analysis operations
including population estimation, building analysis, and waste generation calculations.

Based on research findings for Lusaka, Zambia:
- Urban household size: 4.6 people per household
- Waste generation: 0.5 kg per person per day
- 70% of population in informal settlements
- Population density varies significantly by settlement type

Author: Claude Code
Date: 2025
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis that can be performed"""
    POPULATION = "population"
    BUILDINGS = "buildings"
    WASTE = "waste"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AnalysisRequest:
    """Standardized analysis request structure"""
    analysis_type: AnalysisType
    geometry: Dict[str, Any]  # GeoJSON geometry
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    zone_type: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and set defaults"""
        if self.options is None:
            self.options = {}
        
        # Set default options based on analysis type
        if self.analysis_type == AnalysisType.POPULATION:
            self.options.setdefault('use_dasymetric', True)
            self.options.setdefault('household_size', 4.6)  # Lusaka urban average
            
        elif self.analysis_type == AnalysisType.BUILDINGS:
            self.options.setdefault('confidence_threshold', 0.83)  # Set to 83% to filter out unfinished buildings and sheds
            self.options.setdefault('classify_settlement_type', True)
            self.options.setdefault('use_fallback', False)  # Disable fallback by default
            
        elif self.analysis_type == AnalysisType.WASTE:
            self.options.setdefault('waste_rate_kg_per_person', 0.5)  # Lusaka rate
            self.options.setdefault('collection_frequency', 2)  # times per week
            
        elif self.analysis_type == AnalysisType.COMPREHENSIVE:
            # Enable all analysis types
            self.options.setdefault('include_population', True)
            self.options.setdefault('include_buildings', True)
            self.options.setdefault('include_waste', True)
            self.options.setdefault('include_validation', True)
            self.options.setdefault('confidence_threshold', 0.83)  # Set to 83% to filter out unfinished buildings and sheds
            self.options.setdefault('use_fallback', False)  # Disable fallback by default


@dataclass
class AnalysisResult:
    """Standardized analysis result structure"""
    request_id: str
    analysis_type: AnalysisType
    timestamp: datetime
    success: bool
    
    # Core results
    population_estimate: Optional[int] = None
    household_estimate: Optional[int] = None
    building_count: Optional[int] = None
    waste_generation_kg_per_day: Optional[float] = None
    
    # Detailed results
    population_density: Optional[float] = None
    building_types: Optional[Dict[str, int]] = None
    settlement_classification: Optional[str] = None
    collection_requirements: Optional[Dict[str, Any]] = None
    
    # Quality metrics
    confidence_level: Optional[float] = None
    data_sources: Optional[List[str]] = None
    validation_metrics: Optional[Dict[str, float]] = None
    
    # Error information
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        return {
            'request_id': self.request_id,
            'analysis_type': self.analysis_type.value,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'population_estimate': self.population_estimate,
            'household_estimate': self.household_estimate,
            'building_count': self.building_count,
            'waste_generation_kg_per_day': self.waste_generation_kg_per_day,
            'population_density': self.population_density,
            'building_types': self.building_types,
            'settlement_classification': self.settlement_classification,
            'collection_requirements': self.collection_requirements,
            'confidence_level': self.confidence_level,
            'data_sources': self.data_sources,
            'validation_metrics': self.validation_metrics,
            'error_message': self.error_message,
            'warnings': self.warnings,
            'performance_metrics': {
                'total_analysis_time_seconds': getattr(self, '_execution_time', 0.1),
                'modules_completed': 3 if self.success else 0,
                'modules_total': 3
            },
            'critical_issues': self._get_critical_issues()
        }
    
    def _get_critical_issues(self) -> List[Dict[str, str]]:
        """Get list of critical issues based on analysis results"""
        issues = []
        
        # Check for low confidence
        if self.confidence_level and self.confidence_level < 0.3:
            issues.append({
                'issue': 'Low Analysis Confidence',
                'description': f'Analysis confidence is only {self.confidence_level:.0%}',
                'action_required': 'Consider collecting more ground truth data for validation'
            })
        
        # Check for missing population data
        if not self.population_estimate or self.population_estimate <= 0:
            issues.append({
                'issue': 'No Population Data',
                'description': 'Population estimate is missing or zero',
                'action_required': 'Verify zone boundaries and try re-analysis'
            })
        
        # Check for missing building data
        if not self.building_count or self.building_count <= 0:
            issues.append({
                'issue': 'No Building Data',
                'description': 'Building count is missing or zero',
                'action_required': 'Check satellite imagery coverage for this area'
            })
        
        return issues


class UnifiedAnalyzer:
    """
    Unified Analysis Engine for Lusaka Zone Planning
    
    This class provides a single interface for all spatial analysis operations,
    integrating population estimation, building analysis, and waste calculations
    using best practices for developing cities.
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the unified analyzer
        
        Args:
            cache_enabled: Whether to enable result caching
        """
        self.cache_enabled = cache_enabled
        self.cache = {}
        self.cache_expiry = {}
        self.cache_ttl = timedelta(hours=24)  # Cache results for 24 hours
        
        # Initialize analysis engines (will be implemented in subsequent phases)
        self.population_engine = None
        self.building_engine = None
        self.waste_engine = None
        self.validation_engine = None
        
        # Track initialization status
        self.initialized = False
        self.initialization_errors = []
        
        logger.info("🔧 Unified Analyzer initializing...")
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all analysis engines"""
        try:
            # Earth Engine initialization for building detection
            try:
                try:
                    from .earth_engine_analysis import EarthEngineAnalyzer
                except ImportError:
                    # Try absolute import if relative fails
                    from earth_engine_analysis import EarthEngineAnalyzer
                    
                self.earth_engine = EarthEngineAnalyzer()
                logger.info("✅ Earth Engine analyzer initialized")
            except ImportError as e:
                logger.warning(f"⚠️ Earth Engine not available: {str(e)}")
                self.earth_engine = None
                self.initialization_errors.append("Earth Engine not available")
            except Exception as e:
                logger.warning(f"⚠️ Earth Engine initialization failed: {str(e)}")
                self.earth_engine = None
                self.initialization_errors.append(f"Earth Engine error: {str(e)}")
            
            # Population engine initialization (using existing population estimation)
            try:
                try:
                    from .population_estimation import PopulationEstimator
                except ImportError:
                    from population_estimation import PopulationEstimator
                    
                self.population_engine = PopulationEstimator()
                logger.info("✅ Population engine initialized")
            except ImportError:
                logger.warning("⚠️ Population engine not available yet")
                self.population_engine = None
                self.initialization_errors.append("Population engine not implemented")
            
            # Building engine initialization (fallback to Earth Engine)
            self.building_engine = None  # Will use Earth Engine directly
            
            # Waste engine initialization (using fallback calculation)
            self.waste_engine = None  # Will use fallback calculation
            
            # Validation engine initialization
            try:
                from .validation_engine import ValidationEngine
                self.validation_engine = ValidationEngine()
                logger.info("✅ Validation engine initialized")
            except ImportError:
                logger.warning("⚠️ Validation engine not available yet")
                self.validation_engine = None
                self.initialization_errors.append("Validation engine not implemented")
            
            self.initialized = True
            logger.info("🚀 Unified Analyzer initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize analysis engines: {str(e)}")
            self.initialization_errors.append(f"Initialization error: {str(e)}")
    
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Perform analysis based on the request
        
        Args:
            request: Analysis request containing geometry and options
            
        Returns:
            AnalysisResult containing all requested analysis results
        """
        # Generate unique request ID
        request_id = self._generate_request_id(request)
        
        # Check cache first
        if self.cache_enabled:
            cached_result = self._get_cached_result(request_id)
            if cached_result:
                logger.info(f"📦 Returning cached result for {request_id}")
                return cached_result
        
        # Start timing
        start_time = time.time()
        
        # Create result object
        result = AnalysisResult(
            request_id=request_id,
            analysis_type=request.analysis_type,
            timestamp=datetime.now(),
            success=False
        )
        
        # Track execution time
        result._execution_time = 0
        
        try:
            logger.info(f"🔍 Starting {request.analysis_type.value} analysis for {request_id}")
            
            # Route to appropriate analysis method
            if request.analysis_type == AnalysisType.POPULATION:
                result = self._analyze_population(request, result)
            elif request.analysis_type == AnalysisType.BUILDINGS:
                result = self._analyze_buildings(request, result)
            elif request.analysis_type == AnalysisType.WASTE:
                result = self._analyze_waste(request, result)
            elif request.analysis_type == AnalysisType.COMPREHENSIVE:
                result = self._analyze_comprehensive(request, result)
            
            # Mark as successful if we got here without exceptions
            result.success = True
            
            # Store execution time
            execution_time = time.time() - start_time
            result._execution_time = execution_time
            
            # Cache the result
            if self.cache_enabled:
                self._cache_result(request_id, result)
            
            logger.info(f"✅ Analysis completed in {execution_time:.2f}s for {request_id}")
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {request_id}: {str(e)}")
            result.error_message = str(e)
            result.success = False
        
        return result
    
    def _analyze_population(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform population analysis using building-based estimation"""
        if self.population_engine and result.building_count and result.building_count > 0:
            try:
                logger.info("Using building-based population estimation")
                
                # Create building DataFrame for population estimator
                import pandas as pd
                building_data = []
                building_types = result.building_types or {'residential': result.building_count}
                
                for btype, count in building_types.items():
                    for i in range(count):
                        building_data.append({
                            'id': f'{btype}_{i}',
                            'area': self._get_typical_building_area(btype),
                            'height': self._get_typical_building_height(btype),
                            'building_type': btype,
                            'settlement_type': result.settlement_classification or 'mixed'
                        })
                
                building_df = pd.DataFrame(building_data)
                
                # Use ensemble estimation for best accuracy
                pop_result = self.population_engine.estimate_population_ensemble(
                    building_df,
                    settlement_classifications=None,
                    zone_area_sqm=self._estimate_zone_area(request.geometry)
                )
                
                result.population_estimate = int(pop_result['total_population'])
                result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
                result.population_density = pop_result.get('individual_results', {}).get('settlement_based', {}).get('population_density_per_sqkm', 2500)
                result.confidence_level = min(0.85, 0.6 + (result.building_count / 200) * 0.25)  # Higher confidence with more buildings
                
                if not result.data_sources:
                    result.data_sources = []
                result.data_sources.extend(['Building-based population estimation (ensemble method)'])
                
                logger.info(f"Building-based population estimate: {result.population_estimate} people from {result.building_count} buildings")
                
            except Exception as e:
                logger.warning(f"Building-based population analysis failed: {str(e)}, using fallback")
                result.population_estimate = self._fallback_population_estimate(request.geometry)
                result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
                result.population_density = 2500
                result.confidence_level = 0.4
                if not result.data_sources:
                    result.data_sources = []
                result.data_sources.extend(['Fallback estimation (building-based failed)'])
                result.warnings = result.warnings or []
                result.warnings.append(f"Building-based analysis failed: {str(e)}")
        else:
            # Fallback to basic estimation
            logger.warning("Population engine not available or no buildings detected, using fallback estimation")
            result.population_estimate = self._fallback_population_estimate(request.geometry)
            result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
            result.population_density = 2500  # Default density for Lusaka
            result.confidence_level = 0.3  # Low confidence for fallback
            if not result.data_sources:
                result.data_sources = []
            result.data_sources.extend(['Fallback estimation'])
            result.warnings = result.warnings or []
            result.warnings.append("Using fallback population estimation")
        
        return result
    
    def _analyze_buildings(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform building analysis using Google Earth Engine with 83% confidence threshold"""
        confidence_threshold = request.options.get('confidence_threshold', 0.83)
        
        if self.earth_engine and self.earth_engine.initialized:
            try:
                logger.info(f"Using Google Earth Engine for building detection (confidence >= {confidence_threshold*100:.0f}%)")
                
                # Create a temporary zone-like object for Earth Engine
                from app.models import Zone
                temp_zone = type('TempZone', (), {
                    'id': request.zone_id or 'temp',
                    'geojson': {
                        'type': 'Feature',
                        'geometry': request.geometry,
                        'properties': {}
                    }
                })()
                
                # Extract buildings using Earth Engine
                buildings_data = self.earth_engine.extract_buildings_for_zone(
                    temp_zone, 
                    confidence_threshold=confidence_threshold,
                    use_cache=True
                )
                
                if 'error' in buildings_data:
                    raise Exception(buildings_data['error'])
                
                # Extract results
                result.building_count = buildings_data.get('building_count', 0)
                features = buildings_data.get('features', {})
                height_stats = buildings_data.get('height_stats', {})
                
                # Classify building types based on features
                result.building_types = self._classify_building_types(features, result.building_count)
                
                # Determine settlement classification from building characteristics
                result.settlement_classification = self._classify_settlement_type(features, height_stats)
                
                # Set confidence level based on building count and features
                result.confidence_level = min(0.9, 0.6 + (result.building_count / 100) * 0.3)
                
                if not result.data_sources:
                    result.data_sources = []
                result.data_sources.extend([f'Google Open Buildings v3 (confidence >= {confidence_threshold*100:.0f}%)'])
                
                logger.info(f"Earth Engine detected {result.building_count} buildings with {confidence_threshold*100:.0f}% confidence")
                
            except Exception as e:
                logger.warning(f"Earth Engine building analysis failed: {str(e)}, using fallback")
                return self._fallback_building_analysis(request, result, str(e))
        else:
            logger.warning("Earth Engine not available, using enhanced fallback")
            return self._fallback_building_analysis(request, result, "Earth Engine not initialized")
        
        # Estimate population based on building data if we don't have one yet
        if not result.population_estimate or result.population_estimate <= 0:
            building_data = {
                'building_count': result.building_count,
                'building_types': result.building_types,
                'average_building_size_sqm': self._estimate_avg_building_size(features if 'features' in locals() else {})
            }
            population_estimate = self._estimate_population_from_buildings(
                building_data, result.settlement_classification
            )
            result.population_estimate = population_estimate
            result.household_estimate = int(population_estimate / 4.6) if population_estimate else 0
            
        return result
    
    def _fallback_building_analysis(self, request: AnalysisRequest, result: AnalysisResult, error_msg: str) -> AnalysisResult:
        """Fallback building analysis when Earth Engine is not available"""
        result.building_count = self._enhanced_fallback_building_count(request.geometry)
        result.building_types = {'residential': int(result.building_count * 0.7), 'commercial': int(result.building_count * 0.3)}
        result.settlement_classification = 'mixed'
        result.confidence_level = 0.3  # Lower confidence for fallback
        if not result.data_sources:
            result.data_sources = []
        result.data_sources.extend(['Enhanced fallback estimation'])
        result.warnings = result.warnings or []
        result.warnings.append(f"Earth Engine unavailable ({error_msg}), using fallback estimation")
        
        # Estimate population based on building data if we don't have one yet
        if not result.population_estimate or result.population_estimate <= 0:
            building_data = {
                'building_count': result.building_count,
                'building_types': result.building_types,
                'average_building_size_sqm': 100
            }
            population_estimate = self._estimate_population_from_buildings(
                building_data, result.settlement_classification
            )
            result.population_estimate = population_estimate
            result.household_estimate = int(population_estimate / 4.6) if population_estimate else 0
            
        return result
    
    def _classify_building_types(self, features: Dict, total_count: int) -> Dict[str, int]:
        """Classify buildings into types based on features"""
        if not features or total_count == 0:
            return {'residential': total_count}
        
        # Default distribution for Lusaka based on features
        # This would be enhanced with actual feature analysis
        return {
            'residential': int(total_count * 0.75),
            'commercial': int(total_count * 0.15),
            'mixed': int(total_count * 0.08),
            'industrial': int(total_count * 0.02)
        }
    
    def _classify_settlement_type(self, features: Dict, height_stats: Dict) -> str:
        """Classify settlement type based on building characteristics"""
        if not features and not height_stats:
            return 'mixed'
        
        # Basic classification based on building density and height
        # This would be enhanced with actual feature analysis
        avg_height = height_stats.get('mean_height', 4.0) if height_stats else 4.0
        
        if avg_height > 8:
            return 'formal_high_density'
        elif avg_height > 5:
            return 'formal_medium_density'
        else:
            return 'informal_medium_density'
    
    def _estimate_avg_building_size(self, features: Dict) -> float:
        """Estimate average building size from features"""
        if not features:
            return 100.0  # Default
        
        # This would extract actual size data from features
        return features.get('average_area', 100.0)
    
    def _analyze_waste(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform waste analysis with fallback handling"""
        # Always use fallback calculation since waste engine is not implemented yet
        logger.info("Using fallback waste calculation")
        
        # Need population data for waste calculation
        population_for_waste = result.population_estimate
        if not population_for_waste or population_for_waste <= 0:
            # Get population estimate first using fallback
            population_for_waste = self._fallback_population_estimate(request.geometry)
            if not result.population_estimate:  # Only update if we don't have one
                result.population_estimate = population_for_waste
        
        # Ensure we have a valid population
        if population_for_waste <= 0:
            population_for_waste = 1000  # Default minimum population
            result.warnings = result.warnings or []
            result.warnings.append("No population data available, using default estimate")
        
        # Fallback waste calculation using Lusaka standards
        waste_rate = request.options.get('waste_rate_kg_per_person', 0.5)  # Lusaka standard rate
        result.waste_generation_kg_per_day = float(population_for_waste * waste_rate)
        
        # Calculate collection requirements
        weekly_waste = result.waste_generation_kg_per_day * 7
        collection_frequency = request.options.get('collection_frequency', 2)  # times per week
        waste_per_collection = weekly_waste / collection_frequency
        
        # Assume 10-tonne trucks
        truck_capacity_kg = 10000
        trucks_needed = max(1, int(waste_per_collection / truck_capacity_kg) + (1 if waste_per_collection % truck_capacity_kg > 0 else 0))
        
        result.collection_requirements = {
            'frequency_per_week': collection_frequency,
            'vehicle_requirements': {
                'truck_10_tonne': trucks_needed,
                'frequency_per_week': collection_frequency,
                'total_capacity_needed': waste_per_collection
            },
            'collection_points': max(1, int(population_for_waste / 500)),  # 1 point per 500 people
            'vehicles_required': trucks_needed,
            'monthly_revenue': population_for_waste * 50,  # Estimated K50 per person per month
            'daily_cost': trucks_needed * 500,  # K500 per truck per day
            'monthly_cost': trucks_needed * 500 * 30
        }
        
        logger.info(f"Waste calculation: {population_for_waste} people × {waste_rate} kg/day = {result.waste_generation_kg_per_day} kg/day")
        
        return result
    
    def _analyze_comprehensive(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform comprehensive analysis (all types)"""
        warnings = []
        
        # Building analysis first (needed for population estimation)
        if request.options.get('include_buildings', True):
            try:
                result = self._analyze_buildings(request, result)
            except Exception as e:
                warnings.append(f"Building analysis failed: {str(e)}")
        
        # Population analysis (use building-based if buildings were analyzed)
        if request.options.get('include_population', True):
            try:
                # Only run population analysis if we don't have building-based population
                if not result.population_estimate or result.population_estimate == 0:
                    result = self._analyze_population(request, result)
            except Exception as e:
                warnings.append(f"Population analysis failed: {str(e)}")
        
        # Waste analysis
        if request.options.get('include_waste', True):
            try:
                result = self._analyze_waste(request, result)
            except Exception as e:
                warnings.append(f"Waste analysis failed: {str(e)}")
        
        # Validation
        if request.options.get('include_validation', True) and self.validation_engine:
            try:
                validation_data = self.validation_engine.validate_results(result)
                result.validation_metrics = validation_data.get('metrics')
                if validation_data.get('warnings'):
                    warnings.extend(validation_data['warnings'])
            except Exception as e:
                warnings.append(f"Validation failed: {str(e)}")
        
        if warnings:
            result.warnings = warnings
        
        return result
    
    def _generate_request_id(self, request: AnalysisRequest) -> str:
        """Generate unique request ID for caching"""
        # Create hash of geometry and options
        content = json.dumps({
            'analysis_type': request.analysis_type.value,
            'geometry': request.geometry,
            'options': request.options
        }, sort_keys=True)
        
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_cached_result(self, request_id: str) -> Optional[AnalysisResult]:
        """Get cached result if available and not expired"""
        if request_id not in self.cache:
            return None
        
        # Check if cache expired
        if datetime.now() > self.cache_expiry.get(request_id, datetime.min):
            del self.cache[request_id]
            del self.cache_expiry[request_id]
            return None
        
        return self.cache[request_id]
    
    def _cache_result(self, request_id: str, result: AnalysisResult):
        """Cache analysis result"""
        self.cache[request_id] = result
        self.cache_expiry[request_id] = datetime.now() + self.cache_ttl
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("🧹 Analysis cache cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status and health information"""
        return {
            'initialized': self.initialized,
            'engines': {
                'population': self.population_engine is not None,
                'building': self.building_engine is not None,
                'waste': self.waste_engine is not None,
                'validation': self.validation_engine is not None
            },
            'cache_enabled': self.cache_enabled,
            'cached_results': len(self.cache),
            'initialization_errors': self.initialization_errors
        }
    
    def _fallback_population_estimate(self, geometry: Dict[str, Any]) -> int:
        """Fallback population estimation using simple area-based calculation"""
        try:
            from shapely.geometry import shape
            
            # Handle both GeoJSON Feature and plain geometry
            if geometry.get('type') == 'Feature':
                # Extract geometry from feature
                geom_data = geometry.get('geometry', {})
            else:
                # Already a geometry object
                geom_data = geometry
            
            # Convert geometry to shape and calculate area
            geom = shape(geom_data)
            area_sqm = geom.area * 111320 ** 2  # Convert degrees to square meters (rough approximation)
            
            # Use Lusaka average population density (2500 people per sq km - more realistic)
            population_density_per_sqm = 2500 / 1_000_000  # 2500 per sq km
            estimated_population = int(area_sqm * population_density_per_sqm)
            
            logger.info(f"Fallback population estimate: {estimated_population} for area {area_sqm:.0f} sqm")
            return estimated_population
            
        except Exception as e:
            logger.error(f"Fallback population estimation failed: {str(e)}")
            return 1000  # Default fallback
    
    def _estimate_population_from_buildings(self, building_data: Dict[str, Any], 
                                           settlement_type: str) -> int:
        """Estimate population based on building characteristics and settlement type"""
        try:
            building_count = building_data.get('building_count', 0)
            building_types = building_data.get('building_types', {})
            avg_building_size = building_data.get('average_building_size_sqm', 100)
            
            # People per building based on settlement type and building size
            if settlement_type in ['informal_high_density', 'informal_medium_density']:
                # Informal settlements have higher occupancy
                if avg_building_size < 50:
                    people_per_building = 5.5  # Very small informal buildings
                elif avg_building_size < 100:
                    people_per_building = 4.8  # Small informal buildings
                else:
                    people_per_building = 4.2  # Larger informal buildings
            elif settlement_type in ['formal_high_density', 'formal_medium_density']:
                # Formal settlements have lower occupancy
                if avg_building_size < 80:
                    people_per_building = 3.2  # Small formal buildings
                elif avg_building_size < 150:
                    people_per_building = 3.8  # Medium formal buildings
                else:
                    people_per_building = 4.5  # Large formal buildings
            else:
                # Mixed or unknown settlement type
                people_per_building = 4.0  # Average for Lusaka
            
            # Calculate population estimate
            population_estimate = int(building_count * people_per_building)
            
            logger.info(f"Building-based population estimate: {population_estimate} people "
                       f"({building_count} buildings × {people_per_building:.1f} people/building)")
            
            return population_estimate
            
        except Exception as e:
            logger.error(f"Building-based population estimation failed: {str(e)}")
            return 0
    
    def _enhanced_fallback_building_count(self, geometry: Dict[str, Any]) -> int:
        """Enhanced fallback building count using multiple estimation methods"""
        try:
            from shapely.geometry import shape
            
            # Handle both GeoJSON Feature and plain geometry
            if geometry.get('type') == 'Feature':
                geom_data = geometry.get('geometry', {})
            else:
                geom_data = geometry
            
            # Convert geometry to shape and calculate area
            geom = shape(geom_data)
            area_sqm = geom.area * 111320 ** 2  # Convert degrees to square meters
            area_km2 = area_sqm / 1_000_000
            
            # Enhanced estimation using multiple density scenarios
            densities = {
                'high_density': 200,    # High density residential (200 buildings/km²)
                'medium_density': 120,  # Medium density residential (120 buildings/km²)
                'low_density': 60,      # Low density residential (60 buildings/km²)
                'mixed_urban': 140      # Mixed urban areas (140 buildings/km²)
            }
            
            # Calculate estimates for each scenario
            estimates = {}
            for scenario, density in densities.items():
                estimates[scenario] = int(area_km2 * density)
            
            # Use weighted average based on typical Lusaka distribution
            # 40% medium density, 30% mixed urban, 20% high density, 10% low density
            weighted_estimate = int(
                estimates['medium_density'] * 0.4 +
                estimates['mixed_urban'] * 0.3 +
                estimates['high_density'] * 0.2 +
                estimates['low_density'] * 0.1
            )
            
            # Ensure minimum of 1 building for areas larger than 1000 sqm
            if area_sqm > 1000 and weighted_estimate == 0:
                weighted_estimate = 1
            
            logger.info(f"Enhanced fallback building estimate: {weighted_estimate} for area {area_km2:.3f} km²")
            return weighted_estimate
            
        except Exception as e:
            logger.error(f"Enhanced fallback building estimation failed: {str(e)}")
            return self._fallback_building_count(geometry)
    
    def _fallback_building_count(self, geometry: Dict[str, Any]) -> int:
        """Fallback building count estimation using simple area-based calculation"""
        try:
            from shapely.geometry import shape
            
            # Handle both GeoJSON Feature and plain geometry
            if geometry.get('type') == 'Feature':
                # Extract geometry from feature
                geom_data = geometry.get('geometry', {})
            else:
                # Already a geometry object
                geom_data = geometry
            
            # Convert geometry to shape and calculate area
            geom = shape(geom_data)
            area_sqm = geom.area * 111320 ** 2  # Convert degrees to square meters (rough approximation)
            
            # Use Lusaka average building density (120 buildings per sq km)
            building_density_per_sqm = 120 / 1_000_000  # 120 per sq km
            estimated_buildings = int(area_sqm * building_density_per_sqm)
            
            # Ensure minimum of 1 building for areas larger than 500 sqm
            if area_sqm > 500 and estimated_buildings == 0:
                estimated_buildings = 1
            
            logger.info(f"Fallback building estimate: {estimated_buildings} for area {area_sqm:.0f} sqm")
            return estimated_buildings
            
        except Exception as e:
            logger.error(f"Fallback building estimation failed: {str(e)}")
            return 50  # Default fallback
    
    def _get_typical_building_area(self, building_type: str) -> float:
        """Get typical building area by type for Lusaka"""
        typical_areas = {
            'residential': 85.0,
            'commercial': 150.0,
            'mixed': 110.0,
            'industrial': 200.0,
            'unknown': 100.0
        }
        return typical_areas.get(building_type, 100.0)
    
    def _get_typical_building_height(self, building_type: str) -> float:
        """Get typical building height by type for Lusaka"""
        typical_heights = {
            'residential': 3.5,
            'commercial': 4.5,
            'mixed': 4.0,
            'industrial': 6.0,
            'unknown': 3.5
        }
        return typical_heights.get(building_type, 3.5)
    
    def _estimate_zone_area(self, geometry: Dict[str, Any]) -> float:
        """Estimate zone area in square meters"""
        try:
            from shapely.geometry import shape
            
            # Handle both GeoJSON Feature and plain geometry
            if geometry.get('type') == 'Feature':
                geom_data = geometry.get('geometry', {})
            else:
                geom_data = geometry
            
            # Convert geometry to shape and calculate area
            geom = shape(geom_data)
            area_sqm = geom.area * 111320 ** 2  # Convert degrees to square meters
            return area_sqm
            
        except Exception as e:
            logger.error(f"Zone area estimation failed: {str(e)}")
            return 1000000  # Default 1 km²


# Global analyzer instance
analyzer = UnifiedAnalyzer()
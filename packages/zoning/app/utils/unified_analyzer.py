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
            'warnings': self.warnings
        }


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
            # Population engine initialization
            try:
                from .population_engine import PopulationEngine
                self.population_engine = PopulationEngine()
                logger.info("✅ Population engine initialized")
            except ImportError:
                logger.warning("⚠️ Population engine not available yet")
                self.initialization_errors.append("Population engine not implemented")
            
            # Building engine initialization
            try:
                from .building_engine import BuildingEngine
                self.building_engine = BuildingEngine()
                logger.info("✅ Building engine initialized")
            except ImportError:
                logger.warning("⚠️ Building engine not available yet")
                self.initialization_errors.append("Building engine not implemented")
            
            # Waste engine initialization
            try:
                from .waste_engine import WasteEngine
                self.waste_engine = WasteEngine()
                logger.info("✅ Waste engine initialized")
            except ImportError:
                logger.warning("⚠️ Waste engine not available yet")
                self.initialization_errors.append("Waste engine not implemented")
            
            # Validation engine initialization
            try:
                from .validation_engine import ValidationEngine
                self.validation_engine = ValidationEngine()
                logger.info("✅ Validation engine initialized")
            except ImportError:
                logger.warning("⚠️ Validation engine not available yet")
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
            
            # Cache the result
            if self.cache_enabled:
                self._cache_result(request_id, result)
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Analysis completed in {execution_time:.2f}s for {request_id}")
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {request_id}: {str(e)}")
            result.error_message = str(e)
            result.success = False
        
        return result
    
    def _analyze_population(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform population analysis with timeout handling"""
        if not self.population_engine:
            # Fallback to basic estimation
            logger.warning("Population engine not available, using fallback estimation")
            result.population_estimate = self._fallback_population_estimate(request.geometry)
            result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
            result.population_density = 2500  # Default density for Lusaka
            result.confidence_level = 0.3  # Low confidence for fallback
            result.data_sources = ['Fallback estimation']
            result.warnings = result.warnings or []
            result.warnings.append("Using fallback population estimation")
            return result
        
        try:
            # Add a simple fallback mode for development
            use_fallback = request.options.get('use_fallback', False)
            
            if use_fallback:
                logger.info("Using fallback mode for population analysis")
                result.population_estimate = self._fallback_population_estimate(request.geometry)
                result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
                result.population_density = 2500
                result.confidence_level = 0.5
                result.data_sources = ['Fallback estimation (requested)']
                result.warnings = result.warnings or []
                result.warnings.append("Using fallback mode for faster analysis")
            else:
                # Try normal analysis but with quick fallback on any error
                try:
                    pop_data = self.population_engine.estimate_population(
                        request.geometry,
                        options=request.options
                    )
                    
                    result.population_estimate = pop_data.get('population_estimate')
                    result.household_estimate = pop_data.get('household_estimate')
                    result.population_density = pop_data.get('population_density')
                    result.confidence_level = pop_data.get('confidence_level')
                    result.data_sources = pop_data.get('data_sources', [])
                    
                except Exception as analysis_error:
                    logger.warning(f"Population analysis failed, using fallback: {str(analysis_error)}")
                    result.population_estimate = self._fallback_population_estimate(request.geometry)
                    result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
                    result.population_density = 2500
                    result.confidence_level = 0.3
                    result.data_sources = ['Fallback estimation (analysis failed)']
                    result.warnings = result.warnings or []
                    result.warnings.append(f"Population analysis failed: {str(analysis_error)}")
                
        except Exception as e:
            logger.error(f"Population analysis completely failed: {str(e)}")
            result.population_estimate = self._fallback_population_estimate(request.geometry)
            result.household_estimate = int(result.population_estimate / 4.6) if result.population_estimate else 0
            result.population_density = 5000
            result.confidence_level = 0.2
            result.data_sources = ['Fallback estimation (error)']
            result.warnings = result.warnings or []
            result.warnings.append(f"Population analysis completely failed: {str(e)}")
        
        return result
    
    def _analyze_buildings(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform building analysis with timeout handling"""
        if not self.building_engine:
            # Fallback to basic estimation
            logger.warning("Building engine not available, using fallback estimation")
            result.building_count = self._fallback_building_count(request.geometry)
            result.building_types = {'residential': result.building_count}
            result.settlement_classification = 'mixed'
            result.confidence_level = 0.3
            if not result.data_sources:
                result.data_sources = []
            result.data_sources.extend(['Fallback estimation'])
            result.warnings = result.warnings or []
            result.warnings.append("Using fallback building estimation")
            return result
        
        try:
            # Add a simple fallback mode for development
            use_fallback = request.options.get('use_fallback', False)
            
            if use_fallback:
                logger.info("Using fallback mode for building analysis")
                result.building_count = self._fallback_building_count(request.geometry)
                result.building_types = {'residential': result.building_count}
                result.settlement_classification = 'mixed'
                result.confidence_level = 0.5
                if not result.data_sources:
                    result.data_sources = []
                result.data_sources.extend(['Fallback estimation (requested)'])
                result.warnings = result.warnings or []
                result.warnings.append("Using fallback mode for faster analysis")
            else:
                # Try normal analysis but with quick fallback on any error
                try:
                    building_data = self.building_engine.analyze_buildings(
                        request.geometry,
                        options=request.options
                    )
                    
                    result.building_count = building_data.get('building_count')
                    result.building_types = building_data.get('building_types')
                    result.settlement_classification = building_data.get('settlement_classification')
                    result.confidence_level = building_data.get('confidence_level')
                    
                    if not result.data_sources:
                        result.data_sources = []
                    result.data_sources.extend(building_data.get('data_sources', []))
                    
                    # Estimate population based on building data
                    if result.building_count and result.building_count > 0:
                        population_estimate = self._estimate_population_from_buildings(
                            building_data, result.settlement_classification
                        )
                        result.population_estimate = population_estimate
                        result.household_estimate = int(population_estimate / 4.6) if population_estimate else 0
                    
                except Exception as analysis_error:
                    logger.warning(f"Building analysis failed, using enhanced fallback: {str(analysis_error)}")
                    
                    # Enhanced fallback based on error type
                    error_str = str(analysis_error).lower()
                    
                    if 'timeout' in error_str or 'rate limit' in error_str:
                        # API timeout or rate limit - use enhanced area-based estimation
                        result.building_count = self._enhanced_fallback_building_count(request.geometry)
                        result.confidence_level = 0.4  # Higher confidence for enhanced fallback
                        result.warnings = result.warnings or []
                        result.warnings.append("Earth Engine API timeout - using enhanced area-based estimation")
                    elif 'invalid geojson' in error_str or 'geometry' in error_str:
                        # Geometry error - use basic fallback
                        result.building_count = self._fallback_building_count(request.geometry)
                        result.confidence_level = 0.2
                        result.warnings = result.warnings or []
                        result.warnings.append("Geometry error - using basic fallback estimation")
                    else:
                        # Other errors - use enhanced fallback
                        result.building_count = self._enhanced_fallback_building_count(request.geometry)
                        result.confidence_level = 0.3
                        result.warnings = result.warnings or []
                        result.warnings.append(f"Building analysis failed: {str(analysis_error)}")
                    
                    result.building_types = {'residential': result.building_count}
                    result.settlement_classification = 'mixed'
                    if not result.data_sources:
                        result.data_sources = []
                    result.data_sources.extend(['Enhanced fallback estimation'])
                
        except Exception as e:
            logger.error(f"Building analysis completely failed: {str(e)}")
            result.building_count = self._fallback_building_count(request.geometry)
            result.building_types = {'residential': result.building_count}
            result.settlement_classification = 'mixed'
            result.confidence_level = 0.2
            if not result.data_sources:
                result.data_sources = []
            result.data_sources.extend(['Fallback estimation (error)'])
            result.warnings = result.warnings or []
            result.warnings.append(f"Building analysis completely failed: {str(e)}")
        
        return result
    
    def _analyze_waste(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Perform waste analysis with fallback handling"""
        if not self.waste_engine:
            logger.warning("Waste engine not available, using fallback calculation")
            # Fallback waste calculation
            population = result.population_estimate or 0
            waste_rate = 0.5  # Lusaka standard rate
            result.waste_generation_kg_per_day = population * waste_rate
            result.collection_requirements = {
                'frequency_per_week': 2,
                'vehicle_requirements': {
                    'truck_10_tonne': 1,
                    'frequency_per_week': 2,
                    'total_capacity_needed': result.waste_generation_kg_per_day * 7 / 2
                }
            }
            return result
        
        # Need population data for waste calculation
        population_for_waste = result.population_estimate
        if not population_for_waste:
            # Get population estimate first using fallback
            population_for_waste = self._fallback_population_estimate(request.geometry)
            if not result.population_estimate:  # Only update if we don't have one
                result.population_estimate = population_for_waste
        
        try:
            # Get waste calculations
            waste_data = self.waste_engine.calculate_waste_generation(
                population=population_for_waste,
                zone_type=request.zone_type,
                options=request.options
            )
            
            result.waste_generation_kg_per_day = waste_data.get('waste_generation_kg_per_day')
            result.collection_requirements = waste_data.get('collection_requirements')
            
        except Exception as e:
            logger.warning(f"Waste analysis failed, using fallback: {str(e)}")
            # Fallback waste calculation
            waste_rate = 0.5  # Lusaka standard rate
            result.waste_generation_kg_per_day = population_for_waste * waste_rate
            result.collection_requirements = {
                'frequency_per_week': 2,
                'vehicle_requirements': {
                    'truck_10_tonne': 1,
                    'frequency_per_week': 2,
                    'total_capacity_needed': result.waste_generation_kg_per_day * 7 / 2
                }
            }
            result.warnings = result.warnings or []
            result.warnings.append(f"Waste analysis failed: {str(e)}")
        
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


# Global analyzer instance
analyzer = UnifiedAnalyzer()
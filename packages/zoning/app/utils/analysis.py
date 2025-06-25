"""
Waste management analysis formulas and calculations
Based on industry standards and Lusaka-specific parameters
"""
import math
from app.models import ZoneTypeEnum
from .earth_engine_analysis import EarthEngineAnalyzer
from .ai_analysis import AIWasteAnalyzer
import time


class WasteAnalysis:
    """Alias for backward compatibility"""
    pass


class WasteAnalyzer:
    """Analyze waste generation and collection requirements for zones"""
    
    def __init__(self):
        """Initialize analyzers"""
        self.earth_engine = EarthEngineAnalyzer()
        self.ai_analyzer = AIWasteAnalyzer()
    
    # Waste generation rates (kg per unit per day)
    WASTE_GENERATION_RATES = {
        'residential': {
            'per_person': 0.5,  # kg/person/day
            'per_household': 2.5  # kg/household/day (avg 5 people)
        },
        'commercial': {
            'small_business': 10,  # kg/day
            'medium_business': 50,  # kg/day
            'large_business': 200  # kg/day
        },
        'industrial': {
            'light_industry': 500,  # kg/day
            'heavy_industry': 2000  # kg/day
        },
        'institutional': {
            'school': 0.1,  # kg/student/day
            'hospital': 2.5,  # kg/bed/day
            'office': 0.5  # kg/employee/day
        }
    }
    
    # Collection parameters
    COLLECTION_PARAMS = {
        'truck_capacity_kg': 5000,  # 5 tons
        'collection_point_capacity_kg': 1000,  # 1 ton
        'collection_efficiency': 0.85,  # 85% efficiency
        'working_days_per_month': 26,
        'trips_per_truck_per_day': 3
    }
    
    # Revenue rates (per kg) - Converted to Zambian Kwacha (ZMW)
    # Exchange rate: 1 USD ≈ 27 ZMW (as of 2024)
    REVENUE_RATES = {
        'residential': 2.70,   # K2.70 per kg (was $0.10)
        'commercial': 4.05,    # K4.05 per kg (was $0.15)
        'industrial': 5.40,    # K5.40 per kg (was $0.20)
        'institutional': 3.24  # K3.24 per kg (was $0.12)
    }
    
    # Settlement-specific waste generation factors from analysis.md
    SETTLEMENT_WASTE_FACTORS = {
        'formal': {
            'density_factor': 4.1,  # persons per 100m²
            'waste_multiplier': 1.0  # baseline rate
        },
        'informal': {
            'density_factor': 6.2,  # persons per 100m²
            'waste_multiplier': 0.8  # lower waste generation due to income
        }
    }
    
    def analyze_zone(self, zone, include_advanced=True):
        """Perform comprehensive waste analysis for a zone"""
        results = {
            'zone_id': zone.id,
            'zone_name': zone.name,
            'zone_type': zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type) if hasattr(zone, 'zone_type') else 'unknown',
            'area_km2': zone.area_sqm / 1000000 if zone.area_sqm else 0
        }
        
        # Calculate waste generation
        waste_gen = self._calculate_waste_generation(zone)
        results.update(waste_gen)
        
        # Calculate collection requirements
        collection_req = self._calculate_collection_requirements(
            waste_gen['total_waste_kg_day'],
            zone.collection_frequency_week or 2
        )
        results.update(collection_req)
        
        # Calculate revenue projections
        revenue = self._calculate_revenue_projection(zone, waste_gen)
        results.update(revenue)
        
        # Calculate population density
        if zone.area_sqm and zone.estimated_population:
            results['population_density_per_km2'] = (
                zone.estimated_population / (zone.area_sqm / 1000000)
            )
        else:
            results['population_density_per_km2'] = 0
        
        # Add advanced analysis if requested
        if include_advanced:
            # Google Open Buildings analysis
            if self.earth_engine.initialized:
                try:
                    # Extract comprehensive building features (includes rich analysis)
                    buildings_data = self.earth_engine.extract_comprehensive_building_features(zone, 2023)
                    results['buildings_analysis'] = buildings_data
                    
                    # Fallback to basic building extraction if comprehensive fails
                    if buildings_data.get('error'):
                        buildings_data = self.earth_engine.extract_buildings_for_zone(zone)
                        results['buildings_analysis'] = buildings_data
                    
                    # Settlement classification
                    if not buildings_data.get('error'):
                        settlement_classification = self.earth_engine.classify_buildings_by_context(zone, buildings_data)
                        results['settlement_classification'] = settlement_classification
                        
                        # Enhanced population estimate using building data
                        enhanced_population = self._calculate_building_based_population(zone, buildings_data, settlement_classification)
                        results['enhanced_population_estimate'] = enhanced_population
                        
                        # Enhanced waste generation based on settlement type
                        enhanced_waste = self._calculate_settlement_specific_waste(zone, buildings_data, settlement_classification)
                        results['enhanced_waste_estimate'] = enhanced_waste
                    
                    # Earth Engine analysis
                    results['land_use_analysis'] = self.earth_engine.analyze_zone_land_use(zone)
                    results['environmental_factors'] = self.earth_engine.analyze_environmental_factors(zone)
                    results['population_estimate'] = self.earth_engine.get_population_estimate(zone)
                    
                except Exception as e:
                    results['earth_engine_error'] = str(e)
            
            # AI predictions and insights
            try:
                results['waste_predictions'] = self.ai_analyzer.predict_waste_generation(zone)
                results['ai_insights'] = self.ai_analyzer.generate_insights(zone, results)
            except Exception as e:
                results['ai_analysis_error'] = str(e)
        
        return results
    
    def _get_best_population_estimate(self, zone):
        """
        Get the best available population estimate using hierarchical approach
        Same logic as dashboard for consistency between display and calculations
        """
        try:
            # Priority hierarchy (same as DashboardCore):
            # 1. Enhanced population estimate (from recent analysis)
            # 2. GPWv4.11/GHSL population data from Earth Engine
            # 3. WorldPop population estimate 
            # 4. Zone's stored estimated_population
            # 5. Conservative area-based fallback
            
            estimated_population = 0
            
            # Try to get comprehensive analysis data if available
            if self.earth_engine and self.earth_engine.initialized and hasattr(zone, 'geometry') and zone.geometry:
                try:
                    comp_result = self.earth_engine.extract_comprehensive_building_features(zone)
                    if not comp_result.get('error'):
                        # 1. Enhanced population estimate
                        enhanced_pop = comp_result.get('enhanced_population_estimate', {})
                        if enhanced_pop.get('estimated_population', 0) > 0:
                            estimated_population = enhanced_pop.get('estimated_population', 0)
                            print(f"🎯 Using enhanced population estimate: {estimated_population}")
                            return estimated_population
                        
                        # 2. GPWv4.11/GHSL population data
                        ghsl_data = comp_result.get('ghsl_population', {})
                        if ghsl_data.get('total_population', 0) > 0:
                            estimated_population = ghsl_data.get('total_population', 0)
                            print(f"🌍 Using GPWv4.11 population data: {estimated_population}")
                            return estimated_population
                        
                        # 3. WorldPop population estimate
                        worldpop_data = comp_result.get('worldpop_population', {})
                        if worldpop_data.get('total_population', 0) > 0:
                            estimated_population = worldpop_data.get('total_population', 0)
                            print(f"🗺️ Using WorldPop population data: {estimated_population}")
                            return estimated_population
                            
                except Exception as e:
                    print(f"⚠️ Earth Engine population analysis failed: {str(e)}")
            
            # 4. Zone's stored estimated_population (if reasonable)
            if hasattr(zone, 'estimated_population') and zone.estimated_population and zone.estimated_population > 0:
                estimated_population = zone.estimated_population
                print(f"📊 Using stored zone population: {estimated_population}")
                return estimated_population
            
            # 5. Conservative area-based fallback (1,250 people/km² as per recent adjustment)
            if hasattr(zone, 'area_sqm') and zone.area_sqm:
                area_km2 = zone.area_sqm / 1000000
                conservative_density = 1250  # Adjusted conservative density
                estimated_population = int(area_km2 * conservative_density)
                print(f"📐 Using conservative area-based estimate: {estimated_population} (density: {conservative_density}/km²)")
                return estimated_population
            
            print(f"⚠️ No population data available, using default: 100")
            return 100  # Minimal fallback
            
        except Exception as e:
            print(f"❌ Population estimation failed: {str(e)}")
            # Final fallback to zone's stored value or minimal default
            return getattr(zone, 'estimated_population', 100) if hasattr(zone, 'estimated_population') and zone.estimated_population else 100
    
    def _calculate_waste_generation(self, zone):
        """Calculate daily waste generation for a zone using best available population data"""
        waste = {
            'residential_waste': 0,
            'commercial_waste': 0,
            'industrial_waste': 0,
            'institutional_waste': 0
        }
        
        # Use hierarchical population estimation - same logic as dashboard for consistency
        actual_population = self._get_best_population_estimate(zone)
        print(f"🏠 Waste generation using population: {actual_population} people (zone {getattr(zone, 'id', 'unknown')})")
        enhanced_waste_data = None
        
        # Always try to get enhanced data if Earth Engine is available
        if hasattr(zone, 'area_sqm') and zone.area_sqm:
            try:
                # Use Earth Engine comprehensive building features for complete analysis
                if self.earth_engine and self.earth_engine.initialized:
                    print(f"🔄 Using Earth Engine comprehensive analysis for zone {getattr(zone, 'id', 'unknown')}")
                    
                    if hasattr(zone, 'geometry') and zone.geometry:
                        # Get comprehensive building features which includes population AND waste generation
                        print(f"🔄 Calling extract_comprehensive_building_features...")
                        comp_result = self.earth_engine.extract_comprehensive_building_features(zone)
                        
                        print(f"📊 Comprehensive result keys: {list(comp_result.keys()) if isinstance(comp_result, dict) else 'Not a dict'}")
                        
                        if not comp_result.get('error'):
                            print(f"✅ No error in comprehensive result")
                            
                            # Extract population from GHSL data within comprehensive results
                            ghsl_data = comp_result.get('ghsl_population', {})
                            print(f"📊 GHSL data keys: {list(ghsl_data.keys()) if isinstance(ghsl_data, dict) else 'No GHSL data'}")
                            
                            if ghsl_data and not ghsl_data.get('error'):
                                actual_population = ghsl_data.get('total_population', 0)
                                print(f"✅ Earth Engine population from comprehensive analysis: {actual_population}")
                                
                                # Get the pre-calculated waste generation data
                                enhanced_waste_data = comp_result.get('waste_generation', {})
                                print(f"📊 Waste data keys: {list(enhanced_waste_data.keys()) if isinstance(enhanced_waste_data, dict) else 'No waste data'}")
                                
                                if enhanced_waste_data and not enhanced_waste_data.get('error'):
                                    daily_waste = enhanced_waste_data.get('daily_waste_generation', {})
                                    if daily_waste:
                                        avg_daily_waste = daily_waste.get('annual_average_kg_day', 0)
                                        print(f"🎯 Earth Engine calculated waste: {avg_daily_waste} kg/day")
                            
                            # Fallback: Use building count for population estimation
                            if not actual_population or actual_population == 0:
                                building_count = comp_result.get('building_count', 0)
                                print(f"📊 Building count from comprehensive: {building_count}")
                                if building_count > 0:
                                    actual_population = building_count * 5.0  # 4-6 people per building
                                    print(f"✅ Building-based population: {actual_population} from {building_count} buildings")
                        else:
                            print(f"❌ Error in comprehensive result: {comp_result.get('error')}")
                    
                    # Update zone population if we found a better estimate
                    if actual_population and actual_population > 0:
                        zone.estimated_population = actual_population
                        print(f"📝 Updated zone.estimated_population to {actual_population}")
                        
            except Exception as e:
                print(f"⚠️  Enhanced population estimation failed: {e}")
        
        # If we have enhanced waste data, use it directly
        if enhanced_waste_data and not enhanced_waste_data.get('error'):
            daily_waste_gen = enhanced_waste_data.get('daily_waste_generation', {})
            if daily_waste_gen:
                total_daily_waste = daily_waste_gen.get('annual_average_kg_day', 0)
                if total_daily_waste > 0:
                    print(f"🎯 Using Earth Engine waste calculation: {total_daily_waste} kg/day")
                    waste = {
                        'residential_waste': total_daily_waste * 0.7,  # Assume 70% residential for mixed zones
                        'commercial_waste': total_daily_waste * 0.25,   # 25% commercial
                        'industrial_waste': total_daily_waste * 0.05,   # 5% industrial
                        'institutional_waste': 0,
                        'total_waste_kg_day': total_daily_waste
                    }
                    zone.waste_generation_kg_day = total_daily_waste
                    print(f"📊 Enhanced waste breakdown: {waste}")
                    return waste
        
        # Handle zone type as both enum and string
        zone_type_str = zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type) if hasattr(zone, 'zone_type') else 'residential'
        
        if zone_type_str in ['residential', 'RESIDENTIAL']:
            # Based on population
            if actual_population:
                waste['residential_waste'] = (
                    actual_population * 
                    self.WASTE_GENERATION_RATES['residential']['per_person']
                )
                print(f"🏠 Residential waste: {waste['residential_waste']} kg/day for {actual_population} people")
            # Or based on households
            elif zone.household_count:
                waste['residential_waste'] = (
                    zone.household_count * 
                    self.WASTE_GENERATION_RATES['residential']['per_household']
                )
        
        elif zone_type_str in ['commercial', 'COMMERCIAL']:
            if zone.business_count:
                # Assume mix of business sizes
                small = zone.business_count * 0.7
                medium = zone.business_count * 0.25
                large = zone.business_count * 0.05
                
                waste['commercial_waste'] = (
                    small * self.WASTE_GENERATION_RATES['commercial']['small_business'] +
                    medium * self.WASTE_GENERATION_RATES['commercial']['medium_business'] +
                    large * self.WASTE_GENERATION_RATES['commercial']['large_business']
                )
        
        elif zone_type_str in ['industrial', 'INDUSTRIAL']:
            # Estimate based on area
            if zone.area_sqm:
                # Assume 1 industry per 10,000 sqm
                industries = zone.area_sqm / 10000
                waste['industrial_waste'] = (
                    industries * self.WASTE_GENERATION_RATES['industrial']['light_industry']
                )
        
        elif zone_type_str in ['mixed_use', 'MIXED_USE', 'mixed']:
            # Split between residential and commercial
            if actual_population:
                waste['residential_waste'] = (
                    actual_population * 0.7 * 
                    self.WASTE_GENERATION_RATES['residential']['per_person']
                )
                print(f"🏘️  Mixed-use residential waste: {waste['residential_waste']} kg/day for {actual_population} people")
            if zone.business_count:
                waste['commercial_waste'] = (
                    zone.business_count * 
                    self.WASTE_GENERATION_RATES['commercial']['small_business']
                )
        
        # Total waste
        waste['total_waste_kg_day'] = sum(waste.values())
        print(f"📊 Total waste generation: {waste['total_waste_kg_day']} kg/day")
        
        # Update zone model
        zone.waste_generation_kg_day = waste['total_waste_kg_day']
        
        return waste
    
    def _calculate_collection_requirements(self, daily_waste_kg, frequency_per_week):
        """Calculate collection infrastructure requirements"""
        # Waste per collection
        waste_per_collection = daily_waste_kg * (7 / frequency_per_week)
        
        # Collection points needed
        collection_points = math.ceil(
            waste_per_collection / self.COLLECTION_PARAMS['collection_point_capacity_kg']
        )
        
        # Enhanced truck calculations with different vehicle types
        # 10-tonne trucks (capacity 10,000 kg)
        trucks_10t_per_collection = math.ceil(
            waste_per_collection / (10000 * self.COLLECTION_PARAMS['collection_efficiency'])
        )
        
        # 20-tonne trucks (capacity 20,000 kg) 
        trucks_20t_per_collection = math.ceil(
            waste_per_collection / (20000 * self.COLLECTION_PARAMS['collection_efficiency'])
        )
        
        # Use the original 5-tonne calculation for backward compatibility
        trucks_per_collection = math.ceil(
            waste_per_collection / 
            (self.COLLECTION_PARAMS['truck_capacity_kg'] * 
             self.COLLECTION_PARAMS['collection_efficiency'])
        )
        
        # Total monthly collections
        monthly_collections = frequency_per_week * 4.33  # avg weeks per month
        
        # Staff requirements (2 staff per truck + 1 supervisor per 5 trucks)
        staff_required = (trucks_per_collection * 2) + math.ceil(trucks_per_collection / 5)
        
        print(f"🚛 Collection requirements: {trucks_10t_per_collection} x 10t trucks, {trucks_20t_per_collection} x 20t trucks")
        
        return {
            'collection_points': collection_points,
            'vehicles_required': trucks_per_collection,
            '10_tonne_trucks': trucks_10t_per_collection,
            '20_tonne_trucks': trucks_20t_per_collection,
            'trucks_required': max(trucks_10t_per_collection, trucks_20t_per_collection, trucks_per_collection),
            'collection_staff': staff_required,
            'collections_per_month': round(monthly_collections),
            'waste_per_collection_kg': round(waste_per_collection, 2)
        }
    
    def _calculate_revenue_projection(self, zone, waste_generation):
        """Calculate monthly revenue projections"""
        revenue = {}
        
        # Handle zone type as both enum and string
        zone_type_str = zone.zone_type.value if hasattr(zone.zone_type, 'value') else str(zone.zone_type) if hasattr(zone, 'zone_type') else 'residential'
        
        # Revenue by waste type
        if zone_type_str in ['residential', 'RESIDENTIAL']:
            rate = self.REVENUE_RATES['residential']
        elif zone_type_str in ['commercial', 'COMMERCIAL']:
            rate = self.REVENUE_RATES['commercial']
        elif zone_type_str in ['industrial', 'INDUSTRIAL']:
            rate = self.REVENUE_RATES['industrial']
        else:
            rate = self.REVENUE_RATES['residential']  # default
        
        # Calculate monthly revenue
        daily_revenue = waste_generation['total_waste_kg_day'] * rate
        monthly_revenue = daily_revenue * self.COLLECTION_PARAMS['working_days_per_month']
        
        revenue['daily_revenue'] = round(daily_revenue, 2)
        revenue['monthly_revenue'] = round(monthly_revenue, 2)
        revenue['annual_revenue'] = round(monthly_revenue * 12, 2)
        
        # Breakdown by type
        revenue['residential_revenue'] = round(
            waste_generation['residential_waste'] * 
            self.REVENUE_RATES['residential'] * 
            self.COLLECTION_PARAMS['working_days_per_month'], 2
        )
        revenue['commercial_revenue'] = round(
            waste_generation['commercial_waste'] * 
            self.REVENUE_RATES['commercial'] * 
            self.COLLECTION_PARAMS['working_days_per_month'], 2
        )
        revenue['industrial_revenue'] = round(
            waste_generation['industrial_waste'] * 
            self.REVENUE_RATES['industrial'] * 
            self.COLLECTION_PARAMS['working_days_per_month'], 2
        )
        
        return revenue
    
    def calculate_route_optimization(self, zones):
        """Calculate optimal collection routes for multiple zones"""
        # This would integrate with routing algorithms
        # For now, return basic estimates
        total_distance = 0
        for zone in zones:
            if zone.perimeter_m:
                # Estimate internal roads as 2x perimeter
                total_distance += (zone.perimeter_m * 2) / 1000  # Convert to km
        
        return {
            'total_route_distance_km': round(total_distance, 2),
            'estimated_time_hours': round(total_distance / 20, 2),  # 20 km/h avg speed
            'fuel_consumption_liters': round(total_distance * 0.35, 2)  # 0.35 L/km
        }
    
    def _calculate_building_based_population(self, zone, buildings_data, settlement_classification):
        """Calculate population based on building analysis and settlement type"""
        try:
            if buildings_data.get('error') or settlement_classification.get('error'):
                return {"error": "Insufficient building data for population calculation"}
            
            features = buildings_data.get('features', {})
            settlement_type = settlement_classification.get('settlement_type', 'formal')
            building_count = buildings_data.get('building_count', 0)
            
            # Get settlement-specific density factors
            density_factor = self.SETTLEMENT_WASTE_FACTORS.get(settlement_type, {}).get('density_factor', 4.1)
            
            # Calculate total building area
            area_stats = features.get('area_statistics', {})
            avg_building_area = area_stats.get('mean', 100)  # Default 100 sqm
            total_building_area = building_count * avg_building_area
            
            # Estimate floors from height data
            height_stats = buildings_data.get('height_stats', {})
            avg_height = height_stats.get('building_height_mean', 3.0)  # Default 3m
            floors = max(1, round(avg_height / 2.5))  # Assume 2.5m per floor
            
            # Calculate population
            # Formula: (building_area * floors * density_factor) / 100
            estimated_population = (total_building_area * floors * density_factor) / 100
            
            return {
                'estimated_population': round(estimated_population),
                'settlement_type': settlement_type,
                'density_factor_used': density_factor,
                'total_building_area_sqm': total_building_area,
                'average_floors': floors,
                'calculation_method': 'building_based_with_settlement_factors',
                'confidence': settlement_classification.get('confidence', 0.5)
            }
            
        except Exception as e:
            return {"error": f"Building-based population calculation failed: {str(e)}"}
    
    def _calculate_settlement_specific_waste(self, zone, buildings_data, settlement_classification):
        """Calculate waste generation with settlement-specific factors"""
        try:
            if buildings_data.get('error') or settlement_classification.get('error'):
                return {"error": "Insufficient data for settlement-specific calculation"}
            
            settlement_type = settlement_classification.get('settlement_type', 'formal')
            building_count = buildings_data.get('building_count', 0)
            
            # Get settlement factors
            settlement_factors = self.SETTLEMENT_WASTE_FACTORS.get(settlement_type, self.SETTLEMENT_WASTE_FACTORS['formal'])
            density_factor = settlement_factors['density_factor']
            waste_multiplier = settlement_factors['waste_multiplier']
            
            # Calculate population using building data
            features = buildings_data.get('features', {})
            area_stats = features.get('area_statistics', {})
            avg_building_area = area_stats.get('mean', 100)
            total_building_area = building_count * avg_building_area
            
            # Estimate floors
            height_stats = buildings_data.get('height_stats', {})
            avg_height = height_stats.get('building_height_mean', 3.0)
            floors = max(1, round(avg_height / 2.5))
            
            # Population calculation
            estimated_population = (total_building_area * floors * density_factor) / 100
            
            # Waste calculation with settlement multiplier
            base_waste_per_person = self.WASTE_GENERATION_RATES['residential']['per_person']
            adjusted_waste_per_person = base_waste_per_person * waste_multiplier
            total_waste_kg_day = estimated_population * adjusted_waste_per_person
            
            return {
                'total_waste_kg_day': round(total_waste_kg_day, 2),
                'waste_per_person_kg_day': adjusted_waste_per_person,
                'settlement_type': settlement_type,
                'waste_multiplier': waste_multiplier,
                'estimated_population': round(estimated_population),
                'calculation_method': 'settlement_specific_building_based'
            }
            
        except Exception as e:
            return {"error": f"Settlement-specific waste calculation failed: {str(e)}"}

    def analyze_building_characteristics(self, zone):
        """Analyze building characteristics for a zone using Google Open Buildings"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Extract building data
            buildings_data = self.earth_engine.extract_buildings_for_zone(zone)
            
            if buildings_data.get('error'):
                return buildings_data
            
            # Classify settlement type
            settlement_classification = self.earth_engine.classify_buildings_by_context(zone, buildings_data)
            
            # Compile comprehensive building analysis
            analysis = {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'building_analysis': buildings_data,
                'settlement_classification': settlement_classification,
                'analysis_date': buildings_data.get('extraction_date'),
                'data_source': buildings_data.get('data_source')
            }
            
            # Calculate derived metrics
            if not buildings_data.get('error'):
                features = buildings_data.get('features', {})
                building_count = buildings_data.get('building_count', 0)
                zone_area_sqkm = features.get('zone_area_sqkm', 1)
                
                analysis['derived_metrics'] = {
                    'building_coverage_ratio': self._calculate_building_coverage_ratio(features),
                    'building_density_per_hectare': building_count / (zone_area_sqkm * 100),
                    'average_building_footprint': features.get('area_statistics', {}).get('mean', 0),
                    'building_size_variability': self._calculate_size_variability(features)
                }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Building characteristics analysis failed: {str(e)}"}
    
    def _calculate_building_coverage_ratio(self, features):
        """Calculate the ratio of built-up area to total zone area"""
        try:
            area_stats = features.get('area_statistics', {})
            total_building_area = area_stats.get('sum', 0)  # Total area of all buildings
            zone_area_sqm = features.get('zone_area_sqkm', 1) * 1000000  # Convert to sqm
            
            if zone_area_sqm > 0:
                return round((total_building_area / zone_area_sqm) * 100, 2)  # Percentage
            else:
                return 0
        except:
            return 0
    
    def _calculate_size_variability(self, features):
        """Calculate coefficient of variation for building sizes"""
        try:
            area_stats = features.get('area_statistics', {})
            mean_area = area_stats.get('mean', 0)
            std_area = area_stats.get('stddev', 0)
            
            if mean_area > 0:
                return round(std_area / mean_area, 3)  # Coefficient of variation
            else:
                return 0
        except:
            return 0

    def get_settlement_waste_recommendations(self, zone):
        """Get waste management recommendations based on settlement analysis"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get building analysis
            buildings_data = self.earth_engine.extract_buildings_for_zone(zone)
            settlement_classification = self.earth_engine.classify_buildings_by_context(zone, buildings_data)
            
            if buildings_data.get('error') or settlement_classification.get('error'):
                return {"error": "Unable to analyze settlement for recommendations"}
            
            settlement_type = settlement_classification.get('settlement_type', 'formal')
            building_density = settlement_classification.get('building_density', 0)
            confidence = settlement_classification.get('confidence', 0)
            
            # Generate recommendations based on settlement type and characteristics
            recommendations = {
                'settlement_type': settlement_type,
                'confidence': confidence,
                'collection_strategy': self._get_collection_strategy(settlement_type, building_density),
                'service_frequency': self._get_service_frequency(settlement_type, building_density),
                'equipment_recommendations': self._get_equipment_recommendations(settlement_type, building_density),
                'access_considerations': self._get_access_considerations(settlement_type),
                'community_engagement': self._get_engagement_strategy(settlement_type)
            }
            
            return recommendations
            
        except Exception as e:
            return {"error": f"Recommendation generation failed: {str(e)}"}
    
    def _get_collection_strategy(self, settlement_type, density):
        """Get collection strategy based on settlement characteristics"""
        if settlement_type == 'informal':
            if density > 150:
                return "High-density informal: Door-to-door collection with small vehicles and frequent service"
            else:
                return "Low-density informal: Community collection points with regular pickup schedules"
        else:
            if density > 80:
                return "High-density formal: Curbside collection with optimized routes"
            else:
                return "Low-density formal: Standard curbside collection with weekly/bi-weekly service"
    
    def _get_service_frequency(self, settlement_type, density):
        """Recommend service frequency based on settlement type"""
        if settlement_type == 'informal':
            return "3-4 times per week (higher organic waste generation and limited storage)"
        else:
            return "2-3 times per week (standard residential service)"
    
    def _get_equipment_recommendations(self, settlement_type, density):
        """Recommend equipment based on settlement characteristics"""
        if settlement_type == 'informal':
            return [
                "Small collection vehicles for narrow roads",
                "Handcarts for difficult access areas",
                "Small containers (20-50L) for households",
                "Motorcycle/tricycle collection units"
            ]
        else:
            return [
                "Standard collection trucks",
                "Wheeled bins (120-240L)",
                "Bulk containers for apartments",
                "Compactor trucks for efficiency"
            ]
    
    def _get_access_considerations(self, settlement_type):
        """Get access considerations for different settlement types"""
        if settlement_type == 'informal':
            return [
                "Narrow, unpaved roads requiring smaller vehicles",
                "Limited vehicle access requiring walking collection",
                "Irregular plot layouts requiring flexible routing",
                "Potential security considerations for collectors"
            ]
        else:
            return [
                "Standard road access for collection vehicles",
                "Planned road network allows efficient routing",
                "Adequate space for container placement",
                "Good visibility and safety for operations"
            ]
    
    def _get_engagement_strategy(self, settlement_type):
        """Get community engagement strategy"""
        if settlement_type == 'informal':
            return [
                "Work with community leaders and local organizations",
                "Flexible payment options and subsidized services",
                "Education on waste separation and reduction",
                "Community-based waste management initiatives"
            ]
        else:
            return [
                "Standard service agreements and billing",
                "Waste separation education and incentives",
                "Regular feedback and service optimization",
                "Environmental awareness programs"
            ]

    def analyze_multitemporal_building_detection(self, zone, years=[2022, 2023]):
        """Perform multi-temporal building detection analysis for enhanced accuracy"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Run comprehensive multi-temporal analysis
            results = self.earth_engine.analyze_multitemporal_building_detection(zone, years)
            
            if results.get('error'):
                return results
            
            # Extract key metrics for waste analysis
            analysis_summary = {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'analysis_years': years,
                'building_detection_accuracy': self._assess_building_detection_accuracy(results),
                'vegetation_filtering_effectiveness': self._extract_vegetation_filtering_metrics(results),
                'temporal_stability_assessment': self._extract_stability_metrics(results),
                'recommended_detection_approach': self._recommend_detection_approach(results),
                'waste_estimation_adjustments': self._calculate_waste_adjustments(results)
            }
            
            # Add cross-year urbanization impact
            if 'cross_year_analysis' in results:
                cross_year = results['cross_year_analysis']
                analysis_summary['urbanization_impact'] = {
                    'trend': cross_year.get('urbanization_trend', 'Stable'),
                    'building_area_change': cross_year.get('building_area_change_percent', 0),
                    'waste_generation_impact': self._estimate_urbanization_waste_impact(cross_year)
                }
            
            # Combine with standard analysis
            analysis_summary['full_analysis'] = results
            
            return analysis_summary
            
        except Exception as e:
            return {"error": f"Multi-temporal analysis failed: {str(e)}"}
    
    def get_enhanced_building_population_estimate(self, zone, use_multitemporal=True):
        """Get enhanced population estimates using multi-temporal building analysis"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get standard building analysis
            buildings_data = self.earth_engine.extract_buildings_for_zone(zone)
            settlement_classification = self.earth_engine.classify_buildings_by_context(zone, buildings_data)
            
            base_population = self._calculate_building_based_population(zone, buildings_data, settlement_classification)
            
            # If multi-temporal analysis is requested and available
            enhanced_estimate = base_population.copy()
            
            if use_multitemporal and not buildings_data.get('error'):
                # Apply multi-temporal corrections
                multitemporal_results = self.analyze_multitemporal_building_detection(zone)
                
                if not multitemporal_results.get('error'):
                    # Get vegetation filtering effectiveness
                    latest_year = max(multitemporal_results.get('analysis_years', [2023]))
                    year_data = multitemporal_results.get('full_analysis', {}).get('multi_temporal_analysis', {}).get(str(latest_year), {})
                    
                    vegetation_filtering = year_data.get('vegetation_filtering', {})
                    building_percentage = vegetation_filtering.get('potential_building_percentage', 0)
                    vegetation_percentage = vegetation_filtering.get('vegetation_percentage', 0)
                    
                    # Adjust population estimate based on vegetation filtering
                    if building_percentage > 0:
                        # Apply confidence adjustment based on vegetation filtering effectiveness
                        confidence_multiplier = min(1.0, (building_percentage + 50) / 100)  # Baseline confidence adjustment
                        
                        if base_population.get('estimated_population'):
                            enhanced_estimate['estimated_population'] = round(
                                base_population['estimated_population'] * confidence_multiplier
                            )
                            enhanced_estimate['confidence_adjustment'] = confidence_multiplier
                            enhanced_estimate['vegetation_filtered'] = True
                            enhanced_estimate['vegetation_percentage'] = vegetation_percentage
                            enhanced_estimate['building_area_percentage'] = building_percentage
                    
                    # Add temporal stability confidence
                    stability_data = year_data.get('temporal_stability', {})
                    stability_interpretation = stability_data.get('stability_interpretation', {})
                    building_likelihood = stability_interpretation.get('building_likelihood', 'Medium')
                    
                    enhanced_estimate['temporal_stability_confidence'] = building_likelihood
                    enhanced_estimate['multitemporal_analysis_applied'] = True
            
            return enhanced_estimate
            
        except Exception as e:
            return {"error": f"Enhanced population estimation failed: {str(e)}"}
    
    def get_seasonal_waste_variations(self, zone, year=2023):
        """Analyze seasonal variations in waste generation using NDVI patterns"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            import ee
            zone_geometry = ee.Geometry(zone.geojson['geometry'])
            
            # Get seasonal composites
            seasonal_data = self.earth_engine.generate_seasonal_composites(zone_geometry, year)
            
            if seasonal_data.get('error'):
                return seasonal_data
            
            # Extract seasonal patterns for waste estimation
            wet_season = seasonal_data.get('wet_season', {})
            dry_season = seasonal_data.get('dry_season', {})
            seasonal_diff = seasonal_data.get('seasonal_difference', {})
            
            # Base waste generation rate
            base_waste_rate = self.WASTE_GENERATION_RATES['residential']['per_person']
            
            # Calculate seasonal adjustments based on NDVI patterns
            # High NDVI areas typically have more organic waste during wet season
            wet_ndvi_mean = wet_season.get('ndvi_stats', {}).get('wet_ndvi_mean', 0.3)
            dry_ndvi_mean = dry_season.get('ndvi_stats', {}).get('dry_ndvi_mean', 0.2)
            
            # Seasonal waste multipliers (empirical factors for Lusaka)
            wet_season_multiplier = 1.0 + min(0.3, wet_ndvi_mean * 0.5)  # More organic waste
            dry_season_multiplier = 1.0 - min(0.2, (0.5 - dry_ndvi_mean) * 0.4)  # Less organic waste
            
            return {
                'zone_id': zone.id,
                'analysis_year': year,
                'base_waste_rate_kg_person_day': base_waste_rate,
                'seasonal_variations': {
                    'wet_season': {
                        'period': wet_season.get('period', 'Nov-Apr'),
                        'waste_multiplier': round(wet_season_multiplier, 3),
                        'adjusted_rate_kg_person_day': round(base_waste_rate * wet_season_multiplier, 3),
                        'ndvi_mean': round(wet_ndvi_mean, 3),
                        'characteristics': "Higher organic waste from vegetation, increased food preparation"
                    },
                    'dry_season': {
                        'period': dry_season.get('period', 'May-Oct'),
                        'waste_multiplier': round(dry_season_multiplier, 3),
                        'adjusted_rate_kg_person_day': round(base_waste_rate * dry_season_multiplier, 3),
                        'ndvi_mean': round(dry_ndvi_mean, 3),
                        'characteristics': "Lower organic waste, increased dust and construction debris"
                    }
                },
                'seasonal_difference_magnitude': abs(wet_season_multiplier - dry_season_multiplier),
                'vegetation_impact_assessment': seasonal_diff.get('interpretation', 'Unknown'),
                'recommended_collection_adjustments': self._get_seasonal_collection_recommendations(
                    wet_season_multiplier, dry_season_multiplier
                )
            }
            
        except Exception as e:
            return {"error": f"Seasonal waste variation analysis failed: {str(e)}"}
    
    def _assess_building_detection_accuracy(self, multitemporal_results):
        """Assess building detection accuracy from multi-temporal analysis"""
        try:
            # Extract key accuracy indicators
            recommendations = multitemporal_results.get('building_detection_recommendations', [])
            
            accuracy_score = 0.7  # Base score
            
            # Boost accuracy based on recommendations
            for rec in recommendations:
                if 'high vegetation' in rec.lower() and 'filtering' in rec.lower():
                    accuracy_score += 0.1
                if 'high temporal stability' in rec.lower():
                    accuracy_score += 0.15
                if 'excellent' in rec.lower():
                    accuracy_score += 0.05
            
            # Get latest year vegetation filtering effectiveness
            years = list(multitemporal_results.get('multi_temporal_analysis', {}).keys())
            if years:
                latest_year = max(years)
                latest_data = multitemporal_results['multi_temporal_analysis'][latest_year]
                
                veg_filter = latest_data.get('vegetation_filtering', {})
                effectiveness = veg_filter.get('mask_effectiveness', {})
                
                if effectiveness.get('vegetation_detection') == 'Excellent':
                    accuracy_score += 0.1
                elif effectiveness.get('vegetation_detection') == 'Good':
                    accuracy_score += 0.05
            
            return {
                'estimated_accuracy_percent': min(95, round(accuracy_score * 100, 1)),
                'confidence_level': 'High' if accuracy_score > 0.85 else 'Medium' if accuracy_score > 0.75 else 'Low',
                'accuracy_factors': recommendations
            }
            
        except:
            return {'estimated_accuracy_percent': 75, 'confidence_level': 'Medium'}
    
    def _extract_vegetation_filtering_metrics(self, multitemporal_results):
        """Extract vegetation filtering effectiveness metrics"""
        try:
            years = list(multitemporal_results.get('multi_temporal_analysis', {}).keys())
            if not years:
                return {}
            
            latest_year = max(years)
            latest_data = multitemporal_results['multi_temporal_analysis'][latest_year]
            veg_filter = latest_data.get('vegetation_filtering', {})
            
            return {
                'vegetation_percentage': veg_filter.get('vegetation_percentage', 0),
                'building_area_percentage': veg_filter.get('potential_building_percentage', 0),
                'mask_effectiveness': veg_filter.get('mask_effectiveness', {}),
                'ndvi_threshold_used': veg_filter.get('ndvi_threshold', 0.2)
            }
            
        except:
            return {}
    
    def _extract_stability_metrics(self, multitemporal_results):
        """Extract temporal stability assessment metrics"""
        try:
            years = list(multitemporal_results.get('multi_temporal_analysis', {}).keys())
            if not years:
                return {}
            
            latest_year = max(years)
            latest_data = multitemporal_results['multi_temporal_analysis'][latest_year]
            stability = latest_data.get('temporal_stability', {})
            
            return {
                'stability_level': stability.get('stability_interpretation', {}).get('stability_level', 'Unknown'),
                'building_likelihood': stability.get('stability_interpretation', {}).get('building_likelihood', 'Unknown'),
                'quarters_analyzed': stability.get('quarters_analyzed', 0)
            }
            
        except:
            return {}
    
    def _recommend_detection_approach(self, multitemporal_results):
        """Recommend optimal building detection approach based on analysis"""
        try:
            accuracy = self._assess_building_detection_accuracy(multitemporal_results)
            vegetation_metrics = self._extract_vegetation_filtering_metrics(multitemporal_results)
            stability_metrics = self._extract_stability_metrics(multitemporal_results)
            
            # Determine approach based on conditions
            if accuracy.get('estimated_accuracy_percent', 0) > 90:
                approach = "Multi-temporal with seasonal filtering (optimal accuracy)"
            elif vegetation_metrics.get('vegetation_percentage', 0) > 50:
                approach = "Seasonal NDVI filtering essential (high vegetation area)"
            elif stability_metrics.get('building_likelihood') == 'High':
                approach = "Temporal stability analysis with Google Open Buildings"
            else:
                approach = "Standard Google Open Buildings with confidence filtering"
            
            return {
                'recommended_approach': approach,
                'accuracy_level': accuracy.get('confidence_level', 'Medium'),
                'special_considerations': self._get_special_considerations(
                    vegetation_metrics, stability_metrics
                )
            }
            
        except:
            return {'recommended_approach': 'Standard Google Open Buildings', 'accuracy_level': 'Medium'}
    
    def _calculate_waste_adjustments(self, multitemporal_results):
        """Calculate waste estimation adjustments based on multi-temporal analysis"""
        try:
            vegetation_metrics = self._extract_vegetation_filtering_metrics(multitemporal_results)
            
            # Base adjustment factor
            adjustment_factor = 1.0
            
            # Adjust based on vegetation filtering effectiveness
            veg_percentage = vegetation_metrics.get('vegetation_percentage', 0)
            building_percentage = vegetation_metrics.get('building_area_percentage', 0)
            
            if veg_percentage > 60:  # High vegetation area
                # Reduce base waste rate as some area is non-residential
                adjustment_factor *= 0.9
            elif building_percentage > 80:  # Dense building area
                # Increase waste rate for dense urban areas
                adjustment_factor *= 1.1
            
            return {
                'adjustment_factor': round(adjustment_factor, 3),
                'reasoning': f"Based on {veg_percentage}% vegetation, {building_percentage}% building coverage",
                'waste_rate_multiplier': adjustment_factor
            }
            
        except:
            return {'adjustment_factor': 1.0, 'reasoning': 'Standard rate applied'}
    
    def _estimate_urbanization_waste_impact(self, cross_year_analysis):
        """Estimate waste generation impact from urbanization trends"""
        try:
            trend = cross_year_analysis.get('urbanization_trend', '')
            building_change = cross_year_analysis.get('building_area_change_percent', 0)
            
            # Estimate waste impact
            if 'rapid urbanization' in trend.lower():
                waste_impact = building_change * 1.5  # Rapid growth increases waste disproportionately
            elif 'moderate urbanization' in trend.lower():
                waste_impact = building_change * 1.2
            elif 'slow' in trend.lower():
                waste_impact = building_change
            else:
                waste_impact = 0
            
            return {
                'estimated_waste_increase_percent': round(waste_impact, 2),
                'impact_level': 'High' if abs(waste_impact) > 5 else 'Medium' if abs(waste_impact) > 2 else 'Low',
                'recommendation': self._get_urbanization_waste_recommendation(waste_impact)
            }
            
        except:
            return {'estimated_waste_increase_percent': 0, 'impact_level': 'Unknown'}
    
    def _get_seasonal_collection_recommendations(self, wet_multiplier, dry_multiplier):
        """Get seasonal waste collection recommendations"""
        difference = abs(wet_multiplier - dry_multiplier)
        
        if difference > 0.2:
            return [
                f"Increase collection frequency by 25% during wet season",
                f"Optimize organic waste collection during wet season",
                f"Adjust container capacity based on seasonal patterns"
            ]
        elif difference > 0.1:
            return [
                f"Minor seasonal adjustments recommended",
                f"Monitor organic waste levels during transitions"
            ]
        else:
            return ["Minimal seasonal variation - maintain standard schedule"]
    
    def _get_special_considerations(self, vegetation_metrics, stability_metrics):
        """Get special considerations for building detection"""
        considerations = []
        
        veg_percentage = vegetation_metrics.get('vegetation_percentage', 0)
        if veg_percentage > 70:
            considerations.append("Very high vegetation - use multiple years for validation")
        
        building_likelihood = stability_metrics.get('building_likelihood', '')
        if building_likelihood == 'Low':
            considerations.append("Low temporal stability - verify with additional data sources")
        
        if not considerations:
            considerations.append("Standard detection protocols appropriate")
        
        return considerations
    
    def _get_urbanization_waste_recommendation(self, waste_impact):
        """Get waste management recommendations based on urbanization impact"""
        if waste_impact > 10:
            return "Significant capacity expansion needed - plan for 50% increase in 2 years"
        elif waste_impact > 5:
            return "Moderate expansion needed - increase capacity by 25% within 1 year"
        elif waste_impact > 0:
            return "Monitor growth trends - prepare for gradual capacity increases"
        else:
            return "Stable waste generation expected - maintain current capacity"

    def integrate_worldpop_validation(self, zone, year=2020):
        """Integrate WorldPop data for population validation and enhancement"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get WorldPop population estimate for zone
            worldpop_data = self.earth_engine.extract_population_for_zone(zone, year)
            
            if worldpop_data.get('error'):
                return worldpop_data
            
            # Get building-based population estimate
            buildings_data = self.earth_engine.extract_buildings_for_zone(zone)
            settlement_classification = self.earth_engine.classify_buildings_by_context(zone, buildings_data)
            building_population = self._calculate_building_based_population(zone, buildings_data, settlement_classification)
            
            # Validate building estimate against WorldPop
            if not building_population.get('error'):
                validation_results = self.earth_engine.validate_building_population_with_worldpop(
                    zone, building_population, year
                )
                
                # Create enhanced population estimate
                enhanced_estimate = self._create_enhanced_population_estimate(
                    worldpop_data, building_population, validation_results
                )
                
                return {
                    'zone_id': zone.id,
                    'zone_name': zone.name,
                    'worldpop_data': worldpop_data,
                    'building_estimate': building_population,
                    'validation_results': validation_results,
                    'enhanced_estimate': enhanced_estimate,
                    'waste_estimation_impact': self._calculate_waste_impact_from_validation(
                        validation_results, enhanced_estimate
                    )
                }
            else:
                return {
                    'zone_id': zone.id,
                    'worldpop_data': worldpop_data,
                    'building_estimate_error': building_population.get('error'),
                    'enhanced_estimate': {
                        'estimated_population': worldpop_data['total_population'],
                        'data_source': 'WorldPop only',
                        'confidence': 'Medium (no building validation)'
                    }
                }
                
        except Exception as e:
            return {"error": f"WorldPop integration failed: {str(e)}"}
    
    def calculate_worldpop_density_analysis(self, zones, year=2020):
        """Calculate comprehensive population density analysis using WorldPop"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get WorldPop density analysis for all zones
            density_analysis = self.earth_engine.calculate_population_density_worldpop(zones, year)
            
            if density_analysis.get('error'):
                return density_analysis
            
            # Add waste generation implications
            enhanced_results = density_analysis.copy()
            enhanced_results['waste_implications'] = []
            
            for zone_result in density_analysis['zone_results']:
                density = zone_result['density_per_sqkm']
                density_category = zone_result['density_category']
                
                # Calculate waste implications based on density
                waste_implications = self._calculate_density_waste_implications(density, density_category)
                zone_result['waste_implications'] = waste_implications
                enhanced_results['waste_implications'].append({
                    'zone_id': zone_result['zone_id'],
                    'zone_name': zone_result['zone_name'],
                    'implications': waste_implications
                })
            
            # Add overall recommendations
            enhanced_results['overall_recommendations'] = self._generate_density_based_recommendations(
                density_analysis
            )
            
            return enhanced_results
            
        except Exception as e:
            return {"error": f"WorldPop density analysis failed: {str(e)}"}
    
    def optimize_worldpop_caching(self, zones, years=[2020, 2021]):
        """Optimize WorldPop data caching for improved performance"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Create cache system for zones
            cache_results = self.earth_engine.create_worldpop_cache_system(zones, years)
            
            if cache_results.get('error'):
                return cache_results
            
            # Add performance recommendations
            cache_results['performance_recommendations'] = []
            
            if cache_results['operation_time_seconds'] > 60:
                cache_results['performance_recommendations'].append(
                    "Consider reducing the number of zones or years for faster caching"
                )
            
            if len(cache_results.get('errors', [])) > 0:
                cache_results['performance_recommendations'].append(
                    "Some zones had errors - check zone geometries and data availability"
                )
            
            cache_results['performance_recommendations'].append(
                f"Cache is valid for 1 hour - {cache_results['cached_zones']} zones cached successfully"
            )
            
            return cache_results
            
        except Exception as e:
            return {"error": f"Cache optimization failed: {str(e)}"}
    
    def get_worldpop_enhanced_zone_analysis(self, zone, year=2020, include_validation=True):
        """Get comprehensive zone analysis enhanced with WorldPop data"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Get standard zone analysis
            standard_analysis = self.analyze_zone(zone, include_advanced=True)
            
            # Add WorldPop integration
            if include_validation:
                worldpop_integration = self.integrate_worldpop_validation(zone, year)
                
                if not worldpop_integration.get('error'):
                    # Merge WorldPop data into analysis
                    standard_analysis['worldpop_validation'] = worldpop_integration
                    
                    # Use enhanced population estimate for waste calculations
                    enhanced_population = worldpop_integration.get('enhanced_estimate', {}).get('estimated_population')
                    if enhanced_population:
                        # Recalculate waste with enhanced population
                        enhanced_waste = self._recalculate_waste_with_enhanced_population(
                            zone, enhanced_population, standard_analysis
                        )
                        standard_analysis['enhanced_waste_estimation'] = enhanced_waste
                else:
                    standard_analysis['worldpop_validation_error'] = worldpop_integration.get('error')
            
            # Add WorldPop density context
            worldpop_data = self.earth_engine.extract_population_for_zone(zone, year)
            if not worldpop_data.get('error'):
                standard_analysis['worldpop_context'] = {
                    'population_density_per_sqkm': worldpop_data['population_density_per_sqkm'],
                    'density_category': self.earth_engine._categorize_population_density(
                        worldpop_data['population_density_per_sqkm']
                    ),
                    'worldpop_population': worldpop_data['total_population']
                }
            
            return standard_analysis
            
        except Exception as e:
            return {"error": f"Enhanced zone analysis failed: {str(e)}"}
    
    def _create_enhanced_population_estimate(self, worldpop_data, building_estimate, validation_results):
        """Create enhanced population estimate combining WorldPop and building data"""
        try:
            worldpop_pop = worldpop_data['total_population']
            building_pop = building_estimate.get('estimated_population', 0)
            accuracy = validation_results.get('accuracy_percent', 0)
            agreement = validation_results.get('agreement_level', 'Poor')
            
            # Determine weighting based on validation results
            if agreement == "Excellent":
                # High confidence in building estimate
                enhanced_population = building_pop
                confidence = 'High'
                method = 'Building-based (validated by WorldPop)'
            elif agreement == "Good":
                # Blend estimates with slight preference for building
                enhanced_population = (building_pop * 0.7) + (worldpop_pop * 0.3)
                confidence = 'High'
                method = 'Blended (building 70%, WorldPop 30%)'
            elif agreement == "Moderate":
                # Equal weighting
                enhanced_population = (building_pop * 0.5) + (worldpop_pop * 0.5)
                confidence = 'Medium'
                method = 'Blended (equal weighting)'
            else:
                # Poor agreement - prefer WorldPop as it's more validated globally
                enhanced_population = (building_pop * 0.3) + (worldpop_pop * 0.7)
                confidence = 'Medium'
                method = 'Blended (WorldPop 70%, building 30%)'
            
            return {
                'estimated_population': round(enhanced_population),
                'confidence': confidence,
                'method': method,
                'worldpop_contribution': worldpop_pop,
                'building_contribution': building_pop,
                'validation_accuracy': accuracy,
                'agreement_level': agreement
            }
            
        except Exception as e:
            return {
                'estimated_population': worldpop_data['total_population'],
                'confidence': 'Low',
                'method': 'WorldPop fallback',
                'error': str(e)
            }
    
    def _calculate_waste_impact_from_validation(self, validation_results, enhanced_estimate):
        """Calculate waste estimation impact from population validation"""
        try:
            original_building_pop = validation_results.get('building_estimate_population', 0)
            enhanced_pop = enhanced_estimate.get('estimated_population', 0)
            
            if original_building_pop > 0:
                population_adjustment = (enhanced_pop - original_building_pop) / original_building_pop
                waste_adjustment = population_adjustment  # Direct relationship assumed
                
                base_waste_rate = self.WASTE_GENERATION_RATES['residential']['per_person']
                original_waste = original_building_pop * base_waste_rate
                enhanced_waste = enhanced_pop * base_waste_rate
                
                return {
                    'population_adjustment_percent': round(population_adjustment * 100, 2),
                    'waste_adjustment_percent': round(waste_adjustment * 100, 2),
                    'original_waste_kg_day': round(original_waste, 2),
                    'enhanced_waste_kg_day': round(enhanced_waste, 2),
                    'waste_difference_kg_day': round(enhanced_waste - original_waste, 2),
                    'impact_level': self._categorize_waste_impact(abs(waste_adjustment * 100))
                }
            else:
                return {
                    'population_adjustment_percent': 0,
                    'waste_adjustment_percent': 0,
                    'impact_level': 'None'
                }
                
        except Exception as e:
            return {'error': f"Waste impact calculation failed: {str(e)}"}
    
    def _calculate_density_waste_implications(self, density_per_sqkm, density_category):
        """Calculate waste management implications based on population density"""
        implications = {
            'collection_frequency': 'Standard (2-3 times/week)',
            'container_type': 'Standard containers',
            'access_challenges': 'Minimal',
            'cost_efficiency': 'Standard',
            'special_considerations': []
        }
        
        if density_per_sqkm < 500:  # Very Low Density
            implications['collection_frequency'] = 'Reduced (1-2 times/week)'
            implications['container_type'] = 'Large containers or bulk collection'
            implications['cost_efficiency'] = 'Lower (longer routes)'
            implications['special_considerations'] = ['Rural collection challenges', 'Longer travel distances']
            
        elif density_per_sqkm < 2000:  # Low Density
            implications['collection_frequency'] = 'Standard (2 times/week)'
            implications['container_type'] = 'Medium containers'
            implications['cost_efficiency'] = 'Good'
            
        elif density_per_sqkm < 5000:  # Medium Density
            implications['collection_frequency'] = 'Standard (2-3 times/week)'
            implications['container_type'] = 'Standard containers'
            implications['cost_efficiency'] = 'Optimal'
            
        elif density_per_sqkm < 10000:  # High Density
            implications['collection_frequency'] = 'Frequent (3-4 times/week)'
            implications['container_type'] = 'Multiple smaller containers'
            implications['access_challenges'] = 'Moderate (traffic, parking)'
            implications['cost_efficiency'] = 'Good (high waste per route)'
            implications['special_considerations'] = ['Traffic management', 'Peak hour restrictions']
            
        else:  # Very High Density (Informal Settlements)
            implications['collection_frequency'] = 'Very frequent (daily or 5-6 times/week)'
            implications['container_type'] = 'Small containers or door-to-door'
            implications['access_challenges'] = 'High (narrow roads, limited access)'
            implications['cost_efficiency'] = 'Challenging (difficult access)'
            implications['special_considerations'] = [
                'Narrow road access', 'Manual collection required',
                'Community engagement essential', 'Flexible payment systems'
            ]
        
        return implications
    
    def _generate_density_based_recommendations(self, density_analysis):
        """Generate overall recommendations based on density analysis"""
        recommendations = []
        
        zone_results = density_analysis.get('zone_results', [])
        if not zone_results:
            return ["No zone data available for recommendations"]
        
        # Analyze density distribution
        high_density_zones = [z for z in zone_results if z['density_per_sqkm'] > 8000]
        low_density_zones = [z for z in zone_results if z['density_per_sqkm'] < 1000]
        
        if len(high_density_zones) > len(zone_results) * 0.3:
            recommendations.append("High proportion of dense areas - prioritize frequent collection and small vehicle access")
            recommendations.append("Consider door-to-door collection in informal settlements")
        
        if len(low_density_zones) > len(zone_results) * 0.3:
            recommendations.append("Significant rural/suburban areas - optimize routes for longer distances")
            recommendations.append("Consider larger containers or less frequent collection in sparse areas")
        
        # Overall efficiency recommendations
        overall_density = density_analysis.get('overall_density_per_sqkm', 0)
        if overall_density > 5000:
            recommendations.append("High overall density enables efficient waste collection operations")
        elif overall_density < 2000:
            recommendations.append("Lower density requires route optimization for cost efficiency")
        
        recommendations.append(f"Analyzed {len(zone_results)} zones with total population of {density_analysis.get('total_population', 0):,}")
        
        return recommendations
    
    def _recalculate_waste_with_enhanced_population(self, zone, enhanced_population, original_analysis):
        """Recalculate waste generation with enhanced population estimate"""
        try:
            # Get original waste calculation
            original_waste = original_analysis.get('total_waste_kg_day', 0)
            original_population = zone.estimated_population or 0
            
            # Calculate new waste based on enhanced population
            if original_population > 0:
                population_ratio = enhanced_population / original_population
                enhanced_waste = original_waste * population_ratio
            else:
                # Use standard rate if no original population
                base_rate = self.WASTE_GENERATION_RATES['residential']['per_person']
                enhanced_waste = enhanced_population * base_rate
            
            # Recalculate collection requirements
            enhanced_collection = self._calculate_collection_requirements(
                enhanced_waste, zone.collection_frequency_week or 2
            )
            
            # Recalculate revenue
            enhanced_revenue = self._calculate_revenue_projection(zone, {'total_waste_kg_day': enhanced_waste})
            
            return {
                'enhanced_population': enhanced_population,
                'original_population': original_population,
                'population_adjustment_ratio': round(enhanced_population / original_population, 3) if original_population > 0 else 1,
                'enhanced_waste_kg_day': round(enhanced_waste, 2),
                'original_waste_kg_day': round(original_waste, 2),
                'waste_adjustment_kg_day': round(enhanced_waste - original_waste, 2),
                'enhanced_collection_requirements': enhanced_collection,
                'enhanced_revenue_projection': enhanced_revenue
            }
            
        except Exception as e:
            return {'error': f"Enhanced waste calculation failed: {str(e)}"}
    
    def _categorize_waste_impact(self, adjustment_percent):
        """Categorize the impact level of waste estimation adjustments"""
        if adjustment_percent < 5:
            return 'Minimal'
        elif adjustment_percent < 15:
            return 'Low'
        elif adjustment_percent < 30:
            return 'Moderate'
        elif adjustment_percent < 50:
            return 'High'
        else:
            return 'Very High'

    def analyze_building_features_for_waste_estimation(self, zone, year=2023):
        """Analyze comprehensive building features for enhanced waste estimation accuracy"""
        if not self.earth_engine.initialized:
            return {"error": "Earth Engine not initialized"}
        
        try:
            # Extract comprehensive building features
            comprehensive_features = self.earth_engine.extract_comprehensive_building_features(zone, year)
            
            if comprehensive_features.get('error'):
                return comprehensive_features
            
            # Extract key metrics for waste analysis
            waste_relevant_analysis = {
                'zone_id': zone.id,
                'zone_name': zone.name,
                'analysis_year': year,
                'building_count': comprehensive_features.get('building_count', 0),
                'feature_extraction_date': comprehensive_features.get('feature_extraction_date', time.time())
            }
            
            # Process area features for waste estimation
            area_features = comprehensive_features.get('area_features', {})
            if not area_features.get('error'):
                waste_relevant_analysis['building_area_metrics'] = {
                    'total_building_area_sqm': area_features.get('total_building_area_sqm', 0),
                    'mean_building_area_sqm': area_features.get('mean_building_area_sqm', 0),
                    'building_coverage_ratio_percent': area_features.get('building_coverage_ratio_percent', 0),
                    'buildings_per_hectare': area_features.get('buildings_per_hectare', 0),
                    'area_variability_coefficient': area_features.get('area_variability_coefficient', 0)
                }
                
                # Calculate waste generation based on building area
                total_area = area_features.get('total_building_area_sqm', 0)
                waste_relevant_analysis['area_based_waste_estimates'] = self._calculate_area_based_waste(total_area, zone)
            
            # Process height features for floor-based estimation
            height_features = comprehensive_features.get('height_features', {})
            if not height_features.get('error'):
                floor_estimates = height_features.get('floor_estimates', {})
                mean_floors = floor_estimates.get('estimated_mean_floors', 1)
                
                waste_relevant_analysis['height_metrics'] = {
                    'mean_height_m': height_features.get('mean_height_m', 3),
                    'estimated_mean_floors': mean_floors,
                    'single_story_pct': floor_estimates.get('single_story_pct', 70),
                    'multi_story_pct': floor_estimates.get('multi_story_pct', 5)
                }
                
                # Enhanced waste estimation with floor consideration
                if 'building_area_metrics' in waste_relevant_analysis:
                    total_floor_area = waste_relevant_analysis['building_area_metrics']['total_building_area_sqm'] * mean_floors
                    waste_relevant_analysis['floor_based_waste_estimates'] = self._calculate_floor_based_waste(total_floor_area, zone)
            
            # Process settlement classification for waste generation rates
            shape_features = comprehensive_features.get('shape_complexity', {})
            if not shape_features.get('error'):
                settlement_context = shape_features.get('settlement_context', 'mixed')
                complexity_index = shape_features.get('shape_complexity_index', 'Medium')
                
                waste_relevant_analysis['settlement_classification'] = {
                    'settlement_type': settlement_context,
                    'complexity_index': complexity_index,
                    'waste_generation_factor': self._get_settlement_waste_factor(settlement_context)
                }
            
            # Process density metrics for collection planning
            density_features = comprehensive_features.get('density_metrics', {})
            if not density_features.get('error'):
                waste_relevant_analysis['density_analysis'] = {
                    'buildings_per_hectare': density_features.get('buildings_per_hectare', 0),
                    'built_up_ratio_percent': density_features.get('built_up_ratio_percent', 0),
                    'density_category': density_features.get('density_category', 'Unknown'),
                    'collection_complexity_score': self._calculate_collection_complexity(density_features)
                }
            
            # Process derived analytics for population and capacity
            derived_analytics = comprehensive_features.get('derived_analytics', {})
            if derived_analytics and not derived_analytics.get('error'):
                waste_relevant_analysis['capacity_estimates'] = {}
                
                if 'estimated_occupancy_capacity' in derived_analytics:
                    occupancy_capacity = derived_analytics['estimated_occupancy_capacity']
                    waste_relevant_analysis['capacity_estimates']['estimated_population'] = occupancy_capacity
                    waste_relevant_analysis['capacity_estimates']['population_based_waste'] = self._calculate_population_based_waste(occupancy_capacity, zone)
                
                if 'development_intensity' in derived_analytics:
                    development_intensity = derived_analytics['development_intensity']
                    waste_relevant_analysis['capacity_estimates']['development_intensity'] = development_intensity
                    waste_relevant_analysis['capacity_estimates']['intensity_waste_modifier'] = self._get_intensity_waste_modifier(development_intensity)
            
            # Quality assessment for waste estimation reliability
            quality_assessment = comprehensive_features.get('quality_assessment', {})
            if not quality_assessment.get('error'):
                waste_relevant_analysis['reliability_metrics'] = {
                    'overall_quality': quality_assessment.get('overall_quality', 'Unknown'),
                    'overall_score': quality_assessment.get('overall_score', 0),
                    'data_completeness_score': quality_assessment.get('data_completeness_score', 0),
                    'reliability_score': quality_assessment.get('reliability_score', 0),
                    'waste_estimation_confidence': self._calculate_waste_estimation_confidence(quality_assessment)
                }
            
            # Comprehensive waste generation estimate
            waste_relevant_analysis['comprehensive_waste_estimate'] = self._calculate_comprehensive_waste_estimate(waste_relevant_analysis)
            
            # Collection recommendations
            waste_relevant_analysis['collection_recommendations'] = self._generate_collection_recommendations(waste_relevant_analysis)
            
            return waste_relevant_analysis
            
        except Exception as e:
            return {"error": f"Building features waste analysis failed: {str(e)}"}
    
    def _calculate_area_based_waste(self, total_area_sqm, zone):
        """Calculate waste generation based on building area"""
        if total_area_sqm <= 0:
            return {"error": "Invalid building area"}
        
        # Use area-based waste generation rates (kg per m² per day)
        # These are estimated rates for Lusaka context
        area_waste_rates = {
            'residential': 0.15,  # kg/m²/day
            'commercial': 0.25,   # kg/m²/day
            'mixed': 0.18        # kg/m²/day
        }
        
        zone_type = getattr(zone, 'zone_type', 'mixed')
        if hasattr(zone, 'zone_type') and zone.zone_type:
            if zone.zone_type in ['residential', 'high_density_residential', 'low_density_residential']:
                rate = area_waste_rates['residential']
            elif zone.zone_type in ['commercial', 'industrial']:
                rate = area_waste_rates['commercial']
            else:
                rate = area_waste_rates['mixed']
        else:
            rate = area_waste_rates['mixed']
        
        daily_waste_kg = total_area_sqm * rate
        
        return {
            'daily_waste_kg': round(daily_waste_kg, 2),
            'weekly_waste_kg': round(daily_waste_kg * 7, 2),
            'monthly_waste_kg': round(daily_waste_kg * 30, 2),
            'waste_rate_per_sqm': rate,
            'estimation_method': 'Area-based calculation'
        }
    
    def _calculate_floor_based_waste(self, total_floor_area_sqm, zone):
        """Calculate waste generation based on total floor area"""
        if total_floor_area_sqm <= 0:
            return {"error": "Invalid floor area"}
        
        # Enhanced rates considering floor area utilization
        floor_area_rates = {
            'residential': 0.12,  # kg/m²/day (slightly lower as floors may not be fully utilized)
            'commercial': 0.22,   # kg/m²/day
            'mixed': 0.15
        }
        
        zone_type = getattr(zone, 'zone_type', 'mixed')
        if hasattr(zone, 'zone_type') and zone.zone_type:
            if zone.zone_type in ['residential', 'high_density_residential', 'low_density_residential']:
                rate = floor_area_rates['residential']
            elif zone.zone_type in ['commercial', 'industrial']:
                rate = floor_area_rates['commercial']
            else:
                rate = floor_area_rates['mixed']
        else:
            rate = floor_area_rates['mixed']
        
        daily_waste_kg = total_floor_area_sqm * rate
        
        return {
            'daily_waste_kg': round(daily_waste_kg, 2),
            'weekly_waste_kg': round(daily_waste_kg * 7, 2),
            'monthly_waste_kg': round(daily_waste_kg * 30, 2),
            'waste_rate_per_floor_sqm': rate,
            'estimation_method': 'Floor area-based calculation'
        }
    
    def _calculate_population_based_waste(self, estimated_population, zone):
        """Calculate waste generation based on estimated population"""
        if estimated_population <= 0:
            return {"error": "Invalid population estimate"}
        
        # Population-based waste generation rates (kg per person per day)
        # Based on Lusaka context from analysis.md
        population_waste_rates = {
                                            'formal': 0.5,    # kg/person/day
                'informal': 0.5,  # kg/person/day (standard rate)
                'mixed': 0.5      # kg/person/day (standard rate)
        }
        
        # Determine settlement type if available
        zone_type = getattr(zone, 'zone_type', 'mixed')
        if hasattr(zone, 'zone_type') and zone.zone_type:
            if 'high_density' in zone.zone_type or 'informal' in zone.zone_type:
                rate = population_waste_rates['informal']
            elif 'low_density' in zone.zone_type or 'formal' in zone.zone_type:
                rate = population_waste_rates['formal']
            else:
                rate = population_waste_rates['mixed']
        else:
            rate = population_waste_rates['mixed']
        
        daily_waste_kg = estimated_population * rate
        
        return {
            'daily_waste_kg': round(daily_waste_kg, 2),
            'weekly_waste_kg': round(daily_waste_kg * 7, 2),
            'monthly_waste_kg': round(daily_waste_kg * 30, 2),
            'waste_rate_per_person': rate,
            'estimated_population': estimated_population,
            'estimation_method': 'Population-based calculation'
        }
    
    def _get_settlement_waste_factor(self, settlement_context):
        """Get waste generation factor based on settlement type"""
        factors = {
            'formal': 1.1,     # Higher consumption, more waste
            'informal': 0.8,   # Lower consumption, less waste
            'mixed': 1.0       # Average factor
        }
        return factors.get(settlement_context, 1.0)
    
    def _calculate_collection_complexity(self, density_features):
        """Calculate collection complexity score based on density metrics"""
        buildings_per_hectare = density_features.get('buildings_per_hectare', 0)
        built_up_ratio = density_features.get('built_up_ratio_percent', 0)
        density_category = density_features.get('density_category', 'Medium Density')
        
        # Base complexity score
        complexity_score = 0.5
        
        # Adjust based on building density
        if buildings_per_hectare > 50:
            complexity_score += 0.3  # High density = more complex
        elif buildings_per_hectare > 25:
            complexity_score += 0.2
        elif buildings_per_hectare < 10:
            complexity_score -= 0.1  # Low density = easier collection
        
        # Adjust based on built-up ratio
        if built_up_ratio > 40:
            complexity_score += 0.2  # High built-up ratio = access challenges
        elif built_up_ratio < 15:
            complexity_score -= 0.1  # Low built-up ratio = easier access
        
        # Density category adjustments
        if 'Very High' in density_category:
            complexity_score += 0.2
        elif 'Very Low' in density_category:
            complexity_score -= 0.2
        
        return round(max(0, min(1, complexity_score)), 3)
    
    def _get_intensity_waste_modifier(self, development_intensity):
        """Get waste modifier based on development intensity"""
        modifiers = {
            'Very High Intensity': 1.3,
            'High Intensity': 1.2,
            'Medium Intensity': 1.0,
            'Low Intensity': 0.8,
            'Very Low Intensity': 0.6
        }
        return modifiers.get(development_intensity, 1.0)
    
    def _calculate_waste_estimation_confidence(self, quality_assessment):
        """Calculate confidence level for waste estimation"""
        overall_score = quality_assessment.get('overall_score', 0)
        reliability_score = quality_assessment.get('reliability_score', 0)
        
        # Combined confidence score
        confidence_score = (overall_score + reliability_score) / 2
        
        if confidence_score >= 80:
            return 'High'
        elif confidence_score >= 60:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_comprehensive_waste_estimate(self, waste_analysis):
        """Calculate final comprehensive waste estimate using all available methods"""
        estimates = []
        weights = []
        
        # Area-based estimate
        area_estimate = waste_analysis.get('area_based_waste_estimates')
        if area_estimate and not area_estimate.get('error'):
            estimates.append(area_estimate['daily_waste_kg'])
            weights.append(0.3)  # 30% weight
        
        # Floor-based estimate
        floor_estimate = waste_analysis.get('floor_based_waste_estimates')
        if floor_estimate and not floor_estimate.get('error'):
            estimates.append(floor_estimate['daily_waste_kg'])
            weights.append(0.4)  # 40% weight (more accurate)
        
        # Population-based estimate
        capacity_estimates = waste_analysis.get('capacity_estimates', {})
        pop_estimate = capacity_estimates.get('population_based_waste')
        if pop_estimate and not pop_estimate.get('error'):
            estimates.append(pop_estimate['daily_waste_kg'])
            weights.append(0.3)  # 30% weight
        
        if not estimates:
            return {"error": "No valid waste estimates available"}
        
        # Calculate weighted average
        if len(estimates) == 1:
            final_estimate = estimates[0]
            estimation_method = "Single method available"
        else:
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            final_estimate = sum(est * weight for est, weight in zip(estimates, normalized_weights))
            estimation_method = f"Weighted average of {len(estimates)} methods"
        
        # Apply settlement and intensity modifiers
        settlement_classification = waste_analysis.get('settlement_classification', {})
        settlement_factor = settlement_classification.get('waste_generation_factor', 1.0)
        
        capacity_estimates = waste_analysis.get('capacity_estimates', {})
        intensity_modifier = capacity_estimates.get('intensity_waste_modifier', 1.0)
        
        final_estimate = final_estimate * settlement_factor * intensity_modifier
        
        return {
            'daily_waste_kg': round(final_estimate, 2),
            'weekly_waste_kg': round(final_estimate * 7, 2),
            'monthly_waste_kg': round(final_estimate * 30, 2),
            'annual_waste_kg': round(final_estimate * 365, 2),
            'estimation_method': estimation_method,
            'methods_used': len(estimates),
            'settlement_factor': settlement_factor,
            'intensity_modifier': intensity_modifier,
            'confidence_level': waste_analysis.get('reliability_metrics', {}).get('waste_estimation_confidence', 'Medium')
        }
    
    def _generate_collection_recommendations(self, waste_analysis):
        """Generate waste collection recommendations based on analysis"""
        recommendations = []
        
        # Density-based recommendations
        density_analysis = waste_analysis.get('density_analysis', {})
        if density_analysis:
            complexity_score = density_analysis.get('collection_complexity_score', 0.5)
            density_category = density_analysis.get('density_category', 'Medium Density')
            
            if complexity_score > 0.7:
                recommendations.append("High collection complexity - consider smaller vehicles and more frequent collection")
            elif complexity_score < 0.3:
                recommendations.append("Low collection complexity - larger vehicles can be used efficiently")
            
            if 'Very High' in density_category:
                recommendations.append("Very high density area - daily collection recommended")
            elif 'High' in density_category:
                recommendations.append("High density area - collection every 2-3 days recommended")
        
        # Settlement type recommendations
        settlement_classification = waste_analysis.get('settlement_classification', {})
        if settlement_classification:
            settlement_type = settlement_classification.get('settlement_type', 'mixed')
            
            if settlement_type == 'informal':
                recommendations.append("Informal settlement - consider community collection points and awareness programs")
            elif settlement_type == 'formal':
                recommendations.append("Formal settlement - standard door-to-door collection is suitable")
        
        # Volume-based recommendations
        comprehensive_estimate = waste_analysis.get('comprehensive_waste_estimate', {})
        if comprehensive_estimate and not comprehensive_estimate.get('error'):
            daily_waste = comprehensive_estimate.get('daily_waste_kg', 0)
            
            if daily_waste > 1000:
                recommendations.append("High waste volume - consider dedicated collection route")
            elif daily_waste < 100:
                recommendations.append("Low waste volume - can be combined with neighboring areas")
        
        # Quality-based recommendations
        reliability_metrics = waste_analysis.get('reliability_metrics', {})
        if reliability_metrics:
            confidence = reliability_metrics.get('waste_estimation_confidence', 'Medium')
            
            if confidence == 'Low':
                recommendations.append("Low estimation confidence - recommend ground survey for validation")
            elif confidence == 'High':
                recommendations.append("High estimation confidence - data suitable for route planning")
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("Standard waste collection protocols recommended - monitor and adjust based on actual collection data")
        
        return recommendations
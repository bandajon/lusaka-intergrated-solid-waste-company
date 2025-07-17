#!/usr/bin/env python3
"""
Demo Smart Population Estimation with Mock Data
Demonstrates the smart estimation feature with controlled scenarios
"""

import sys
import os
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType, AnalysisResult
from app.analytics.config import AnalyticsConfig
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUnifiedAnalyzer(UnifiedAnalyzer):
    """Mock analyzer to simulate specific scenarios"""
    
    def __init__(self, mock_satellite_population=None, mock_building_count=None):
        super().__init__()
        self.mock_satellite_population = mock_satellite_population
        self.mock_building_count = mock_building_count
    
    def _analyze_population(self, request: AnalysisRequest, result: AnalysisResult) -> AnalysisResult:
        """Override to simulate specific scenarios"""
        
        # Simulate satellite data
        if self.mock_satellite_population is not None:
            satellite_population = self.mock_satellite_population
            satellite_success = True
            
            result.population_estimate = satellite_population
            result.household_estimate = int(satellite_population / 4.6)
            result.population_density = 2500
            result.confidence_level = 0.90
            result.data_sources = ['Mocked Satellite Data']
            
            logger.info(f"✅ Mocked satellite population estimate: {satellite_population} people")
        else:
            # Fall back to real analysis
            return super()._analyze_population(request, result)
        
        # Simulate building count
        if self.mock_building_count is not None:
            building_count = self.mock_building_count
            result.building_count = building_count
            result.building_types = {'residential': int(building_count * 0.8), 'commercial': int(building_count * 0.2)}
            result.settlement_classification = 'informal_high_density'
            
            logger.info(f"✅ Mocked building count: {building_count} buildings")
        else:
            building_count = 0
        
        # Apply smart validation logic (copied from parent class)
        if building_count > 0 and satellite_success:
            from app.analytics.config import AnalyticsConfig
            
            user_classification = {
                'settlement_density': request.options.get('settlement_density', 'medium_density'),
                'socioeconomic_level': request.options.get('socioeconomic_level', 'middle_income'),
                'average_household_charge': request.options.get('average_household_charge'),
                'waste_generation_rate': request.options.get('waste_generation_rate')
            }
            
            if AnalyticsConfig.is_smart_estimation_enabled():
                threshold_multiplier = AnalyticsConfig.get_building_threshold_multiplier()
                high_density_multiplier = AnalyticsConfig.get_high_density_multiplier()
                medium_low_density_multiplier = AnalyticsConfig.get_medium_low_density_multiplier()
                smart_confidence = AnalyticsConfig.get_smart_estimation_confidence()
                
                # Extract zone classification
                settlement_density = user_classification.get('settlement_density', 'medium_density')
                zone_type = request.zone_type or request.options.get('zone_type', 'mixed_use')
                
                is_high_density = settlement_density == 'high_density'
                is_medium_low_density_residential = (
                    settlement_density in ['medium_density', 'low_density'] and 
                    zone_type.lower() in ['residential', 'mixed_use']
                )
                
                building_threshold = building_count * threshold_multiplier
                
                logger.info(f"Smart validation: satellite={satellite_population}, building_threshold={building_threshold:.0f} (buildings={building_count}×{threshold_multiplier})")
                logger.info(f"Zone classification: density={settlement_density}, type={zone_type}, high_density={is_high_density}, medium_low_residential={is_medium_low_density_residential}")
                
                conditions_met = (
                    satellite_population < building_threshold and 
                    (is_high_density or is_medium_low_density_residential)
                )
                
                if conditions_met:
                    # Apply appropriate smart estimation based on density and zone type
                    if is_high_density:
                        smart_population = int(building_count * high_density_multiplier)
                        multiplier_used = high_density_multiplier
                        adjustment_reason = 'High-density area with satellite underestimation'
                    else:  # medium/low density residential
                        smart_population = int(building_count * medium_low_density_multiplier)
                        multiplier_used = medium_low_density_multiplier
                        adjustment_reason = f'Medium/low density residential area ({settlement_density}) with satellite underestimation'
                    
                    # Store original estimates for reference
                    if not hasattr(result, 'validation_metrics') or result.validation_metrics is None:
                        result.validation_metrics = {}
                    
                    result.validation_metrics.update({
                        'smart_estimation_applied': True,
                        'original_satellite_population': satellite_population,
                        'building_count_used': building_count,
                        'building_threshold': building_threshold,
                        'threshold_multiplier': threshold_multiplier,
                        'smart_multiplier': multiplier_used,
                        'settlement_density': settlement_density,
                        'zone_type': zone_type,
                        'adjustment_reason': adjustment_reason
                    })
                    
                    # Update population estimate
                    result.population_estimate = smart_population
                    result.household_estimate = int(smart_population / 4.6)
                    result.confidence_level = smart_confidence
                    
                    # Update data sources
                    result.data_sources = [source for source in result.data_sources if 'Smart Building-Based Estimation' not in source]
                    result.data_sources.append(f'Smart Building-Based Estimation (×{multiplier_used})')
                    
                    # Add warning about adjustment
                    if not result.warnings:
                        result.warnings = []
                    result.warnings.append(f"Population adjusted from {satellite_population} to {smart_population} based on {building_count} buildings (×{multiplier_used} multiplier for {settlement_density} {zone_type})")
                    
                    logger.info(f"🏢 Smart population adjustment applied: {satellite_population} → {smart_population} people (buildings: {building_count}×{multiplier_used} for {settlement_density} {zone_type})")
                else:
                    # Store validation info
                    if not hasattr(result, 'validation_metrics') or result.validation_metrics is None:
                        result.validation_metrics = {}
                    
                    result.validation_metrics.update({
                        'smart_estimation_applied': False,
                        'satellite_population': satellite_population,
                        'building_count_available': building_count,
                        'building_threshold': building_threshold,
                        'threshold_multiplier': threshold_multiplier,
                        'settlement_density': settlement_density,
                        'zone_type': zone_type,
                        'high_density_area': is_high_density,
                        'medium_low_density_residential': is_medium_low_density_residential,
                        'validation_reason': 'Satellite data appears accurate' if satellite_population >= building_threshold else 'Zone conditions not met for smart estimation'
                    })
        
        return result

def demo_scenario_1():
    """Scenario 1: High-density area where satellite underestimates"""
    logger.info("=" * 60)
    logger.info("SCENARIO 1: High-density area with satellite underestimation")
    logger.info("- 20 buildings detected")
    logger.info("- Satellite says only 50 people")
    logger.info("- Building threshold: 20 × 4.5 = 90 people")
    logger.info("- Should trigger smart estimation: 20 × 10 = 200 people")
    logger.info("=" * 60)
    
    # Mock: 20 buildings, but satellite only reports 50 people
    analyzer = MockUnifiedAnalyzer(mock_satellite_population=50, mock_building_count=20)
    
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [28.2816, -15.3875],
            [28.2820, -15.3875],
            [28.2820, -15.3870],
            [28.2816, -15.3870],
            [28.2816, -15.3875]
        ]]
    }
    
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="scenario_1_high_density",
        options={
            'settlement_density': 'high_density',  # High density area
            'socioeconomic_level': 'low_income'
        }
    )
    
    result = analyzer.analyze(request)
    
    logger.info(f"📊 RESULTS:")
    logger.info(f"  Final population: {result.population_estimate} people")
    logger.info(f"  Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Confidence level: {result.confidence_level:.0%}")
    logger.info(f"  Data sources: {result.data_sources}")
    if result.warnings:
        logger.info(f"  Warnings: {result.warnings}")
    
    if result.validation_metrics and result.validation_metrics.get('smart_estimation_applied'):
        logger.info(f"  ✅ Smart estimation worked! {result.validation_metrics['original_satellite_population']} → {result.population_estimate}")
    
    return result

def demo_scenario_2():
    """Scenario 2: Medium-density residential area (should trigger with ×6 multiplier)"""
    logger.info("=" * 60)
    logger.info("SCENARIO 2: Medium-density residential area")
    logger.info("- 20 buildings detected")
    logger.info("- Satellite says only 50 people")
    logger.info("- Building threshold: 20 × 4.5 = 90 people")
    logger.info("- Should trigger smart estimation: 20 × 6 = 120 people")
    logger.info("=" * 60)
    
    analyzer = MockUnifiedAnalyzer(mock_satellite_population=50, mock_building_count=20)
    
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [28.2816, -15.3875],
            [28.2820, -15.3875],
            [28.2820, -15.3870],
            [28.2816, -15.3870],
            [28.2816, -15.3875]
        ]]
    }
    
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="scenario_2_medium_density_residential",
        zone_type="residential",  # Residential zone
        options={
            'settlement_density': 'medium_density',  # Medium density
            'socioeconomic_level': 'middle_income',
            'zone_type': 'residential'
        }
    )
    
    result = analyzer.analyze(request)
    
    logger.info(f"📊 RESULTS:")
    logger.info(f"  Final population: {result.population_estimate} people")
    logger.info(f"  Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Multiplier used: {result.validation_metrics.get('smart_multiplier') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Expected: 120 people (20 buildings × 6)")
    
    if result.validation_metrics and result.validation_metrics.get('smart_estimation_applied'):
        logger.info(f"  ✅ Smart estimation worked! {result.validation_metrics['original_satellite_population']} → {result.population_estimate}")
    
    return result

def demo_scenario_3():
    """Scenario 3: High-density but satellite data is already good"""
    logger.info("=" * 60)
    logger.info("SCENARIO 3: High-density but satellite data looks accurate")
    logger.info("- 20 buildings detected")
    logger.info("- Satellite says 120 people (higher than threshold)")
    logger.info("- Should NOT apply smart estimation")
    logger.info("=" * 60)
    
    analyzer = MockUnifiedAnalyzer(mock_satellite_population=120, mock_building_count=20)
    
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [28.2816, -15.3875],
            [28.2820, -15.3875],
            [28.2820, -15.3870],
            [28.2816, -15.3870],
            [28.2816, -15.3875]
        ]]
    }
    
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="scenario_3_accurate_satellite",
        options={
            'settlement_density': 'high_density',
            'socioeconomic_level': 'low_income'
        }
    )
    
    result = analyzer.analyze(request)
    
    logger.info(f"📊 RESULTS:")
    logger.info(f"  Final population: {result.population_estimate} people")
    logger.info(f"  Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Should remain at satellite value (120)")
    
    return result

def demo_scenario_4():
    """Scenario 4: Low-density residential area (should trigger with ×6 multiplier)"""
    logger.info("=" * 60)
    logger.info("SCENARIO 4: Low-density residential area")
    logger.info("- 15 buildings detected")
    logger.info("- Satellite says only 40 people")
    logger.info("- Building threshold: 15 × 4.5 = 67.5 people")
    logger.info("- Should trigger smart estimation: 15 × 6 = 90 people")
    logger.info("=" * 60)
    
    analyzer = MockUnifiedAnalyzer(mock_satellite_population=40, mock_building_count=15)
    
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [28.2816, -15.3875],
            [28.2820, -15.3875],
            [28.2820, -15.3870],
            [28.2816, -15.3870],
            [28.2816, -15.3875]
        ]]
    }
    
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="scenario_4_low_density_residential",
        zone_type="residential",  # Residential zone
        options={
            'settlement_density': 'low_density',  # Low density
            'socioeconomic_level': 'high_income',
            'zone_type': 'residential'
        }
    )
    
    result = analyzer.analyze(request)
    
    logger.info(f"📊 RESULTS:")
    logger.info(f"  Final population: {result.population_estimate} people")
    logger.info(f"  Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Multiplier used: {result.validation_metrics.get('smart_multiplier') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Expected: 90 people (15 buildings × 6)")
    
    if result.validation_metrics and result.validation_metrics.get('smart_estimation_applied'):
        logger.info(f"  ✅ Smart estimation worked! {result.validation_metrics['original_satellite_population']} → {result.population_estimate}")
    
    return result

def demo_scenario_5():
    """Scenario 5: Medium-density commercial area (should NOT trigger)"""
    logger.info("=" * 60)
    logger.info("SCENARIO 5: Medium-density commercial area")
    logger.info("- 20 buildings detected")
    logger.info("- Satellite says only 50 people")
    logger.info("- Commercial zone, so should NOT apply smart estimation")
    logger.info("=" * 60)
    
    analyzer = MockUnifiedAnalyzer(mock_satellite_population=50, mock_building_count=20)
    
    test_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [28.2816, -15.3875],
            [28.2820, -15.3875],
            [28.2820, -15.3870],
            [28.2816, -15.3870],
            [28.2816, -15.3875]
        ]]
    }
    
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="scenario_5_medium_density_commercial",
        zone_type="commercial",  # Commercial zone
        options={
            'settlement_density': 'medium_density',  # Medium density
            'socioeconomic_level': 'middle_income',
            'zone_type': 'commercial'
        }
    )
    
    result = analyzer.analyze(request)
    
    logger.info(f"📊 RESULTS:")
    logger.info(f"  Final population: {result.population_estimate} people")
    logger.info(f"  Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  Should remain at satellite value (50)")
    
    return result

def main():
    """Run demonstration scenarios"""
    logger.info("🚀 Smart Population Estimation Demonstration")
    logger.info(f"Current configuration:")
    logger.info(f"  Building threshold multiplier: {AnalyticsConfig.get_building_threshold_multiplier()}")
    logger.info(f"  High density multiplier: {AnalyticsConfig.get_high_density_multiplier()}")
    logger.info(f"  Medium/low density multiplier: {AnalyticsConfig.get_medium_low_density_multiplier()}")
    logger.info(f"  Smart estimation confidence: {AnalyticsConfig.get_smart_estimation_confidence():.0%}")
    logger.info("")
    
    # Run scenarios
    result1 = demo_scenario_1()
    logger.info("")
    
    result2 = demo_scenario_2()
    logger.info("")
    
    result3 = demo_scenario_3()
    logger.info("")
    
    result4 = demo_scenario_4()
    logger.info("")
    
    result5 = demo_scenario_5()
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("📋 SUMMARY")
    logger.info("=" * 60)
    
    scenarios = [
        ("High-density underestimation", result1, True, 13),
        ("Medium-density residential", result2, True, 6),
        ("High-density accurate satellite", result3, False, None),
        ("Low-density residential", result4, True, 6),
        ("Medium-density commercial", result5, False, None)
    ]
    
    for name, result, expected_smart, expected_multiplier in scenarios:
        smart_applied = result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else False
        multiplier_used = result.validation_metrics.get('smart_multiplier') if result.validation_metrics else None
        
        status = "✅" if smart_applied == expected_smart else "❌"
        multiplier_status = ""
        if expected_smart and smart_applied and expected_multiplier:
            multiplier_status = f" (×{multiplier_used})" if multiplier_used == expected_multiplier else f" (×{multiplier_used}, expected ×{expected_multiplier})"
        elif smart_applied and multiplier_used:
            multiplier_status = f" (×{multiplier_used})"
            
        logger.info(f"{status} {name}: {result.population_estimate} people (smart: {smart_applied}){multiplier_status}")
    
    logger.info("=" * 60)
    logger.info("🎉 Extended smart estimation demonstration complete!")
    logger.info("Feature now supports high-density (×13) and medium/low-density residential (×6) areas")

if __name__ == "__main__":
    main()
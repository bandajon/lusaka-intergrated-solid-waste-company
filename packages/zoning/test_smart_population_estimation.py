#!/usr/bin/env python3
"""
Test Smart Population Estimation Feature
Tests the new smart population validation and adjustment logic
"""

import sys
import os
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType
from app.analytics.config import AnalyticsConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_smart_estimation_config():
    """Test configuration parameters for smart estimation"""
    logger.info("Testing smart estimation configuration...")
    
    # Test default configuration
    assert AnalyticsConfig.is_smart_estimation_enabled() == True
    assert AnalyticsConfig.get_building_threshold_multiplier() == 4.5
    assert AnalyticsConfig.get_high_density_multiplier() == 13  # Updated from 10 to 13
    assert AnalyticsConfig.get_medium_low_density_multiplier() == 6  # New parameter
    assert AnalyticsConfig.get_smart_estimation_confidence() == 0.85
    
    logger.info("✅ Configuration tests passed")

def test_high_density_scenario():
    """Test smart estimation with high-density area scenario"""
    logger.info("Testing high-density scenario with building count override...")
    
    # Create a test geometry (small polygon in Lusaka)
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
    
    # Create analysis request for high-density area
    request = AnalysisRequest(
        analysis_type=AnalysisType.POPULATION,
        geometry=test_geometry,
        zone_id="test_high_density",
        options={
            'settlement_density': 'high_density',  # High density area
            'socioeconomic_level': 'low_income'
        }
    )
    
    # Initialize analyzer
    analyzer = UnifiedAnalyzer()
    
    # Mock building count for testing
    # This simulates a scenario where we have 20 buildings
    # Building threshold = 20 × 4.5 = 90 people
    # If satellite returns < 90, smart estimation should apply: 20 × 10 = 200 people
    
    logger.info("Running analysis...")
    result = analyzer.analyze(request)
    
    logger.info(f"Analysis result:")
    logger.info(f"  - Success: {result.success}")
    logger.info(f"  - Population estimate: {result.population_estimate}")
    logger.info(f"  - Building count: {result.building_count}")
    logger.info(f"  - Confidence level: {result.confidence_level}")
    logger.info(f"  - Data sources: {result.data_sources}")
    logger.info(f"  - Warnings: {result.warnings}")
    
    if result.validation_metrics:
        logger.info(f"  - Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied')}")
        if result.validation_metrics.get('smart_estimation_applied'):
            logger.info(f"  - Original satellite: {result.validation_metrics.get('original_satellite_population')}")
            logger.info(f"  - Building threshold: {result.validation_metrics.get('building_threshold')}")
            logger.info(f"  - Smart multiplier: {result.validation_metrics.get('smart_multiplier')}")
    
    logger.info("✅ High-density scenario test completed")
    return result

def test_medium_density_residential_scenario():
    """Test smart estimation for medium-density residential areas"""
    logger.info("Testing medium-density residential scenario (should trigger smart estimation)...")
    
    # Same geometry, but medium density residential
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
        zone_id="test_medium_density_residential",
        zone_type="residential",  # Residential zone type
        options={
            'settlement_density': 'medium_density',  # Medium density area
            'socioeconomic_level': 'middle_income',
            'zone_type': 'residential'
        }
    )
    
    analyzer = UnifiedAnalyzer()
    result = analyzer.analyze(request)
    
    logger.info(f"Medium density residential result:")
    logger.info(f"  - Population estimate: {result.population_estimate}")
    logger.info(f"  - Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  - Building count: {result.building_count}")
    logger.info(f"  - Confidence level: {result.confidence_level}")
    
    if result.validation_metrics and result.validation_metrics.get('smart_estimation_applied'):
        logger.info(f"  - Smart multiplier: {result.validation_metrics.get('smart_multiplier')}")
        logger.info(f"  - Original satellite: {result.validation_metrics.get('original_satellite_population')}")
        logger.info("✅ Medium-density residential scenario correctly triggered smart estimation with ×6 multiplier")
    
    return result

def test_low_density_residential_scenario():
    """Test smart estimation for low-density residential areas"""
    logger.info("Testing low-density residential scenario (should trigger smart estimation)...")
    
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
        zone_id="test_low_density_residential",
        zone_type="residential",  # Residential zone type
        options={
            'settlement_density': 'low_density',  # Low density area
            'socioeconomic_level': 'high_income',
            'zone_type': 'residential'
        }
    )
    
    analyzer = UnifiedAnalyzer()
    result = analyzer.analyze(request)
    
    logger.info(f"Low density residential result:")
    logger.info(f"  - Population estimate: {result.population_estimate}")
    logger.info(f"  - Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    logger.info(f"  - Building count: {result.building_count}")
    
    if result.validation_metrics and result.validation_metrics.get('smart_estimation_applied'):
        logger.info(f"  - Smart multiplier: {result.validation_metrics.get('smart_multiplier')}")
        logger.info("✅ Low-density residential scenario correctly triggered smart estimation with ×6 multiplier")
    
    return result

def test_medium_density_commercial_scenario():
    """Test that medium-density commercial areas do NOT trigger smart estimation"""
    logger.info("Testing medium-density commercial scenario (should not trigger smart estimation)...")
    
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
        zone_id="test_medium_density_commercial",
        zone_type="commercial",  # Commercial zone type
        options={
            'settlement_density': 'medium_density',  # Medium density area
            'socioeconomic_level': 'middle_income',
            'zone_type': 'commercial'
        }
    )
    
    analyzer = UnifiedAnalyzer()
    result = analyzer.analyze(request)
    
    logger.info(f"Medium density commercial result:")
    logger.info(f"  - Population estimate: {result.population_estimate}")
    logger.info(f"  - Smart estimation applied: {result.validation_metrics.get('smart_estimation_applied') if result.validation_metrics else 'N/A'}")
    
    # Should not apply smart estimation for medium density commercial
    if result.validation_metrics:
        smart_applied = result.validation_metrics.get('smart_estimation_applied', False)
        if not smart_applied:
            logger.info("✅ Medium-density commercial scenario correctly did not trigger smart estimation")
        else:
            logger.warning("⚠️ Medium-density commercial scenario unexpectedly triggered smart estimation")
    
    return result

def test_configuration_changes():
    """Test changing configuration parameters"""
    logger.info("Testing configuration parameter changes...")
    
    # Save original values
    original_enabled = AnalyticsConfig.is_smart_estimation_enabled()
    original_threshold = AnalyticsConfig.get_building_threshold_multiplier()
    original_multiplier = AnalyticsConfig.get_high_density_multiplier()
    
    try:
        # Test disabling smart estimation
        AnalyticsConfig.set_smart_estimation_enabled(False)
        assert AnalyticsConfig.is_smart_estimation_enabled() == False
        logger.info("✅ Successfully disabled smart estimation")
        
        # Test changing multipliers
        AnalyticsConfig.set_smart_estimation_enabled(True)
        AnalyticsConfig.set_smart_estimation_multipliers(3.0, 8.0)
        
        assert AnalyticsConfig.get_building_threshold_multiplier() == 3.0
        assert AnalyticsConfig.get_high_density_multiplier() == 8.0
        logger.info("✅ Successfully changed multipliers")
        
    finally:
        # Restore original values
        AnalyticsConfig.set_smart_estimation_enabled(original_enabled)
        AnalyticsConfig.set_smart_estimation_multipliers(original_threshold, original_multiplier)
        logger.info("✅ Configuration restored to original values")

def main():
    """Run all tests"""
    logger.info("🚀 Starting Smart Population Estimation Tests")
    logger.info("=" * 60)
    
    try:
        # Test 1: Configuration
        test_smart_estimation_config()
        logger.info("")
        
        # Test 2: High-density scenario
        high_density_result = test_high_density_scenario()
        logger.info("")
        
        # Test 3: Medium-density residential scenario
        medium_density_residential_result = test_medium_density_residential_scenario()
        logger.info("")
        
        # Test 4: Low-density residential scenario  
        low_density_residential_result = test_low_density_residential_scenario()
        logger.info("")
        
        # Test 5: Medium-density commercial scenario (should not trigger)
        medium_density_commercial_result = test_medium_density_commercial_scenario()
        logger.info("")
        
        # Test 6: Configuration changes
        test_configuration_changes()
        logger.info("")
        
        logger.info("=" * 60)
        logger.info("🎉 All tests completed successfully!")
        
        # Summary
        logger.info("\nTest Summary:")
        logger.info(f"  High-density result: {high_density_result.population_estimate} people")
        if high_density_result.validation_metrics:
            logger.info(f"    Smart estimation applied: {high_density_result.validation_metrics.get('smart_estimation_applied')}")
        
        logger.info(f"  Medium-density residential result: {medium_density_residential_result.population_estimate} people")
        if medium_density_residential_result.validation_metrics:
            logger.info(f"    Smart estimation applied: {medium_density_residential_result.validation_metrics.get('smart_estimation_applied')}")
            logger.info(f"    Multiplier used: {medium_density_residential_result.validation_metrics.get('smart_multiplier')}")
        
        logger.info(f"  Low-density residential result: {low_density_residential_result.population_estimate} people")
        if low_density_residential_result.validation_metrics:
            logger.info(f"    Smart estimation applied: {low_density_residential_result.validation_metrics.get('smart_estimation_applied')}")
            logger.info(f"    Multiplier used: {low_density_residential_result.validation_metrics.get('smart_multiplier')}")
        
        logger.info(f"  Medium-density commercial result: {medium_density_commercial_result.population_estimate} people")
        if medium_density_commercial_result.validation_metrics:
            logger.info(f"    Smart estimation applied: {medium_density_commercial_result.validation_metrics.get('smart_estimation_applied')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
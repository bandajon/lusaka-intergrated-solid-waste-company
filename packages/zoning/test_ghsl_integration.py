#!/usr/bin/env python3
"""
Test script to verify GHSL population integration is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.earth_engine_analysis import EarthEngineAnalyzer
from app.utils.real_time_zone_analyzer import RealTimeZoneAnalyzer
from app.models import Zone

class MockZone:
    """Mock zone for testing"""
    def __init__(self):
        self.id = "test_zone"
        self.name = "Test Zone"
        self.geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.280, -15.385],
                [28.285, -15.385], 
                [28.285, -15.390],
                [28.280, -15.390],
                [28.280, -15.385]
            ]]
        }
        self.area_sqm = 500000  # 0.5 km²
        self.centroid = [28.2825, -15.3875]
        self.analysis_results = {}
    
    @property
    def geojson(self):
        return {
            "type": "Feature",
            "geometry": self.geometry,
            "properties": {
                "id": self.id,
                "name": self.name
            }
        }

def test_ghsl_integration():
    """Test GHSL population integration"""
    print("🧪 Testing GHSL Population Integration")
    print("=" * 50)
    
    # Create mock zone
    mock_zone = MockZone()
    print(f"📍 Test zone: {mock_zone.name}")
    print(f"📏 Area: {mock_zone.area_sqm / 1000000:.2f} km²")
    
    # Test Earth Engine analyzer
    print("\n1️⃣ Testing Earth Engine Analyzer...")
    try:
        analyzer = EarthEngineAnalyzer()
        if analyzer.initialized:
            print("   ✅ Earth Engine initialized successfully")
            
            # Clear cache to ensure fresh results
            print("   🧹 Clearing Earth Engine cache...")
            analyzer.cache.clear()
            
            # Test comprehensive building features (includes GHSL)
            print("   🏗️  Testing comprehensive building features...")
            result = analyzer.extract_comprehensive_building_features(mock_zone, 2025)
            
            if result.get('error'):
                print(f"   ❌ Error: {result['error']}")
            else:
                print("   ✅ Comprehensive analysis completed")
                
                # Check for GHSL population data
                ghsl_pop = result.get('ghsl_population', {})
                if ghsl_pop and not ghsl_pop.get('error'):
                    print(f"   🎯 GHSL Population: {ghsl_pop.get('estimated_population', 0):,.0f}")
                    print(f"   📊 Population Density: {ghsl_pop.get('population_density', 0):.1f} per km²")
                    print(f"   🏘️  Settlement Type: {ghsl_pop.get('settlement_type', 'Unknown')}")
                else:
                    print(f"   ⚠️  GHSL population data not available: {ghsl_pop.get('error', 'No data')}")
                
                # Check for comprehensive waste generation
                waste_gen = result.get('comprehensive_waste_generation', {})
                if waste_gen and not waste_gen.get('error'):
                    print(f"   🗑️  Daily Waste: {waste_gen.get('daily_waste_kg', 0):.1f} kg")
                    print(f"   📅 Weekly Waste: {waste_gen.get('weekly_waste_kg', 0):.1f} kg")
                    print(f"   🌍 Seasonal Factor: {waste_gen.get('seasonal_factor', 1.0):.2f}")
                    print(f"   🏙️  Density Factor: {waste_gen.get('density_factor', 1.0):.2f}")
                else:
                    print(f"   ⚠️  Comprehensive waste generation not available: {waste_gen.get('error', 'No data')}")
                    
        else:
            print("   ❌ Earth Engine not initialized")
            print(f"   ℹ️  Error: {analyzer.auth_error_details}")
            
    except Exception as e:
        print(f"   ❌ Earth Engine test failed: {e}")
    
    # Test Real-Time Zone Analyzer
    print("\n2️⃣ Testing Real-Time Zone Analyzer...")
    try:
        rt_analyzer = RealTimeZoneAnalyzer()
        print("   ✅ Real-time analyzer initialized")
        
        # Test enhanced Earth Engine analysis
        print("   🔍 Testing enhanced Earth Engine analysis...")
        ee_result = rt_analyzer._run_enhanced_earth_engine_analysis(mock_zone)
        
        if ee_result.get('error'):
            print(f"   ❌ Error: {ee_result['error']}")
        else:
            print("   ✅ Enhanced analysis completed")
            
            # Check population data
            if 'estimated_population' in ee_result:
                print(f"   👥 Population: {ee_result['estimated_population']:,.0f}")
                print(f"   📊 Density: {ee_result.get('population_density', 0):.1f} per km²")
                print(f"   🔄 Source: {ee_result.get('population_source', 'Unknown')}")
            
            # Check GHSL specific data
            ghsl_data = ee_result.get('ghsl_population', {})
            if ghsl_data and not ghsl_data.get('error'):
                print(f"   🎯 GHSL Data Available: Yes")
            else:
                print(f"   🎯 GHSL Data Available: No")
                
    except Exception as e:
        print(f"   ❌ Real-time analyzer test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ GHSL Integration Test Completed")
    print("   Next step: Create a zone in the web app to see live results!")

if __name__ == "__main__":
    test_ghsl_integration()
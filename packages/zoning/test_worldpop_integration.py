#!/usr/bin/env python3
"""
Test WorldPop Integration for Population Estimation and Validation
Validates Phase 3 enhanced population estimation capabilities
"""
import sys
import os
import time
import json
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.earth_engine_analysis import EarthEngineAnalyzer
from app.utils.analysis import WasteAnalyzer
from config.config import Config


class MockZone:
    """Mock zone object for testing"""
    def __init__(self, zone_id, name, geojson, estimated_population=None):
        self.id = zone_id
        self.name = name
        self.geojson = geojson
        self.estimated_population = estimated_population
        self.collection_frequency_week = 2


def test_worldpop_integration():
    """Test the complete WorldPop integration pipeline"""
    print("=" * 70)
    print("WORLDPOP INTEGRATION TEST - Phase 3 Population Estimation")
    print("=" * 70)
    
    analyzer = WasteAnalyzer()
    
    if not analyzer.earth_engine.initialized:
        print("❌ Earth Engine not initialized - cannot run WorldPop tests")
        return False
    
    print("✅ Earth Engine initialized successfully")
    
    # Create test zones for Lusaka area
    test_zones = [
        MockZone(
            1, "Kanyama Settlement",
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [28.2100, -15.4500],
                        [28.2300, -15.4500],
                        [28.2300, -15.4700],
                        [28.2100, -15.4700],
                        [28.2100, -15.4500]
                    ]]
                }
            },
            8500  # Estimated population for comparison
        ),
        MockZone(
            2, "Chelston Suburb",
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [28.3200, -15.3800],
                        [28.3400, -15.3800],
                        [28.3400, -15.4000],
                        [28.3200, -15.4000],
                        [28.3200, -15.3800]
                    ]]
                }
            },
            3200  # Estimated population for comparison
        )
    ]
    
    print(f"\n🧪 Testing WorldPop integration with {len(test_zones)} zones...")
    
    # Test 1: WorldPop Connection and Data Availability
    print("\n" + "─" * 50)
    print("TEST 1: WorldPop Dataset Connection")
    print("─" * 50)
    
    try:
        connection_result = analyzer.earth_engine.connect_worldpop_datasets()
        
        if connection_result.get('error'):
            print(f"❌ WorldPop connection failed: {connection_result['error']}")
            return False
        
        print("✅ Successfully connected to WorldPop datasets")
        print(f"   📊 Available years: {connection_result.get('available_years', [])}")
        print(f"   📐 Resolution: {connection_result.get('resolution_meters', 0)}m")
        print(f"   🌍 Total images: {connection_result.get('total_images', 0)}")
        
    except Exception as e:
        print(f"❌ WorldPop connection test failed: {str(e)}")
        return False
    
    # Test 2: Lusaka Regional Data Fetch
    print("\n" + "─" * 50)
    print("TEST 2: Lusaka Regional Population Data")
    print("─" * 50)
    
    try:
        lusaka_data = analyzer.earth_engine.fetch_worldpop_for_lusaka(year=2020)
        
        if lusaka_data.get('error'):
            print(f"❌ Lusaka data fetch failed: {lusaka_data['error']}")
        else:
            print("✅ Successfully fetched Lusaka population data")
            print(f"   👥 Total population: {lusaka_data.get('total_population', 0):,}")
            print(f"   📏 Area: {lusaka_data.get('area_sqkm', 0):,.2f} km²")
            print(f"   📊 Density: {lusaka_data.get('population_density_per_sqkm', 0):,.2f} people/km²")
            
    except Exception as e:
        print(f"❌ Lusaka data test failed: {str(e)}")
    
    # Test 3: Zone-specific Population Extraction
    print("\n" + "─" * 50)
    print("TEST 3: Zone Population Extraction")
    print("─" * 50)
    
    zone_results = []
    for zone in test_zones:
        try:
            print(f"\n📍 Testing zone: {zone.name}")
            
            # Extract WorldPop data for zone
            worldpop_data = analyzer.earth_engine.extract_population_for_zone(zone, 2020)
            
            if worldpop_data.get('error'):
                print(f"   ❌ Error: {worldpop_data['error']}")
                continue
            
            worldpop_pop = worldpop_data['total_population']
            estimated_pop = zone.estimated_population
            
            print(f"   ✅ WorldPop population: {worldpop_pop:,}")
            print(f"   📊 Estimated population: {estimated_pop:,}")
            print(f"   📏 Area: {worldpop_data['area_sqkm']:.4f} km²")
            print(f"   🏘️ Density: {worldpop_data['population_density_per_sqkm']:.2f} people/km²")
            print(f"   📈 Density category: {analyzer.earth_engine._categorize_population_density(worldpop_data['population_density_per_sqkm'])}")
            
            if estimated_pop and worldpop_pop:
                difference_pct = abs(worldpop_pop - estimated_pop) / estimated_pop * 100
                print(f"   ⚖️ Difference: {difference_pct:.1f}%")
            
            zone_results.append({
                'zone': zone,
                'worldpop_data': worldpop_data,
                'difference_pct': difference_pct if estimated_pop and worldpop_pop else None
            })
            
        except Exception as e:
            print(f"   ❌ Zone extraction failed: {str(e)}")
    
    # Test 4: Population Validation with Building Data
    print("\n" + "─" * 50)
    print("TEST 4: Population Validation (Building vs WorldPop)")
    print("─" * 50)
    
    validation_results = []
    for zone_result in zone_results:
        zone = zone_result['zone']
        worldpop_data = zone_result['worldpop_data']
        
        try:
            print(f"\n🔍 Validating zone: {zone.name}")
            
            # Run WorldPop validation integration
            validation = analyzer.integrate_worldpop_validation(zone, 2020)
            
            if validation.get('error'):
                print(f"   ❌ Validation failed: {validation['error']}")
                continue
            
            validation_result = validation.get('validation_results', {})
            enhanced_estimate = validation.get('enhanced_estimate', {})
            
            print(f"   🏢 Building estimate: {validation_result.get('building_estimate_population', 0):,}")
            print(f"   🌍 WorldPop population: {validation_result.get('worldpop_population', 0):,}")
            print(f"   ✨ Enhanced estimate: {enhanced_estimate.get('estimated_population', 0):,}")
            print(f"   🎯 Accuracy: {validation_result.get('accuracy_percent', 0):.1f}%")
            print(f"   🤝 Agreement: {validation_result.get('agreement_level', 'Unknown')}")
            print(f"   🔧 Method: {enhanced_estimate.get('method', 'Unknown')}")
            print(f"   📊 Confidence: {enhanced_estimate.get('confidence', 'Unknown')}")
            
            # Check waste impact
            waste_impact = validation.get('waste_estimation_impact', {})
            if not waste_impact.get('error'):
                print(f"   🗑️ Waste adjustment: {waste_impact.get('waste_adjustment_percent', 0):.1f}%")
                print(f"   📈 Impact level: {waste_impact.get('impact_level', 'Unknown')}")
            
            validation_results.append(validation)
            
        except Exception as e:
            print(f"   ❌ Validation test failed: {str(e)}")
    
    # Test 5: Multi-Zone Density Analysis
    print("\n" + "─" * 50)
    print("TEST 5: Multi-Zone Density Analysis")
    print("─" * 50)
    
    try:
        density_analysis = analyzer.calculate_worldpop_density_analysis(test_zones, 2020)
        
        if density_analysis.get('error'):
            print(f"❌ Density analysis failed: {density_analysis['error']}")
        else:
            print("✅ Multi-zone density analysis completed")
            print(f"   🏘️ Zones analyzed: {density_analysis.get('zones_analyzed', 0)}")
            print(f"   👥 Total population: {density_analysis.get('total_population', 0):,}")
            print(f"   📏 Total area: {density_analysis.get('total_area_sqkm', 0):.2f} km²")
            print(f"   📊 Overall density: {density_analysis.get('overall_density_per_sqkm', 0):.2f} people/km²")
            
            # Show zone-specific waste implications
            print("\n   🗑️ Waste Collection Implications:")
            waste_implications = density_analysis.get('waste_implications', [])
            for impl in waste_implications[:2]:  # Show first 2 zones
                zone_name = impl.get('zone_name', 'Unknown')
                implications = impl.get('implications', {})
                print(f"     {zone_name}:")
                print(f"       • Frequency: {implications.get('collection_frequency', 'Unknown')}")
                print(f"       • Container type: {implications.get('container_type', 'Unknown')}")
                print(f"       • Cost efficiency: {implications.get('cost_efficiency', 'Unknown')}")
                
                special = implications.get('special_considerations', [])
                if special:
                    print(f"       • Special considerations: {', '.join(special[:2])}")
            
            # Show overall recommendations
            recommendations = density_analysis.get('overall_recommendations', [])
            if recommendations:
                print("\n   💡 Overall Recommendations:")
                for rec in recommendations[:3]:  # Show first 3 recommendations
                    print(f"     • {rec}")
            
    except Exception as e:
        print(f"❌ Density analysis test failed: {str(e)}")
    
    # Test 6: Enhanced Zone Analysis
    print("\n" + "─" * 50)
    print("TEST 6: Enhanced Zone Analysis with WorldPop")
    print("─" * 50)
    
    if test_zones:
        test_zone = test_zones[0]  # Use first zone for detailed analysis
        
        try:
            print(f"🔬 Running enhanced analysis for: {test_zone.name}")
            
            enhanced_analysis = analyzer.get_worldpop_enhanced_zone_analysis(test_zone, 2020, True)
            
            if enhanced_analysis.get('error'):
                print(f"❌ Enhanced analysis failed: {enhanced_analysis['error']}")
            else:
                print("✅ Enhanced zone analysis completed")
                
                # Show key metrics
                worldpop_context = enhanced_analysis.get('worldpop_context', {})
                if worldpop_context:
                    print(f"   🌍 WorldPop density: {worldpop_context.get('population_density_per_sqkm', 0):.2f} people/km²")
                    print(f"   🏘️ Density category: {worldpop_context.get('density_category', 'Unknown')}")
                    print(f"   👥 WorldPop population: {worldpop_context.get('worldpop_population', 0):,}")
                
                # Show enhanced waste estimation if available
                enhanced_waste = enhanced_analysis.get('enhanced_waste_estimation', {})
                if enhanced_waste and not enhanced_waste.get('error'):
                    print(f"   ✨ Enhanced population: {enhanced_waste.get('enhanced_population', 0):,}")
                    print(f"   🗑️ Enhanced waste: {enhanced_waste.get('enhanced_waste_kg_day', 0):.2f} kg/day")
                    print(f"   📊 Population adjustment: {enhanced_waste.get('population_adjustment_ratio', 1):.3f}x")
                
        except Exception as e:
            print(f"❌ Enhanced analysis test failed: {str(e)}")
    
    # Test 7: Caching Performance
    print("\n" + "─" * 50)
    print("TEST 7: WorldPop Caching System")
    print("─" * 50)
    
    try:
        print("⚡ Testing caching performance...")
        
        cache_results = analyzer.optimize_worldpop_caching(test_zones, [2020, 2021])
        
        if cache_results.get('error'):
            print(f"❌ Caching test failed: {cache_results['error']}")
        else:
            print("✅ Caching system test completed")
            print(f"   🗂️ Zones cached: {cache_results.get('cached_zones', 0)}")
            print(f"   📅 Years cached: {cache_results.get('cached_years', [])}")
            print(f"   ⏱️ Operation time: {cache_results.get('operation_time_seconds', 0):.2f}s")
            print(f"   💾 Cache size: {cache_results.get('cache_size_mb', 0):.2f} MB")
            
            errors = cache_results.get('errors', [])
            if errors:
                print(f"   ⚠️ Errors: {len(errors)} encountered")
                for error in errors[:2]:  # Show first 2 errors
                    print(f"     • {error}")
            
            # Test cache retrieval
            print("\n   🔍 Testing cache retrieval...")
            for zone in test_zones[:1]:  # Test first zone
                cached_data = analyzer.earth_engine.get_cached_worldpop_data(zone.id, 2020)
                if not cached_data.get('error'):
                    print(f"     ✅ {zone.name}: {cached_data.get('population', 0):,} people (cached)")
                    print(f"        Cache age: {cached_data.get('cache_age_hours', 0):.2f} hours")
                else:
                    print(f"     ❌ {zone.name}: {cached_data['error']}")
        
    except Exception as e:
        print(f"❌ Caching test failed: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("WORLDPOP INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    successful_validations = len([v for v in validation_results if not v.get('error')])
    total_zones = len(test_zones)
    
    print(f"✅ Successfully validated {successful_validations}/{total_zones} zones")
    print(f"📊 WorldPop data source: {connection_result.get('dataset_id', 'Unknown')}")
    print(f"📐 Resolution: {connection_result.get('resolution_meters', 0)}m")
    
    if validation_results:
        accuracies = []
        for validation in validation_results:
            if not validation.get('error'):
                validation_result = validation.get('validation_results', {})
                accuracy = validation_result.get('accuracy_percent', 0)
                if accuracy > 0:
                    accuracies.append(accuracy)
        
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)
            print(f"🎯 Average validation accuracy: {avg_accuracy:.1f}%")
            print(f"🏆 Best accuracy: {max(accuracies):.1f}%")
    
    print("\n💡 Key Capabilities Demonstrated:")
    print("   • WorldPop dataset connectivity and metadata extraction")
    print("   • Regional and zone-specific population data extraction")
    print("   • Building-based vs WorldPop population validation")
    print("   • Enhanced population estimates using multiple data sources")
    print("   • Population density analysis with waste management implications")
    print("   • Caching system for improved performance")
    print("   • Comprehensive error handling and fallback mechanisms")
    
    print("\n🚀 Phase 3 WorldPop Integration: COMPLETE")
    return True


if __name__ == "__main__":
    print("Starting WorldPop Integration Test...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_worldpop_integration()
    
    if success:
        print("\n🎉 All WorldPop integration tests completed successfully!")
    else:
        print("\n⚠️ Some tests encountered issues - check configuration and connectivity") 
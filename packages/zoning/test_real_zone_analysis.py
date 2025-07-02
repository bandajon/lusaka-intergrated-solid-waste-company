#!/usr/bin/env python3
"""
Test Real Zone Analysis to Debug Population Issues
Tests the same zone area as shown in the UI screenshot
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
import json

def test_screenshot_zone():
    """Test a zone similar to what's shown in the screenshot (3.37 km²)"""
    print("🎯 Testing Zone Analysis (Similar to Screenshot)")
    print("=" * 60)
    
    # Create a zone similar to the screenshot - 3.37 km² in Lusaka
    # Using coordinates that should have population data
    screenshot_zone_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.260, -15.430],
                [28.290, -15.430],
                [28.290, -15.400],
                [28.260, -15.400],
                [28.260, -15.430]
            ]]
        },
        "properties": {
            "name": "Screenshot Test Zone",
            "area_km2": 3.37
        }
    }
    
    print(f"📍 Zone: {screenshot_zone_geojson['properties']['name']}")
    print(f"📏 Expected Area: {screenshot_zone_geojson['properties']['area_km2']} km²")
    
    # Initialize the real-time analyzer
    try:
        analyzer = EnhancedRealTimeZoneAnalyzer()
        print("✅ Real-time analyzer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {str(e)}")
        return
    
    # Run the same analysis that happens in the UI
    try:
        print("\n🔄 Running complete zone analysis...")
        analysis_results = analyzer.analyze_drawn_zone(screenshot_zone_geojson)
        
        print("\n📊 ANALYSIS RESULTS:")
        print("=" * 40)
        
        # Check geometry analysis
        geometry = analysis_results.get('analysis_modules', {}).get('geometry', {})
        if geometry:
            print(f"📐 Calculated Area: {geometry.get('area_km2', 0):.2f} km²")
            print(f"📐 Area sqm: {geometry.get('area_sqm', 0):,.0f}")
        
        # Check population analysis
        population = analysis_results.get('analysis_modules', {}).get('population_estimation', {})
        if population:
            print(f"\n👥 POPULATION ANALYSIS:")
            consensus = population.get('consensus_estimate', 0)
            confidence = population.get('confidence_level', 'unknown')
            source = population.get('primary_source', 'unknown')
            
            print(f"   Total Population: {consensus:,} people")
            print(f"   Confidence Level: {confidence}")
            print(f"   Primary Source: {source}")
            
            # Show estimation methods used
            methods = population.get('estimation_methods', {})
            print(f"\n   📋 Estimation Methods Used:")
            for method_name, method_data in methods.items():
                if isinstance(method_data, dict) and 'estimated_population' in method_data:
                    pop = method_data.get('estimated_population', 0)
                    data_source = method_data.get('data_source', 'Unknown')
                    print(f"      {method_name}: {pop:,} people (Source: {data_source})")
        
        # Check waste generation
        waste = analysis_results.get('analysis_modules', {}).get('waste_generation', {})
        if waste and not waste.get('error'):
            daily_waste = waste.get('daily_waste_kg', 0)
            weekly_waste = waste.get('weekly_waste_tonnes', 0)
            print(f"\n🗑️ WASTE GENERATION:")
            print(f"   Daily: {daily_waste:,.0f} kg")
            print(f"   Weekly: {weekly_waste:.1f} tonnes")
        
        # Check for errors
        errors = []
        offline_components = analysis_results.get('offline_components', [])
        if offline_components:
            print(f"\n⚠️ Offline Components: {offline_components}")
        
        for module_name, module_data in analysis_results.get('analysis_modules', {}).items():
            if isinstance(module_data, dict) and module_data.get('error'):
                errors.append(f"{module_name}: {module_data['error']}")
        
        if errors:
            print(f"\n❌ ERRORS FOUND:")
            for error in errors:
                print(f"   {error}")
        
        # Overall assessment
        print(f"\n📈 ZONE VIABILITY SCORE: {analysis_results.get('zone_viability_score', 0)}")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_small_zone():
    """Test a smaller zone to see if size affects results"""
    print("\n🎯 Testing Smaller Zone (1 km²)")
    print("=" * 60)
    
    small_zone_geojson = {
        "type": "Feature", 
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.275, -15.415],
                [28.285, -15.415], 
                [28.285, -15.405],
                [28.275, -15.405],
                [28.275, -15.415]
            ]]
        },
        "properties": {
            "name": "Small Test Zone",
            "expected_area_km2": 1.0
        }
    }
    
    analyzer = EnhancedRealTimeZoneAnalyzer()
    results = analyzer.analyze_drawn_zone(small_zone_geojson)
    
    population = results.get('analysis_modules', {}).get('population_estimation', {})
    if population:
        consensus = population.get('consensus_estimate', 0)
        source = population.get('primary_source', 'unknown')
        print(f"👥 Small Zone Population: {consensus:,} people (Source: {source})")
    
    return results

def main():
    """Main test function"""
    print("🧪 Real Zone Analysis Test Suite")
    print("=" * 80)
    print("Testing the same type of analysis that happens in the UI")
    
    # Test 1: Screenshot-like zone
    screenshot_results = test_screenshot_zone()
    
    # Test 2: Smaller zone for comparison
    small_results = test_small_zone()
    
    # Summary and diagnosis
    print("\n🔍 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if screenshot_results:
        pop_analysis = screenshot_results.get('analysis_modules', {}).get('population_estimation', {})
        if pop_analysis:
            consensus = pop_analysis.get('consensus_estimate', 0)
            if consensus == 0:
                print("🚨 ISSUE CONFIRMED: Population estimation returning 0")
                
                # Check what methods were tried
                methods = pop_analysis.get('estimation_methods', {})
                print("🔍 Methods attempted:")
                for method, data in methods.items():
                    print(f"   {method}: {data}")
                
                # Check error details
                if pop_analysis.get('error'):
                    print(f"❌ Error: {pop_analysis['error']}")
                    
            else:
                print(f"✅ Population estimation working: {consensus:,} people")
                print(f"📊 Using source: {pop_analysis.get('primary_source', 'unknown')}")
        else:
            print("❌ No population analysis found in results")
    else:
        print("❌ Failed to get analysis results")
    
    print("\n💡 NEXT STEPS:")
    if screenshot_results:
        pop_est = screenshot_results.get('analysis_modules', {}).get('population_estimation', {})
        if pop_est and pop_est.get('consensus_estimate', 0) > 0:
            print("   • Population estimation is working correctly")
            print("   • If you're seeing 0 in UI, check for caching or coordinate issues")
        else:
            print("   • Population estimation is failing - check Earth Engine connectivity")
            print("   • Fallback methods should activate for non-zero results")

if __name__ == "__main__":
    main()